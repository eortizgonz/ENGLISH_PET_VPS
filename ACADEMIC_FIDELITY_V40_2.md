# PET Quest V40.2 — Academic Fidelity Corrections

This release corrects exam-interaction mismatches identified in V40.1.

## Reading
- Part 1: 5 multiple-choice short-text items.
- Part 2: 5 matching questions against 8 candidate texts.
- Part 3: one longer text with 5 multiple-choice questions.
- Part 4: one gapped text with 5 missing sentences selected from 8 options.
- Part 5: one 6-gap multiple-choice cloze.
- Part 6: one 6-gap **open cloze**. The learner types one word for every gap; there are no answer choices.
- Total: 32 marks / 45 minutes.

Part 6 learning practice has also been changed from recognition to production. Existing learning-bank content is retained, but any Part 6 practice question is rendered as a text input and validated as one word.

## Listening
- Part 1: 7 multiple-choice recordings with schematic visual-choice cards.
- Part 2: 6 short dialogue multiple-choice recordings.
- Part 3: one monologue with **6 gap-fill answers typed by the learner**.
- Part 4: one interview with 6 multiple-choice questions.
- Total: 25 marks / approximately 30 minutes.
- Recordings are limited to two plays in exam mode.

The exam-mode player now uses packaged MP3 assets instead of browser `SpeechSynthesisUtterance`.

### Important audio-quality note
The bundled MP3s are original PET Quest **pre-recorded reference assets** produced for technical validation. They prove the application can operate with fixed audio files and multiple speakers without browser TTS. They are **not represented as studio-quality human recordings**. Before premium commercial production, replace them with professionally recorded natural voices using the same file names/manifest. No Cambridge copyrighted audio is included.

## Speaking
PET Quest keeps its automatic transcript-based coach for learning, but V40.2 adds a Cambridge-aligned **human review** with five 0–5 criteria:
- Grammar and Vocabulary
- Discourse Management
- Pronunciation
- Interactive Communication
- Global Achievement

PET Quest does not infer Pronunciation or official Speaking performance from transcription alone. A teacher/examiner of practice can listen to the recording and enter the human ratings. This separates automated learning feedback from a defensible assessment workflow.

## Source of format decisions
The interaction types are aligned to the current Cambridge B1 Preliminary for Schools exam format. PET Quest content is original and is not an official Cambridge product.


## V41 academic correction
- Reading Part 6 is open cloze (one produced word per gap).
- Listening Part 3 is a six-gap monologue task.
- Exact mock uses packaged audio files; bundled files are reference QA audio and do **not** satisfy the studio-human production gate.
- Writing includes a rule-based Error Intelligence layer with category, severity, recurrence, mini-lesson and corrective practice; it is formative, not an official Cambridge mark.
- Speaking automatic feedback no longer scores pronunciation/true interaction from text; human review uses Cambridge-aligned criteria and Part 3 has an interactive partner simulator.
- Current server includes privacy export, rectification, deletion request/resolution and consent revocation.
- Commercial QA waits on `/api/ready` instead of fixed startup sleep.
- Production readiness refuses SQLite when PostgreSQL is required.
