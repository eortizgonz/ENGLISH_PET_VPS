import os,sys,time,json,sqlite3,subprocess,urllib.request,urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PORT=8199
DB=ROOT/'qa_v469_full_persistence.db'
if DB.exists(): DB.unlink()
env=os.environ.copy(); env.update({
 'PORT':str(PORT),'PETQUEST_SQLITE_PATH':str(DB),'PETQUEST_ENV':'development','PETQUEST_DEV_MODE':'1',
 'PETQUEST_SEED_DEMO_DATA':'1','PETQUEST_REQUIRE_GUARDIAN_CONSENT':'0'
})
p=subprocess.Popen([sys.executable,'api_server.py'],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
base=f'http://127.0.0.1:{PORT}/api'
def req(path,method='GET',body=None,token=None,ok=(200,201)):
    data=None if body is None else json.dumps(body).encode()
    h={'Content-Type':'application/json'}
    if token:h['Authorization']='Bearer '+token
    r=urllib.request.Request(base+path,data=data,method=method,headers=h)
    try:
        with urllib.request.urlopen(r,timeout=8) as x:
            raw=x.read(); code=x.status
    except urllib.error.HTTPError as e:
        raw=e.read(); code=e.code
    if code not in ok:
        raise AssertionError(f'{method} {path} -> {code} {raw[:300]!r}')
    return json.loads(raw.decode() or '{}')
def wait():
    for _ in range(80):
        try:
            if req('/health')['ok']: return
        except Exception: time.sleep(.1)
    raise RuntimeError('server not ready')
def login(email,pw): return req('/login','POST',{'email':email,'password':pw})
def one(sql,args=()):
    con=sqlite3.connect(DB); con.row_factory=sqlite3.Row
    r=con.execute(sql,args).fetchone(); con.close(); return dict(r) if r else None
def rows(sql,args=()):
    con=sqlite3.connect(DB); con.row_factory=sqlite3.Row
    r=[dict(x) for x in con.execute(sql,args).fetchall()]; con.close(); return r
checks=[]
def ck(name,cond,detail=''):
    checks.append((name,bool(cond),detail));
    if not cond: raise AssertionError(name+(' :: '+detail if detail else ''))
try:
    wait()
    st=login('student@petquest.local','Student123!'); tt=login('teacher@petquest.local','Teacher123!'); sc=login('school@petquest.local','School123!'); ad=login('admin@petquest.local','Admin123!')
    S,T,C,A=st['token'],tt['token'],sc['token'],ad['token']
    sid=st['user']['id']; tid=tt['user']['id']; school_id=st['user']['school_id']
    ck('sessions/student row',one('select user_id from sessions where token=?',(S,))['user_id']==sid)
    # complete student snapshot covers all local forms/progress structures
    snap={'profile':{'name':'Mia QA','xp':77,'streak':4,'role':'student','examDate':'2026-12-01','dailyGoal':20},
      'history':[{'date':'2026-09-02T10:00:00Z','qid':'r101','skill':'reading','level':1,'focus':'notices','correct':False,'answer':0,'answerText':'A'},
                 {'date':'2026-09-02T10:02:00Z','qid':'r101','skill':'reading','level':1,'focus':'notices','correct':True,'answer':1,'answerText':'B'}],
      'writing':[{'date':'2026-09-02T10:10:00Z','part':1,'score':16,'text':'Test writing'}],
      'speaking':[{'date':'2026-09-02T10:20:00Z','part':1,'score':16,'text':'Test speaking'},{'date':'2026-09-02T10:21:00Z','part':1,'durationHint':True}],
      'words':[{'term':'arrive at','strength':2,'nextReview':'2026-09-03T00:00:00Z'}],
      'settings':{'support':'guided','largeText':True,'dyslexia':False,'sound':True},
      'mockAttempts':[{'date':'2026-09-02','skill':'reading','score':75,'correct':24,'total':32,'source':'qa'}],
      'achievements':[{'id':'first10','title':'QA','date':'2026-09-02'}],
      'studySessions':[{'id':'s1','skill':'reading','completed':True}],
      'assignmentProgress':{'999':{'started':'2026-09-02','done':False,'skill':'reading'}},'courseCompletions':{},'notifications':[]}
    req('/snapshot','POST',{'snapshot':snap},S)
    sr=req('/snapshot',token=S)['snapshot']; ck('snapshot exact readback',sr==snap)
    dbsnap=json.loads(one('select payload from snapshots where user_id=?',(sid,))['payload']); ck('snapshot exact database',dbsnap==snap)
    # course/class form
    course=req('/courses','POST',{'name':'QA Class'},T)['id']; cr=one('select * from courses where id=?',(course,)); ck('courses form -> table',cr['name']=='QA Class' and cr['teacher_id']==tid and cr['school_id']==school_id)
    req('/enrollments','POST',{'course_id':course,'student_id':sid},T); ck('enrollment -> table',one('select * from enrollments where course_id=? and user_id=?',(course,sid)) is not None)
    # assignment form
    aid=req('/assignments','POST',{'course_id':course,'title':'QA Reading','skill':'reading','due_date':'2026-09-20'},T)['id']; ar=one('select * from assignments where id=?',(aid,)); ck('assignment -> table',ar['title']=='QA Reading' and ar['skill']=='reading' and ar['due_date']=='2026-09-20')
    got=req('/assignments',token=S)['assignments']; ck('assignment student readback',any(x['id']==aid and x['title']=='QA Reading' for x in got))
    # CMS question form
    qid=req('/questions','POST',{'skill':'reading','part':1,'level':1,'focus':'notices','prompt':'QA prompt','options':['One','Two','Three'],'answer_index':1,'explanation':'QA why','tip':'QA tip','status':'draft'},T)['id']; qr=one('select * from questions where id=?',(qid,)); ck('question -> table',qr['prompt']=='QA prompt' and json.loads(qr['options_json'])==['One','Two','Three'] and qr['answer_index']==1 and qr['explanation']=='QA why' and qr['tip']=='QA tip')
    # support group/intervention form
    gid=req('/support-groups','POST',{'course_id':course,'name':'QA Support','skill':'reading','focus':'notices','student_ids':[sid]},T)['id']; gr=one('select * from support_groups where id=?',(gid,)); ck('support group -> table',gr['name']=='QA Support' and gr['skill']=='reading' and gr['focus']=='notices'); ck('support member -> table',one('select * from support_group_members where group_id=? and user_id=?',(gid,sid)) is not None); ck('intervention run auto-created',one('select * from intervention_runs where group_id=?',(gid,)) is not None)
    # academic error/remediation forms
    er=req('/academic-errors','POST',{'events':[{'skill':'writing','part':1,'competence':'grammar','subcompetence':'past_simple','error_code':'past_simple_form','severity':'medium','original_text':'I go yesterday','correction':'I went yesterday','mastery_proxy':45,'source':'qa'}]},S); ck('academic error inserted',er.get('inserted')==1); e=one('select * from academic_error_events where student_id=? and error_code=?',(sid,'past_simple_form')); ck('academic error fields match',e['skill']=='writing' and e['part']==1 and e['correction']=='I went yesterday' and abs(e['mastery_proxy']-45)<.01)
    rid=req('/academic-remediation','POST',{'error_code':'past_simple_form','prompt':'Choose past','answer':'went','correct':True,'source':'qa'},S)['id']; rr=one('select * from academic_remediation_attempts where id=?',(rid,)); ck('remediation -> table',rr['student_id']==sid and rr['answer']=='went' and rr['correct']==1)
    # mock attempt + response detail
    mi=[{'part':1,'item_id':'qa1','answer_text':'','answer_option':1,'is_correct':True,'response_ms':1200},{'part':1,'item_id':'qa2','answer_text':'','answer_option':0,'is_correct':False,'response_ms':900}]
    ma=req('/mock-attempts','POST',{'pack_id':'QA-FORM','skill':'reading','started_at':'2026-09-02T10:00:00Z','items':mi,'source':'qa'},S); mar=one('select * from mock_attempts where id=?',(ma['id'],)); ck('mock attempt totals match',mar['total_items']==2 and mar['correct_items']==1 and abs(mar['pct']-50)<.01); mrs=rows('select * from mock_item_responses where attempt_id=? order by item_id',(ma['id'],)); ck('mock responses count/values',len(mrs)==2 and mrs[0]['item_id']=='qa1' and mrs[0]['is_correct']==1 and mrs[1]['item_id']=='qa2' and mrs[1]['is_correct']==0)
    # guardian consent form
    cid=req('/consents','POST',{'student_id':sid,'guardian_name':'QA Guardian','guardian_email':'guardian@example.com','consent_version':'2026-09'},C)['id']; gc=one('select * from guardian_consents where id=?',(cid,)); ck('consent -> table',gc['student_id']==sid and gc['guardian_name']=='QA Guardian' and gc['guardian_email']=='guardian@example.com' and gc['consent_version']=='2026-09')
    # availability form
    av=req('/teacher-availability','POST',{'teacher_id':tid,'weekday':2,'start_min':540,'end_min':720},C); avr=one('select * from teacher_availability where teacher_id=? and weekday=2 and start_min=540 and end_min=720',(tid,)); ck('teacher availability -> table',avr is not None)
    # strategy target + governance forms
    target=req('/strategy-targets','POST',{'year':2026,'metric':'reading','target_value':82,'owner_user_id':tid,'note':'QA target'},C)['id']; tr=one('select * from strategic_targets where id=?',(target,)); ck('strategy target -> table',tr['metric']=='reading' and abs(tr['target_value']-82)<.01 and tr['note']=='QA target')
    goal=req('/governance/goals','POST',{'title':'QA Goal','metric':'reading','target_value':85,'owner_user_id':tid,'due_date':'2026-12-01'},C)['id']; action=req('/governance/actions','POST',{'goal_id':goal,'title':'QA Action','owner_user_id':tid,'due_date':'2026-10-01','expected_impact':'Improve reading'},C)['id']; req('/governance/review','POST',{'goal_id':goal,'observed_value':61,'decision':'continue','note':'QA review'},C); ck('governance goal -> table',one('select * from governance_goals where id=?',(goal,))['current_value']==61); ck('governance action -> table',one('select * from governance_actions where id=?',(action,))['title']=='QA Action'); ck('governance review -> table',one('select * from governance_reviews where goal_id=?',(goal,))['note']=='QA review')
    # onboarding form
    req('/onboarding','POST',{'item_key':'first_assignment','status':'done'},C); ob=one('select * from onboarding_items where school_id=? and item_key=?',(school_id,'first_assignment')); ck('onboarding -> table',ob['status']=='done' and ob['completed_at'])
    # admin license form
    lic=req('/commercial/license','POST',{'school_id':school_id,'plan':'pilot','student_seats':100,'teacher_seats':20,'expires_at':'2027-01-01'},A)['id']; lr=one('select * from school_licenses where id=?',(lic,)); ck('license -> table',lr['plan']=='pilot' and lr['student_seats']==100 and lr['teacher_seats']==20 and lr['expires_at']=='2027-01-01')
    # account creation form/account token
    nu=req('/users','POST',{'email':'qa.new.user@example.com','name':'QA New User','role':'student','password':'StrongPass123!','school_id':school_id},C)['id']; ur=one('select * from users where id=?',(nu,)); ck('user form -> users table',ur['email']=='qa.new.user@example.com' and ur['name']=='QA New User' and ur['role']=='student'); ck('verification token created',one('select * from account_tokens where user_id=? and kind="verify"',(nu,)) is not None)
    # privacy request form
    pr=req('/privacy/delete-request','POST',{'note':'QA deletion request'},S)['id']; prr=one('select * from privacy_requests where id=?',(pr,)); ck('privacy request -> table',prr['user_id']==sid and prr['request_type']=='delete' and prr['status']=='open')
    # account/profile form -> users table, snapshot remains user-owned
    prof=req('/profile','POST',{'name':'Mia QA Synced'},S); ck('profile form -> users.name',prof.get('name')=='Mia QA Synced' and one('select name from users where id=?',(sid,))['name']=='Mia QA Synced')
    # V8 learning event form -> learning_events + analytics readback
    ev=req('/events','POST',{'event_type':'practice_answer','detail':{'skill':'reading','qid':'qa-event','correct':True,'minutes':2.5}},S); ler=one('select * from learning_events where id=?',(ev['id'],)); ck('learning event -> table',ler['user_id']==sid and ler['event_type']=='practice_answer' and ler['skill']=='reading' and ler['item_id']=='qa-event' and ler['success']==1 and abs(ler['minutes']-2.5)<.01)
    an=req('/analytics',token=T); ck('analytics reads persisted events',an.get('events',0)>=1 and an.get('by_skill',{}).get('reading',{}).get('answers',0)>=1)
    mm=req('/mastery/me',token=S); ck('mastery/me reads user snapshot',all(k in mm for k in ('accuracy','risk','skills','weak_focus')))
    ms=req('/mastery/school',token=T); ck('mastery/school isolates school',any(x.get('id')==sid for x in ms.get('students',[])))
    # Planning forms now persist every executed scenario
    dsi={'extra_teacher_hours':2,'weeks':4,'target_skill':'reading','coverage':'all','intensity':'standard'}; ds=req('/decision-simulator/run','POST',dsi,C); dsr=one('select * from planning_scenarios where id=?',(ds.get('scenario_id'),)); ck('decision simulator -> planning_scenarios',bool(ds.get('scenario_id')) and dsr['scenario_type']=='decision_simulator' and json.loads(dsr['inputs_json'])==dsi and json.loads(dsr['result_json']).get('inputs')==ds.get('inputs'))
    boi={'budget':1200,'cost_per_hour':30,'max_hours_week':4,'weeks':4,'strategy':'balanced'}; bo=req('/budget-optimizer/run','POST',boi,C); bor=one('select * from planning_scenarios where id=?',(bo.get('scenario_id'),)); ck('budget optimizer -> planning_scenarios',bool(bo.get('scenario_id')) and bor['scenario_type']=='budget_optimizer' and json.loads(bor['inputs_json'])==boi and json.loads(bor['result_json']).get('constraints')==bo.get('constraints'))
    poi={'budget':1800,'cost_per_hour':30,'max_hours_week':4,'weeks':4,'max_interventions':2,'max_student_overlap':2,'strategy':'balanced'}; po=req('/portfolio-optimizer/run','POST',poi,C); por=one('select * from planning_scenarios where id=?',(po.get('scenario_id'),)); ck('portfolio optimizer -> planning_scenarios',bool(po.get('scenario_id')) and por['scenario_type']=='portfolio_optimizer' and json.loads(por['inputs_json'])==poi and json.loads(por['result_json']).get('constraints')==po.get('constraints'))
    # Backup verification form -> recovery_checks
    bk=req('/backup','POST',{},A); bname=bk.get('backup') or bk.get('name'); rv=req('/recovery/verify','POST',{'name':bname},A); rvr=one('select * from recovery_checks where id=?',(rv['id'],)); ck('recovery verify -> table',rv.get('ok') is True and rvr['backup_name']==bname and rvr['ok']==1)
    rc=req('/recovery/checks',token=A); ck('recovery checks readback',any(x.get('id')==rv['id'] for x in rc.get('checks',[])))
    # preparation report computed from persisted data
    prep=req('/my-preparation',token=S); ck('preparation endpoint user isolated',prep.get('student',{}).get('id')==sid, str(prep)[:300]); ck('preparation has errors/corrections',int(prep.get('errors',{}).get('total_error_targets',0))>=1 and int(prep.get('errors',{}).get('corrected',0))>=1, str(prep)[:300]); ck('unscored speaking recording ignored',abs(float(prep.get('skills',{}).get('speaking',0))-80.0)<0.1,str(prep.get('skills')))
    report=req('/report',token=T)['students']; mine=next(x for x in report if x['id']==sid); ck('teacher report matches student id',mine['id']==sid); ck('teacher report includes preparation fields',all(k in mine for k in ('errors','corrections','pending_errors','preparation_score','remaining')))
    # audit trail created for persisted writes
    ac=one('select count(*) n from audit_log')['n']; ck('audit log populated',ac>=15,f'audit rows={ac}')
    # referential integrity
    con=sqlite3.connect(DB); fk=con.execute('PRAGMA foreign_key_check').fetchall(); con.close(); ck('foreign key integrity',not fk,str(fk[:5]))
    # logout destroys session
    req('/logout','POST',{},S); ck('logout removes session',one('select * from sessions where token=?',(S,)) is None)
    print(f'FULL PERSISTENCE V46.9: {sum(x[1] for x in checks)}/{len(checks)} PASS')
    for n,ok,d in checks: print(('PASS ' if ok else 'FAIL ')+n+((' :: '+d) if d else ''))
finally:
    p.terminate()
    try:p.wait(timeout=3)
    except Exception:p.kill()
