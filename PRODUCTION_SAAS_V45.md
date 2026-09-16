# PET Quest V45 — Production SaaS Foundation

This release integrates the production-readiness roadmap into executable controls. It is intentionally **release-blocked** until external and infrastructure requirements are proven.

## Implemented now
- Production startup guard: refuses DEV mode, demo seeding, non-HTTPS, missing SMTP, and SQLite runtime.
- Demo accounts are development/test only (`PETQUEST_SEED_DEMO_DATA`).
- Tenant boundary is formalized as `school_id`/`tenant_id`; backend resources must validate tenant ownership.
- Expanded role vocabulary: Student, Guardian, Teacher, School Admin, Platform Support, Platform Admin (`admin` legacy), Academic Reviewer, Content Author.
- Request-size limit and strict CORS configuration surface.
- Production environment template and Docker Compose topology for PostgreSQL, Redis and Caddy.
- Unified release gate (`PETQUEST_RELEASE_GATE.py`).
- Backup/restore drill and tenant-isolation QA scripts.

## Deliberately BLOCKED
- The current runtime data access layer still executes SQLite. A PostgreSQL URL/schema exists, but that is not equivalent to a migrated runtime. Therefore production startup is blocked until `DATABASE_ENGINE=postgres` is implemented and verified across every module.
- FastAPI/Gunicorn is documented as target architecture; the legacy HTTP handler remains development runtime. Production backend migration is therefore BLOCKED.
- Human studio audio, independent pentest, legal review, device matrix and real pilots require external evidence.

## Release principle
No configuration flag may convert missing external evidence into PASS. The release gate consumes evidence files/results and otherwise returns BLOCKED.
