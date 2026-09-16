#!/usr/bin/env python3
import json, os, subprocess, sys, tempfile, time, urllib.request, urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PORT='18841'
DB=ROOT/'qa_v41_privacy.db'
try: DB.unlink()
except FileNotFoundError: pass
env=os.environ.copy(); env.update({'PORT':PORT,'PETQUEST_DB_PATH':str(DB),'PETQUEST_DEV_MODE':'1'})
p=subprocess.Popen([sys.executable,str(ROOT/'api_server.py')],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
base=f'http://127.0.0.1:{PORT}'
def req(path, method='GET', data=None, token=None):
    b=None if data is None else json.dumps(data).encode()
    h={'Content-Type':'application/json'}
    if token: h['Authorization']='Bearer '+token
    r=urllib.request.Request(base+path,data=b,headers=h,method=method)
    try:
        with urllib.request.urlopen(r,timeout=5) as x: return x.status,json.loads(x.read().decode() or '{}')
    except urllib.error.HTTPError as e:
        try: body=json.loads(e.read().decode() or '{}')
        except Exception: body={}
        return e.code,body
try:
    deadline=time.time()+20
    while time.time()<deadline:
        try:
            s,_=req('/api/health')
            if s==200: break
        except Exception: pass
        time.sleep(.15)
    else: raise RuntimeError('server not ready')
    s,d=req('/api/login','POST',{'email':'student@petquest.local','password':'Student123!'})
    assert s==200,(s,d); st=d['token']
    assert req('/api/privacy/export',token=st)[0]==200
    s,d=req('/api/privacy/rectify','POST',{'name':'Student Privacy QA'},st); assert s==200,(s,d)
    s,d=req('/api/privacy/delete-request','POST',{'note':'QA request'},st); assert s in (200,201),(s,d); rid=d['id']
    s,d=req('/api/login','POST',{'email':'admin@petquest.local','password':'Admin123!'})
    assert s==200,(s,d); at=d['token']
    s,d=req('/api/privacy/requests',token=at); assert s==200 and any(x['id']==rid for x in d.get('requests',[])),(s,d)
    s,d=req('/api/privacy/resolve','POST',{'request_id':rid,'action':'reject'},at); assert s==200,(s,d)
    print('PET Quest V41 Privacy QA: PASS')
finally:
    p.terminate()
    try: p.wait(timeout=3)
    except Exception: p.kill()
    try: DB.unlink()
    except FileNotFoundError: pass
