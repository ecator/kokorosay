"""Integration tests that use the real Kokoro model and/or a sound device.

Deselected by default; run with ``uv run pytest -m integration``.
"""

from pathlib import Path

import pytest
import soundfile as sf

from kokorosay import cli

pytestmark = pytest.mark.integration


def test_synthesize_english_to_wav(tmp_path: Path) -> None:
    target = tmp_path / "en.wav"
    assert cli.main(["Hello from kokorosay.", str(target)]) == 0
    info = sf.info(target)
    assert info.samplerate == 24000
    assert info.frames > 0


def test_synthesize_japanese_to_mp3(tmp_path: Path) -> None:
    target = tmp_path / "ja.mp3"
    assert cli.main(["こんにちは、世界。", str(target), "--voice", "jf_nezumi"]) == 0
    assert sf.info(target).frames > 0


def test_playback() -> None:
    assert cli.main(["Testing playback."]) == 0
