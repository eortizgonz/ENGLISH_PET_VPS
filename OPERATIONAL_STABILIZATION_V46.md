# V46 — Operational Stabilization

No new learning/admin feature modules are added in V46. The purpose is operational stability and release governance.

## Release rule
Commercial approval is possible only when all 12 required gates are PASS and both critical/high issue counts are zero.

## Evidence policy
A UI click or environment variable cannot turn an external requirement into PASS. Dated evidence artifacts are required for academic review, email delivery, off-site backup/restore, device matrix, load testing, pentest, legal/privacy review, and pilot evidence.

## Architecture blockers
Production remains blocked until the application actually runs its data layer on PostgreSQL and its production API runtime on FastAPI/Gunicorn-Uvicorn. Merely having a schema file, dependency, or DATABASE_URL is not sufficient.
