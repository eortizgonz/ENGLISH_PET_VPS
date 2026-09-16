#!/usr/bin/env python3
import os, sys, json, time, tempfile, subprocess, urllib.request, urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PORT='8098'
tmp=Path(tempfile.mkdtemp(prefix='petquest-v8-qa-'))
env=os.environ.copy(); env.update({'PORT':PORT,'PETQUEST_SQLITE_PATH':str(tmp/'qa.db'),'PETQUEST_BACKUP_DIR':str(tmp/'backups'),'PETQUEST_DEV_MODE':'1','PETQUEST_ENV':'development','PETQUEST_AUTO_BACKUP_HOURS':'0'})
proc=subprocess.Popen([sys.executable,str(ROOT/'api_server_v8.py')],cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
BASE=f'http://127.0.0.1:{PORT}'

def req(path,method='GET',body=None,token=None):
    data=None if body is None else json.dumps(body).encode()
    h={'Content-Type':'application/json'}
    if token:h['Authorization']='Bearer '+token
    r=urllib.request.Request(BASE+path,data=data,headers=h,method=method)
    try:
        with urllib.request.urlopen(r,timeout=5) as x:return x.status,json.loads(x.read().decode())
    except urllib.error.HTTPError as e:
        try:j=json.loads(e.read().decode())
        except Exception:j={}
        return e.code,j

def wait():
    for _ in range(50):
        try:
            s,j=req('/api/health')
            if s==200:return
        except Exception:pass
        time.sleep(.1)
    raise RuntimeError('server did not start')

try:
    wait()
    s,h=req('/api/health'); assert s==200 and h['version']=='8.0'
    s,r=req('/api/ready'); assert s==200 and r['version']=='8.0'
    s,a=req('/api/login','POST',{'email':'admin@petquest.local','password':'Admin123!'}); assert s==200; at=a['token']
    s,st=req('/api/login','POST',{'email':'student@petquest.local','password':'Student123!'}); assert s==200; token=st['token']; sid=st['user']['id']
    # Consent required: record it as admin.
    s,c=req('/api/consents','POST',{'student_id':sid,'guardian_name':'QA Guardian','guardian_email':'guardian@example.com','consent_version':'v8-qa'},at); assert s==201
    # Learning event.
    s,e=req('/api/events','POST',{'event_type':'practice_answer','skill':'reading','item_id':'qa-r1','success':True,'duration_ms':1200,'meta':{'focus':'detail'}},token); assert s==201
    s,an=req('/api/analytics',token=at); assert s==200 and an['events']>=1 and an['by_skill']['reading']['accuracy']==100
    # Privacy export and deletion request.
    s,ex=req('/api/privacy/export',token=token); assert s==200 and ex['account']['email']=='student@petquest.local' and len(ex['learning_events'])>=1
    s,d=req('/api/privacy/delete-request','POST',{'note':'QA only'},token); assert s==201
    s,prs=req('/api/privacy/requests',token=at); assert s==200 and any(x['request_type']=='delete' for x in prs['requests'])
    # Revoke consent and verify sync is blocked again.
    s,rv=req('/api/consents/revoke','POST',{'student_id':sid},at); assert s==200 and rv['revoked']>=1
    s,sync=req('/api/snapshot','POST',{'snapshot':{'history':[]}},token); assert s==403 and sync['error']=='guardian_consent_required'
    # Observability must have traffic.
    s,o=req('/api/observability',token=at); assert s==200 and o['metrics']['requests']>0
    # Backup job endpoint.
    s,b=req('/api/backup','POST',{},at); assert s==200 and b['ok']
    print('PET Quest V8 QA: PASS')
    print(json.dumps({'analytics_events':an['events'],'observability_requests':o['metrics']['requests'],'backup':b['name']},ensure_ascii=False))
finally:
    proc.terminate()
    try:proc.wait(timeout=3)
    except subprocess.TimeoutExpired:proc.kill()
