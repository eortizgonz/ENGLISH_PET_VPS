#!/usr/bin/env python3
"""PostgreSQL-only database/auth helpers for PET Quest.

The public.users table is the single source of truth for identity and credentials.
The legacy public.pet_users table is not used by this module.
"""
import os
import re
from pathlib import Path

PG_HOST = os.environ.get('PETQUEST_PG_HOST', 'localhost')
PG_PORT = int(os.environ.get('PETQUEST_PG_PORT', '5432'))
PG_DB = os.environ.get('PETQUEST_PG_DB', 'PET')
PG_USER = os.environ.get('PETQUEST_PG_USER', 'postgres')
PG_PASSWORD = os.environ.get('PETQUEST_PG_PASSWORD', '12345')


def _psycopg():
    try:
        import psycopg
        return psycopg
    except Exception as exc:
        raise RuntimeError('psycopg_not_installed') from exc


def connect(dbname=None, autocommit=False):
    psycopg = _psycopg()
    return psycopg.connect(
        host=PG_HOST,
        port=PG_PORT,
        dbname=dbname or PG_DB,
        user=PG_USER,
        password=PG_PASSWORD,
        autocommit=autocommit,
    )


def ensure_database_exists():
    with connect('postgres', autocommit=True) as c:
        with c.cursor() as cur:
            cur.execute('SELECT 1 FROM pg_database WHERE datname=%s', (PG_DB,))
            if not cur.fetchone():
                safe_name = PG_DB.replace('"', '""')
                cur.execute(f'CREATE DATABASE "{safe_name}" ENCODING \'UTF8\' TEMPLATE template0')
    return True


def init_schema():
    schema_path = Path(__file__).with_name('postgres_full_schema.sql')
    sql = schema_path.read_text(encoding='utf-8')
    with connect() as c:
        with c.cursor() as cur:
            cur.execute(sql)
        c.commit()
    return True


def health():
    try:
        with connect() as c:
            with c.cursor() as cur:
                cur.execute('SELECT current_database(), current_user, COUNT(*) FROM public.users')
                db, user, count = cur.fetchone()
        return {'ok': True, 'database': db, 'user': user, 'registered_users': int(count), 'identity_table': 'users'}
    except Exception as exc:
        return {'ok': False, 'database': PG_DB, 'user': PG_USER, 'error': str(exc)[:240]}


def find_identity(identifier):
    ident = str(identifier or '').strip().lower()
    if not ident:
        return None
    with connect() as c:
        with c.cursor() as cur:
            cur.execute('''SELECT id,id AS local_user_id,username,email,password_hash,name AS display_name,
                                  role,profile_mode,disabled,created_at,last_login_at
                           FROM public.users
                           WHERE lower(username)=%s OR lower(email)=%s
                           LIMIT 1''', (ident, ident))
            row = cur.fetchone()
    if not row:
        return None
    keys = ['id','local_user_id','username','email','password_hash','display_name','role','profile_mode','disabled','created_at','last_login_at']
    return dict(zip(keys, row))


def identity_exists(username, email):
    with connect() as c:
        with c.cursor() as cur:
            cur.execute('''SELECT username,email FROM public.users
                           WHERE lower(username)=lower(%s) OR lower(email)=lower(%s)
                           LIMIT 1''', (username, email))
            row = cur.fetchone()
    return None if not row else {'username': row[0], 'email': row[1]}


def create_identity(local_user_id, username, email, password_hash, display_name, role='student', profile_mode='schools'):
    """Compatibility helper for older maintenance scripts; public.users remains authoritative."""
    with connect() as c:
        with c.cursor() as cur:
            cur.execute('''INSERT INTO public.users(id,username,email,password_hash,name,role,profile_mode,created_at)
                           VALUES(%s,%s,%s,%s,%s,%s,%s,CURRENT_TIMESTAMP::text)
                           ON CONFLICT(id) DO UPDATE SET username=EXCLUDED.username,email=EXCLUDED.email,
                             password_hash=EXCLUDED.password_hash,name=EXCLUDED.name,role=EXCLUDED.role,
                             profile_mode=EXCLUDED.profile_mode
                           RETURNING id,created_at''',
                        (int(local_user_id), username, email, password_hash, display_name, role, profile_mode))
            row = cur.fetchone()
        c.commit()
    return {'id': int(row[0]), 'created_at': row[1].isoformat() if hasattr(row[1], 'isoformat') else str(row[1])}


def update_last_login(identity_id):
    with connect() as c:
        with c.cursor() as cur:
            cur.execute('UPDATE public.users SET last_login_at=CURRENT_TIMESTAMP::text WHERE id=%s', (int(identity_id),))
        c.commit()


def update_local_user_id(identity_id, local_user_id):
    if int(identity_id) != int(local_user_id):
        raise RuntimeError('postgres_only_identity_id_is_user_id')
    return True


def delete_identity_by_local_user(local_user_id):
    with connect() as c:
        with c.cursor() as cur:
            cur.execute('UPDATE public.users SET disabled=1 WHERE id=%s', (int(local_user_id),))
        c.commit()


def update_password_by_local_user(local_user_id, password_hash):
    with connect() as c:
        with c.cursor() as cur:
            cur.execute('UPDATE public.users SET password_hash=%s WHERE id=%s', (password_hash, int(local_user_id)))
            if cur.rowcount != 1:
                raise RuntimeError('postgres_identity_not_found')
        c.commit()
    return True


def username_valid(value):
    return bool(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{2,31}', str(value or '').strip()))
