from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from kokorosay import audio_io


@pytest.mark.parametrize("name", ["out.wav", "out.WAV", "out.mp3", "OUT.Mp3", "dir/x.wav"])
def test_validate_output_path_accepts_supported(name: str) -> None:
    assert audio_io.validate_output_path(name) == Path(name)


@pytest.mark.parametrize("name", ["out.ogg", "out.flac", "out", "out.wav.txt", "mp3"])
def test_validate_output_path_rejects_unsupported(name: str) -> None:
    with pytest.raises(audio_io.OutputFormatError, match="unsupported output extension"):
        audio_io.validate_output_path(name)


def test_write_wav_creates_parent_directories(tmp_path: Path) -> None:
    target = tmp_path / "a" / "b" / "speech.wav"
    audio = np.linspace(-0.5, 0.5, 2400, dtype=np.float32)
    audio_io.write_audio(target, audio, 24000)
    data, rate = sf.read(target, dtype="float32")
    assert rate == 24000
    assert len(data) == 2400


def test_write_overwrites_existing_file(tmp_path: Path) -> None:
    target = tmp_path / "speech.WAV"
    target.write_bytes(b"not audio")
    audio_io.write_audio(target, np.zeros(480, dtype=np.float32), 24000)
    info = sf.info(target)
    assert info.format == "WAV"
    assert info.frames == 480


@pytest.mark.skipif("MP3" not in sf.available_formats(), reason="libsndfile lacks MP3")
def test_write_mp3(tmp_path: Path) -> None:
    target = tmp_path / "nested" / "speech.mp3"
    audio_io.write_audio(target, np.zeros(24000, dtype=np.float32), 24000)
    assert sf.info(target).format == "MP3"


def test_write_rejects_unsupported_extension(tmp_path: Path) -> None:
    with pytest.raises(audio_io.OutputFormatError):
        audio_io.write_audio(tmp_path / "x.ogg", np.zeros(10), 24000)
    assert not (tmp_path / "x.ogg").exists()


def test_play_chunks_streams_sequentially(fake_sounddevice) -> None:
    chunks = [np.full(10, 0.1), np.zeros(0), np.full(5, 0.2)]
    played = audio_io.play_chunks(iter(chunks), 24000)
    assert played == 15
    assert fake_sounddevice.stream_kwargs == [
        {"samplerate": 24000, "channels": 1, "dtype": "float32"}
    ]
    assert fake_sounddevice.events == ["open", "start", "write", "write", "stop", "close"]
    assert [w.shape for w in fake_sounddevice.written] == [(10, 1), (5, 1)]
    assert all(w.dtype == np.float32 for w in fake_sounddevice.written)


def test_play_chunks_without_audio_opens_no_stream(fake_sounddevice) -> None:
    assert audio_io.play_chunks([], 24000) == 0
    assert fake_sounddevice.events == []


def test_play_chunks_closes_stream_on_error(fake_sounddevice) -> None:
    def chunks():
        yield np.ones(4)
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        audio_io.play_chunks(chunks(), 24000)
    assert fake_sounddevice.events[-1] == "close"
