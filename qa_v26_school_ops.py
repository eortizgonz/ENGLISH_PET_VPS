#!/usr/bin/env python3
import os, json, subprocess, time, urllib.request, urllib.error, tempfile, pathlib, sys
ROOT=pathlib.Path(__file__).resolve().parent
port='8126'; db=str(ROOT/'qa_v26.db')
try: os.remove(db)
except FileNotFoundError: pass
env=os.environ.copy(); env.update({'PORT':port,'PETQUEST_SQLITE_PATH':db,'PETQUEST_REQUIRE_GUARDIAN_CONSENT':'0'})
p=subprocess.Popen([sys.executable,'api_server.py'],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
base=f'http://127.0.0.1:{port}/api'
def req(path,method='GET',body=None,token=None):
    data=json.dumps(body).encode() if body is not None else None
    h={'Content-Type':'application/json'}
    if token:h['Authorization']='Bearer '+token
    r=urllib.request.Request(base+path,data=data,headers=h,method=method)
    with urllib.request.urlopen(r,timeout=5) as x:return x.status,json.loads(x.read().decode())
try:
    for _ in range(40):
        try:req('/health');break
        except Exception:time.sleep(.1)
    _,login=req('/login','POST',{'email':'teacher@petquest.local','password':'Teacher123!'})
    tok=login['token']
    st,classes=req('/classes',token=tok); assert st==200 and classes['classes']
    st,newc=req('/courses','POST',{'name':'V26 Pilot Class'},tok); assert st==201
    cid=newc['id']
    st,students=req('/school-students',token=tok); assert st==200 and students['students']
    sid=students['students'][0]['id']
    st,_=req('/enrollments','POST',{'course_id':cid,'student_id':sid},tok); assert st==201
    st,cs=req('/class-students?course_id='+str(cid),token=tok); assert st==200 and len(cs['students'])==1
    st,a=req('/assignments','POST',{'course_id':cid,'title':'Collective Reading Reinforcement','skill':'reading','due_date':''},tok); assert st==201
    st,intel=req('/class-intelligence?course_id='+str(cid),token=tok); assert st==200 and intel['course']['name']=='V26 Pilot Class'
    print('PET Quest V26 School Ops QA: PASS')
    print('class=',intel['course']['name'],'students=',len(cs['students']),'priority=',intel['common_priority'])
finally:
    p.terminate();
    try:p.wait(timeout=3)
    except Exception:p.kill()
