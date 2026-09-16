#!/usr/bin/env python3
import os,json,subprocess,time,urllib.request,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parent
port='8127'; db=str(ROOT/'qa_v27.db')
try: os.remove(db)
except FileNotFoundError: pass
env=os.environ.copy(); env.update({'PORT':port,'PETQUEST_SQLITE_PATH':db,'PETQUEST_REQUIRE_GUARDIAN_CONSENT':'0'})
p=subprocess.Popen([sys.executable,'api_server.py'],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
base=f'http://127.0.0.1:{port}/api'
def req(path,method='GET',body=None,token=None):
    data=json.dumps(body).encode() if body is not None else None; h={'Content-Type':'application/json'}
    if token:h['Authorization']='Bearer '+token
    r=urllib.request.Request(base+path,data=data,headers=h,method=method)
    with urllib.request.urlopen(r,timeout=5) as x:return x.status,json.loads(x.read().decode())
def login(email,pw):return req('/login','POST',{'email':email,'password':pw})[1]['token']
def hist(skill,n,correct):return [{'skill':skill,'correct':i<correct,'focus':'inference' if skill=='reading' else 'detail'} for i in range(n)]
try:
    for _ in range(50):
        try:req('/health');break
        except Exception:time.sleep(.1)
    school=login('school@petquest.local','School123!')
    students=[]
    for i in range(1,5):
        email=f'v27student{i}@test.local'; pw='Student123!'
        st,u=req('/users','POST',{'email':email,'password':pw,'name':f'V27 Student {i}','role':'student'},school); assert st==201
        students.append((u['id'],email,pw))
    # create two classes
    st,a=req('/courses','POST',{'name':'V27 Reading Group'},school); assert st==201; ca=a['id']
    st,b=req('/courses','POST',{'name':'V27 Listening Group'},school); assert st==201; cb=b['id']
    for sid,_,_ in students[:2]: req('/enrollments','POST',{'course_id':ca,'student_id':sid},school)
    for sid,_,_ in students[2:]: req('/enrollments','POST',{'course_id':cb,'student_id':sid},school)
    # sync distinct profiles: class A reading weak, class B listening weak
    profiles=[
      hist('reading',10,4)+hist('listening',10,8),
      hist('reading',10,5)+hist('listening',10,9),
      hist('reading',10,9)+hist('listening',10,4),
      hist('reading',10,8)+hist('listening',10,5),
    ]
    for (_,email,pw),history in zip(students,profiles):
        tok=login(email,pw); st,_=req('/snapshot','POST',{'snapshot':{'history':history,'skills':{}}},tok); assert st==200
    st,si=req('/school-intelligence',token=school); assert st==200 and len(si['classes'])>=3
    A=next(x for x in si['classes'] if x['id']==ca); B=next(x for x in si['classes'] if x['id']==cb)
    assert A['common_priority']=='reading',A
    assert B['common_priority']=='listening',B
    st,ia=req('/class-intelligence?course_id='+str(ca),token=school); assert st==200
    member_ids=[r['id'] for r in ia['students']]
    st,g=req('/support-groups','POST',{'course_id':ca,'name':'Reading Inference Boost','skill':'reading','focus':'inference','student_ids':member_ids},school); assert st==201 and g['members']==2
    st,groups=req('/support-groups',token=school); assert st==200 and any(x['id']==g['id'] and x['member_count']==2 for x in groups['groups'])
    st,plan=req('/weekly-class-plan?course_id='+str(ca),token=school); assert st==200 and plan['priority']=='reading' and len(plan['plan'])==4
    print('PET Quest V27 Classroom QA: PASS')
    print('classA_priority=',A['common_priority'],'classB_priority=',B['common_priority'],'group_members=',g['members'],'plan_days=',len(plan['plan']))
finally:
    p.terminate()
    try:p.wait(timeout=3)
    except Exception:p.kill()
