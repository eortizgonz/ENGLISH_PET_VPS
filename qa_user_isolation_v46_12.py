import os,sys,time,json,sqlite3,subprocess,urllib.request,urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parent; PORT=8238; DB=ROOT/'qa_v4612_user_isolation.db'
if DB.exists(): DB.unlink()
env=os.environ.copy();env.update({'PORT':str(PORT),'PETQUEST_SQLITE_PATH':str(DB),'PETQUEST_ENV':'development','PETQUEST_DEV_MODE':'1','PETQUEST_SEED_DEMO_DATA':'1','PETQUEST_REQUIRE_GUARDIAN_CONSENT':'0'})
p=subprocess.Popen([sys.executable,'api_server.py'],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
base=f'http://127.0.0.1:{PORT}/api'
def req(path,method='GET',body=None,token=None,ok=(200,201)):
 data=None if body is None else json.dumps(body).encode();h={'Content-Type':'application/json'}
 if token:h['Authorization']='Bearer '+token
 r=urllib.request.Request(base+path,data=data,method=method,headers=h)
 try:
  with urllib.request.urlopen(r,timeout=8) as x: raw=x.read();code=x.status
 except urllib.error.HTTPError as e: raw=e.read();code=e.code
 if code not in ok: raise AssertionError(f'{method} {path} -> {code} {raw[:200]!r}')
 return json.loads(raw.decode() or '{}')
def wait():
 for _ in range(80):
  try:
   if req('/health').get('ok'):return
  except Exception:time.sleep(.1)
 raise RuntimeError('server')
def login(email,pw):return req('/login','POST',{'email':email,'password':pw})
def one(sql,args=()):
 c=sqlite3.connect(DB);c.row_factory=sqlite3.Row;r=c.execute(sql,args).fetchone();c.close();return dict(r) if r else None
checks=[]
def ck(n,c,d=''): checks.append((n,bool(c))); print(('PASS' if c else 'FAIL'),n,d); assert c
try:
 wait(); s1=login('student@petquest.local','Student123!'); school=login('school@petquest.local','School123!'); t1=s1['token']; cs=school['token']; uid1=s1['user']['id']; school_id=s1['user']['school_id']
 # Student 1 snapshot + mock.
 snap1={'profile':{'name':'Student One','role':'student'},'history':[{'date':'2026-09-02T10:00:00Z','qid':'r1','skill':'reading','correct':True}], 'writing':[], 'speaking':[], 'words':[], 'settings':{}, 'mockAttempts':[]}
 req('/snapshot','POST',{'snapshot':snap1},t1)
 req('/mock-attempts','POST',{'pack_id':'ISO-A','skill':'listening','started_at':'2026-09-02T10:00:00Z','items':[{'item_id':'a1','part':1,'answer_option':0,'is_correct':False},{'item_id':'a2','part':1,'answer_option':1,'is_correct':True}]},t1)
 # Create second student from school account.
 email='student.two.v4612@example.com'; pw='StrongPass123!'; u2=req('/users','POST',{'email':email,'name':'Student Two','role':'student','password':pw,'school_id':school_id},cs)['id']; s2=login(email,pw); t2=s2['token']; ck('different user ids',u2!=uid1)
 # Second user begins clean.
 g2=req('/snapshot',token=t2).get('snapshot') or {}; ck('user2 does not receive user1 snapshot',g2!=snap1)
 snap2={'profile':{'name':'Student Two','role':'student'},'history':[{'date':'2026-09-02T11:00:00Z','qid':'r2','skill':'reading','correct':False},{'date':'2026-09-02T11:02:00Z','qid':'r2','skill':'reading','correct':True}], 'writing':[{'date':'2026-09-02','part':1,'score':20,'text':'ok'}], 'speaking':[], 'words':[], 'settings':{}, 'mockAttempts':[]}
 req('/snapshot','POST',{'snapshot':snap2},t2)
 req('/mock-attempts','POST',{'pack_id':'ISO-B','skill':'listening','started_at':'2026-09-02T11:00:00Z','items':[{'item_id':'b1','part':1,'answer_option':1,'is_correct':True},{'item_id':'b2','part':1,'answer_option':2,'is_correct':True}]},t2)
 # Readback exact and independent.
 ck('user1 snapshot unchanged',req('/snapshot',token=t1).get('snapshot')==snap1)
 ck('user2 snapshot exact',req('/snapshot',token=t2).get('snapshot')==snap2)
 p1=req('/my-preparation',token=t1); p2=req('/my-preparation',token=t2)
 ck('preparation owner1',p1.get('student',{}).get('id')==uid1)
 ck('preparation owner2',p2.get('student',{}).get('id')==u2)
 ck('preparation scores independent',p1.get('preparation',{}).get('score')!=p2.get('preparation',{}).get('score'),str((p1.get('preparation'),p2.get('preparation'))))
 ck('mock attempts tied user1',one('select student_id from mock_attempts where pack_id=?',('ISO-A',))['student_id']==uid1)
 ck('mock attempts tied user2',one('select student_id from mock_attempts where pack_id=?',('ISO-B',))['student_id']==u2)
 # DB snapshot rows independent.
 ck('snapshot db user1',json.loads(one('select payload from snapshots where user_id=?',(uid1,))['payload'])==snap1)
 ck('snapshot db user2',json.loads(one('select payload from snapshots where user_id=?',(u2,))['payload'])==snap2)
 print(f'USER ISOLATION V46.12: {sum(v for _,v in checks)}/{len(checks)} PASS')
finally:
 p.terminate();
 try:p.wait(timeout=3)
 except Exception:p.kill()
