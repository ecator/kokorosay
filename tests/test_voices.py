import pytest

from kokorosay.voices import (
    DEFAULT_VOICE,
    LANGUAGES,
    VOICES,
    VoiceError,
    format_voice_list,
    resolve_lang_code,
    voices_by_language,
)


@pytest.mark.parametrize(
    ("voice", "expected"),
    [
        ("af_heart", "a"),
        ("bm_george", "b"),
        ("ef_dora", "e"),
        ("ff_siwis", "f"),
        ("hf_alpha", "h"),
        ("im_nicola", "i"),
        ("jf_nezumi", "j"),
        ("pm_alex", "p"),
        ("zf_xiaoxiao", "z"),
    ],
)
def test_resolve_lang_code(voice: str, expected: str) -> None:
    assert resolve_lang_code(voice) == expected


def test_default_voice_is_in_catalog() -> None:
    assert DEFAULT_VOICE in VOICES


def test_unknown_voice_with_valid_prefix() -> None:
    with pytest.raises(VoiceError, match="unknown voice"):
        resolve_lang_code("jf_doesnotexist")


@pytest.mark.parametrize("voice", ["kf_somebody", "xx", "Af_heart"])
def test_unsupported_language_prefix(voice: str) -> None:
    with pytest.raises(VoiceError, match="unsupported language prefix"):
        resolve_lang_code(voice)


def test_empty_voice() -> None:
    with pytest.raises(VoiceError):
        resolve_lang_code("")


def test_catalog_is_consistent() -> None:
    assert len(VOICES) == len(set(VOICES))
    for voice in VOICES:
        assert voice[0] in LANGUAGES
        assert voice[1] in "fm"
        assert voice[2] == "_"


def test_voices_by_language_groups_every_voice_once() -> None:
    groups = voices_by_language()
    assert list(groups) == [code for code in LANGUAGES if code in groups]
    assert set(groups) == set(LANGUAGES)
    flattened = [voice for names in groups.values() for voice in names]
    assert sorted(flattened) == sorted(VOICES)
    for code, names in groups.items():
        assert all(name.startswith(code) for name in names)
    assert "jf_nezumi" in groups["j"]


def test_format_voice_list() -> None:
    text = format_voice_list()
    for code, name in LANGUAGES.items():
        assert f"{name} ({code}):" in text
    for voice in VOICES:
        assert f"  {voice}\n" in text
    # Japanese voices appear under the Japanese heading, before the next heading.
    japanese = text.split("Japanese (j):", 1)[1].split("\n\n", 1)[0]
    assert "jf_nezumi" in japanese
    assert "af_heart" not in japanese
