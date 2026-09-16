import os,sys,time,json,sqlite3,subprocess,urllib.request,urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parent; PORT=8243; DB=ROOT/'qa_writing_v4613.db'
if DB.exists(): DB.unlink()
env=os.environ.copy();env.update({'PORT':str(PORT),'PETQUEST_SQLITE_PATH':str(DB),'PETQUEST_ENV':'development','PETQUEST_DEV_MODE':'1','PETQUEST_SEED_DEMO_DATA':'1','PETQUEST_REQUIRE_GUARDIAN_CONSENT':'0'})
p=subprocess.Popen([sys.executable,'api_server.py'],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
base=f'http://127.0.0.1:{PORT}/api'
def req(path,method='GET',body=None,token=None,ok=(200,201)):
    data=None if body is None else json.dumps(body).encode();h={'Content-Type':'application/json'}
    if token:h['Authorization']='Bearer '+token
    r=urllib.request.Request(base+path,data=data,method=method,headers=h)
    try:
        with urllib.request.urlopen(r,timeout=8) as x: raw=x.read();code=x.status
    except urllib.error.HTTPError as e: raw=e.read();code=e.code
    if code not in ok: raise AssertionError(f'{method} {path}: {code} {raw[:200]!r}')
    return json.loads(raw.decode() or '{}')
def wait():
    for _ in range(80):
        try:
            if req('/health')['ok']: return
        except Exception: time.sleep(.1)
    raise RuntimeError('server not ready')
def row(sql,args=()):
    con=sqlite3.connect(DB);con.row_factory=sqlite3.Row;r=con.execute(sql,args).fetchone();con.close();return dict(r) if r else None
checks=[]
def ck(name,cond,detail=''):
    checks.append((name,bool(cond),detail));
    if not cond: raise AssertionError(name+' '+detail)
try:
    wait(); login=req('/login','POST',{'email':'student@petquest.local','password':'Student123!'});token=login['token'];sid=login['user']['id']
    weaknesses=[]
    specs=[('writing-content','Content'),('writing-communication','Communicative Achievement'),('writing-organisation','Organisation'),('past-go','Language')]
    for code,criterion in specs:
        weaknesses.append({'criterion':criterion,'code':code,'title':'QA weakness','why':'QA reason','exercise':{'code':code,'title':criterion,'prompt':'QA exercise '+criterion,'options':['A','B','C'],'answer':1,'why':'QA explanation','status':'pending','selected':None}})
    review={'date':'2026-09-02T20:20:00Z','engine':'v46.13-writing-mastery','part':1,'taskVariant':'email','words':98,'score':13,'text':'QA writing','rubric':{'content':5,'communication':3,'organisation':3,'language':2},'explanations':{'content':'Respondiste todos los puntos del email.','communication':'El tono es comprensible pero demasiado informal.','organisation':'Faltan conectores.','language':'Hay problemas con past simple y prepositions.'},'errors':[{'rule':'past-go'}],'weaknesses':weaknesses,'targetScore':18}
    snap={'profile':{'name':'Student Demo','xp':10,'streak':1,'role':'student','examDate':'','dailyGoal':15},'history':[],'writing':[review],'speaking':[],'words':[],'settings':{'support':'guided','largeText':False,'dyslexia':False,'sound':True},'mockAttempts':[],'achievements':[],'studySessions':[],'assignmentProgress':{},'courseCompletions':{},'notifications':[]}
    req('/snapshot','POST',{'snapshot':snap},token);got=req('/snapshot',token=token)['snapshot']
    ck('writing snapshot exact',got['writing'][0]==review)
    ck('rubric exact 5+3+3+2',sum(got['writing'][0]['rubric'].values())==13)
    ck('four weaknesses persisted',len(got['writing'][0]['weaknesses'])==4)
    for i,(code,criterion) in enumerate(specs):
        rr=req('/academic-remediation','POST',{'error_code':code,'prompt':'QA exercise '+criterion,'answer':'B','correct':i<3,'source':'v46.13-writing-mastery'},token)
        db=row('select * from academic_remediation_attempts where id=?',(rr['id'],))
        ck('remediation '+code,db['student_id']==sid and db['error_code']==code and db['source']=='v46.13-writing-mastery' and db['correct']==(1 if i<3 else 0))
    prep=req('/my-preparation',token=token)
    ck('writing preparation from 13/20 = 65%',abs(float(prep['skills']['writing'])-65.0)<0.1,str(prep['skills']))
    rem=req('/academic-remediation',token=token)
    ck('remediation readback 4',len([x for x in rem['attempts'] if x['source']=='v46.13-writing-mastery'])==4)
    con=sqlite3.connect(DB);fk=con.execute('pragma foreign_key_check').fetchall();con.close();ck('foreign keys',not fk,str(fk))
    print(f'WRITING MASTERY V46.13: {sum(x[1] for x in checks)}/{len(checks)} PASS')
    for n,ok,d in checks: print(('PASS ' if ok else 'FAIL ')+n+((' :: '+d) if d else ''))
finally:
    p.terminate()
    try:p.wait(timeout=3)
    except Exception:p.kill()
