#!/usr/bin/env python3
import os,sys,json,time,tempfile,subprocess,urllib.request,urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parent; PORT='8099'; tmp=Path(tempfile.mkdtemp(prefix='petquest-v9-qa-'))
env=os.environ.copy(); env.update({'PORT':PORT,'PETQUEST_SQLITE_PATH':str(tmp/'qa.db'),'PETQUEST_BACKUP_DIR':str(tmp/'backups'),'PETQUEST_DEV_MODE':'1','PETQUEST_ENV':'development','PETQUEST_AUTO_BACKUP_HOURS':'0','PETQUEST_RISK_MIN_ANSWERS':'4','PETQUEST_RISK_ACCURACY':'60'})
proc=subprocess.Popen([sys.executable,str(ROOT/'api_server_v9.py')],cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True); BASE=f'http://127.0.0.1:{PORT}'
def req(path,method='GET',body=None,token=None):
 d=None if body is None else json.dumps(body).encode(); h={'Content-Type':'application/json'}
 if token:h['Authorization']='Bearer '+token
 try:
  with urllib.request.urlopen(urllib.request.Request(BASE+path,data=d,headers=h,method=method),timeout=5) as r:return r.status,json.loads(r.read().decode())
 except urllib.error.HTTPError as e:
  try:j=json.loads(e.read().decode())
  except:j={}
  return e.code,j
def wait():
 for _ in range(60):
  try:
   if req('/api/health')[0]==200:return
  except:pass
  time.sleep(.1)
 raise RuntimeError('server not ready')
try:
 wait(); s,h=req('/api/health'); assert s==200 and h['version']=='9.0'
 s,a=req('/api/login','POST',{'email':'admin@petquest.local','password':'Admin123!'}); at=a['token']
 s,st=req('/api/login','POST',{'email':'student@petquest.local','password':'Student123!'}); token=st['token']; sid=st['user']['id']
 req('/api/consents','POST',{'student_id':sid,'guardian_name':'QA Guardian','guardian_email':'guardian@example.com','consent_version':'v9'},at)
 for i,ok in enumerate([False,False,True,False]):
  s,e=req('/api/events','POST',{'event_type':'practice_answer','skill':'reading','item_id':f'q{i}','success':ok,'duration_ms':1000,'meta':{'focus':'inference'}},token); assert s==201
 s,m=req('/api/mastery/me',token=token); assert s==200 and m['answers']==4 and m['risk'] is True
 s,sm=req('/api/mastery/school',token=at); assert s==200 and sm['at_risk']>=1
 s,b=req('/api/backup','POST',{},at); assert s==200 and b['ok']; name=b['name']
 s,v=req('/api/recovery/verify','POST',{'name':name},at); assert s==200 and v['ok'] and v['integrity']=='ok'
 s,d=req('/api/privacy/delete-request','POST',{'note':'V9 QA'},token); rid=d['id']; assert s==201
 s,r=req('/api/privacy/resolve','POST',{'request_id':rid,'action':'reject'},at); assert s==200 and r['status']=='rejected'
 print('PET Quest V9 QA: PASS'); print(json.dumps({'risk':m['risk'],'accuracy':m['accuracy'],'backup':name,'integrity':v['integrity']},ensure_ascii=False))
finally:
 proc.terminate()
 try:proc.wait(timeout=3)
 except:proc.kill()
