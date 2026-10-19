"""Thin wrapper around the Kokoro pipeline."""

from collections.abc import Iterable, Iterator
from typing import Any

import numpy as np

from .voices import resolve_lang_code

#: Sample rate of the audio produced by Kokoro.
SAMPLE_RATE = 24000

#: Hugging Face repository holding the Kokoro model and voices.
REPO_ID = "hexgrad/Kokoro-82M"


def _to_numpy(audio: Any) -> np.ndarray:
    """Convert a Kokoro audio chunk (torch tensor or array-like) to a 1-D float32 array."""
    if hasattr(audio, "detach"):
        audio = audio.detach().cpu().numpy()
    return np.asarray(audio, dtype=np.float32).reshape(-1)


def iter_audio(
    text: str,
    voice: str,
    speed: float = 1.0,
    split_pattern: str | None = None,
) -> Iterator[np.ndarray]:
    """Synthesize ``text`` and yield one float32 audio chunk per segment.

    The language is derived from the first letter of ``voice``. When
    ``split_pattern`` is ``None`` it is not passed to Kokoro, so Kokoro's own
    default applies.
    """
    lang_code = resolve_lang_code(voice)

    from kokoro import KPipeline  # heavy import (torch), keep lazy

    pipeline = KPipeline(lang_code=lang_code, repo_id=REPO_ID)
    kwargs: dict[str, Any] = {"voice": voice, "speed": speed}
    if split_pattern is not None:
        kwargs["split_pattern"] = split_pattern

    for _graphemes, _phonemes, audio in pipeline(text, **kwargs):
        if audio is None:
            continue
        chunk = _to_numpy(audio)
        if chunk.size:
            yield chunk


def merge_segments(chunks: Iterable[np.ndarray]) -> np.ndarray:
    """Concatenate audio chunks in order into a single 1-D float32 array."""
    parts = [np.asarray(chunk, dtype=np.float32).reshape(-1) for chunk in chunks]
    if not parts:
        return np.zeros(0, dtype=np.float32)
    return np.concatenate(parts)
