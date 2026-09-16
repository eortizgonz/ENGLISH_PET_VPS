"""Small stdlib-only concurrency smoke test; not a substitute for k6/Locust production load testing."""
import os,time,urllib.request,concurrent.futures,statistics
URL=os.environ.get('PETQUEST_HEALTH_URL','http://127.0.0.1:8080/api/health')
N=int(os.environ.get('PETQUEST_LOAD_REQUESTS','100'))
WORKERS=int(os.environ.get('PETQUEST_LOAD_WORKERS','10'))
def one(_):
    t=time.perf_counter()
    with urllib.request.urlopen(URL,timeout=5) as r:
        ok=r.status==200; r.read()
    return ok,(time.perf_counter()-t)*1000
with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as ex:
    rows=list(ex.map(one,range(N)))
lat=[x[1] for x in rows]
print({'requests':N,'workers':WORKERS,'ok':sum(1 for x in rows if x[0]),'p50_ms':round(statistics.median(lat),2),'p95_ms':round(sorted(lat)[max(0,int(len(lat)*.95)-1)],2),'max_ms':round(max(lat),2)})
