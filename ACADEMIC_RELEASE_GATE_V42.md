# PET Quest V42 Academic Release Gate

## PASS — code/structure
- Reading Part 6 is typed one-word open cloze in the exact mock.
- Listening Part 3 is a six-gap fill fed by one monologue; exam audio is limited to two plays.
- Writing exact mock and Speaking turn-based Part 3 simulator remain active.
- Privacy lifecycle is active in the current server.
- Fixed-sleep commercial startup QA has been replaced by readiness polling.
- Exam-pack validator enforces Reading 32 / Listening 25 and the exact interaction contract.
- Academic error events can persist by skill, part, competence, subcompetence and error code.
- PET Readiness calibration records predictions before external outcomes and keeps pass-probability publication disabled.
- PostgreSQL production requirement remains an explicit production gate.

## BLOCKED — external evidence/assets
1. Human studio Listening pack: replace reference MP3s with licensed recordings and pass `validate_studio_audio.py`.
2. Acoustic Speaking: validated pronunciation/intelligibility assessment or trained human examiner workflow.
3. Human interaction: validate Speaking Part 3 with real candidate-to-candidate sessions.
4. Item bank scale: author and independently review multiple full mock forms; `validate_exam_pack.py` validates structure, not item quality.
5. Calibration: collect real outcomes; current API deliberately returns `probability_enabled: false`.
6. Managed PostgreSQL: deploy and exercise the documented migration path in staging/production.
7. External legal/privacy review, pentest, physical-device/browser testing and child/parent/teacher pilot.

Do not market PET Quest as “100% Cambridge-equivalent” or publish a pass probability while these blockers remain open.
