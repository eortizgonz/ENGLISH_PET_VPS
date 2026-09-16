#!/usr/bin/env python3
import json,os,sqlite3,subprocess,sys,tempfile,time,urllib.request,urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PORT=18969

def call(path,method='GET',body=None,token=''):
    h={'Content-Type':'application/json'}
    if token:h['Authorization']='Bearer '+token
    r=urllib.request.Request(f'http://127.0.0.1:{PORT}/api'+path,data=None if body is None else json.dumps(body).encode(),headers=h,method=method)
    try:
        with urllib.request.urlopen(r,timeout=5) as x:return x.status,json.loads(x.read() or b'{}')
    except urllib.error.HTTPError as e:return e.code,json.loads(e.read() or b'{}')

def login(email,pw):
    st,j=call('/login','POST',{'email':email,'password':pw}); assert st==200,(st,j); return j['token']

with tempfile.TemporaryDirectory() as td:
    db=Path(td)/'p.db'; env=os.environ.copy(); env.update({'PORT':str(PORT),'PETQUEST_SQLITE_PATH':str(db),'PETQUEST_DEV_MODE':'1','PETQUEST_ENV':'test','PETQUEST_SEED_DEMO_DATA':'1'})
    p=subprocess.Popen([sys.executable,str(ROOT/'api_server.py')],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        for _ in range(100):
            try:
                if call('/health')[0]==200:break
            except Exception:pass
            time.sleep(.1)
        S=login('student@petquest.local','Student123!'); C=login('school@petquest.local','School123!')
        con=sqlite3.connect(db); con.row_factory=sqlite3.Row; sid=con.execute("select id from users where email='student@petquest.local'").fetchone()['id']; con.close()
        call('/events','POST',{'event_type':'qa','detail':{'skill':'reading','correct':False}},S)
        call('/academic-errors','POST',{'events':[{'skill':'reading','part':1,'error_code':'qa_delete','source':'qa'}]},S)
        call('/academic-remediation','POST',{'error_code':'qa_delete','prompt':'x','answer':'y','correct':False,'source':'qa'},S)
        call('/mock-attempts','POST',{'pack_id':'QA-DEL','skill':'reading','items':[{'part':1,'item_id':'x','is_correct':False}],'source':'qa'},S)
        st,j=call('/privacy/delete-request','POST',{'note':'qa purge'},S); assert st==201,(st,j); rid=j['id']
        st,j=call('/privacy/resolve','POST',{'request_id':rid,'action':'approve_delete'},C); assert st==200,(st,j)
        con=sqlite3.connect(db)
        tables=[('snapshots','user_id'),('academic_error_events','student_id'),('academic_remediation_attempts','student_id'),('mock_attempts','student_id'),('mock_item_responses','student_id'),('calibration_outcomes','student_id'),('learning_events','user_id')]
        failed=[]
        for t,col in tables:
            n=con.execute(f'select count(*) from {t} where {col}=?',(sid,)).fetchone()[0]
            if n:failed.append(f'{t}:{n}')
        u=con.execute('select name,email,disabled from users where id=?',(sid,)).fetchone(); con.close()
        ok=not failed and u[0]=='Deleted User' and u[2]==1
        print('PRIVACY PURGE V46.9:', 'PASS' if ok else 'FAIL', 'remaining=',failed,'user=',u)
        raise SystemExit(0 if ok else 1)
    finally:
        p.terminate()
        try:p.wait(timeout=2)
        except Exception:p.kill()
