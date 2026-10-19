"""Command-line interface for kokorosay."""

import argparse
import contextlib
import re
import sys
import warnings
from collections.abc import Sequence
from typing import BinaryIO

from . import __version__, audio_io, setup_cmd, synth
from .voices import DEFAULT_VOICE, VoiceError, format_voice_list, resolve_lang_code

PROG = "kokorosay"

EXIT_OK = 0
EXIT_FAILURE = 1
EXIT_USAGE = 2
EXIT_INTERRUPTED = 130


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the ``kokorosay`` command."""
    parser = argparse.ArgumentParser(
        prog=PROG,
        usage=(
            f"{PROG} INPUT [OUTPUT] [OPTIONS]\n       {PROG} --list-voices\n       {PROG} --setup"
        ),
        description="Text-to-speech on the command line, powered by Kokoro.",
        epilog=(
            "The language is derived from the first letter of the voice name. "
            "Text starting with '-' can be passed after '--', e.g. "
            f'`{PROG} -- "-5 degrees"`.'
        ),
    )
    parser.add_argument(
        "input",
        nargs="?",
        metavar="INPUT",
        help="text to synthesize; use '-' to read UTF-8 text from stdin",
    )
    parser.add_argument(
        "output",
        nargs="?",
        metavar="OUTPUT",
        help="output file (.wav or .mp3); if omitted, the audio is played directly",
    )
    parser.add_argument(
        "--voice",
        default=DEFAULT_VOICE,
        metavar="NAME",
        help=f"voice name, e.g. jf_nezumi (default: {DEFAULT_VOICE})",
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=1.0,
        metavar="FLOAT",
        help="speech rate multiplier (default: 1.0)",
    )
    parser.add_argument(
        "--split-pattern",
        default=None,
        metavar="REGEX",
        help="regex used to split text into segments (default: Kokoro's own default)",
    )
    parser.add_argument(
        "--list-voices",
        action="store_true",
        help="print all supported voices grouped by language, then exit",
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="download the full UniDic dictionary (needed for Japanese), then exit",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def read_stdin_text(stream: BinaryIO | None = None) -> str:
    """Read raw bytes from stdin and decode them as UTF-8, stripping a leading BOM."""
    if stream is None:
        stream = sys.stdin.buffer
    return stream.read().decode("utf-8-sig")


def _error(message: str) -> None:
    """Print a runtime error message to stderr."""
    print(f"{PROG}: error: {message}", file=sys.stderr)


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point of the ``kokorosay`` console script. Returns the exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)
    has_positional = args.input is not None or args.output is not None

    # Standalone modes.
    if args.setup:
        if args.list_voices:
            parser.error("--setup cannot be combined with --list-voices")
        if has_positional:
            parser.error("--setup cannot be combined with INPUT/OUTPUT")
        return setup_cmd.run_setup()

    if args.list_voices:
        if has_positional:
            parser.error("--list-voices cannot be combined with INPUT/OUTPUT")
        sys.stdout.write(format_voice_list())
        return EXIT_OK

    # Validate everything before loading the model.
    if args.input is None:
        parser.error("the following arguments are required: INPUT")

    try:
        resolve_lang_code(args.voice)
    except VoiceError as exc:
        parser.error(f"{exc} Run '{PROG} --list-voices' to see available voices.")

    if not args.speed > 0:
        parser.error(f"--speed must be a positive number, got {args.speed}")

    if args.split_pattern is not None:
        try:
            re.compile(args.split_pattern)
        except re.error as exc:
            parser.error(f"invalid --split-pattern {args.split_pattern!r}: {exc}")

    output_path = None
    if args.output is not None:
        try:
            output_path = audio_io.validate_output_path(args.output)
        except audio_io.OutputFormatError as exc:
            parser.error(str(exc))

    if args.input == "-":
        try:
            text = read_stdin_text()
        except UnicodeDecodeError as exc:
            _error(f"stdin is not valid UTF-8: {exc}")
            return EXIT_FAILURE
    else:
        text = args.input

    if not text.strip():
        parser.error("input text is empty")

    try:
        # Third-party libraries occasionally print to stdout; keep stdout clean.
        # torch emits internal deprecation/user warnings that are noise for CLI users.
        with contextlib.redirect_stdout(sys.stderr), warnings.catch_warnings():
            warnings.filterwarnings("ignore", module=r"torch(\..*)?$")
            chunks = synth.iter_audio(
                text,
                voice=args.voice,
                speed=args.speed,
                split_pattern=args.split_pattern,
            )
            if output_path is not None:
                audio = synth.merge_segments(chunks)
                if not audio.size:
                    _error("no audio was generated")
                    return EXIT_FAILURE
                audio_io.write_audio(output_path, audio, synth.SAMPLE_RATE)
            else:
                if not audio_io.play_chunks(chunks, synth.SAMPLE_RATE):
                    _error("no audio was generated")
                    return EXIT_FAILURE
    except KeyboardInterrupt:
        _error("interrupted")
        return EXIT_INTERRUPTED
    except Exception as exc:  # noqa: BLE001 - report any runtime failure concisely
        _error(str(exc) or type(exc).__name__)
        return EXIT_FAILURE
    return EXIT_OK
