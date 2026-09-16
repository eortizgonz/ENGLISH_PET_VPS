#!/usr/bin/env python3
import os, subprocess, time, json, urllib.request, urllib.error, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PORT='18943'; DB=ROOT/'qa_v43.db'
try: DB.unlink()
except FileNotFoundError: pass
env=os.environ.copy(); env.update({'PORT':PORT,'PETQUEST_SQLITE_PATH':str(DB),'PETQUEST_DEV_MODE':'1','PETQUEST_ENV':'development'})
p=subprocess.Popen([sys.executable,'api_server.py'],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
base=f'http://127.0.0.1:{PORT}'
def req(path,method='GET',body=None,token=None):
    data=json.dumps(body).encode() if body is not None else None; h={'Content-Type':'application/json'}
    if token:h['Authorization']='Bearer '+token
    r=urllib.request.Request(base+path,data=data,headers=h,method=method)
    try:
        with urllib.request.urlopen(r,timeout=4) as x:
            raw=x.read(); return x.status, json.loads(raw or b'{}') if 'application/json' in x.headers.get('Content-Type','') else raw
    except urllib.error.HTTPError as e:return e.code,json.loads(e.read() or b'{}')
try:
    for _ in range(100):
        try:
            st,j=req('/api/ready')
            if st==200: break
        except Exception: pass
        time.sleep(.08)
    else: raise RuntimeError('server_not_ready')
    st,h=req('/api/health'); assert st==200 and float(h['version'])>=43.0
    st,l=req('/api/login','POST',{'email':'school@petquest.local','password':'School123!'}); assert st==200; tok=l['token']
    st,ss=req('/api/school-students',token=tok); assert st==200 and ss['students']; sid=ss['students'][0]['id']
    ev={'skill':'writing','part':1,'competence':'Grammar','subcompetence':'Past Simple','error_code':'past-go','severity':'medium','original_text':'Yesterday I go','correction':'Yesterday I went','mastery_proxy':40,'source':'qa-v43'}
    st,e=req('/api/academic-errors','POST',{'student_id':sid,'events':[ev]},tok); assert st==201
    for ans,correct in [('went',True),('went',True),('went',True)]:
        st,r=req('/api/academic-remediation','POST',{'student_id':sid,'error_code':'past-go','prompt':'Yesterday I ___ to the park.','answer':ans,'correct':correct,'source':'qa-v43'},tok); assert st==201
    st,r=req(f'/api/academic-remediation?student_id={sid}',token=tok); assert st==200
    ptn=next(x for x in r['patterns'] if x['error_code']=='past-go'); assert ptn['practice_attempts']==3 and ptn['practice_accuracy']==100.0 and ptn['mastered'] is True
    print('PET Quest V43 Mock Bank QA: PASS | version=43.0 remediation_mastery=3/3')
finally:
    p.terminate()
    try:p.wait(timeout=3)
    except Exception:p.kill()
    try: DB.unlink()
    except Exception: pass
