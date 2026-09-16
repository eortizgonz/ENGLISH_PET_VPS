#!/usr/bin/env python3
import os,json,subprocess,time,urllib.request,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parent
port='8128'; db=str(ROOT/'qa_v28.db')
try: os.remove(db)
except FileNotFoundError: pass
env=os.environ.copy(); env.update({'PORT':port,'PETQUEST_SQLITE_PATH':db,'PETQUEST_REQUIRE_GUARDIAN_CONSENT':'0'})
p=subprocess.Popen([sys.executable,'api_server.py'],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
base=f'http://127.0.0.1:{port}/api'
def req(path,method='GET',body=None,token=None):
    data=json.dumps(body).encode() if body is not None else None; h={'Content-Type':'application/json'}
    if token:h['Authorization']='Bearer '+token
    q=urllib.request.Request(base+path,data=data,headers=h,method=method)
    with urllib.request.urlopen(q,timeout=5) as x:return x.status,json.loads(x.read().decode())
def login(email,pw):return req('/login','POST',{'email':email,'password':pw})[1]['token']
def hist(skill,n,correct):return [{'skill':skill,'correct':i<correct,'focus':'inference' if skill=='reading' else 'detail'} for i in range(n)]
try:
    for _ in range(50):
        try:req('/health');break
        except Exception:time.sleep(.1)
    school=login('school@petquest.local','School123!')
    pupils=[]
    profiles=[
      hist('reading',12,5)+hist('listening',12,10),
      hist('reading',12,6)+hist('listening',12,9),
      hist('reading',12,11)+hist('listening',12,11),
    ]
    for i,history in enumerate(profiles,1):
        email=f'v28student{i}@test.local'; pw='Student123!'
        st,u=req('/users','POST',{'email':email,'password':pw,'name':f'V28 Student {i}','role':'student'},school); assert st==201
        pupils.append((u['id'],email,pw))
    st,c=req('/courses','POST',{'name':'V28 Intervention Class'},school); assert st==201; cid=c['id']
    for sid,_,_ in pupils: req('/enrollments','POST',{'course_id':cid,'student_id':sid},school)
    for (_,email,pw),history in zip(pupils,profiles):
        tok=login(email,pw); st,_=req('/snapshot','POST',{'snapshot':{'history':history,'skills':{}}},tok); assert st==200
    st,plan=req('/intervention-plan?course_id='+str(cid),token=school); assert st==200
    assert plan['student_count']==3,plan
    reading=next(x for x in plan['interventions'] if x['skill']=='reading')
    assert reading['count']==2 and reading['priority'] in ('alta','media'),reading
    assert len(plan['advance_candidates'])>=1,plan
    st,g=req('/support-groups','POST',{'course_id':cid,'name':'Intervención Reading','skill':'reading','focus':reading['success_criteria'],'student_ids':reading['student_ids']},school); assert st==201 and g['members']==2
    st,a=req('/assignments','POST',{'course_id':cid,'title':'Intervención Reading · 12 min','skill':'reading','due_date':''},school); assert st==201
    print('PET Quest V28 Intervention QA: PASS')
    print('reading_group=',reading['count'],'advance=',len(plan['advance_candidates']),'group_members=',g['members'])
finally:
    p.terminate()
    try:p.wait(timeout=3)
    except Exception:p.kill()
    try: os.remove(db)
    except FileNotFoundError: pass
