#!/usr/bin/env python3
import os, json, sqlite3, subprocess, time, urllib.request, urllib.error, pathlib, sys
ROOT=pathlib.Path(__file__).resolve().parent
DB=ROOT/'qa_v31.db'; PORT='8131'
for p in [DB, ROOT/'qa_v31.db-shm', ROOT/'qa_v31.db-wal']:
    try:p.unlink()
    except FileNotFoundError:pass
env=os.environ.copy(); env.update({'PETQUEST_SQLITE_PATH':str(DB),'PORT':PORT,'PETQUEST_DEV_MODE':'1'})
proc=subprocess.Popen([sys.executable,'api_server.py'],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
def req(path,method='GET',body=None,token=None):
    data=json.dumps(body).encode() if body is not None else None
    r=urllib.request.Request(f'http://127.0.0.1:{PORT}{path}',data=data,method=method)
    if data:r.add_header('Content-Type','application/json')
    if token:r.add_header('Authorization','Bearer '+token)
    with urllib.request.urlopen(r,timeout=5) as x:
        ct=x.headers.get('Content-Type',''); raw=x.read()
        return json.loads(raw) if 'json' in ct else raw.decode('utf-8','replace')
try:
    for _ in range(50):
        try:
            if req('/api/health').get('ok'):break
        except Exception:time.sleep(.1)
    login=req('/api/login','POST',{'email':'school@petquest.local','password':'School123!'})
    tok=login['token']
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row
    st=c.execute("SELECT id FROM users WHERE email='student@petquest.local'").fetchone()['id']
    payload={'history':[{'skill':'reading','correct':i<6} for i in range(10)]+[{'skill':'listening','correct':i<7} for i in range(10)],'skills':{'reading':60,'listening':70},'writing':[{'score':12}],'speaking':[{'score':13}]}
    c.execute('INSERT OR REPLACE INTO snapshots(user_id,payload,updated_at) VALUES(?,?,datetime("now"))',(st,json.dumps(payload))); c.commit(); c.close()
    base=req('/api/executive-review?window=monthly',token=tok)
    assert base['school']['reading']==60
    snap=req('/api/executive-review/snapshot','POST',{'period_label':'2026-08','window_type':'monthly'},tok)
    assert snap['ok'] and snap['window_type']=='monthly'
    c=sqlite3.connect(DB)
    payload['history']=[{'skill':'reading','correct':i<9} for i in range(10)]+[{'skill':'listening','correct':i<8} for i in range(10)]
    payload['skills']={'reading':85,'listening':80}; payload['writing']=[{'score':15}]; payload['speaking']=[{'score':16}]
    c.execute('UPDATE snapshots SET payload=?,updated_at=datetime("now") WHERE user_id=?',(json.dumps(payload),st)); c.commit(); c.close()
    after=req('/api/executive-review?window=monthly',token=tok)
    assert after['growth']['reading']==25.0, after['growth']
    assert after['growth']['listening']==10.0
    assert len(after['history'])==1
    assert after['classes'] and 'teacher' in after['classes'][0]
    assert all('student' not in str(x).lower() for x in after.get('class_improvements',[]))
    q=req('/api/executive-review/snapshot','POST',{'period_label':'Q3-2026','window_type':'quarterly'},tok)
    assert q['ok']
    quarterly=req('/api/executive-review?window=quarterly',token=tok)
    assert quarterly['window']=='quarterly' and len(quarterly['history'])==1
    csv=req('/api/executive-review.csv',token=tok)
    assert 'student,readiness,accuracy,reading,listening,writing,speaking,attempts' in csv
    health=req('/api/health'); assert health['version']=='31.0'
    print('PET Quest V31 Executive QA: PASS')
    print('Growth Reading:',after['growth']['reading'],'Listening:',after['growth']['listening'])
finally:
    proc.terminate()
    try:proc.wait(timeout=3)
    except:proc.kill()
    for p in [DB, ROOT/'qa_v31.db-shm', ROOT/'qa_v31.db-wal']:
        try:p.unlink()
        except FileNotFoundError:pass
