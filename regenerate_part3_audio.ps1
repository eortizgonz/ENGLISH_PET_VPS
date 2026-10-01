$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
    $speaker.SelectVoice('Microsoft Zira Desktop')
    $speaker.Rate = -1
    $speaker.Volume = 85
    $format = New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo(24000, [System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen, [System.Speech.AudioFormat.AudioChannel]::Mono)
    $target = Join-Path $PSScriptRoot 'assets/audio/fidelity/lp3_monologue_clean.wav'
    $speaker.SetOutputToWaveFile($target, $format)
    $speaker.Speak("Here is the information for Friday's school visit. Please meet at eight thirty in the school car park. The coach will leave from there shortly afterwards. Everyone should bring a light jacket. Lunch will be provided in the cafe, and we expect to return at about five fifteen.")
    $speaker.SetOutputToNull()
    Get-Item -LiteralPath $target | Select-Object Name, Length
} finally {
    $speaker.Dispose()
}
