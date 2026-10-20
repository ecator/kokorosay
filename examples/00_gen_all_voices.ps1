[CmdletBinding()]
param (
    [Parameter()]
    [switch]
    $Force
)

$OutputDir = Resolve-Path $PSScriptRoot

$TextMap = @{
    "a" = "Hello, welcome to this text-to-speech tool."
    "b" = "Good day, welcome to this text-to-speech tool."
    "e" = "Hola, bienvenido a la herramienta de texto a voz."
    "f" = "Bonjour, bienvenue sur cet outil de synthèse vocale."
    "h" = "नमस्ते, टेक्स्ट-टू-स्पीच टूल में आपका स्वागत है।"
    "i" = "Ciao, benvenuto nello strumento di sintesi vocale."
    "j" = "こんにちは、音声合成ツールへようこそ。"
    "p" = "Olá, seja bem-vindo à ferramenta de conversão de texto em fala."
    "z" = "你好，欢迎使用文本转语音工具。"
}

$Voices = @(
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
    "zm_yunyang"
)

foreach ($voice in $Voices) {
    $text = $TextMap[$voice.Substring(0, 1)]
    $target = Join-Path $OutputDir ($voice + ".mp3")
    if (!$Force -and (Test-Path $target)) {
        Write-Host -ForegroundColor DarkGray "Skipping voice ""$voice"" because ""$target"" already exists."
        continue
    }
    Write-Host -ForegroundColor Yellow "Generating ""$text"" for voice ""$voice"""
    uv run kokorosay $text $target --voice $voice
}