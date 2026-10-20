# AGENTS.md

Guidelines for AI agents and contributors working on **kokorosay**, a command-line
text-to-speech tool built on top of [Kokoro](https://github.com/hexgrad/kokoro).

## Language Policy

- **Conversation**: Reply to the user in the same language the user writes in.
- **Artifacts**: Everything committed to the repository MUST be in English:
  code comments, docstrings, identifiers, log/error messages, CLI help text,
  commit messages, `README.md`, and any other documentation.

## Keeping This Document in Sync

- This file is the source of truth for the project's specification.
- Any code change that adds, removes, or alters behavior covered here (CLI
  arguments, options, subcommands, defaults, exit codes, supported formats,
  module layout, dependencies, tooling, testing requirements, etc.) MUST update
  `AGENTS.md` **in the same change**.
- A task is not considered done while the code and `AGENTS.md` disagree.

## Tooling

| Purpose            | Tool                          |
| ------------------ | ----------------------------- |
| Package / env mgmt | [uv](https://docs.astral.sh/uv/) (`uv.lock` is committed) |
| Lint + format      | [ruff](https://docs.astral.sh/ruff/) |
| Tests              | [pytest](https://docs.pytest.org/) |
| Build backend      | hatchling + hatch-vcs (version derived from git tags) |
| Python             | `>=3.14` (see `.python-version`) |

Common commands:

```sh
uv sync                     # install runtime + dev dependencies
uv add <pkg>                # add a runtime dependency
uv add --dev <pkg>          # add a dev dependency
uv run ruff check .         # lint
uv run ruff check --fix .   # lint with autofix
uv run ruff format .        # format
uv run pytest               # run tests
uv run kokorosay --help     # run the CLI from source
```

Rules:

- Never edit `uv.lock` by hand; always go through `uv add` / `uv remove` / `uv lock`.
- Do not use `pip install` directly in this project.
- Code must pass `ruff check` and `ruff format --check` before a task is considered done.
- All tests must pass before a task is considered done.

## Project Layout (src layout)

```
kokorosay/
├── AGENTS.md
├── README.md
├── pyproject.toml
├── uv.lock
├── examples/            # pre-generated sample MP3s for all voices & generator script
├── src/
│   └── kokorosay/
│       ├── __init__.py
│       ├── __main__.py      # enables `python -m kokorosay`
│       ├── cli.py           # argument parsing and entry point `main()`
│       ├── setup_cmd.py     # `--setup`: UniDic dictionary download
│       ├── voices.py        # voice catalog, language-code mapping
│       ├── synth.py         # Kokoro pipeline wrapper, segment merging
│       ├── audio_io.py      # writing WAV/MP3, playback
│       └── py.typed
└── tests/
    ├── conftest.py          # fake kokoro / sounddevice / stdin fixtures
    └── test_*.py
```

- The console script is registered in `pyproject.toml` as
  `kokorosay = "kokorosay.cli:main"`.
- Keep modules small and focused; the module list above is a guideline, not a contract.
- Inside the package, reference sibling modules with **relative imports**
  (e.g. `from .voices import resolve_lang_code`, `from . import audio_io`),
  never `from kokorosay.xxx import ...`. Tests (outside the package) import via
  the absolute package name `kokorosay`.

## CLI Specification

```
kokorosay INPUT [OUTPUT] [OPTIONS]
kokorosay --list-voices
kokorosay --setup
```

### `--setup` option

`kokorosay --setup` downloads the full UniDic dictionary required by the
Japanese G2P backend (the `unidic` package is a runtime dependency, but its
dictionary data must be fetched separately). Implementation sketch:

```python
import subprocess
import sys

subprocess.check_call([sys.executable, "-m", "unidic", "download"])
```

- `--setup` is a standalone mode like `--list-voices`: `INPUT` is not required,
  and the program exits after the download.
- `--setup` cannot be combined with `INPUT`/`OUTPUT` or `--list-voices`; doing
  so is a usage error (exit code `2`).
- Use `sys.executable` so the download runs in the same environment kokorosay
  is installed in. Do not invoke `python`/`pip` from `PATH`.
- Progress output from the child process goes straight to the terminal. If the
  child exits non-zero (`CalledProcessError`) or cannot be started, print a
  concise error to stderr and exit with code `1`.
- Must not import `kokoro` or `torch`.

### Positional arguments

| Argument | Description |
| -------- | ----------- |
| `INPUT`  | Text to synthesize. If it is exactly `-`, read the text from stdin. |
| `OUTPUT` | Optional output file path. If omitted, the audio is played directly. |

### Options

| Option | Default | Description |
| ------ | ------- | ----------- |
| `--voice NAME` | `af_heart` | Voice name, e.g. `jf_nezumi`. The language is derived from the **first letter** of the voice name; there is no separate language option. |
| `--speed FLOAT` | `1.0` | Speech rate multiplier passed to Kokoro. |
| `--split-pattern REGEX` | `None` | Regex used to split text into segments. When not given, do **not** pass `split_pattern` so Kokoro's own default applies. |
| `--list-voices` | – | Print all supported voices grouped by language, then exit. `INPUT` is not required in this mode; combining it with `INPUT`/`OUTPUT` is a usage error (exit code `2`). |
| `--setup` | – | Download the full UniDic dictionary, then exit. `INPUT` is not required in this mode. See [`--setup` option](#--setup-option). |
| `--version` | – | Print the package version (from git tags via hatch-vcs), then exit. |

### Behavior requirements

1. **Stdin input (`-`)**
   - Read raw bytes from `sys.stdin.buffer` and decode as UTF-8 explicitly
     (use `utf-8-sig` so a leading BOM, common from PowerShell, is stripped).
   - Never rely on the platform default encoding; Windows consoles often use a
     non-UTF-8 code page.
   - Bytes that are not valid UTF-8 are a runtime failure (exit code `1`).
   - Text that is empty or whitespace-only (from `INPUT` or stdin) is a usage
     error (exit code `2`).
   - Text starting with `-` can be passed after `--` (argparse convention).
2. **Output file**
   - Only `.mp3` and `.wav` are supported (extension check is case-insensitive).
     Any other extension is a usage error and must be rejected **before** loading
     the model.
   - Files are written with `soundfile` (libsndfile, which supports MP3).
   - Existing files are overwritten without prompting.
   - Missing parent directories are created automatically
     (`Path.parent.mkdir(parents=True, exist_ok=True)`).
   - After a successful write, print `Wrote <OUTPUT> (<seconds> s)` to
     **stderr**, where the duration is `samples / 24000` rounded to two
     decimal places (e.g. `Wrote out.wav (3.27 s)`). Nothing is printed to
     stdout.
3. **Segment merging**
   - Kokoro yields one audio chunk per segment. When writing to a file, all chunks
     MUST be concatenated in order and written as a **single** file, regardless of
     whether `--split-pattern` was supplied.
4. **Playback (no `OUTPUT`)**
   - Play the synthesized audio on the default output device using
     `sounddevice` (PortAudio).
   - Chunks are played sequentially as they are generated to reduce latency; the
     output stream is opened when the first chunk arrives.
5. **Voice → language**
   - `lang_code = voice[0]`, passed to `KPipeline(lang_code=..., repo_id="hexgrad/Kokoro-82M")`
     (passing `repo_id` explicitly suppresses Kokoro's stdout warning).
   - An unknown voice or unsupported language prefix is a usage error with a
     helpful message (suggest `--list-voices`).
   - Other argument validation (`--speed` must be positive, `--split-pattern`
     must be a valid regex) also happens before loading the model and is a usage
     error.
6. **Exit codes**
   - `0` success, `1` runtime failure, `2` usage error (argparse convention),
     `130` interrupted with Ctrl+C.
   - Synthesis that produces no audio at all is a runtime failure.
   - Errors go to stderr; stdout is reserved for user-requested output
     (e.g. `--list-voices`). Anything third-party libraries print to stdout
     during synthesis is redirected to stderr, warnings emitted by `torch`
     are suppressed, and so are `huggingface_hub`'s symlink-cache warning
     (shown on Windows without Developer Mode) and its "unauthenticated
     requests to the HF Hub" notice (the public model needs no `HF_TOKEN`);
     other `huggingface_hub` warnings remain visible.

### Kokoro reference

- Audio sample rate is **24000 Hz**.
- Language prefixes:

  | Prefix | Language |
  | ------ | -------- |
  | `a` | American English |
  | `b` | British English |
  | `e` | Spanish |
  | `f` | French |
  | `h` | Hindi |
  | `i` | Italian |
  | `j` | Japanese |
  | `p` | Brazilian Portuguese |
  | `z` | Mandarin Chinese |

- Basic pipeline usage:

  ```python
  from kokoro import KPipeline

  pipeline = KPipeline(lang_code="j")
  for graphemes, phonemes, audio in pipeline(text, voice="jf_nezumi", speed=1.0):
      ...
  ```

## Coding Conventions

- Target Python 3.14; use modern syntax (type hints everywhere, `pathlib.Path`,
  `from __future__ import annotations` is unnecessary).
- Public functions have English docstrings.
- Keep heavy imports (`kokoro`, `torch`) lazy, inside the functions that need them,
  so `--help`, `--list-voices`, `--setup`, and argument validation stay fast.
- Prefer the standard library (`argparse`) for CLI parsing unless a dependency is
  explicitly approved by the user.
- Do not add new runtime dependencies without the user's approval.
- Approved runtime dependencies: `kokoro`, `misaki[en,ja,ko,vi,zh]`, `unidic`
  (Japanese dictionary), `soundfile` (WAV/MP3 writing), `sounddevice`
  (playback). `numpy` comes in transitively and may be used directly.

## Testing

- Tests live in `tests/` and use pytest.
- Unit tests MUST NOT download models or require audio hardware: mock
  `KPipeline` and the playback backend. `tests/conftest.py` provides the
  `fake_kokoro`, `fake_sounddevice`, and `set_stdin` fixtures, which install fake
  `kokoro` / `sounddevice` modules into `sys.modules`.
- Tests that need the real model or a sound device are marked
  `@pytest.mark.integration` and deselected by default (`addopts` in
  `pyproject.toml`); run them with `uv run pytest -m integration`.
- Cover at least: argument parsing, stdin UTF-8 decoding (including BOM and
  non-ASCII text), output extension validation, parent directory creation,
  segment concatenation, voice-to-language mapping, `--list-voices` grouping,
  and `--setup` handling (mock `subprocess.check_call`; never actually download
  UniDic in unit tests; verify the command uses `sys.executable`, that a
  failing child results in exit code `1`, and that combining `--setup` with
  `INPUT` or `--list-voices` results in exit code `2`).
