#!/usr/bin/env python3
"""Apply postgres_schema.sql to a managed PostgreSQL target.
Requires: pip install -r requirements-postgres.txt
Set PETQUEST_DATABASE_URL before running.
"""
import os, sys
from pathlib import Path
url=os.environ.get('PETQUEST_DATABASE_URL','').strip()
if not url:
    raise SystemExit('PETQUEST_DATABASE_URL is required')
try:
    import psycopg
except ImportError:
    raise SystemExit('psycopg is not installed; run: pip install -r requirements-postgres.txt')
sql=Path(__file__).with_name('postgres_schema.sql').read_text()
with psycopg.connect(url) as conn:
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()
print('PostgreSQL schema applied successfully.')
