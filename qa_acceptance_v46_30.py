#!/usr/bin/env python3
from pathlib import Path
import json,re,subprocess,sys,sqlite3
R=Path(__file__).resolve().parent
checks=[]
def ck(name,ok,detail=''):
    checks.append((name,bool(ok),str(detail)))
    print(('PASS' if ok else 'FAIL'),name,detail)
# Windows launchers
pg=(R/'START_PET_QUEST_POSTGRES_WINDOWS.bat').read_bytes()
std=(R/'START_PET_QUEST_WINDOWS.bat').read_text(encoding='utf-8')
ck('launcher clean CRLF',b'\r\r\n' not in pg)
txt=pg.decode('utf-8')
labels=set(re.findall(r'^:([A-Za-z0-9_-]+)\s*$',txt,re.M))
gotos=re.findall(r'\bgoto\s+:([A-Za-z0-9_-]+)',txt,re.I)
ck('launcher labels valid',all(x in labels for x in gotos),gotos)
for token in ['PETQUEST_PG_DB=PET','PETQUEST_PG_USER=postgres','PETQUEST_PG_PASSWORD=12345','setup_postgres_pet.py','postgres_check.py','verify_windows_runtime.py']:
    ck('launcher '+token,token in txt)
ck('standard launcher delegates PostgreSQL','START_PET_QUEST_POSTGRES_WINDOWS.bat' in std)
start=(R/'start_pet_quest.py').read_text(encoding='utf-8')
ck('start uses ready endpoint','/api/ready' in start)
ck('start does not force demo seed',"'PETQUEST_SEED_DEMO_DATA':'1'" not in start)
# PostgreSQL identity schema and checker
pgcode=(R/'postgres_auth.py').read_text(encoding='utf-8')
for token in ['CREATE TABLE IF NOT EXISTS pet_users','uq_pet_users_username_ci','uq_pet_users_email_ci','idx_pet_users_local_user','update_password_by_local_user']:
    ck('postgres auth '+token,token in pgcode)
checkcode=(R/'postgres_check.py').read_text(encoding='utf-8')
ck('postgres checker uses pet_users','pet_users' in checkcode and 'information_schema.columns' in checkcode)
# API mappings
api=(R/'api_server.py').read_text(encoding='utf-8')
for token in ["AUTH_DATABASE_ENGINE='postgres'",'postgres_auth.create_identity','postgres_auth.find_identity','postgres_auth.update_password_by_local_user',"INSERT INTO snapshots", "INSERT INTO learning_events", "INSERT INTO academic_error_events", "INSERT INTO academic_remediation_attempts", "INSERT INTO mock_attempts", "INSERT INTO mock_item_responses", "INSERT INTO speaking_attempts"]:
    ck('API mapping '+token,token in api)
ck('health exposes auth database',"'auth_database_engine':AUTH_DATABASE_ENGINE" in api and "'postgres_auth':pg_health" in api)
# UI registration/recovery
ux=(R/'v46_30_registration_ux.js').read_text(encoding='utf-8')
for token in ['registerName','registerUsername','registerEmail','registerPassword','registerPassword2','registerPermission','data-register','data-login','data-recover','data-reset-password','Generar contraseña segura']:
    ck('UI '+token,token in ux)
# JS refs/syntax
html=(R/'index.html').read_text(encoding='utf-8')
scripts=[x.split('?',1)[0] for x in re.findall(r'<script[^>]+src=["\']([^"\']+)["\']',html,re.I)]
missing=[s for s in scripts if not (R/s).exists()]
ck('all referenced scripts exist',not missing,missing)
bad=[]
for s in scripts:
    if s.endswith('.js'):
        p=subprocess.run(['node','--check',str(R/s)],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
        if p.returncode:bad.append(s)
ck('all referenced JS syntax',not bad,bad)
# Audio bank integrity
bank=json.loads((R/'PET_AUDIO_BANK_V46_18.json').read_text(encoding='utf-8'))
items=bank.get('items',[])
ck('audio bank 500',len(items)==500,len(items))
missing_audio=[x['id'] for x in items if not (R/x['audio_file']).is_file()]
ck('audio files present',not missing_audio,missing_audio[:5])
ck('audio current status truthful',bank.get('voice_policy',{}).get('synthetic_voice_simulation') is True and bank.get('voice_policy',{}).get('human_recordings') is False)
# Local SQLite package integrity
c=sqlite3.connect(R/'petquest.db')
integ=c.execute('PRAGMA integrity_check').fetchone()[0]
uc=c.execute('select count(*) from users').fetchone()[0]
c.close()
ck('SQLite integrity',integ=='ok',integ)
ck('release ships without test users',uc==0,uc)
print(f'ACCEPTANCE STATIC RESULT {sum(x[1] for x in checks)}/{len(checks)}')
sys.exit(0 if all(x[1] for x in checks) else 1)
