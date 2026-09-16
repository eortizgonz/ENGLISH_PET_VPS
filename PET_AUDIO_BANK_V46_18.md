# PET Quest V46.18 — PET Audio Bank

## Scope implemented

A new training bank of **500 original synthetic-voice recordings** has been added:

- Listening Part 1: **180 clips**
- Listening Part 2: **160 clips**
- Listening Part 3: **80 monologues**
- Listening Part 4: **80 interviews**
- Total: **500 new recordings**

The previous full-mock and fidelity audio remains in the package. The new bank is additional practice content.

## Playback modes

### Training
- 0.75×
- 0.85×
- 1.00×
- 1.10×
- unlimited replays
- transcript available for review

### Exam Mode
- fixed 1.00×
- maximum 2 plays per clip
- transcript hidden until the learner returns to Training

## Voice diversity

The bank uses 17 offline synthetic voice profiles and varied speaker-role combinations. The distribution is predominantly British English, with a smaller set of comprehensible international-English profiles for listening exposure.

This is **voice simulation**, not a recording of 500 different human speakers. Therefore `human_recording=false` remains explicit in the manifest. Human studio recording remains an external production gate.

## Audio technical target

- MP3
- 48 kHz
- mono
- target 160 kbps
- loudness target about -16 LUFS
- true-peak target about -1.5 dBTP
- high-pass / low-pass cleanup and dynamics control before final mastering

## Individual tracking

Audio-bank answers send a `learning_events` record using `event_type=audio_bank_answer` when the authenticated API is available. Local playback state is namespaced per authenticated user id.

## Academic honesty

The bank is original PET Quest practice content and is not official Cambridge material. It is designed around the PET/B1 Listening part structure but does not claim external Cambridge sign-off or human-studio equivalence.
