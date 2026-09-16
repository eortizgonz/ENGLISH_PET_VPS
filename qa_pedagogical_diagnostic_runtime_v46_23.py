from pathlib import Path
import os,sys,subprocess,time,json,urllib.request,urllib.error,tempfile
R=Path(__file__).parent
port='8792'; db=R/'qa_diag_v4623.db'
try: db.unlink()
except: pass
env=os.environ.copy(); env.update({'PETQUEST_SQLITE_PATH':str(db),'PORT':port,'PETQUEST_DEV_MODE':'1','PETQUEST_SEED_DEMO_DATA':'1','PETQUEST_ENV':'development'})
p=subprocess.Popen([sys.executable,'api_server.py'],cwd=R,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
def req(path,method='GET',data=None,token=None):
    b=None if data is None else json.dumps(data).encode(); h={'Content-Type':'application/json'}
    if token:h['Authorization']='Bearer '+token
    r=urllib.request.Request('http://127.0.0.1:'+port+path,data=b,headers=h,method=method)
    with urllib.request.urlopen(r,timeout=5) as x:return x.status,json.loads(x.read())
try:
    for _ in range(60):
        try:
            if req('/api/health')[0]==200:break
        except:time.sleep(.1)
    _,login=req('/api/login','POST',{'email':'student@petquest.local','password':'Student123!'})
    tok=login['token']
    # Exact target counts: gist 8/9=88.9, numbers 5/12=41.7, times 3/8=37.5,
    # opinion 5/7=71.4, corrected 7/20=35.0, spelling 7/12=58.3. Listening overall = 31/50=62%.
    specs=[('gist',9,8,'listening'),('numbers',12,5,'listening'),('times',8,3,'listening'),('opinion',7,5,'listening'),('corrected_information',20,7,'listening'),('spelling',12,7,'reading')]
    # Avoid double-counting overall by making first five listening groups total 56; target example overall is independent.
    # Add direct 50 listening events separately with neutral pattern for exact 62%; patterns remain exact.
    # Instead, use only 50 listening events arranged across first five by denominator: 9+8+7+20+6=50; numbers is overlapping tag on 12 of them.
    # Rebuild event plan explicitly.
    events=[]
    def add(pattern,n,ok,skill='listening',extra=None):
        for i in range(n): events.append((skill,i<ok,[pattern]+(extra or [])))
    # 9 gist (8 correct), 8 times (3 correct, all tagged numbers for first 8), 7 opinion (5), 20 corrected (7, first 4 also numbers), 6 neutral detail (8 correct impossible -> choose 8? no)
    # Correct sum first four: 8+3+5+7=23 across 44. Need 8 more correct across 6 -> impossible. So exact skill 62 is not coupled to pattern example; test endpoint percentages independently using separate skills would be messy.
    # Use 50 listening events with 31 correct and attach patterns as overlapping tags to subsets while preserving subset ratios.
    for i in range(50):
        success=i in set(list(range(31)))
        pats=[]
        # Construct subsets with desired correct counts by explicit indices.
        gist_idx=[0,1,2,3,4,5,6,7,40]; gist_ok=set(range(8))
        num_idx=[0,1,2,3,4,31,32,33,34,35,36,37]
        time_idx=[0,1,2,31,32,33,34,35]
        opin_idx=[0,1,2,3,4,31,32]
        corr_idx=[0,1,2,3,4,5,6]+list(range(31,44))
        if i in gist_idx:pats.append('gist')
        if i in num_idx:pats.append('numbers')
        if i in time_idx:pats.append('times')
        if i in opin_idx:pats.append('opinion')
        if i in corr_idx:pats.append('corrected_information')
        if not pats:pats=['detail']
        req('/api/events','POST',{'event_type':'practice_bank_answer','skill':'listening','item_id':'seed-'+str(i),'success':success,'minutes':.2,'meta':{'diagnostic_patterns':pats,'source':'qa-v46.23'}},tok)
    # spelling 12, 7 correct, reading
    for i in range(12):req('/api/events','POST',{'event_type':'practice_bank_answer','skill':'reading','item_id':'spell-'+str(i),'success':i<7,'meta':{'diagnostic_patterns':['spelling']}},tok)
    _,d=req('/api/practice-diagnostic',token=tok)
    pmap={x['pattern']:x for x in d['patterns']}
    checks=[('listening_62',d['skills']['listening']['accuracy']==62.0),('gist_88_9',pmap['gist']['accuracy']==88.9),('numbers_41_7',pmap['numbers']['accuracy']==41.7),('times_37_5',pmap['times']['accuracy']==37.5),('opinion_71_4',pmap['opinion']['accuracy']==71.4),('corrected_35',pmap['corrected_information']['accuracy']==35.0),('spelling_58_3',pmap['spelling']['accuracy']==58.3),('primary_corrected',d['primary_issue']['pattern']=='corrected_information'),('min_evidence_3',d['min_evidence']==3)]
    for n,v in checks:print(('PASS' if v else 'FAIL'),n)
    print(f'{sum(v for _,v in checks)}/{len(checks)} PASS');sys.exit(0 if all(v for _,v in checks) else 1)
finally:
    p.terminate();
    try:p.wait(timeout=3)
    except:p.kill()
