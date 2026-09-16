#!/usr/bin/env python3
import sys
import postgres_auth
try:
    postgres_auth.ensure_database_exists(); postgres_auth.init_schema()
    import postgres_content
    content=postgres_content.seed_all()
    import postgres_full_sync
    sync=postgres_full_sync.sync_once()
    h=postgres_auth.health(); ch=postgres_content.health()
    if not h.get('ok'): raise RuntimeError(h.get('error') or 'auth_health_failed')
    if not ch.get('ok'): raise RuntimeError('content_seed_incomplete:'+str(ch))
    print(f'POSTGRES READY: database="{postgres_auth.PG_DB}" host={postgres_auth.PG_HOST}:{postgres_auth.PG_PORT} user={postgres_auth.PG_USER}')
    print('Relational schema: operational + master content tables ready')
    print('Master content:', content)
    print('Academic mirror:', sync)
except Exception as exc:
    print('POSTGRES SETUP ERROR:',exc)
    print('Verifica PostgreSQL y psycopg: python -m pip install -r requirements-postgres.txt')
    sys.exit(2)
