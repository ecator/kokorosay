from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from kokorosay import cli, synth
from kokorosay.voices import VOICES


def run_usage_error(argv: list[str]) -> None:
    with pytest.raises(SystemExit) as excinfo:
        cli.main(argv)
    assert excinfo.value.code == 2


@pytest.fixture
def no_synthesis(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail the test if the model would be loaded."""

    def fail(*args, **kwargs):
        raise AssertionError("synthesis must not start")

    monkeypatch.setattr(synth, "iter_audio", fail)


# --- argument parsing -------------------------------------------------------


def test_parse_defaults() -> None:
    args = cli.build_parser().parse_args(["hello"])
    assert args.input == "hello"
    assert args.output is None
    assert args.voice == "af_heart"
    assert args.speed == 1.0
    assert args.split_pattern is None
    assert not args.list_voices
    assert not args.setup


def test_parse_all_options() -> None:
    args = cli.build_parser().parse_args(
        ["-", "out.mp3", "--voice", "jf_nezumi", "--speed", "1.25", "--split-pattern", r"\n+"]
    )
    assert args.input == "-"
    assert args.output == "out.mp3"
    assert args.voice == "jf_nezumi"
    assert args.speed == 1.25
    assert args.split_pattern == r"\n+"


def test_help_exits_0(capsys) -> None:
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["--help"])
    assert excinfo.value.code == 0
    assert "--list-voices" in capsys.readouterr().out


def test_missing_input_is_usage_error(no_synthesis, capsys) -> None:
    run_usage_error([])
    assert "INPUT" in capsys.readouterr().err


def test_invalid_speed_is_usage_error(no_synthesis) -> None:
    run_usage_error(["hello", "--speed", "fast"])
    run_usage_error(["hello", "--speed", "0"])
    run_usage_error(["hello", "--speed=-1"])


def test_invalid_split_pattern_is_usage_error(no_synthesis) -> None:
    run_usage_error(["hello", "--split-pattern", "("])


def test_empty_text_is_usage_error(no_synthesis) -> None:
    run_usage_error(["   "])


# --- voices -----------------------------------------------------------------


def test_unknown_voice_is_usage_error(no_synthesis, capsys) -> None:
    run_usage_error(["hello", "--voice", "jf_nobody"])
    assert "--list-voices" in capsys.readouterr().err


def test_unsupported_prefix_is_usage_error(no_synthesis, capsys) -> None:
    run_usage_error(["hello", "--voice", "kf_nobody"])
    assert "--list-voices" in capsys.readouterr().err


def test_list_voices_prints_grouped_catalog(no_synthesis, capsys) -> None:
    assert cli.main(["--list-voices"]) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert "American English (a):" in captured.out
    assert "Japanese (j):" in captured.out
    for voice in VOICES:
        assert voice in captured.out


def test_list_voices_with_input_is_usage_error(no_synthesis) -> None:
    run_usage_error(["--list-voices", "hello"])


# --- stdin ------------------------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (b"hello", "hello"),
        ("こんにちは、世界".encode(), "こんにちは、世界"),
        (b"\xef\xbb\xbf" + "你好".encode(), "你好"),
        (b"\xef\xbb\xbfplain", "plain"),
        ("Ça va? ¿Qué tal?".encode(), "Ça va? ¿Qué tal?"),
    ],
)
def test_read_stdin_text_decodes_utf8(set_stdin, raw: bytes, expected: str) -> None:
    set_stdin(raw)
    assert cli.read_stdin_text() == expected


def test_stdin_input_is_passed_to_pipeline(fake_kokoro, set_stdin, tmp_path: Path) -> None:
    set_stdin(b"\xef\xbb\xbf" + "今日はいい天気です。".encode())
    assert cli.main(["-", str(tmp_path / "out.wav"), "--voice", "jf_nezumi"]) == 0
    text, kwargs = fake_kokoro.call_args[0]
    assert text == "今日はいい天気です。"
    assert kwargs["voice"] == "jf_nezumi"
    assert fake_kokoro.init_kwargs[0]["lang_code"] == "j"


def test_invalid_utf8_stdin_exits_1(fake_kokoro, set_stdin, capsys) -> None:
    set_stdin(b"\xff\xfe\x00bad")
    assert cli.main(["-"]) == 1
    assert "UTF-8" in capsys.readouterr().err
    assert fake_kokoro.call_args == []


# --- output files -----------------------------------------------------------


@pytest.mark.parametrize("name", ["out.ogg", "out.flac", "out", "out.txt"])
def test_unsupported_output_extension_rejected_before_model_load(
    no_synthesis, tmp_path: Path, name: str
) -> None:
    run_usage_error(["hello", str(tmp_path / name)])
    assert not (tmp_path / name).exists()


def test_output_creates_parents_and_merges_segments(fake_kokoro, tmp_path: Path) -> None:
    target = tmp_path / "deep" / "nested" / "speech.WAV"
    assert cli.main(["hello world", str(target)]) == 0
    data, rate = sf.read(target, dtype="float32")
    assert rate == synth.SAMPLE_RATE
    assert len(data) == 100 + 50 + 25
    # Segments are concatenated in order.
    assert data[0] == pytest.approx(0.1, abs=1e-3)
    assert data[120] == pytest.approx(0.2, abs=1e-3)
    assert data[-1] == pytest.approx(0.3, abs=1e-3)


def test_output_merges_segments_with_split_pattern(fake_kokoro, tmp_path: Path) -> None:
    target = tmp_path / "speech.wav"
    assert cli.main(["a. b. c.", str(target), "--split-pattern", r"\.\s*"]) == 0
    assert fake_kokoro.call_args[0][1]["split_pattern"] == r"\.\s*"
    assert sf.info(target).frames == 175


def test_output_overwrites_existing_file(fake_kokoro, tmp_path: Path) -> None:
    target = tmp_path / "speech.wav"
    target.write_bytes(b"old content")
    assert cli.main(["hello", str(target)]) == 0
    assert sf.info(target).frames == 175


def test_output_reports_path_and_duration(fake_kokoro, tmp_path: Path, capsys) -> None:
    fake_kokoro.chunks = [np.zeros(36_000, dtype=np.float32), np.zeros(1_234, dtype=np.float32)]
    target = tmp_path / "speech.wav"
    assert cli.main(["hello", str(target)]) == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    # (36000 + 1234) / 24000 = 1.55141... -> "1.55"
    assert f"Wrote {target} (1.55 s)" in captured.err


def test_no_audio_generated_exits_1(fake_kokoro, tmp_path: Path, capsys) -> None:
    fake_kokoro.chunks = []
    assert cli.main(["hello", str(tmp_path / "x.wav")]) == 1
    assert "no audio" in capsys.readouterr().err


def test_runtime_failure_exits_1(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys) -> None:
    def broken(*args, **kwargs):
        raise RuntimeError("model download failed")
        yield  # pragma: no cover

    monkeypatch.setattr(synth, "iter_audio", broken)
    assert cli.main(["hello", str(tmp_path / "x.wav")]) == 1
    captured = capsys.readouterr()
    assert "model download failed" in captured.err
    assert captured.out == ""


def test_third_party_stdout_is_redirected_to_stderr(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys
) -> None:
    def noisy(*args, **kwargs):
        print("library chatter")
        yield np.ones(10, dtype=np.float32)

    monkeypatch.setattr(synth, "iter_audio", noisy)
    assert cli.main(["hello", str(tmp_path / "x.wav")]) == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "library chatter" in captured.err


def test_torch_warnings_are_suppressed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys
) -> None:
    import warnings

    def noisy(*args, **kwargs):
        warnings.warn_explicit("torch noise", FutureWarning, "rnn.py", 1, module="torch.nn.rnn")
        warnings.warn_explicit("keep me", UserWarning, "other.py", 1, module="misaki.ja")
        yield np.ones(10, dtype=np.float32)

    monkeypatch.setattr(synth, "iter_audio", noisy)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        assert cli.main(["hello", str(tmp_path / "x.wav")]) == 0
    messages = [str(w.message) for w in caught]
    assert "torch noise" not in messages
    assert "keep me" in messages


def test_hf_symlink_warning_is_suppressed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    import warnings

    symlink_msg = (
        "`huggingface_hub` cache-system uses symlinks by default to efficiently "
        "store duplicated files but your machine does not support them."
    )

    def noisy(*args, **kwargs):
        warnings.warn_explicit(
            symlink_msg, UserWarning, "file_download.py", 1, module="huggingface_hub.file_download"
        )
        warnings.warn_explicit(
            "other hf warning",
            UserWarning,
            "file_download.py",
            2,
            module="huggingface_hub.file_download",
        )
        yield np.ones(10, dtype=np.float32)

    monkeypatch.setattr(synth, "iter_audio", noisy)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        assert cli.main(["hello", str(tmp_path / "x.wav")]) == 0
    messages = [str(w.message) for w in caught]
    assert symlink_msg not in messages
    assert "other hf warning" in messages


def test_hf_unauthenticated_notice_is_suppressed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    import logging

    hf_logger = logging.getLogger("huggingface_hub.utils._http")
    notice = (
        "Warning: You are sending unauthenticated requests to the HF Hub. "
        "Please set a HF_TOKEN to enable higher rate limits and faster downloads."
    )

    def noisy(*args, **kwargs):
        hf_logger.warning(notice)
        hf_logger.warning("other hf server warning")
        yield np.ones(10, dtype=np.float32)

    monkeypatch.setattr(synth, "iter_audio", noisy)
    with caplog.at_level(logging.WARNING):
        assert cli.main(["hello", str(tmp_path / "x.wav")]) == 0
    messages = [r.getMessage() for r in caplog.records]
    assert notice not in messages
    assert "other hf server warning" in messages
    # The filter is scoped to synthesis and must not leak.
    assert hf_logger.filters == []


# --- playback ---------------------------------------------------------------


def test_playback_when_output_omitted(fake_kokoro, fake_sounddevice) -> None:
    assert cli.main(["hello", "--speed", "0.8"]) == 0
    assert fake_kokoro.call_args[0][1] == {"voice": "af_heart", "speed": 0.8}
    assert [len(w) for w in fake_sounddevice.written] == [100, 50, 25]
    assert fake_sounddevice.stream_kwargs[0]["samplerate"] == synth.SAMPLE_RATE


def test_playback_failure_exits_1(fake_kokoro, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    from kokorosay import audio_io

    def broken(chunks, sample_rate):
        raise OSError("no default output device")

    monkeypatch.setattr(audio_io, "play_chunks", broken)
    assert cli.main(["hello"]) == 1
    assert "no default output device" in capsys.readouterr().err
