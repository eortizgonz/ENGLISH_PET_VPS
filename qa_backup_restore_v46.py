#!/usr/bin/env python3
import json, os, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PORT='18847'
def main():
    with tempfile.TemporaryDirectory() as td:
        db=Path(td)/'source.db'; env=os.environ.copy(); env.update({'PORT':PORT,'PETQUEST_SQLITE_PATH':str(db),'PETQUEST_DEV_MODE':'1','PETQUEST_ENV':'test','PETQUEST_SEED_DEMO_DATA':'1'})
        p=subprocess.Popen([sys.executable,str(ROOT/'api_server.py')],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        try:
            deadline=time.time()+20
            while time.time()<deadline:
                try:
                    with urllib.request.urlopen(f'http://127.0.0.1:{PORT}/api/health',timeout=2) as r:
                        if r.status==200:break
                except Exception:pass
                time.sleep(.15)
            else:raise RuntimeError('server not ready')
        finally:
            p.terminate()
            try:p.wait(timeout=3)
            except Exception:p.kill()
        q=subprocess.run([sys.executable,str(ROOT/'restore_drill.py'),'--source',str(db)],cwd=ROOT,capture_output=True,text=True,timeout=30)
        print(q.stdout or q.stderr)
        return q.returncode
if __name__=='__main__': raise SystemExit(main())
