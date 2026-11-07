---
name: use-kokorosay
description: Use the kokorosay command-line tool to convert text to speech (play it aloud or save it as WAV/MP3) with Kokoro voices in 9 languages. Use when the user asks to read text aloud, speak something, generate narration/voice-over audio, or produce an audio file from text.
---

# Using kokorosay

`kokorosay` is a CLI text-to-speech tool built on Kokoro (82M model, 24 kHz audio).

## Synopsis

```
kokorosay INPUT [OUTPUT] [OPTIONS]
kokorosay --list-voices
kokorosay --setup
```

- `INPUT`: text to synthesize, or `-` to read from stdin.
- `OUTPUT` (optional): `.mp3` or `.wav` path. If omitted, audio is played on the default speaker.

| Option | Default | Meaning |
| ------ | ------- | ------- |
| `--voice NAME` | `af_heart` | Voice; the language comes from the **first letter** of the name. There is no language option. |
| `--speed FLOAT` | `1.0` | Speech rate multiplier (must be > 0). |
| `--split-pattern REGEX` | Kokoro default | Regex used to split text into segments. |
| `--list-voices` | – | Print all voices grouped by language, then exit (stdout). |
| `--setup` | – | One-time UniDic download for Japanese, then exit. |
| `--version` | – | Print version. |

## Choosing a voice

The voice must match the language of the text, otherwise pronunciation is wrong.

| Prefix | Language | Example voices |
| ------ | -------- | -------------- |
| `a` | American English | `af_heart`, `af_bella`, `am_adam` |
| `b` | British English | `bf_emma`, `bm_george` |
| `e` | Spanish | `ef_dora`, `em_alex` |
| `f` | French | `ff_siwis` |
| `h` | Hindi | `hf_alpha`, `hm_omega` |
| `i` | Italian | `if_sara`, `im_nicola` |
| `j` | Japanese | `jf_nezumi`, `jf_alpha`, `jm_kumo` |
| `p` | Brazilian Portuguese | `pf_dora`, `pm_alex` |
| `z` | Mandarin Chinese | `zf_xiaoxiao`, `zm_yunxi` |

Second letter is gender (`f`/`m`). Run `kokorosay --list-voices` for the full list. A single run uses one voice, so for mixed-language content run the tool once per language and produce separate files.

## Recipes

```sh
# Speak aloud with the default voice
kokorosay "Hello, world!"

# Chinese / Japanese
kokorosay --voice zf_xiaoxiao "你好，世界。"
kokorosay --voice jf_nezumi "こんにちは。"

# Save to a file (parent dirs are created, existing files are overwritten)
kokorosay "Welcome to the show." out/intro.mp3
kokorosay --voice bf_emma --speed 0.9 "Good evening." out/evening.wav

# Long or multi-line text via stdin (read as UTF-8, BOM stripped)
Get-Content -Raw -Encoding utf8 script.txt | kokorosay - out/script.mp3   # PowerShell
cat script.txt | kokorosay - out/script.mp3                                 # POSIX shell

# Text starting with "-" needs the argparse separator
kokorosay -- "-5 degrees tonight"
```

## Guidelines for the AI

1. **Prefer a file output when running non-interactively.** Without `OUTPUT` the tool plays audio and blocks until playback finishes, and it needs an audio device. Only play aloud if the user wants to hear it now; otherwise write a file and tell the user its path.
2. **Pass long or special-character text via stdin (`-`)** instead of the command line to avoid shell quoting problems.
3. **Pick the voice from the text's language** (see the table); default to `af_heart` for English.
4. **All chunks are merged into a single output file** regardless of `--split-pattern`; you normally do not need that option.
5. **Output goes to stderr:** on success `Wrote <OUTPUT> (<seconds> s)` is printed to stderr and nothing to stdout. Use that line to confirm the result.
6. The first synthesis downloads model weights (~330 MB) from Hugging Face, so it can be slow; later runs use the cache. Allow generous time for the first call.
7. Run `kokorosay --setup` once before using Japanese voices if synthesis fails with a UniDic/dictionary error.
8. If `kokorosay` is not on `PATH`, install it with `uv tool install kokorosay`.

## Exit codes

| Code | Meaning |
| ---- | ------- |
| `0` | Success |
| `1` | Runtime failure (invalid UTF-8 on stdin, no audio produced, playback/write error, `--setup` failure) |
| `2` | Usage error (empty/whitespace text, unknown voice, bad extension other than `.mp3`/`.wav`, `--speed <= 0`, invalid regex, conflicting modes) |
| `130` | Interrupted with Ctrl+C |

On exit code `2`, read the stderr message and fix the arguments (e.g. check `--list-voices`); validation happens before the model loads, so it fails fast.
