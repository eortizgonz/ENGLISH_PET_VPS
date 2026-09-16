# PET Quest V45 — Production roadmap implementation matrix

Status legend: **PASS** implemented and internally verified; **IN PROGRESS** integrated control/scaffold exists but migration is incomplete; **BLOCKED EXTERNAL** requires real external evidence/service; **PENDING** not yet implemented.

| # | Requirement | V45 status | Release effect |
|---|---|---|---|
| 1 | PostgreSQL real runtime | IN PROGRESS — schema/runbook/DATABASE_URL + hard startup block; runtime still SQLite | BLOCKER |
| 2 | Production backend FastAPI + Gunicorn/Uvicorn | IN PROGRESS — target dependencies/topology added; legacy handler still runtime | BLOCKER |
| 3 | Remove demo accounts in production | PASS — `PETQUEST_SEED_DEMO_DATA=0` + startup protection | BLOCKER if violated |
| 4 | Real user creation flows | PARTIAL — school/admin flows exist; guardian/B2C workflow needs dedicated UX | BLOCKER before B2C |
| 5 | Transactional email | IN PROGRESS — SMTP provider configuration supported; real provider evidence required | BLOCKER |
| 6 | Domain + HTTPS | IN PROGRESS — Caddy/prod compose/template; real domain/TLS evidence required | BLOCKER |
| 7 | CSP + hardening | PARTIAL — headers/rate limit/request cap present; remove unsafe-inline and complete CORS/XSS review | BLOCKER |
| 8 | Multi-school security | PASS foundation — `school_id` formalized as tenant boundary; static isolation QA PASS | BLOCKER if test fails |
| 9 | Expanded roles | PASS vocabulary; fine-grained permission matrix still requires endpoint-by-endpoint review | HIGH |
| 10 | Professional human Listening audio | BLOCKED EXTERNAL | BLOCKER |
| 11 | Large question bank | IN PROGRESS — 3 full forms + governance; target scale not reached | HIGH |
| 12 | Professional question manager | PENDING full authoring UI/workflow | HIGH |
| 13 | Academic approval workflow | IN PROGRESS metadata/gates; dual external reviewer workflow pending | BLOCKER for content release |
| 14 | Deep Writing error analysis | PASS foundation; rule/model expansion ongoing | HIGH |
| 15 | Central Error Intelligence | IN PROGRESS — persisted errors/remediation; cross-skill cause engine incomplete | HIGH |
| 16 | Store Speaking audio in object storage | PENDING | BLOCKER for production Speaking evidence |
| 17 | Separate AI vs human Speaking | PASS in academic UX/rubric | HIGH |
| 18 | Speaking Part 3 real interaction | PARTIAL — AI turn simulator exists; paired student mode pending | BLOCKER for exact simulation claim |
| 19 | Granular progress by part/weakness | PARTIAL | HIGH |
| 20 | Transparent PET Readiness | PASS principle; probability remains OFF until calibration | BLOCKER for probability claim |
| 21 | Practice vs Exam mode | PASS | — |
| 22 | Correct exam timing | PASS core | — |
| 23 | Exam recovery/autosave | PARTIAL; full IndexedDB recovery needs dedicated QA | HIGH |
| 24 | PWA/offline | PASS foundation; offline answer sync expansion pending | HIGH |
| 25 | Real backups + restore | PASS internal restore drill; off-site schedule/evidence pending | BLOCKER |
| 26 | Observability | IN PROGRESS requirements documented; production metrics/alerts pending | BLOCKER |
| 27 | Unified automated QA | PASS foundation — `PETQUEST_RELEASE_GATE.py`; legacy suites retained for traceability | BLOCKER if any required gate blocked |
| 28 | DEV/STAGING/PRODUCTION separation | PASS configuration/topology foundation | BLOCKER if violated |
| 29 | Test with children | BLOCKED EXTERNAL | BLOCKER |
| 30 | 100+ academic pilot/calibration | BLOCKED EXTERNAL | BLOCKER |
| 31 | Device/browser matrix | BLOCKED EXTERNAL; template included | BLOCKER |
| 32 | Independent pentest | BLOCKED EXTERNAL | BLOCKER |
| 33 | Legal/child privacy review | BLOCKED EXTERNAL; checklist included | BLOCKER |
| 34 | Final learning cycle | PASS architecture foundation; continuous validation required | — |

## V45 release decision
`COMMERCIAL_RELEASE=BLOCKED` until every P0 blocker is proven with evidence. V45 is a production-foundation build, not the final commercial 1.0.
