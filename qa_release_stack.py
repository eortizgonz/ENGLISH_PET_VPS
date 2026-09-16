#!/usr/bin/env python3
import argparse, json, urllib.request, urllib.error

def get(url, headers=None):
    req=urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.status, dict(r.headers), json.loads(r.read().decode()) if 'application/json' in r.headers.get('Content-Type','') else r.read().decode()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--base-url',default='http://127.0.0.1:8080'); args=ap.parse_args()
    base=args.base_url.rstrip('/')
    checks=[]
    status,headers,health=get(base+'/api/health')
    checks.append(('health_http_200',status==200))
    checks.append(('health_ok',bool(health.get('ok'))))
    checks.append(('version_current',str(health.get('version'))=='46.2'))
    status,headers,ready=get(base+'/api/ready')
    checks.append(('ready_http_200',status==200))
    checks.append(('database_ready',bool(ready.get('database'))))
    hstatus,hheaders,_=get(base+'/')
    required=['X-Content-Type-Options','X-Frame-Options','Referrer-Policy','Content-Security-Policy','Permissions-Policy','X-PETQuest-Version']
    for key in required: checks.append((f'header_{key.lower()}', bool(hheaders.get(key))))
    failed=[name for name,ok in checks if not ok]
    print(json.dumps({'base_url':base,'checks':checks,'passed':len(checks)-len(failed),'total':len(checks),'failed':failed},indent=2))
    raise SystemExit(1 if failed else 0)
if __name__=='__main__': main()
