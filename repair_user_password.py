#!/usr/bin/env python3
"""PET Quest V46.30 credential repair utility.

Repairs a single linked user by writing one fresh PBKDF2-SHA256 hash to both
PostgreSQL pet_users and the local SQLite users table. The password is entered
interactively and is never printed or stored in plaintext.
"""
import getpass, hashlib, secrets, sqlite3, re, sys
from pathlib import Path
import postgres_auth

ROOT=Path(__file__).resolve().parent
DB=ROOT/'petquest.db'
PBKDF2_ITERS=310000

def strong(v):
    return len(v)>=10 and bool(re.search(r'[A-Z]',v)) and bool(re.search(r'[a-z]',v)) and bool(re.search(r'\d',v))

def hash_pw(password):
    salt=secrets.token_bytes(16)
    digest=hashlib.pbkdf2_hmac('sha256',password.encode(),salt,PBKDF2_ITERS)
    return salt.hex()+'$'+digest.hex()

def main():
    print('PET Quest - Reparar contraseña de usuario')
    ident=input('Usuario o correo: ').strip()
    if not ident:
        print('ERROR: usuario/correo requerido'); return 2
    pg=postgres_auth.find_identity(ident)
    if not pg:
        print('ERROR: usuario no existe en PostgreSQL pet_users'); return 3
    pw1=getpass.getpass('Nueva contraseña: ')
    pw2=getpass.getpass('Repetir nueva contraseña: ')
    if pw1!=pw2:
        print('ERROR: las contraseñas no coinciden'); return 4
    if not strong(pw1):
        print('ERROR: use mínimo 10 caracteres, mayúscula, minúscula y número'); return 5
    new_hash=hash_pw(pw1)
    postgres_auth.update_password_by_local_user(pg['local_user_id'],new_hash)
    with sqlite3.connect(DB) as c:
        cur=c.execute('UPDATE users SET password_hash=? WHERE id=?',(new_hash,int(pg['local_user_id'])))
        if cur.rowcount!=1:
            raise RuntimeError('sqlite_user_not_found')
        c.execute('DELETE FROM sessions WHERE user_id=?',(int(pg['local_user_id']),))
        c.execute('DELETE FROM login_attempts WHERE lower(email) IN (?,?)',(str(pg.get('email') or '').lower(),str(pg.get('username') or '').lower()))
        c.commit()
    print('OK: contraseña sincronizada en PostgreSQL y SQLite. Inicie sesión nuevamente.')
    return 0

if __name__=='__main__':
    try: raise SystemExit(main())
    except Exception as exc:
        print('ERROR:',exc); raise SystemExit(1)
