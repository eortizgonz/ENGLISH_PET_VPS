#!/usr/bin/env python3
from __future__ import annotations
import os, socket, subprocess, sys, time, urllib.request, webbrowser
from pathlib import Path
ROOT=Path(__file__).resolve().parent
HOST='127.0.0.1'

def free_port(start=8080, stop=8100):
    for port in range(start, stop+1):
        s=socket.socket();
        try:
            s.bind((HOST,port)); return port
        except OSError:
            pass
        finally:
            s.close()
    raise RuntimeError('No hay puerto libre entre 8080 y 8100.')

def wait_ready(port, timeout=20):
    deadline=time.time()+timeout
    url=f'http://{HOST}:{port}/api/ready'
    while time.time()<deadline:
        try:
            with urllib.request.urlopen(url,timeout=1) as r:
                if r.status==200:return True
        except Exception:
            time.sleep(.2)
    return False

def main():
    os.chdir(ROOT)
    port=int(os.environ.get('PETQUEST_LOCAL_PORT') or free_port())
    env=os.environ.copy()
    env.update({'PETQUEST_ENV':'development','PETQUEST_DEV_MODE':'1','PETQUEST_HOST':HOST,'PORT':str(port)})
    env.setdefault('PETQUEST_SEED_DEMO_DATA','0')
    env.setdefault('PETQUEST_REQUIRE_POSTGRES_AUTH','1')
    print(f'Iniciando PET Quest V46.30 en http://{HOST}:{port} ...')
    proc=subprocess.Popen([sys.executable,'api_server.py'],cwd=ROOT,env=env)
    try:
        if not wait_ready(port):
            proc.terminate(); raise SystemExit('ERROR: el servidor no alcanzo /api/ready en 20 segundos (SQLite + PostgreSQL PET).')
        url=f'http://{HOST}:{port}'
        print('PET Quest esta operativo:',url)
        if os.environ.get('PETQUEST_NO_BROWSER')!='1': webbrowser.open(url)
        return proc.wait()
    except KeyboardInterrupt:
        print('\nCerrando PET Quest...')
        proc.terminate()
        try: proc.wait(timeout=5)
        except subprocess.TimeoutExpired: proc.kill()
        return 0
if __name__=='__main__': raise SystemExit(main())
