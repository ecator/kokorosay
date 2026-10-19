"""Writing audio files and playing audio on the default output device."""

from collections.abc import Iterable
from pathlib import Path

import numpy as np

#: Supported output file extensions (lower-case) mapped to libsndfile formats.
SUPPORTED_FORMATS: dict[str, str] = {
    ".wav": "WAV",
    ".mp3": "MP3",
}


class OutputFormatError(ValueError):
    """Raised when the output path has an unsupported extension."""


def validate_output_path(path: str | Path) -> Path:
    """Return ``path`` as a ``Path`` if its extension is supported.

    The extension check is case-insensitive.

    Raises:
        OutputFormatError: If the extension is not ``.wav`` or ``.mp3``.
    """
    path = Path(path)
    if path.suffix.lower() not in SUPPORTED_FORMATS:
        supported = ", ".join(SUPPORTED_FORMATS)
        shown = path.suffix or "(none)"
        raise OutputFormatError(
            f"unsupported output extension {shown!r} for {str(path)!r}; supported: {supported}."
        )
    return path


def write_audio(path: str | Path, audio: np.ndarray, sample_rate: int) -> Path:
    """Write mono ``audio`` to ``path`` as WAV or MP3, based on the extension.

    Missing parent directories are created and existing files are overwritten.
    """
    import soundfile as sf

    path = validate_output_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = np.asarray(audio, dtype=np.float32).reshape(-1)
    sf.write(path, data, sample_rate, format=SUPPORTED_FORMATS[path.suffix.lower()])
    return path


def play_chunks(chunks: Iterable[np.ndarray], sample_rate: int) -> int:
    """Play audio chunks sequentially on the default output device.

    The output stream is opened when the first chunk arrives, so playback can
    start while later segments are still being synthesized. Returns the total
    number of samples played.
    """
    import sounddevice as sd

    played = 0
    stream = None
    try:
        for chunk in chunks:
            data = np.ascontiguousarray(chunk, dtype=np.float32).reshape(-1, 1)
            if not data.size:
                continue
            if stream is None:
                stream = sd.OutputStream(samplerate=sample_rate, channels=1, dtype="float32")
                stream.start()
            stream.write(data)
            played += len(data)
        if stream is not None:
            stream.stop()  # blocks until queued audio has been played
    finally:
        if stream is not None:
            stream.close()
    return played
