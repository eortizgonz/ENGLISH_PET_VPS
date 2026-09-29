#!/usr/bin/env python3
from pathlib import Path
import re
root=Path(__file__).resolve().parent
schema=(root/'postgres_full_schema.sql').read_text(encoding='utf-8')
pg=set(re.findall(r'CREATE TABLE IF NOT EXISTS public\.([A-Za-z_][A-Za-z0-9_]*)',schema))
required={'users','sessions','snapshots','learning_events','mock_attempts','mock_item_responses','speaking_attempts','schools','courses','assignments'}
missing=sorted(required-pg)
print('POSTGRES DECLARED',len(pg))
print('CORE REQUIRED',len(required))
print('MISSING CORE',missing)
print('LEGACY PET_USERS PRESENT','pet_users' in pg)
assert not missing
assert 'users' in pg
assert 'pet_users' not in pg
print('POSTGRES FULL SCHEMA PASS: users-only identity')
