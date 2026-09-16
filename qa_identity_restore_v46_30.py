#!/usr/bin/env python3
import os,tempfile,importlib.util,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent
fd,tmp=tempfile.mkstemp(prefix='petquest_identity_restore_',suffix='.db'); os.close(fd); Path(tmp).unlink(missing_ok=True)
os.environ['PETQUEST_SQLITE_PATH']=tmp
os.environ['PETQUEST_REQUIRE_POSTGRES_AUTH']='0'
os.environ['PETQUEST_SEED_DEMO_DATA']='0'
spec=importlib.util.spec_from_file_location('pq_restore',R/'api_server.py'); pq=importlib.util.module_from_spec(spec);spec.loader.exec_module(pq);pq.init_db()
pw='RestorePass123!'; legacy=hashlib.sha256(pw.encode()).hexdigest()
ident={'id':77,'local_user_id':5,'username':'restoreuser','email':'restore@example.test','password_hash':legacy,'display_name':'Restore User','role':'student','profile_mode':'schools','disabled':False,'created_at':pq.now()}
c=pq.conn(); row=pq.ensure_local_user_for_identity(c,ident); c.commit();
checks=[]
def ck(n,v): checks.append(bool(v)); print(('PASS' if v else 'FAIL'),n)
ck('restored local id',row['id']==5)
ck('restored username',row['username']=='restoreuser')
ck('restored email',row['email']=='restore@example.test')
ck('restored legacy credential verifies',pq.verify_pw(pw,row['password_hash']))
ck('no demo users',c.execute("select count(*) from users where email like '%@petquest.local'").fetchone()[0]==0)
ck('individual school created',c.execute("select count(*) from schools where name='PET Quest Individual Learners'").fetchone()[0]==1)
c.close();Path(tmp).unlink(missing_ok=True)
print(f'IDENTITY RESTORE QA {sum(checks)}/{len(checks)}')
raise SystemExit(0 if all(checks) else 1)
