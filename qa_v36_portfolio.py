#!/usr/bin/env python3
import os,json,subprocess,time,urllib.request,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parent
port='8136'; db=str(ROOT/'qa_v36.db')
try: os.remove(db)
except FileNotFoundError: pass
env=os.environ.copy(); env.update({'PORT':port,'PETQUEST_SQLITE_PATH':db,'PETQUEST_REQUIRE_GUARDIAN_CONSENT':'0'})
p=subprocess.Popen([sys.executable,'api_server.py'],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
base=f'http://127.0.0.1:{port}/api'
def req(path,method='GET',body=None,token=None):
    data=json.dumps(body).encode() if body is not None else None; h={'Content-Type':'application/json'}
    if token:h['Authorization']='Bearer '+token
    q=urllib.request.Request(base+path,data=data,headers=h,method=method)
    with urllib.request.urlopen(q,timeout=7) as x:return x.status,json.loads(x.read().decode())
def login(email,pw):return req('/login','POST',{'email':email,'password':pw})[1]['token']
def hist(skill,n,correct):return [{'skill':skill,'correct':i<correct,'focus':'inference' if skill=='reading' else ('detail' if skill=='listening' else 'structure')} for i in range(n)]
try:
    for _ in range(60):
        try:req('/health');break
        except Exception:time.sleep(.1)
    school=login('school@petquest.local','School123!')
    profiles=[
      hist('reading',12,5)+hist('listening',12,10)+hist('writing',10,6)+hist('speaking',10,8),
      hist('reading',12,6)+hist('listening',12,9)+hist('writing',10,5)+hist('speaking',10,8),
      hist('reading',12,10)+hist('listening',12,5)+hist('writing',10,8)+hist('speaking',10,8),
      hist('reading',12,9)+hist('listening',12,6)+hist('writing',10,7)+hist('speaking',10,9),
      hist('reading',12,10)+hist('listening',12,10)+hist('writing',10,5)+hist('speaking',10,8),
      hist('reading',12,11)+hist('listening',12,10)+hist('writing',10,8)+hist('speaking',10,5),
    ]
    pupils=[]
    for i,history in enumerate(profiles,1):
        email=f'v36student{i}@test.local'; pw='Student123!'
        st,u=req('/users','POST',{'email':email,'password':pw,'name':f'V36 Student {i}','role':'student'},school); assert st==201
        pupils.append((u['id'],email,pw,history))
    st,c=req('/courses','POST',{'name':'V36 Portfolio Class'},school); assert st==201; cid=c['id']
    for sid,email,pw,history in pupils:
        req('/enrollments','POST',{'course_id':cid,'student_id':sid},school)
        tok=login(email,pw); st,_=req('/snapshot','POST',{'snapshot':{'history':history,'skills':{}}},tok); assert st==200
    st,meta=req('/portfolio-optimizer',token=school); assert st==200 and meta['priority_skill'] in ('reading','listening','writing','speaking')
    body={'budget':1800,'cost_per_hour':30,'max_hours_week':8,'weeks':8,'max_interventions':3,'max_student_overlap':2,'strategy':'balanced'}
    st,out=req('/portfolio-optimizer/run','POST',body,school); assert st==200,out
    best=out['best_portfolio']; assert best and 2<=best['intervention_count']<=3,best
    assert best['budget_used']<=1800+1e-6 and best['hours_week_used']<=8+1e-6,best
    assert best['overlap_events']>=0 and best['unique_students']>0,best
    skills={x['skill'] for x in best['plans']}; assert len(skills)==best['intervention_count'],best
    # Too-small constraints must return no portfolio instead of fabricating one.
    tiny={'budget':10,'cost_per_hour':50,'max_hours_week':0.1,'weeks':8,'max_interventions':3,'max_student_overlap':1,'strategy':'balanced'}
    st,out2=req('/portfolio-optimizer/run','POST',tiny,school); assert st==200 and out2['best_portfolio'] is None,out2
    print('PET Quest V36 Portfolio QA: PASS')
    print('interventions=',best['intervention_count'],'skills=',sorted(skills),'budget=',best['budget_used'],'hours=',best['hours_week_used'],'unique=',best['unique_students'],'impact_eq=',best['institutional_equivalent_gain'])
finally:
    p.terminate()
    try:p.wait(timeout=3)
    except Exception:p.kill()
    try: os.remove(db)
    except FileNotFoundError: pass
