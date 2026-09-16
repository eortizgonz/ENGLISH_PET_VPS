#!/usr/bin/env python3
import argparse, json, urllib.request, urllib.error

def request(url, method='GET', data=None, headers=None):
    body=None if data is None else json.dumps(data).encode()
    h={'Content-Type':'application/json'}; h.update(headers or {})
    req=urllib.request.Request(url,data=body,headers=h,method=method)
    try:
        with urllib.request.urlopen(req,timeout=10) as r: return r.status,dict(r.headers),r.read().decode()
    except urllib.error.HTTPError as e: return e.code,dict(e.headers),e.read().decode()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--base-url',default='http://127.0.0.1:8080'); args=ap.parse_args(); b=args.base_url.rstrip('/')
    checks=[]
    s,h,_=request(b+'/api/courses'); checks.append(('private_endpoint_requires_auth',s==401))
    s,h,_=request(b+'/api/login','POST',{'email':'nobody@example.invalid','password':'wrong'}); checks.append(('bad_login_rejected',s in (400,401,403,429)))
    s,h,_=request(b+'/');
    checks += [('frame_denied',h.get('X-Frame-Options')=='DENY'),('nosniff',h.get('X-Content-Type-Options')=='nosniff'),('csp_present','Content-Security-Policy' in h),('permissions_policy','Permissions-Policy' in h)]
    failed=[x for x,ok in checks if not ok]
    print(json.dumps({'checks':checks,'failed':failed},indent=2)); raise SystemExit(1 if failed else 0)
if __name__=='__main__': main()
