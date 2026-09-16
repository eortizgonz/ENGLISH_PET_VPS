# PET Quest V46.12 - Full Function / User Isolation / Voice Simulation Audit

## Scope
This release was audited from V46.11 after the request to verify buttons, data-entry controls, persistence by user, visible progress and high-quality human-like voice simulation.

## UI action integrity
- 45 JavaScript layers loaded from `index.html`.
- 334 literal active/disabled buttons detected in loaded layers.
- 0 active buttons without an addressable handler (`data-*`, id-bound handler, submit or inline handler).
- 104 input/select/textarea controls detected.
- 0 editable fields without an id/name/data binding.
- All loaded JavaScript layers pass `node --check`.
- Full student E2E regression: 74/74 PASS.

This is a structural + functional regression audit. It does not claim that a human physically clicked all 334 controls on every browser/device combination; physical-device testing remains a separate release gate.

## Persistence and forms
`qa_full_persistence_v46_9.py` was re-run against V46.12 and returns 45/45 PASS. It verifies values written by forms/actions against the exact database rows and API readback, including:
- snapshots / local learning state
- courses and enrollments
- assignments
- CMS questions
- support groups and intervention runs
- academic errors and remediation attempts
- mock attempts and item responses
- guardian consent
- teacher availability
- strategy/governance goals, actions and reviews
- onboarding
- school licences
- user creation and account token
- privacy request
- profile
- learning events / analytics
- mastery
- planning scenarios
- backup/recovery verification
- preparation report and teacher report
- audit log and foreign key integrity

## User isolation
V46.12 adds per-user namespacing to in-progress Full Mock Listening state. A two-student test verifies:
- student 2 does not receive student 1 snapshot
- exact snapshot readback remains separate
- preparation report returns the authenticated user id
- preparation percentages differ according to each user's evidence
- mock attempts are tied to the correct `student_id`
- snapshot rows are separate in the DB

Result: 11/11 PASS.

## Progress visibility
The existing `/api/my-preparation` summary remains the source of truth. V46.12 additionally shows `Avance X%` in the authenticated student's top bar on every screen. The detailed home/dashboard card continues to show:
- overall PET Quest Preparation Score
- remaining percentage
- errors, corrected errors and pending errors
- correction rate
- Reading / Writing / Listening / Speaking
- per-exam scores

The score is an internal preparation indicator, not an official Cambridge English Scale score.

## Voice simulation
### Coverage
- 45 Full Mock recordings: Mock A/B/C (75 Listening questions covered).
- 15 V40.2 fidelity/practice recordings.
- Total: 60 voice-simulated MP3 files.

### Synthesis and mastering
- distinct offline synthetic profiles assigned by speaker and mock
- dialogue speaker changes rendered as different profiles
- natural inter-speaker pauses
- British-English-led voice variants
- 48 kHz mono
- 192 kbps MP3 derivative
- loudness target approx. -16 LUFS
- true peak target -1.5 dBTP
- measured file peaks approximately -1.8 to -1.7 dBFS; no clipping detected

`qa_audio_quality_v46_12.py`: 434/434 PASS.

### Important evidence label
These recordings are synthetic voice simulations. They are designed to be clearer and more varied than the previous generated set, but they are not human studio recordings. Therefore:
- `voice_simulation_ready: true`
- `studio_audio_ready: false`
- `external_academic_signoff: false`

A real human-studio release still requires recording actors, rights clearance and independent academic review.

## Final internal regression
- Startup: 9/9 PASS
- Authentication/session: 15/15 PASS
- Security: 8/8 PASS
- Student E2E: 74/74 PASS
- Full persistence/readback: 45/45 PASS
- User isolation: 11/11 PASS
- UI action integrity: PASS (334 buttons, 104 fields, 0 orphans)
- Audio quality/decoding: 434/434 PASS
- Python compilation: 106/106 PASS at audit time
- Foreign key check: PASS / no violations

## Release position
V46.12 is validated for local/QA/staging functional use with full internal generated-audio coverage. External human-audio, legal, psychometric, physical-device and academic sign-off gates remain independent evidence requirements.
