#!/usr/bin/env python3
import json, os, subprocess, time, urllib.request, urllib.error, tempfile, signal
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PORT=8143; DB=ROOT/'qa_v40_commercial.db'; LOG=ROOT/'qa_v40_commercial.log'
for f in (DB,LOG):
    try:f.unlink()
    except FileNotFoundError:pass
env=os.environ.copy(); env.update({'PETQUEST_SQLITE_PATH':str(DB),'PORT':str(PORT),'PETQUEST_DEV_MODE':'1','PETQUEST_ENV':'development'})
p=subprocess.Popen(['python3','api_server.py'],cwd=ROOT,env=env,stdout=LOG.open('w'),stderr=subprocess.STDOUT)
BASE=f'http://127.0.0.1:{PORT}/api'
def req(path,method='GET',body=None,token=None):
    data=None if body is None else json.dumps(body).encode(); headers={'Content-Type':'application/json'}
    if token:headers['Authorization']='Bearer '+token
    r=urllib.request.Request(BASE+path,data=data,method=method,headers=headers)
    try:
        with urllib.request.urlopen(r,timeout=5) as x:return x.status,json.loads(x.read() or b'{}')
    except urllib.error.HTTPError as e:return e.code,json.loads(e.read() or b'{}')
def login(e,pw):
    st,j=req('/login','POST',{'email':e,'password':pw}); assert st==200,(st,j); return j['token'],j['user']
try:
    deadline=time.time()+30
    ready=None
    while time.time()<deadline:
        try:
            with urllib.request.urlopen(f'http://127.0.0.1:{PORT}/api/ready',timeout=2) as x:
                ready=(x.status,json.loads(x.read() or b'{}'))
                if x.status==200 and ready[1].get('ok'): break
        except Exception:
            pass
        time.sleep(.15)
    assert ready and ready[0]==200 and ready[1].get('ok'), f'server_not_ready:{ready}'
    admin,au=login('admin@petquest.local','Admin123!'); school,su=login('school@petquest.local','School123!'); teacher,tu=login('teacher@petquest.local','Teacher123!'); student,stu=login('student@petquest.local','Student123!')
    assert req('/commercial/license','POST',{'school_id':1,'plan':'pilot','student_seats':30,'teacher_seats':5},admin)[0]==201
    for k in ['school_profile','teacher_setup','student_import','guardian_consent','first_class','first_assignment','readiness_baseline','privacy_review']:
        assert req('/onboarding','POST',{'item_key':k,'status':'done'},school)[0]==200
    classes=req('/classes',token=school)[1]['classes']; cid=classes[0]['id']
    students=req('/school-students',token=school)[1]['students']; sid=next(x['id'] for x in students if x['email']=='student@petquest.local')
    req('/enrollments','POST',{'course_id':cid,'student_id':sid},school)
    assert req('/consents','POST',{'student_id':sid,'guardian_name':'Guardian Demo','guardian_email':'guardian@example.com'},school)[0]==201
    snap={'history':[{'skill':'reading','correct':True},{'skill':'reading','correct':False},{'skill':'listening','correct':True}], 'writing':[{'score':3.5}], 'speaking':[{'score':3.2}], 'skills':{'reading':70,'listening':75,'writing':68,'speaking':72}}
    assert req('/snapshot','POST',{'snapshot':snap},student)[0]==200
    assert req('/teacher-availability','POST',{'teacher_id':tu['id'],'weekday':1,'start_min':900,'end_min':1020},school)[0]==201
    st,g=req('/support-groups','POST',{'course_id':cid,'name':'Reading Pilot','skill':'reading','focus':'inference','student_ids':[sid]},school); assert st==201,(st,g)
    sch=req('/schedule-planner/auto','POST',{'duration_min':30,'sessions_per_group':2},school)[1]; assert sch['feasible'] and len(sch['created'])==2
    assert req('/backup','POST',{},admin)[0]==200
    rr=req('/release-readiness',token=school)[1]; assert rr['score']==100.0,rr
    assert rr['commercial_candidate'] is True
    cr=req('/commercial-readiness',token=school)[1]; assert cr['onboarding_complete'] and cr['seat_compliance']
    assert req('/release-readiness/snapshot','POST',{},school)[0]==201
    for path in ['index.html','v37_schedule_capacity.js','v38_production_hardening.js','v39_commercial_onboarding.js','v40_release_readiness.js','sw.js']:
        with urllib.request.urlopen(f'http://127.0.0.1:{PORT}/{path}',timeout=5) as x: assert x.status==200,path
    print('PET Quest V41 Commercial QA: PASS | internal readiness 100/100')
finally:
    p.terminate()
    try:p.wait(3)
    except subprocess.TimeoutExpired:p.kill()
    try:DB.unlink()
    except FileNotFoundError:pass
