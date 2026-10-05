$ErrorActionPreference = 'Stop'

$outputDirectory = Join-Path $PSScriptRoot 'assets/audio/fidelity'
$tracks = [ordered]@{
    'lp1_1_clean.wav' = "Hi Ben. The football match starts at half past four, not four o'clock. Meet me outside the sports centre at quarter past four."
    'lp1_2_clean.wav' = "The art club is not in room twelve today. Please go to the library on the first floor instead."
    'lp1_3_clean.wav' = "The blue notebook costs three pounds fifty, but the green one is only two pounds ninety."
    'lp1_4_clean.wav' = "The bus leaves at twenty past eight. Please be at the stop ten minutes earlier."
    'lp1_5_clean.wav' = "We planned to meet outside the cinema, but it is raining, so wait for me inside the cafe next door."
    'lp1_6_clean.wav' = "There are fourteen students in my art class and sixteen in the music class."
    'lp1_7_clean.wav' = "I forgot my water bottle, but I remembered my lunch box and my blue cap."
    'lp2_1_clean.wav' = "I thought the film would be scary, but it was actually very funny. My sister loved it too, especially the ending."
    'lp2_2_clean.wav' = "I usually walk to school, but today my dad drove me because the rain was really heavy."
    'lp2_3_clean.wav' = "We chose the earlier train because the later one arrives after the museum closes."
    'lp2_4_clean.wav' = "The book started slowly, but after chapter three I could not stop reading."
    'lp2_5_clean.wav' = "I was nervous about performing, yet once the music began I forgot about the audience and really enjoyed it."
    'lp2_6_clean.wav' = "I keep a small notebook beside my bed so I can write down new story ideas before I forget them."
    'lp4_interview_clean.wav' = "Interviewer: Olivia, why did you first start volunteering at the community garden? Olivia: A friend invited me. I liked the idea, so I went with her. Interviewer: What was difficult at first? Olivia: Remembering all the plant names was difficult. I learned to use the tools safely quite quickly. Interviewer: What do you enjoy most now? Olivia: Working with different people. Everyone brings a different idea. Interviewer: Has the garden changed recently? Olivia: Yes. We now run activities for younger children on Saturday mornings. Interviewer: What happens when the weather is bad? Olivia: We still work, although bad weather sometimes makes the jobs harder. Interviewer: What would you like to do next? Olivia: I would like to design a new area of the garden."
}

$speaker = New-Object -ComObject SAPI.SpVoice
try {
    $voiceName = 'Microsoft Zira Desktop'
    $selectedVoice = $speaker.GetVoices() | Where-Object { $_.GetDescription() -like "$voiceName*" } | Select-Object -First 1
    if (-not $selectedVoice) { throw "No se encontró la voz $voiceName" }
    $speaker.Voice = $selectedVoice
    $speaker.Rate = -1
    $speaker.Volume = 85
    foreach ($track in $tracks.GetEnumerator()) {
        $target = Join-Path $outputDirectory $track.Key
        $stream = New-Object -ComObject SAPI.SpFileStream
        $format = New-Object -ComObject SAPI.SpAudioFormat
        $format.Type = 26 # SAFT24kHz16BitMono
        $stream.Format = $format
        try {
            $stream.Open($target, 3, $false) # SSFMCreateForWrite
            $speaker.AudioOutputStream = $stream
            [void]$speaker.Speak($track.Value)
        } finally {
            $stream.Close()
            [void][Runtime.InteropServices.Marshal]::ReleaseComObject($format)
            [void][Runtime.InteropServices.Marshal]::ReleaseComObject($stream)
        }
        Get-Item -LiteralPath $target | Select-Object Name, Length
    }
} finally {
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($speaker)
}

$metadata = [ordered]@{
    version = '46.37'
    engine = 'Windows System.Speech'
    voice = $voiceName
    synthetic = $true
    human_recording = $false
    sample_rate_hz = 24000
    bits_per_sample = 16
    channels = 1
    files = @($tracks.Keys)
    transcripts = $tracks
}
$metadata | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $outputDirectory 'fidelity_clean_audio.json') -Encoding UTF8
