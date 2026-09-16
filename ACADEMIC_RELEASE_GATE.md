# PET Quest V41 Academic Release Gate

## PASS — structurally corrected

- Reading: 6 parts / 32 marks, exact distribution 5/5/5/5/6/6.
- Reading Part 6: one-word open cloze with typed answers; no multiple-choice recognition in the exact mock.
- Listening: 4 parts / 25 marks, exact distribution 7/6/6/6.
- Listening Part 3: one monologue feeding six typed gap-fill answers.
- Exact Listening mock: maximum two plays per recording.
- Exact Listening mock: packaged audio files via `Audio`, not browser `SpeechSynthesisUtterance`.
- Writing mock: 45 minutes; compulsory email + choice of article/story; no coaching while the exam is active.
- Writing formative intelligence: recurring-error records, rule/category/severity, correction, explanation, mini-lesson and corrective practice.
- Speaking practice: Cambridge-aligned human-review rubric fields retained.
- Speaking automatic transcript coach: does not claim to score pronunciation acoustically.
- Speaking Part 3 exam practice: turn-based partner simulator, not a single monologue.
- Commercial QA: deterministic readiness polling replaces fixed startup sleep.
- Active privacy lifecycle: export, rectification, deletion request/resolution and consent revocation.
- Production DB honesty: production readiness fails on SQLite when PostgreSQL is required.

## BLOCKED — external assets/validation required before claiming 100% exam fidelity

1. Replace reference MP3 files with licensed human studio recordings and pass `validate_studio_audio.py`.
2. Deploy and test a managed PostgreSQL runtime; the current application runtime remains SQLite.
3. Add a validated acoustic pronunciation engine or trained human examiner workflow for phonemes/stress/intonation/rhythm/intelligibility.
4. Validate Speaking Part 3 with live candidate-to-candidate interaction; the built-in partner is a simulator.
5. Expand and academically review the item bank beyond the included exact mock set.
6. Calibrate readiness/scoring against real learner outcomes and teacher/examiner judgements.
7. Run external legal/privacy review, penetration test and child/teacher/parent pilot.

The product must not display an unconditional “100% Cambridge fidelity” while any blocker above is open.
