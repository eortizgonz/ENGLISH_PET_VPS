"""Smoke/E2E test for a running PET Quest V9 server. Set PETQUEST_TEST_URL if needed."""
import json, os, urllib.request, urllib.error
BASE=os.environ.get('PETQUEST_TEST_URL','http://127.0.0.1:8080/api')
def req(path,method='GET',body=None,token=None):
    data=json.dumps(body).encode() if body is not None else None
    h={'Content-Type':'application/json'}
    if token:h['Authorization']='Bearer '+token
    r=urllib.request.Request(BASE+path,data=data,headers=h,method=method)
    try:
        with urllib.request.urlopen(r,timeout=5) as x:return x.status,json.loads(x.read().decode())
    except urllib.error.HTTPError as e:
        return e.code,json.loads(e.read().decode())

def main():
    _,h=req('/health'); assert h['version']=='9.0'
    _,r=req('/ready'); assert r.get('checks',{}).get('database') is True
    _,a=req('/login','POST',{'email':'admin@petquest.local','password':'Admin123!'}); at=a['token']
    _,m=req('/metrics',token=at); assert m['stats']['users']>=4
    _,users=req('/users?all=1',token=at); student=next(x for x in users['users'] if x['role']=='student')
    _,s=req('/login','POST',{'email':'student@petquest.local','password':'Student123!'}); st=s['token']
    status,blocked=req('/snapshot','POST',{'snapshot':{'history':[{'correct':True}]}},st); assert status==403 and blocked['error']=='guardian_consent_required'
    status,c=req('/consents','POST',{'student_id':student['id'],'guardian_name':'QA Guardian','guardian_email':'guardian@example.com','consent_version':'qa-v8'},at); assert status==201
    status,sync=req('/snapshot','POST',{'snapshot':{'history':[{'correct':True}]}},st); assert status==200 and sync['ok']
    _,b=req('/backup','POST',{},at); assert b['bytes']>0
    print('PET Quest V9 compatibility QA OK')
if __name__=='__main__':main()
