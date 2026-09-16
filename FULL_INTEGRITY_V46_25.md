# PET Quest V46.25 — Full Integrity + Voice Technical Validation

## Scope
This release audits and hardens action bindings, user-scoped persistence, progress visibility/refresh, and audio technical integrity.

## Corrections
- Main browser snapshot is now stored under `petQuestV5_u_<user_id>` after authentication.
- Base Writing has a per-user, per-part draft key: `petquest_v4625_writing_draft_u_<user_id>_p<part>` and an explicit **Guardar borrador** action.
- The anonymous calibration save button now has an explicit ID/handler address, removing the only orphan reported by the structural UI audit.
- Student progress refreshes after local saves and server mutations and periodically while the app is visible.

## Validation evidence
- UI action inventory: 392 buttons, 122 editable fields, 0 orphan active buttons, 0 unaddressed editable fields.
- Full persistence API/table/readback regression: 45/45 PASS.
- Two-user isolation regression: 11/11 PASS.
- Student E2E: 85/85 PASS.
- Startup: 10/10 PASS.
- Security: 8/8 PASS.
- Practice Bank matrix: 18/18 PASS.
- Pedagogical diagnostic: 25/25 PASS.
- Writing Mastery: 10/10 PASS.
- Speaking AI: 40/40 PASS.
- Part 3 AI Candidate: 24/24 PASS.
- Full Mock 20: 272/272 PASS.
- Error DNA UI: 35/35 PASS.
- PET Audio Bank structural regression: 28/28 PASS.
- PET Audio Bank deep audit: 500/500 SHA/MP3/spec checks + 500/500 full decodes PASS; 80-file peak sample max -1.9 dBFS.
- Legacy/fidelity voice-sim bank: 434/434 PASS.

## Audio truth boundary
The audio bank is synthetic multi-voice simulation. Technical integrity can be validated (file integrity, decode, sample rate, channel count, bitrate, peak headroom), but subjective “100% perfect human sound” and human-studio provenance cannot be truthfully certified from synthetic voices. Human recordings remain `false` where applicable.
