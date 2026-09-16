#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys, json, re, os
R=Path(__file__).resolve().parent
checks=[]
def ck(name, ok, detail=''):
    checks.append((name,bool(ok),detail))

# Static integrity
app=(R/'app.js').read_text(encoding='utf-8')
api=(R/'api_server.py').read_text(encoding='utf-8')
sw=(R/'sw.js').read_text(encoding='utf-8')
idx=(R/'index.html').read_text(encoding='utf-8')
docker=(R/'Dockerfile').read_text(encoding='utf-8')
ck('version_46_5', "APP_VERSION='46.6'" in api)
ck('no_window_top_collision', 'function top()' not in app and 'function topBar()' in app)
ck('docker_uses_current_server', 'CMD ["python3","api_server.py"]' in docker)
ck('pwa_cache_46_6', "petquest-v46-6" in sw)
ck('index_cache_bust_46_5', 'app.js?v=46.6' in idx)
ck('demo_seed_production_guard', 'PETQUEST_SEED_DEMO_DATA must be false in production' in api)
ck('production_postgres_guard', "runtime database engine is SQLite; PostgreSQL runtime migration is required before production" in api)
ck('local_windows_launcher', (R/'START_PET_QUEST_WINDOWS.bat').exists())
ck('local_shell_launcher', (R/'start_pet_quest.sh').exists())
ck('local_docker_compose', (R/'docker-compose.local.yml').exists())
# Loaded scripts exist
srcs=re.findall(r'<script src="([^"?]+)',idx)
missing=[s for s in srcs if not (R/s).exists()]
ck('all_index_scripts_present', not missing, repr(missing))
# JS syntax
for p in sorted(R.glob('*.js')):
    r=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
    ck('js:'+p.name,r.returncode==0,r.stderr[-250:])
# Python compile
for p in sorted(R.glob('*.py')):
    r=subprocess.run([sys.executable,'-m','py_compile',str(p)],capture_output=True,text=True)
    ck('py:'+p.name,r.returncode==0,r.stderr[-250:])
# Current regression suites
suite=['qa_v46_5_startup.py','qa_security_v46.py','qa_v43_mock_bank.py','qa_v41_academic.py','qa_v44_psychometrics.py','qa_v46_release_gate.py','qa_student_end_to_end_v46_2.py']
for q in suite:
    r=subprocess.run([sys.executable,str(R/q)],cwd=R,capture_output=True,text=True,timeout=180)
    ck('suite:'+q,r.returncode==0,(r.stdout+r.stderr)[-700:])
# Exam packs
for q in ['validate_exam_pack.py','validate_exam_pack_v43.py']:
    r=subprocess.run([sys.executable,str(R/q)],cwd=R,capture_output=True,text=True,timeout=60)
    ck('validator:'+q,r.returncode==0,(r.stdout+r.stderr)[-500:])
# Audio exists. Studio audio is intentionally an external commercial gate.
audio=list((R/'assets'/'audio').rglob('*.mp3'))
ck('reference_audio_present',len(audio)>=15,str(len(audio)))
failed=[x for x in checks if not x[1]]
for name,ok,detail in checks:
    print(('PASS' if ok else 'FAIL'),name,(':: '+detail if detail and not ok else ''))
print(f'\nMASTER TOTAL {len(checks)-len(failed)}/{len(checks)} PASS')
if failed:
    print(json.dumps([{'check':n,'detail':d} for n,_,d in failed],indent=2)); raise SystemExit(1)
