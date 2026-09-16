#!/usr/bin/env python3
import os,json,sqlite3,subprocess,time,urllib.request,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parent; DB=ROOT/'qa_v33.db'; PORT='8133'
for p in [DB,ROOT/'qa_v33.db-shm',ROOT/'qa_v33.db-wal']:
    try:p.unlink()
    except FileNotFoundError:pass
env=os.environ.copy(); env.update({'PETQUEST_SQLITE_PATH':str(DB),'PORT':PORT,'PETQUEST_DEV_MODE':'1'})
proc=subprocess.Popen([sys.executable,'api_server.py'],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
def req(path,method='GET',body=None,token=None):
    data=json.dumps(body).encode() if body is not None else None
    r=urllib.request.Request(f'http://127.0.0.1:{PORT}{path}',data=data,method=method)
    if data:r.add_header('Content-Type','application/json')
    if token:r.add_header('Authorization','Bearer '+token)
    with urllib.request.urlopen(r,timeout=5) as x:return json.loads(x.read())
try:
    for _ in range(50):
        try:
            if req('/api/health')['ok']:break
        except Exception:time.sleep(.1)
    tok=req('/api/login','POST',{'email':'school@petquest.local','password':'School123!'})['token']
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; st=c.execute("SELECT id FROM users WHERE email='student@petquest.local'").fetchone()['id']
    def set_payload(score):
        p={'history':[{'skill':'reading','correct':i<score//10} for i in range(10)]+[{'skill':'listening','correct':i<score//10} for i in range(10)],'skills':{'reading':score,'listening':score},'writing':[{'score':score/5}],'speaking':[{'score':score/5}]}
        c.execute('INSERT OR REPLACE INTO snapshots(user_id,payload,updated_at) VALUES(?,?,datetime("now"))',(st,json.dumps(p)));c.commit()
    for label,score in [('2026-05',60),('2026-06',65),('2026-07',70),('2026-08',75)]:
        set_payload(score); req('/api/executive-review/snapshot','POST',{'period_label':label,'window_type':'monthly'},tok)
    c.close()
    f=req('/api/strategy-forecast',token=tok)
    assert f['confidence']=='high',f['confidence']
    assert f['forecast']['30']['readiness']['no_action']>=f['current']['readiness']
    assert f['forecast']['90']['readiness']['with_action']>=f['forecast']['90']['readiness']['no_action']
    assert 'teacher_hours_week' in f['capacity']
    t=req('/api/strategy-targets','POST',{'year':2027,'metric':'readiness','target_value':85,'note':'Annual target'},tok)
    assert t['ok']
    f2=req('/api/strategy-forecast',token=tok); assert any(x['year']==2027 for x in f2['strategic_targets'])
    assert req('/api/health')['version']=='33.0'
    print('PET Quest V33 Forecast Flow QA: PASS')
    print('Confidence:',f['confidence'],'30d:',f['forecast']['30']['readiness'],'90d:',f['forecast']['90']['readiness'])
finally:
    proc.terminate();
    try:proc.wait(timeout=3)
    except:proc.kill()
    for p in [DB,ROOT/'qa_v33.db-shm',ROOT/'qa_v33.db-wal']:
        try:p.unlink()
        except FileNotFoundError:pass
