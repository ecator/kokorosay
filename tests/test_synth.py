import numpy as np
import pytest

from kokorosay import synth
from kokorosay.voices import VoiceError


def test_sample_rate() -> None:
    assert synth.SAMPLE_RATE == 24000


def test_iter_audio_uses_voice_prefix_as_lang_code(fake_kokoro) -> None:
    chunks = list(synth.iter_audio("こんにちは", voice="jf_nezumi", speed=1.5))
    assert fake_kokoro.init_kwargs == [{"lang_code": "j", "repo_id": synth.REPO_ID}]
    assert fake_kokoro.call_args == [("こんにちは", {"voice": "jf_nezumi", "speed": 1.5})]
    assert [len(c) for c in chunks] == [100, 50, 25]
    assert all(c.dtype == np.float32 for c in chunks)


def test_iter_audio_omits_split_pattern_by_default(fake_kokoro) -> None:
    list(synth.iter_audio("hello", voice="af_heart"))
    _, kwargs = fake_kokoro.call_args[0]
    assert "split_pattern" not in kwargs


def test_iter_audio_passes_split_pattern(fake_kokoro) -> None:
    list(synth.iter_audio("a. b.", voice="af_heart", split_pattern=r"\.\s*"))
    _, kwargs = fake_kokoro.call_args[0]
    assert kwargs["split_pattern"] == r"\.\s*"


def test_iter_audio_skips_missing_and_empty_chunks(fake_kokoro) -> None:
    fake_kokoro.chunks = [None, np.zeros(0), np.ones(10), [0.5, 0.5]]
    chunks = list(synth.iter_audio("hello", voice="af_heart"))
    assert [len(c) for c in chunks] == [10, 2]


def test_iter_audio_rejects_unknown_voice(fake_kokoro) -> None:
    with pytest.raises(VoiceError):
        list(synth.iter_audio("hello", voice="xx_nobody"))
    assert fake_kokoro.init_kwargs == []


def test_merge_segments_concatenates_in_order() -> None:
    merged = synth.merge_segments(
        [np.full(3, 1.0), np.full(2, 2.0, dtype=np.float32), np.full(1, 3.0)]
    )
    assert merged.dtype == np.float32
    np.testing.assert_array_equal(merged, [1, 1, 1, 2, 2, 3])


def test_merge_segments_accepts_generator_and_empty() -> None:
    merged = synth.merge_segments(np.full(2, i, dtype=np.float32) for i in range(3))
    np.testing.assert_array_equal(merged, [0, 0, 1, 1, 2, 2])
    assert synth.merge_segments([]).size == 0
