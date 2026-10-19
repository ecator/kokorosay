"""Shared test fixtures: fake Kokoro pipeline and fake playback backend."""

import sys
import types
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pytest


class FakeTensor:
    """Mimics the subset of the torch tensor API used by kokorosay."""

    def __init__(self, data: np.ndarray) -> None:
        self._data = data

    def detach(self) -> FakeTensor:
        return self

    def cpu(self) -> FakeTensor:
        return self

    def numpy(self) -> np.ndarray:
        return self._data


@dataclass
class FakeKokoro:
    """Records how ``KPipeline`` was constructed and called."""

    chunks: list[Any] = field(
        default_factory=lambda: [
            FakeTensor(np.full(100, 0.1, dtype=np.float32)),
            FakeTensor(np.full(50, 0.2, dtype=np.float32)),
            FakeTensor(np.full(25, 0.3, dtype=np.float32)),
        ]
    )
    init_kwargs: list[dict[str, Any]] = field(default_factory=list)
    call_args: list[tuple[str, dict[str, Any]]] = field(default_factory=list)


@pytest.fixture
def fake_kokoro(monkeypatch: pytest.MonkeyPatch) -> FakeKokoro:
    """Install a fake ``kokoro`` module so no model is downloaded or loaded."""
    state = FakeKokoro()

    class KPipeline:
        def __init__(self, **kwargs: Any) -> None:
            state.init_kwargs.append(kwargs)

        def __call__(self, text: str, **kwargs: Any):
            state.call_args.append((text, kwargs))
            for chunk in state.chunks:
                yield ("graphemes", "phonemes", chunk)

    module = types.ModuleType("kokoro")
    module.KPipeline = KPipeline  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "kokoro", module)
    return state


@dataclass
class FakeSoundDevice:
    """Records audio written to fake output streams."""

    written: list[np.ndarray] = field(default_factory=list)
    stream_kwargs: list[dict[str, Any]] = field(default_factory=list)
    events: list[str] = field(default_factory=list)


@pytest.fixture
def fake_sounddevice(monkeypatch: pytest.MonkeyPatch) -> FakeSoundDevice:
    """Install a fake ``sounddevice`` module so no audio hardware is needed."""
    state = FakeSoundDevice()

    class OutputStream:
        def __init__(self, **kwargs: Any) -> None:
            state.stream_kwargs.append(kwargs)
            state.events.append("open")

        def start(self) -> None:
            state.events.append("start")

        def write(self, data: np.ndarray) -> None:
            state.written.append(np.array(data))
            state.events.append("write")

        def stop(self) -> None:
            state.events.append("stop")

        def close(self) -> None:
            state.events.append("close")

    module = types.ModuleType("sounddevice")
    module.OutputStream = OutputStream  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "sounddevice", module)
    return state


class FakeStdin:
    """Stand-in for ``sys.stdin`` exposing a binary ``buffer``."""

    def __init__(self, data: bytes) -> None:
        import io

        self.buffer = io.BytesIO(data)


@pytest.fixture
def set_stdin(monkeypatch: pytest.MonkeyPatch):
    """Return a helper that replaces ``sys.stdin`` with the given raw bytes."""

    def _set(data: bytes) -> None:
        monkeypatch.setattr(sys, "stdin", FakeStdin(data))

    return _set
