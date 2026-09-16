# PET Quest V46 — Production Release Contract

Commercial approval requires exactly:

- ACADEMIC = PASS
- DATABASE = PASS
- SECURITY = PASS
- MULTI-TENANT = PASS
- PRIVACY = PASS
- EMAIL = PASS
- AUDIO = PASS
- BACKUP/RESTORE = PASS
- DEVICE MATRIX = PASS
- LOAD TEST = PASS
- PENTEST = PASS
- PILOT = PASS
- CRITICAL ISSUES = 0
- HIGH ISSUES = 0

Only then may `COMMERCIAL_RELEASE` change from `BLOCKED` to `APPROVED`.

`DATABASE` includes the production-backend/PostgreSQL runtime subcontrols. `PRIVACY` includes legal/child-data review evidence. HTTPS/demo-data/CORS/CSP/session hardening are security subcontrols rather than extra public gates.
