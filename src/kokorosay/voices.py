"""Voice catalog and voice-to-language mapping for Kokoro."""

#: Kokoro language prefixes mapped to human-readable language names.
LANGUAGES: dict[str, str] = {
    "a": "American English",
    "b": "British English",
    "e": "Spanish",
    "f": "French",
    "h": "Hindi",
    "i": "Italian",
    "j": "Japanese",
    "p": "Brazilian Portuguese",
    "z": "Mandarin Chinese",
}

#: All voices shipped with Kokoro-82M v1.0. The first letter of each name is
#: the language prefix, the second letter is the gender (``f``/``m``).
VOICES: tuple[str, ...] = (
    # American English
    "af_heart",
    "af_alloy",
    "af_aoede",
    "af_bella",
    "af_jessica",
    "af_kore",
    "af_nicole",
    "af_nova",
    "af_river",
    "af_sarah",
    "af_sky",
    "am_adam",
    "am_echo",
    "am_eric",
    "am_fenrir",
    "am_liam",
    "am_michael",
    "am_onyx",
    "am_puck",
    "am_santa",
    # British English
    "bf_alice",
    "bf_emma",
    "bf_isabella",
    "bf_lily",
    "bm_daniel",
    "bm_fable",
    "bm_george",
    "bm_lewis",
    # Spanish
    "ef_dora",
    "em_alex",
    "em_santa",
    # French
    "ff_siwis",
    # Hindi
    "hf_alpha",
    "hf_beta",
    "hm_omega",
    "hm_psi",
    # Italian
    "if_sara",
    "im_nicola",
    # Japanese
    "jf_alpha",
    "jf_gongitsune",
    "jf_nezumi",
    "jf_tebukuro",
    "jm_kumo",
    # Brazilian Portuguese
    "pf_dora",
    "pm_alex",
    "pm_santa",
    # Mandarin Chinese
    "zf_xiaobei",
    "zf_xiaoni",
    "zf_xiaoxiao",
    "zf_xiaoyi",
    "zm_yunjian",
    "zm_yunxi",
    "zm_yunxia",
    "zm_yunyang",
)

DEFAULT_VOICE = "af_heart"


class VoiceError(ValueError):
    """Raised when a voice name is unknown or has an unsupported language prefix."""


def resolve_lang_code(voice: str) -> str:
    """Return the Kokoro ``lang_code`` for ``voice``.

    The language code is the first letter of the voice name.

    Raises:
        VoiceError: If the voice is not in the catalog or its prefix is not a
            supported language.
    """
    if not voice:
        raise VoiceError("voice name must not be empty.")
    lang_code = voice[0]
    if lang_code not in LANGUAGES:
        raise VoiceError(
            f"unsupported language prefix {lang_code!r} in voice {voice!r}; "
            f"supported prefixes: {', '.join(LANGUAGES)}."
        )
    if voice not in VOICES:
        raise VoiceError(f"unknown voice {voice!r}.")
    return lang_code


def voices_by_language() -> dict[str, list[str]]:
    """Group the voice catalog by language prefix, preserving ``LANGUAGES`` order."""
    groups: dict[str, list[str]] = {code: [] for code in LANGUAGES}
    for voice in VOICES:
        groups[voice[0]].append(voice)
    return {code: names for code, names in groups.items() if names}


def format_voice_list() -> str:
    """Return a human-readable listing of all voices grouped by language."""
    blocks = []
    for code, names in voices_by_language().items():
        lines = [f"{LANGUAGES[code]} ({code}):"]
        lines.extend(f"  {name}" for name in names)
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks) + "\n"
