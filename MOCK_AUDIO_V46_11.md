# PET Quest V46.11 - Full Mock Listening Audio Correction

## Corrected
- Mock A: 25 Listening items, 15 mapped recordings.
- Mock B: 25 Listening items, 15 mapped recordings.
- Mock C: 25 Listening items, 15 mapped recordings.
- Total: 75 questions covered by 45 recordings.
- Part 3 uses one shared monologue for six gaps.
- Part 4 uses one shared interview for six questions.
- Every item has `audio_id` and `audio_file`.
- Every audio file is present, decodable, 44.1 kHz mono, 128 kbps MP3.
- Full Listening practice UI is enabled for A/B/C.
- Practice mode allows unlimited repeats.
- Optional strict simulation mode limits each recording to two starts.
- Listening attempts persist through `/api/mock-attempts` with `skill=listening`.

## Evidence status
`generated_audio_ready: true` means the application has complete functional generated audio.

`studio_audio_ready: false` remains intentionally false because generated synthetic speech is not a human studio recording.

`external_academic_signoff: false` remains intentionally false because independent academic review has not been performed.

## Important content finding
The current authored Listening questions/transcripts for Mock A, B and C are duplicates of the same Listening form even though the pack titles/themes differ. V46.11 does not hide this. Audio has been generated per pack and the runtime is complete, but three academically independent Listening forms will require new authored B/C content plus review.
