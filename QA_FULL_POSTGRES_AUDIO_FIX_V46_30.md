# PET Quest V46.30 - PostgreSQL 42 Tables + Listening Audio Safety

## Database
- Required application tables detected from api_server.py: 42.
- Tables declared in postgres_full_schema.sql: 42/42.
- setup_postgres_pet.py applies the complete schema.
- postgres_check.py verifies all 42 required tables and blocks startup if any is missing.
- pet_users remains authoritative for credentials/login.
- postgres_full_sync.py mirrors the legacy V46.30 academic SQLite state into PostgreSQL every 10 seconds while the server runs.

## Listening audio
- PET Audio Bank files present: 500/500.
- Full MP3 decode check: 500/500 PASS.
- Existing technical contract: 48 kHz, mono, 160 kbps.
- Playback safety added in Audio Bank, Mock Listening and Exam Fidelity players:
  - preservesPitch enabled where supported;
  - default volume reduced to 0.85;
  - mock/fidelity playback capped at 0.90.
- Current recordings remain synthetic reference recordings; human studio replacement remains a separate academic/production gate.

## Executed checks
- Python syntax: PASS.
- JavaScript syntax: PASS.
- Full PostgreSQL table-name coverage: 42/42 PASS.
- Windows Safe Login: 27/27 PASS.
- Registration/recovery static QA: PASS.
- Audio Bank: 28/28 PASS.
- 500 audio full decode: PASS.
- 20 Full Mocks regression: 272/272 PASS.
- Practice Bank regression: 18/18 PASS.

## Live PostgreSQL gate
This build environment does not have PostgreSQL/psycopg available. Live PostgreSQL execution is therefore performed on the target Windows PC by START_PET_QUEST_POSTGRES_WINDOWS.bat. postgres_check.py verifies the 42-table schema before PET Quest opens.
