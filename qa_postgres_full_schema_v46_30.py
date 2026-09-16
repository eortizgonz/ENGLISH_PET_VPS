#!/usr/bin/env python3
from pathlib import Path
import re
root=Path(__file__).resolve().parent
api=(root/'api_server.py').read_text(encoding='utf-8')
schema=(root/'postgres_full_schema.sql').read_text(encoding='utf-8')
pairs=re.findall(r'CREATE TABLE IF NOT EXISTS\s+([A-Za-z_][A-Za-z0-9_]*)|CREATE TABLE\s+([A-Za-z_][A-Za-z0-9_]*)',api)
app={a or b for a,b in pairs}
pg=set(re.findall(r'CREATE TABLE IF NOT EXISTS public\.([A-Za-z_][A-Za-z0-9_]*)',schema))
missing=sorted(app-pg); required=app|{'pet_users'}; missing_required=sorted(required-pg); extra=sorted(pg-required)
print('SQLITE ACADEMIC TABLES',len(app)); print('POSTGRES REQUIRED',len(required)); print('POSTGRES DECLARED',len(pg)); print('MISSING REQUIRED',missing_required); print('EXTRA',extra)
assert len(app)==41 and len(required)==42 and len(pg)==42 and not missing_required and not extra
print('POSTGRES FULL SCHEMA V46.30: 42/42 PASS')
