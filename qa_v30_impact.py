#!/usr/bin/env python3
import os,json,subprocess,time,urllib.request,pathlib,sys
R=pathlib.Path(__file__).resolve().parent; port='8130'; db=str(R/'qa_v30.db')
try: os.remove(db)
except FileNotFoundError: pass
env=os.environ.copy();env.update({'PORT':port,'PETQUEST_SQLITE_PATH':db,'PETQUEST_REQUIRE_GUARDIAN_CONSENT':'0'})
p=subprocess.Popen([sys.executable,'api_server.py'],cwd=R,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
base=f'http://127.0.0.1:{port}/api'
def req(path,method='GET',body=None,t=None):
 d=json.dumps(body).encode() if body is not None else None;h={'Content-Type':'application/json'}
 if t:h['Authorization']='Bearer '+t
 q=urllib.request.Request(base+path,data=d,headers=h,method=method)
 with urllib.request.urlopen(q,timeout=5) as x:return x.status,json.loads(x.read().decode())
def login(e,pw):return req('/login','POST',{'email':e,'password':pw})[1]['token']
def hist(correct,total=10,skill='reading'):return [{'skill':skill,'correct':i<correct,'focus':'detail'} for i in range(total)]
try:
 for _ in range(50):
  try:req('/health');break
  except:time.sleep(.1)
 school=login('school@petquest.local','School123!')
 students=[]
 for i,corr in enumerate((5,8),1):
  st,u=req('/users','POST',{'email':f'v30{i}@t.local','password':'Student123!','name':f'V30 {i}','role':'student'},school);students.append((u['id'],f'v30{i}@t.local',corr))
 st,c=req('/courses','POST',{'name':'V30 Impact'},school);cid=c['id']
 for sid,email,corr in students:
  req('/enrollments','POST',{'course_id':cid,'student_id':sid},school);tok=login(email,'Student123!');req('/snapshot','POST',{'snapshot':{'history':hist(corr),'skills':{'listening':70,'writing':68,'speaking':74}}},tok)
 st,a=req('/school-impact',t=school);assert st==200 and a['school']['students_with_data']>=2,a
 st,snap=req('/school-impact/snapshot','POST',{'period_label':'baseline'},school);assert st==201,snap
 for sid,email,corr in students:
  tok=login(email,'Student123!');req('/snapshot','POST',{'snapshot':{'history':hist(9),'skills':{'listening':80,'writing':78,'speaking':84}}},tok)
 st,b=req('/school-impact',t=school);assert st==200 and b['growth'] and b['growth']['accuracy']>0,b
 print('PET Quest V30 Impact QA: PASS',b['growth'])
finally:
 p.terminate();
 try:p.wait(timeout=3)
 except: p.kill()
 try:os.remove(db)
 except:pass
