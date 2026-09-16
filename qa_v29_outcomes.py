#!/usr/bin/env python3
import os,json,subprocess,time,urllib.request,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parent; port='8129'; db=str(ROOT/'qa_v29.db')
try: os.remove(db)
except FileNotFoundError: pass
env=os.environ.copy(); env.update({'PORT':port,'PETQUEST_SQLITE_PATH':db,'PETQUEST_REQUIRE_GUARDIAN_CONSENT':'0'})
p=subprocess.Popen([sys.executable,'api_server.py'],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
base=f'http://127.0.0.1:{port}/api'
def req(path,method='GET',body=None,token=None):
    data=json.dumps(body).encode() if body is not None else None; h={'Content-Type':'application/json'}
    if token:h['Authorization']='Bearer '+token
    q=urllib.request.Request(base+path,data=data,headers=h,method=method)
    with urllib.request.urlopen(q,timeout=5) as x:return x.status,json.loads(x.read().decode())
def login(email,pw):return req('/login','POST',{'email':email,'password':pw})[1]['token']
def hist(correct,total=12):return [{'skill':'reading','correct':i<correct,'focus':'inference'} for i in range(total)]
try:
    for _ in range(50):
        try:req('/health');break
        except Exception:time.sleep(.1)
    school=login('school@petquest.local','School123!')
    pupils=[]
    for i,corr in enumerate((5,6),1):
        st,u=req('/users','POST',{'email':f'v29s{i}@test.local','password':'Student123!','name':f'V29 Student {i}','role':'student'},school); assert st==201
        pupils.append((u['id'],f'v29s{i}@test.local',corr))
    st,c=req('/courses','POST',{'name':'V29 Outcomes'},school); cid=c['id']
    for sid,email,corr in pupils:
        req('/enrollments','POST',{'course_id':cid,'student_id':sid},school)
        tok=login(email,'Student123!'); req('/snapshot','POST',{'snapshot':{'history':hist(corr),'skills':{}}},tok)
    st,g=req('/support-groups','POST',{'course_id':cid,'name':'Reading Outcome Test','skill':'reading','focus':'Subir 8 puntos o lograr 75%+','student_ids':[x[0] for x in pupils]},school); assert st==201,g
    assert 40 <= g['baseline_average'] <= 50,g
    # Improve both students strongly.
    for sid,email,corr in pupils:
        tok=login(email,'Student123!'); req('/snapshot','POST',{'snapshot':{'history':hist(10),'skills':{}}},tok)
    st,e=req('/interventions/evaluate','POST',{'group_id':g['id']},school); assert st==200,e
    assert e['delta']>=30 and e['recommendation']=='close' and e['status']=='closed',e
    st,o=req('/intervention-outcomes?course_id='+str(cid),token=school); assert st==200 and len(o['outcomes'])==1,o
    assert o['outcomes'][0]['recommendation']=='close'
    st,eff=req('/intervention-effectiveness',token=school); assert st==200 and eff['by_skill'],eff
    print('PET Quest V29 Outcome QA: PASS')
    print('baseline=',e['baseline_average'],'current=',e['current_average'],'delta=',e['delta'],'decision=',e['recommendation'])
finally:
    p.terminate()
    try:p.wait(timeout=3)
    except Exception:p.kill()
    try: os.remove(db)
    except FileNotFoundError: pass
