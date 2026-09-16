#!/usr/bin/env python3
import os,sys,time,json,subprocess,urllib.request,urllib.error
from pathlib import Path
R=Path(__file__).resolve().parent; PORT='18961'; DB=R/'qa_v4611_audio.db'
try: DB.unlink()
except: pass
env=os.environ.copy(); env.update({'PORT':PORT,'PETQUEST_SQLITE_PATH':str(DB),'PETQUEST_DEV_MODE':'1','PETQUEST_ENV':'development'})
p=subprocess.Popen([sys.executable,'api_server.py'],cwd=R,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
base='http://127.0.0.1:'+PORT
def get(path):
 with urllib.request.urlopen(base+path,timeout=5) as r:return r.status,r.read(),r.headers.get('Content-Type','')
def req(path,method='GET',body=None,token=None):
 data=json.dumps(body).encode() if body is not None else None; h={'Content-Type':'application/json'}
 if token:h['Authorization']='Bearer '+token
 q=urllib.request.Request(base+path,data=data,headers=h,method=method)
 with urllib.request.urlopen(q,timeout=5) as r:return r.status,json.loads(r.read() or b'{}')
try:
 for _ in range(100):
  try:
   st,b,ct=get('/api/ready')
   if st==200:break
  except: time.sleep(.08)
 else: raise RuntimeError('not_ready')
 st,b,ct=get('/api/health'); h=json.loads(b); assert h['version']=='46.11'
 total=0
 for c in 'abc':
  st,b,ct=get(f'/exam_packs/pq-mock-{c}.json'); assert st==200
  d=json.loads(b); assert len(d['listening'])==25
  for rel in sorted({x['audio_file'] for x in d['listening']}):
   st,a,ct=get('/'+rel); assert st==200 and len(a)>10000 and ('audio' in ct or 'mpeg' in ct or 'octet' in ct); total+=1
 st,l=req('/api/login','POST',{'email':'student@petquest.local','password':'Student123!'}); tok=l['token']
 pack=json.loads(get('/exam_packs/pq-mock-a.json')[1]); items=[]
 for q in pack['listening']:
  items.append({'item_id':q['id'],'part':q['part'],'answer_text':str(q['answer']) if q['part']==3 else None,'answer_option':q['answer'] if q['part']!=3 else None,'is_correct':True,'response_ms':500})
 st,r=req('/api/mock-attempts','POST',{'pack_id':'pq-mock-a','skill':'listening','started_at':'2026-09-02T12:00:00Z','items':items,'source':'qa-v46.11'},tok); assert st in (200,201)
 print(f'PET Quest V46.11 Runtime Audio QA: PASS | audio_http={total}/45 mock_attempt_items=25 version={h["version"]}')
finally:
 p.terminate()
 try:p.wait(timeout=2)
 except: p.kill()
 try: DB.unlink()
 except: pass
