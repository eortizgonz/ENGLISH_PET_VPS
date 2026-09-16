# PET Quest V46.14 — Speaking AI Examiner

V46.14 adds a complete automatic formative Speaking practice layer on top of V46.13.

## What it measures

For every recorded or transcribed attempt, PET Quest calculates and stores:

- fluency
- words per minute (WPM)
- long pauses
- total/max pause time
- hesitations
- restarts
- appropriate fillers
- grammar proxy
- vocabulary range
- discourse markers
- pronunciation proxy
- intelligibility proxy
- stress variation
- intonation variation
- response length
- interaction markers

## 0–5 practice rubric

The automatic practice rubric records:

- Grammar & Vocabulary: 0–5
- Discourse Management: 0–5
- Pronunciation: 0–5 automatic acoustic proxy
- Interactive Communication: 0–5 automatic interaction proxy
- Global Achievement: 0–5

Total: 0–25, converted to a 0–100 PET Quest Speaking practice percentage.

The interface always displays:

> Automatic practice evaluation; it is not equivalent to an official Cambridge grade.

## Audio and privacy

The browser records microphone audio with MediaRecorder when available. Audio playback is available immediately. To reduce child voice-data exposure, the audio blob is stored only in IndexedDB on the current device, keyed by authenticated user and attempt. The backend stores the transcript, acoustic/linguistic metrics, rubric, score and local audio key, not the voice blob itself.

When guardian consent is required, the backend rejects Speaking persistence until valid consent exists.

## Per-user persistence

Table: `speaking_attempts`

Stored fields include student_id, part, mode, transcript, duration, metrics JSON, rubric JSON, score, local audio key, timestamp and source.

The latest evidence for each Speaking part is used by `/api/my-preparation` to calculate the student's Speaking preparation percentage. Teacher/school reports also consume that value.

## Parts and interaction

The examiner presents a prompt for Parts 1–4 and can read it aloud with an English voice. Part 3 explicitly asks the learner to respond to a suggestion, propose an alternative and negotiate an agreement. Existing V41 pair-simulator functionality remains available.

## Academic honesty

The module provides 100% coverage of the requested automatic practice metrics. It does not claim official Cambridge validity. Pronunciation, stress, intonation, intelligibility, interaction and Global Achievement remain automatic proxies and should be complemented by human review when a high-stakes judgement is required.
