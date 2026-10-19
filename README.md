# kokorosay

[![PyPI version](https://img.shields.io/pypi/v/kokorosay.svg)](https://pypi.org/project/kokorosay/)
[![Python versions](https://img.shields.io/pypi/pyversions/kokorosay.svg)](https://pypi.org/project/kokorosay/)

`kokorosay` is a fast, lightweight command-line text-to-speech (TTS) tool built on top of [Kokoro](https://github.com/hexgrad/kokoro).

Pass text as an argument or pipe it via standard input; `kokorosay` will immediately stream speech through your speakers or export it to high-quality WAV or MP3 audio files.

---

## Features

- ⚡ **Fast & Lightweight**: Built on the open-weights 82M parameter Kokoro model (`hexgrad/Kokoro-82M`).
- 🔊 **Direct Low-Latency Playback**: Streams audio chunks to your default audio device in real time as they are generated.
- 💾 **WAV & MP3 Export**: Concatenates synthesized chunks into a seamless 24 kHz audio file; parent directories are created automatically.
- 🌐 **9 Languages & 50+ Voices**: Supports English, Japanese, Mandarin Chinese, Spanish, French, Hindi, Italian, and Brazilian Portuguese.
- 🔀 **Automatic Language Detection**: The target language is derived directly from the voice name prefix (e.g. `jf_nezumi` &rarr; Japanese, `zf_xiaobei` &rarr; Mandarin, `af_heart` &rarr; American English).
- 📥 **Pipeline & Stdin Friendly**: Supports `-` as input with explicit UTF-8 and BOM decoding, ideal for shell pipes and automation scripts.
- 🎛️ **Synthesis Controls**: Easily adjust speech rate multiplier (`--speed`) or provide custom segment-splitting regexes (`--split-pattern`).
- 🛡️ **Clean CLI & Standard Exit Codes**: Suppresses third-party noise, outputs errors to `stderr`, and adheres to standard exit codes (`0`, `1`, `2`, `130`).

---

## Installation

`kokorosay` requires **Python 3.14+**.

### Recommended: Using [uv](https://docs.astral.sh/uv/)

Install `kokorosay` as a globally isolated command-line tool:

```sh
uv tool install kokorosay
```

### Alternative: Using [pipx](https://github.com/pypa/pipx) or pip

```sh
# Using pipx
pipx install kokorosay

# Using standard pip (inside an active virtual environment)
pip install kokorosay
```

### System Prerequisites (Linux only)

On Windows and macOS, audio dependencies are bundled automatically. On Linux systems, `portaudio` might be needed for direct speaker playback:

```sh
# Debian / Ubuntu
sudo apt-get install libportaudio2
```

---

## Setup

Before first use, run the one-time dictionary setup:

```sh
kokorosay --setup
```

- **Japanese UniDic**: `kokorosay --setup` downloads the full UniDic dictionary required for Japanese G2P (grapheme-to-phoneme) processing.
- **Model weights**: The Kokoro-82M model and voice weights (~330 MB) are automatically fetched from Hugging Face on your first speech synthesis and cached locally for future offline use.

---

## Quick Start & Examples

### 1. Direct Playback

Provide text in quotes to play speech instantly through the default audio device:

```sh
# Play using default voice (af_heart - American English female)
kokorosay "Hello! Kokorosay brings text to life right from your terminal."

# British English voice, slightly faster
kokorosay "Mind the gap between the train and the platform." --voice bm_george --speed 1.15
```

### 2. Exporting to Audio Files (`.wav` / `.mp3`)

Specify an output file path as the second positional argument. Only `.mp3` and `.wav` formats are supported (case-insensitive). Missing directories will be created automatically:

```sh
# Save as MP3
kokorosay "Speech saved to an MP3 file." output.mp3

# Japanese voice saved to a nested directory
kokorosay "こんにちは、世界。" audio/japanese/hello.wav --voice jf_nezumi

# Mandarin Chinese voice
kokorosay "你好，欢迎使用文本转语音工具。" out/welcome.mp3 --voice zf_xiaobei
```

### 3. Piping from Stdin (`-`)

Pass `-` as `INPUT` to read text from standard input. `kokorosay` decodes standard input as UTF-8 (and strips PowerShell's UTF-8 BOM if present):

```sh
# Pipe the output of any command
fortune | kokorosay -

# Read from a file via stdin
cat story.txt | kokorosay - story.mp3 --voice bf_emma

# In PowerShell:
Get-Content notes.txt -Raw | kokorosay - notes.wav
```

### 4. Text Starting with Hyphens (`--`)

If your input text begins with a dash or minus sign, use `--` so the argument parser does not interpret it as a flag:

```sh
kokorosay -- "-5 degrees Celsius outside today."
```

---

## CLI Reference

### Synopsis

```sh
kokorosay INPUT [OUTPUT] [OPTIONS]
kokorosay --list-voices
kokorosay --setup
```

### Arguments and Options

| Argument / Option | Default | Description |
| ----------------- | ------- | ----------- |
| `INPUT` | – | Text to synthesize. Use `-` to read UTF-8 text from stdin. |
| `OUTPUT` | – | Output audio path (`.wav` or `.mp3`). If omitted, audio plays directly. |
| `--voice NAME` | `af_heart` | Voice identifier (e.g. `jf_nezumi`, `bf_emma`). First letter sets language. |
| `--speed FLOAT` | `1.0` | Speech rate multiplier (must be a positive number). |
| `--split-pattern REGEX` | Kokoro default | Regular expression to split input text into segments. |
| `--list-voices` | – | Print all supported voices grouped by language and exit. |
| `--setup` | – | Download the UniDic dictionary for Japanese support and exit. |
| `--version` | – | Show version number and exit. |
| `-h`, `--help` | – | Show command help and exit. |

> **Note:** `--setup` and `--list-voices` are standalone modes. They cannot be combined with positional arguments (`INPUT` / `OUTPUT`) or with each other.

---

## Supported Languages & Voices

Kokoro determines the language from the **first letter** of the voice name. The **second letter** indicates voice gender (`f` for female, `m` for male).

| Prefix | Language | Example Voices |
| :---: | --- | --- |
| `a` | American English | `af_heart` (default), `af_alloy`, `af_bella`, `am_adam`, `am_michael` |
| `b` | British English | `bf_alice`, `bf_emma`, `bm_daniel`, `bm_george` |
| `e` | Spanish | `ef_dora`, `em_alex`, `em_santa` |
| `f` | French | `ff_siwis` |
| `h` | Hindi | `hf_alpha`, `hf_beta`, `hm_omega`, `hm_psi` |
| `i` | Italian | `if_sara`, `im_nicola` |
| `j` | Japanese | `jf_alpha`, `jf_gongitsune`, `jf_nezumi`, `jf_tebukuro`, `jm_kumo` |
| `p` | Brazilian Portuguese | `pf_dora`, `pm_alex`, `pm_santa` |
| `z` | Mandarin Chinese | `zf_xiaobei`, `zf_xiaoni`, `zf_xiaoxiao`, `zm_yunjian`, `zm_yunyang` |

To view the complete list of available voices grouped by language, run:

```sh
kokorosay --list-voices
```

---

## Exit Codes

| Code | Meaning |
| :---: | --- |
| `0` | **Success**: Audio played or written successfully, or `--help` / `--list-voices` completed. |
| `1` | **Runtime Failure**: Network error downloading weights, synthesis failure, missing audio device, or invalid UTF-8 bytes on stdin. |
| `2` | **Usage Error**: Missing `INPUT`, invalid argument, unknown voice name, unsupported output extension, or empty text. |
| `130` | **Interrupted**: Execution aborted by `SIGINT` (Ctrl+C). |

---

## Development

If you wish to contribute or modify `kokorosay`:

```sh
# Clone repository
git clone https://github.com/ecator/kokorosay.git
cd kokorosay

# Install runtime and dev dependencies
uv sync

# Lint and check formatting
uv run ruff check .
uv run ruff format --check .

# Run unit tests (offline, mocked Kokoro/sounddevice)
uv run pytest

# Run integration tests (requires real model weights & audio device)
uv run pytest -m integration
```

See [AGENTS.md](AGENTS.md) for full architecture specifications and coding conventions.

---

## Acknowledgments

- [Kokoro](https://github.com/hexgrad/kokoro) for the TTS model.
- [Misaki](https://github.com/hexgrad/misaki) for G2P text pre-processing.
- [UniDic](https://github.com/polm/unidic-py) for Japanese morphological analysis.
