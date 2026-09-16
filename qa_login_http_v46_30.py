from pathlib import Path
import os, subprocess, time, urllib.request, urllib.error, json, sys
ROOT=Path(__file__).resolve().parent
PORT=8097
ENV=os.environ.copy();ENV.update({'PETQUEST_ENV':'development','PETQUEST_DEV_MODE':'1','PETQUEST_SEED_DEMO_DATA':'1','PETQUEST_HOST':'127.0.0.1','PORT':str(PORT)})
P=subprocess.Popen([sys.executable,'api_server.py'],cwd=ROOT,env=ENV,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
base=f'http://127.0.0.1:{PORT}/api'
def req(path,method='GET',body=None,token=None):
    data=json.dumps(body).encode() if body is not None else None
    h={'Content-Type':'application/json'}
    if token:h['Authorization']='Bearer '+token
    r=urllib.request.Request(base+path,data=data,headers=h,method=method)
    t=time.perf_counter()
    try:
        with urllib.request.urlopen(r,timeout=5) as x:return x.status,json.loads(x.read() or b'{}'),time.perf_counter()-t
    except urllib.error.HTTPError as e:return e.code,json.loads(e.read() or b'{}'),time.perf_counter()-t
try:
    for _ in range(100):
        try:
            st,_,_=req('/health')
            if st==200:break
        except Exception:pass
        time.sleep(.1)
    checks=[]
    st,h,dt=req('/health');checks.append(('health',st==200 and h.get('version')=='46.30',dt))
    st,l,dt=req('/login','POST',{'email':'student@petquest.local','password':'Student123!'});checks.append(('login',st==200 and bool(l.get('token')),dt));tok=l.get('token','')
    for path in ['/me','/snapshot','/courses','/assignments','/my-preparation']:
        st,j,dt=req(path,token=tok);checks.append((path,st==200,dt))
    # privileged endpoints stay server-protected; V46.30 client guard prevents these calls for students.
    st,_,dt=req('/release-readiness',token=tok);checks.append(('student_release_readiness_forbidden',st==403,dt))
    for n,ok,dt in checks:print(('PASS' if ok else 'FAIL'),n,f'{dt*1000:.0f}ms')
    print('RESULT',sum(x[1] for x in checks),'/',len(checks))
    sys.exit(0 if all(x[1] for x in checks) else 1)
finally:
    P.terminate()
    try:P.wait(timeout=4)
    except: P.kill()
