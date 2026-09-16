#!/usr/bin/env python3
import argparse, concurrent.futures, statistics, time, urllib.request, json

def hit(url):
    t=time.perf_counter()
    try:
        with urllib.request.urlopen(url,timeout=10) as r: ok=(r.status==200); r.read()
    except Exception: ok=False
    return ok,(time.perf_counter()-t)*1000

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--base-url',default='http://127.0.0.1:8080'); ap.add_argument('--requests',type=int,default=200); ap.add_argument('--workers',type=int,default=20); args=ap.parse_args()
    url=args.base_url.rstrip('/')+'/api/health'
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as ex: results=list(ex.map(lambda _:hit(url),range(args.requests)))
    times=[t for ok,t in results]; passed=sum(1 for ok,_ in results if ok); times_sorted=sorted(times)
    p95=times_sorted[max(0,min(len(times_sorted)-1,int(len(times_sorted)*0.95)-1))]
    out={'requests':args.requests,'workers':args.workers,'passed':passed,'p50_ms':round(statistics.median(times),2),'p95_ms':round(p95,2),'max_ms':round(max(times),2)}
    print(json.dumps(out,indent=2)); raise SystemExit(0 if passed==args.requests else 1)
if __name__=='__main__': main()
