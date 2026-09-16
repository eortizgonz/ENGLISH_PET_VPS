#!/usr/bin/env python3
import hashlib, os, tempfile, importlib.util
from pathlib import Path
R=Path(__file__).resolve().parent
# Import server functions against an isolated SQLite path.
os.environ['PETQUEST_SQLITE_PATH']=str(Path(tempfile.gettempdir())/'petquest_qa_hash_migration.db')
os.environ['PETQUEST_SEED_DEMO_DATA']='0'
spec=importlib.util.spec_from_file_location('pq_api',R/'api_server.py')
pq=importlib.util.module_from_spec(spec); spec.loader.exec_module(pq)
checks=[]
def ck(name,ok):
    checks.append(bool(ok)); print(('PASS' if ok else 'FAIL'),name)
pw='MigrationTest123!'
current=pq.hash_pw(pw)
legacy=hashlib.sha256(pw.encode()).hexdigest()
ck('current scheme detected',pq.password_hash_scheme(current)=='pbkdf2_sha256')
ck('current password verifies',pq.verify_pw(pw,current))
ck('wrong current password rejected',not pq.verify_pw('wrong',current))
ck('legacy scheme detected',pq.password_hash_scheme(legacy)=='legacy_sha256')
ck('legacy password verifies',pq.verify_pw(pw,legacy))
ck('wrong legacy password rejected',not pq.verify_pw('wrong',legacy))
api=(R/'api_server.py').read_text(encoding='utf-8')
ck('login self-heal present','password_hash_migrated' in api and 'postgres_was_valid' in api and 'sqlite_was_valid' in api)
ck('password reset clears lockout',"DELETE FROM login_attempts" in api and 'password_reset_completed' in api)
ux=(R/'v46_30_registration_ux.js').read_text(encoding='utf-8')
ck('demo UI requires actual demo accounts','API.demoAccountsAvailable' in ux and 'API.demoSeedEnabled' in ux)
app=(R/'app.js').read_text(encoding='utf-8')
ck('health loads demo availability','demo_accounts_available' in app)
repair=(R/'repair_user_password.py').read_text(encoding='utf-8')
ck('repair tool syncs both stores','update_password_by_local_user' in repair and 'UPDATE users SET password_hash' in repair)
ck('repair tool clears lockout','DELETE FROM login_attempts' in repair)
sw=(R/'sw.js').read_text(encoding='utf-8')
idx=(R/'index.html').read_text(encoding='utf-8')
ck('authfix3 cache active','authfix-3' in sw and '46.30-authfix3' in idx)
print(f'LOGIN HASH MIGRATION QA {sum(checks)}/{len(checks)}')
raise SystemExit(0 if all(checks) else 1)
