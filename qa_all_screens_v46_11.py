from pathlib import Path
import re, subprocess, sys, json, os, time, urllib.request, urllib.error
ROOT=Path(__file__).resolve().parent
checks=[]; fails=[]
def ck(name, cond, detail=''):
    ok=bool(cond); checks.append((name,ok,detail))
    if not ok: fails.append((name,detail))

app=(ROOT/'app.js').read_text()
v10=(ROOT/'v10_ux.js').read_text(); v11=(ROOT/'v11_ux.js').read_text(); idx=(ROOT/'index.html').read_text(); sw=(ROOT/'sw.js').read_text()
# Core route registry and screen implementations
m=re.search(r"\(\{([^}]+)\}\[state\.view\]\|\|home\)\(\)",app)
routes=[]
if m: routes=[x.strip() for x in m.group(1).split(',') if x.strip()]
required=['home','dashboard','practice','answers','writing','speaking','plan','wordbook','mock','settings','parent','teacher','school','account','review','achievements','login','assignments','reports','cms']
ck('route_registry_found',bool(routes),str(routes))
for r in required:
    ck('route:'+r,r in routes and re.search(rf'function\s+{re.escape(r)}\s*\(',app) is not None)
# All literal data-view targets must be registered or extension screens assigned in later layers.
alljs='\n'.join(p.read_text(errors='ignore') for p in ROOT.glob('*.js'))
view_targets=set(re.findall(r'data-view=["\']([A-Za-z0-9_-]+)["\']', idx+'\n'+alljs))
extension_views=set(re.findall(r"state\.view\s*===?\s*['\"]([A-Za-z0-9_-]+)['\"]",alljs)) | set(re.findall(r"state\.view\s*=\s*['\"]([A-Za-z0-9_-]+)['\"]",alljs)) | {'security','recover','resetPassword','admin','privacy'}
for v in sorted(view_targets): ck('view_target:'+v, v in routes or v in extension_views, 'unregistered literal view')
# Regression: child mode must never hide main.container.
ck('kid_no_parent_main_hide', "firstTitle.parentElement.style.display='none'" not in v11)
ck('kid_hides_only_heading', "firstTitle.style.display='none'" in v11)
ck('kid_main_visibility_failsafe', "if(main)main.style.display=''" in v11)
ck('kid_adult_switch_present', 'data-ux-mode="kid"' in v10 and 'data-ux-mode="adult"' in v10 and "setUxMode(mode)" in v10)
ck('kid_home_replacement_present', 'v11-map' in v11 and 'v10-welcome' in v10)
ck('no_window_top_collision', re.search(r'function\s+top\s*\(',alljs) is None)
# Every JS included by index exists and syntax-checks.
scripts=re.findall(r'<script\s+src=["\']([^"\'?]+)',idx)
for s in scripts:
    p=ROOT/s; ck('script_exists:'+s,p.exists())
    if p.exists():
        r=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
        ck('script_syntax:'+s,r.returncode==0,r.stderr[-300:])
# Referenced local assets should exist. Ignore API/runtime-generated URLs.
refs=set(re.findall(r"(?:src=|href=)[\"']((?:assets|audio)/[^\"'?]+)", idx+'\n'+alljs))
refs |= set(re.findall(r"['\"]((?:assets|audio)/[^'\"?]+\.(?:svg|png|jpg|jpeg|webp|mp3|wav))['\"]",alljs,re.I))
for ref in sorted(refs): ck('asset:'+ref,(ROOT/ref).exists())
# SW cache and version must be current.
ck('sw_cache_46_8',"petquest-v46-10" in sw)
ck('index_version_46_8','v=46.11' in idx)
ck('backend_version_46_8',"APP_VERSION='46.11'" in (ROOT/'api_server.py').read_text())
# Child mode modules expected for guided journey.
for f in ['v10_ux.js','v11_ux.js','v12_ux.js','v13_adaptive.js','v14_tutor.js','v15_autonomy.js','v16_speaking_writing.js','v17_conversation.js','v18_listening.js','v19_reading.js','v20_full_journey.js','v21_weekly_evolution.js','v22_adult_intelligence.js','v23_retention.js','v24_portfolio.js','v25_personal_path.js']:
    ck('guided_layer:'+f,(ROOT/f).exists())
# High value regression suites.
for qa in ['qa_v46_11_startup.py','qa_student_end_to_end_v46_2.py','qa_security_v46_11.py','qa_v43_mock_bank.py','qa_v41_academic.py','qa_v44_psychometrics.py','qa_backup_restore_v46.py']:
    p=ROOT/qa
    if not p.exists(): ck('suite:'+qa,False,'missing'); continue
    try:
        r=subprocess.run([sys.executable,str(p)],cwd=ROOT,capture_output=True,text=True,timeout=180)
        ck('suite:'+qa,r.returncode==0,(r.stdout+r.stderr)[-600:])
    except subprocess.TimeoutExpired:
        ck('suite:'+qa,False,'timeout')
print(f'PET Quest V46.11 Screen Integrity QA: {sum(x[1] for x in checks)}/{len(checks)} PASS')
for n,ok,d in checks:
    if not ok: print('FAIL',n,d)
if fails: raise SystemExit(1)
