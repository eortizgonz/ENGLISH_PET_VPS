#!/usr/bin/env python3
import os, subprocess, time, json, urllib.request, urllib.error, tempfile, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PORT='18942'; DB=ROOT/'qa_v42.db'
try: DB.unlink()
except FileNotFoundError: pass
env=os.environ.copy(); env.update({'PORT':PORT,'PETQUEST_SQLITE_PATH':str(DB),'PETQUEST_DEV_MODE':'1','PETQUEST_ENV':'development'})
p=subprocess.Popen([sys.executable,'api_server.py'],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
base=f'http://127.0.0.1:{PORT}'
def req(path,method='GET',body=None,token=None):
    data=json.dumps(body).encode() if body is not None else None
    h={'Content-Type':'application/json'}
    if token:h['Authorization']='Bearer '+token
    r=urllib.request.Request(base+path,data=data,headers=h,method=method)
    try:
        with urllib.request.urlopen(r,timeout=4) as x:return x.status,json.loads(x.read() or b'{}')
    except urllib.error.HTTPError as e:return e.code,json.loads(e.read() or b'{}')
try:
    for _ in range(80):
        try:
            st,j=req('/api/ready')
            if st==200:break
        except Exception:pass
        time.sleep(.1)
    else: raise RuntimeError('server_not_ready')
    st,h=req('/api/health'); assert st==200 and float(h['version'])>=42.0
    st,l=req('/api/login','POST',{'email':'school@petquest.local','password':'School123!'}); assert st==200; tok=l['token']
    st,ss=req('/api/school-students',token=tok); assert st==200 and ss['students']; sid=ss['students'][0]['id']
    st,c=req('/api/academic-calibration',token=tok); assert st==200 and c['status']=='insufficient' and c['probability_enabled'] is False
    # balanced 40 outcomes => provisional, still probability OFF
    for i in range(40):
        passed=i%2==0; pred=82 if passed else 55
        st,o=req('/api/calibration/outcomes','POST',{'student_id':sid,'source':'external_mock','predicted_readiness':pred,'actual_scale_score':150 if passed else 132,'actual_pass':passed,'exam_date':'2026-08-01'},tok)
        assert st==201, (st,o)
    st,c=req('/api/academic-calibration',token=tok); assert st==200 and c['status']=='provisional' and c['sample_size']==40 and c['classification_accuracy']==100.0 and c['probability_enabled'] is False
    ev={'skill':'writing','part':1,'competence':'Grammar','subcompetence':'Past Simple','error_code':'past-go','severity':'medium','original_text':'Yesterday I go','correction':'Yesterday I went','mastery_proxy':64,'source':'qa-v42'}
    st,e=req('/api/academic-errors','POST',{'student_id':sid,'events':[ev,dict(ev,mastery_proxy=46)]},tok); assert st==201 and e['inserted']==2
    st,e=req(f'/api/academic-errors?student_id={sid}',token=tok); assert st==200 and e['patterns']['past-go']['count']==2 and e['patterns']['past-go']['mastery_proxy']==46.0
    print('PET Quest V42 Calibration QA: PASS | sample=40 status=provisional probability=OFF errors=2')
finally:
    p.terminate()
    try:p.wait(timeout=3)
    except Exception:p.kill()
    try: DB.unlink()
    except Exception: pass
