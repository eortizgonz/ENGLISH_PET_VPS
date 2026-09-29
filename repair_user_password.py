#!/usr/bin/env python3
"""PET Quest V46.30 credential repair utility.

Repairs a single user in PostgreSQL public.users, the single source of truth.
The password is entered interactively and is never printed or stored in plaintext.
"""
import getpass, hashlib, secrets, re, sys
from pathlib import Path
import postgres_auth

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
        print('ERROR: usuario no existe en PostgreSQL users'); return 3
    pw1=getpass.getpass('Nueva contraseña: ')
    pw2=getpass.getpass('Repetir nueva contraseña: ')
    if pw1!=pw2:
        print('ERROR: las contraseñas no coinciden'); return 4
    if not strong(pw1):
        print('ERROR: use mínimo 10 caracteres, mayúscula, minúscula y número'); return 5
    new_hash=hash_pw(pw1)
    postgres_auth.update_password_by_local_user(pg['id'],new_hash)
    with postgres_auth.connect() as c:
        with c.cursor() as cur:
            cur.execute('DELETE FROM public.sessions WHERE user_id=%s',(int(pg['id']),))
            cur.execute('DELETE FROM public.login_attempts WHERE lower(email) IN (%s,%s)',(str(pg.get('email') or '').lower(),str(pg.get('username') or '').lower()))
        c.commit()
    print('OK: contraseña actualizada en PostgreSQL public.users. Inicie sesión nuevamente.')
    return 0

if __name__=='__main__':
    try: raise SystemExit(main())
    except Exception as exc:
        print('ERROR:',exc); raise SystemExit(1)
