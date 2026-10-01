#!/usr/bin/env python3
from __future__ import annotations
import os, socket, subprocess, sys, time, json, urllib.request, urllib.error, webbrowser
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
    last_error='El servidor no responde.'
    while time.time()<deadline:
        try:
            with urllib.request.urlopen(url,timeout=1) as r:
                if r.status==200:return True
        except urllib.error.HTTPError as exc:
            try:
                report=json.loads(exc.read())
                content=report.get('master_content',{})
                if not report.get('postgres_auth_ok'):
                    last_error='No se pudo conectar a PostgreSQL. Revisa su servicio y configuración.'
                elif not report.get('master_content_ok'):
                    last_error='Contenido académico incompleto en PostgreSQL. Conteos: '+str(content.get('counts',{}))
                else:
                    last_error=f'La comprobación de disponibilidad devolvió HTTP {exc.code}.'
            except (ValueError, OSError):
                last_error=f'HTTP {exc.code} al comprobar disponibilidad.'
        except (OSError, TimeoutError):
            last_error='El servidor no responde. Revisa los mensajes anteriores.'
        time.sleep(.5)
    print(last_error)
    return False

def main():
    os.chdir(ROOT)
    port=int(os.environ.get('PETQUEST_LOCAL_PORT') or free_port())
    env=os.environ.copy()
    env.update({'PETQUEST_ENV':'development','PETQUEST_HOST':HOST,'PORT':str(port)})
    env.setdefault('PETQUEST_DEV_MODE','1')
    env.setdefault('PETQUEST_PUBLIC_BASE_URL',f'http://{HOST}:{port}')
    env.setdefault('PETQUEST_SEED_DEMO_DATA','0')
    env.setdefault('PETQUEST_REQUIRE_POSTGRES_AUTH','1')
    print(f'Iniciando PET Quest en http://{HOST}:{port} ...',flush=True)
    proc=subprocess.Popen([sys.executable,'api_server.py'],cwd=ROOT,env=env)
    try:
        if not wait_ready(port):
            proc.terminate(); proc.wait(timeout=5)
            raise SystemExit('ERROR: PET Quest no completó la comprobación de disponibilidad en 20 segundos.')
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
