# PET Quest V46.26 — Dual Profile: Adult + For Schools

## Objective
V46.26 separates the learner content universe into two explicit exam profiles while preserving the same B1 preparation architecture:

- **B1 Preliminary for Schools** — school-age contexts and child/teen learning UX.
- **B1 Preliminary – Adult** — adult everyday-life contexts and adult-facing UX.

The selected profile is stored in `data.profile.examProfile`, persisted through the authenticated snapshot flow, and also used to separate local mock/practice state.

## Adult content universe
The adult profile covers: work, travel, banking, housing, shopping, transport, appointments, technology, everyday healthcare, restaurants, relationships, community, holidays, services and employment.

## Adult Full Mock Bank
20 adult-specific Full Mocks (A–T):

- Reading: 32 per mock / **640 total**
- Listening: 25 per mock / **500 total**
- Writing: 2 per mock / **40 total**
- Speaking: 4 parts per mock / **80 total**

The adult pack identifiers are `pq-adult-a` through `pq-adult-t`. They are separate authored payloads rather than aliases of the For Schools A–T packs.

## Adult Listening audio
The adult mock bank includes **300 synthetic recordings** (15 per mock) stored under `assets/audio/adult_mock_bank/`.

Technical target: MP3, 48 kHz, mono, ~160 kbps. V46.26 QA verifies all 300 file paths and formats and performs complete decode checks on a distributed 40-file sample.

These are **synthetic voice simulations**, not human studio recordings. `human_recording=false` remains explicit.

## Adult Practice Bank
`PRACTICE_BANK_ADULT_V46_26.json` contains **3,000 adult-context activities** across:

- A2, A2+, B1-, B1, B1+, B2 bridge
- grammar, vocabulary, reading inference, gist, detail, attitude, listening distractor, spelling, sentence cohesion, phrasal verbs, prepositions, linkers, pronunciation

Every item retains the diagnostic B1 Matrix metadata used by PET Quest adaptive practice and Error DNA.

## Profile routing
Profile-aware modules include:

- Full Mock Bank (`exam_packs/index.json` vs `exam_packs/adult_index.json`)
- Practice Bank (`PRACTICE_BANK_V46_21.json` vs `PRACTICE_BANK_ADULT_V46_26.json`)
- Pedagogical diagnostic/remediation
- profile-specific local state keys
- child UX gates (disabled for Adult)

## Academic boundary
V46.26 validates the **functional separation and integrity** of the two profiles. It does not claim that the Adult and For Schools item banks are psychometrically equated forms. External academic review, pilot evidence and psychometric equivalence remain external validation gates.
