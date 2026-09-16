from pathlib import Path
import os,sys,re,json,time,subprocess,urllib.request,urllib.error
ROOT=Path(__file__).resolve().parent
PORT='18186'; DB=ROOT/'qa_runtime_http_v466.db'
try: DB.unlink()
except: pass
env=os.environ.copy(); env.update({'PORT':PORT,'PETQUEST_SQLITE_PATH':str(DB),'PETQUEST_ENV':'test','PETQUEST_DEV_MODE':'1','PETQUEST_SEED_DEMO_DATA':'1','PETQUEST_REQUIRE_GUARDIAN_CONSENT':'0'})
proc=subprocess.Popen([sys.executable,'api_server.py'],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
def req(path,method='GET',body=None,token=None,raw=False):
    data=None if body is None else json.dumps(body).encode(); h={}
    if body is not None:h['Content-Type']='application/json'
    if token:h['Authorization']='Bearer '+token
    r=urllib.request.urlopen(urllib.request.Request(f'http://127.0.0.1:{PORT}{path}',data=data,headers=h,method=method),timeout=5)
    b=r.read(); return (r.status,b) if raw else json.loads(b or b'{}')
try:
    for _ in range(80):
        try:
            h=req('/api/health'); break
        except: time.sleep(.1)
    assert h['version']=='46.6'
    idx=(ROOT/'index.html').read_text(); files=set(re.findall(r'(?:src|href)=["\']([^"\']+)',idx))
    files={x.split('?')[0] for x in files if not x.startswith(('http:','https:','#'))}
    for f in sorted(files):
        st,b=req('/'+f.lstrip('./'),raw=True); assert st==200 and len(b)>0,(f,st,len(b))
    # all packaged listening audio
    for p in sorted((ROOT/'audio').glob('*.mp3')):
        st,b=req('/audio/'+p.name,raw=True); assert st==200 and len(b)>100,(p.name,st,len(b))
    creds={'student':('student@petquest.local','Student123!'),'teacher':('teacher@petquest.local','Teacher123!'),'school':('school@petquest.local','School123!'),'admin':('admin@petquest.local','Admin123!')}
    tokens={}
    for role,(email,pw) in creds.items():
        j=req('/api/login','POST',{'email':email,'password':pw}); assert j['user']['role']==role; tokens[role]=j['token']; assert req('/api/me',token=j['token'])['user']['role']==role
    # student-facing synchronized screens
    t=tokens['student']
    for path in ['/api/snapshot','/api/assignments']:
        req(path,token=t)
    # teacher/school/admin operational screens
    for role in ['teacher','school','admin']:
        t=tokens[role]
        for path in ['/api/classes','/api/courses','/api/report','/api/school-intelligence','/api/class-intelligence','/api/support-groups']:
            try:req(path,token=t)
            except urllib.error.HTTPError as e:
                if e.code not in (400,404): raise
    # school/admin production/release panels
    for role in ['school','admin']:
        t=tokens[role]
        for path in ['/api/production-gate','/api/release-readiness','/api/governance','/api/strategy-forecast','/api/budget-optimizer','/api/portfolio-optimizer','/api/schedule-planner']:
            try:req(path,token=t)
            except urllib.error.HTTPError as e:
                if e.code not in (400,404): raise
    print('PET Quest V46.6 Runtime HTTP QA: PASS')
finally:
    proc.terminate()
    try:proc.wait(timeout=5)
    except:proc.kill()
