#!/usr/bin/env python3
import json, os, subprocess, sys, tempfile, time, urllib.request, urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PORT='18846'
APP_VERSION='46.27'

def req(base,path,method='GET',data=None):
    raw=None if data is None else json.dumps(data).encode()
    r=urllib.request.Request(base+path,data=raw,headers={'Content-Type':'application/json'},method=method)
    try:
        with urllib.request.urlopen(r,timeout=5) as x:return x.status,dict(x.headers),x.read().decode()
    except urllib.error.HTTPError as e:return e.code,dict(e.headers),e.read().decode()

def main():
    with tempfile.TemporaryDirectory() as td:
        db=Path(td)/'security.db'
        env=os.environ.copy(); env.update({'PORT':PORT,'PETQUEST_SQLITE_PATH':str(db),'PETQUEST_DEV_MODE':'1','PETQUEST_ENV':'test','PETQUEST_SEED_DEMO_DATA':'1'})
        p=subprocess.Popen([sys.executable,str(ROOT/'api_server.py')],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        base=f'http://127.0.0.1:{PORT}'
        try:
            deadline=time.time()+20
            while time.time()<deadline:
                try:
                    s,_,_=req(base,'/api/health')
                    if s==200:break
                except Exception:pass
                time.sleep(.15)
            else:raise RuntimeError('server not ready')
            checks=[]
            s,_,_=req(base,'/api/courses'); checks.append(('auth_required',s==401))
            s,_,_=req(base,'/api/login','POST',{'email':'nobody@example.invalid','password':'wrong'}); checks.append(('bad_login_rejected',s in (400,401,403,429)))
            s,h,_=req(base,'/');
            checks += [
                ('frame_denied',h.get('X-Frame-Options')=='DENY'),
                ('nosniff',h.get('X-Content-Type-Options')=='nosniff'),
                ('csp_present',bool(h.get('Content-Security-Policy'))),
                ('permissions_policy',bool(h.get('Permissions-Policy'))),
                ('referrer_policy',bool(h.get('Referrer-Policy'))),
                ('version_header',h.get('X-PETQuest-Version')==APP_VERSION)]
            failed=[n for n,ok in checks if not ok]
            print(json.dumps({'checks':checks,'failed':failed},indent=2))
            return 1 if failed else 0
        finally:
            p.terminate()
            try:p.wait(timeout=3)
            except Exception:p.kill()
if __name__=='__main__': raise SystemExit(main())
