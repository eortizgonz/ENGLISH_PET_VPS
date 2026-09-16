from pathlib import Path
import os,sys,subprocess,time,json,urllib.request,sqlite3
R=Path(__file__).parent
port='8796'; db=R/'qa_error_dna_v4624.db'
try: db.unlink()
except: pass
env=os.environ.copy(); env.update({'PETQUEST_SQLITE_PATH':str(db),'PORT':port,'PETQUEST_DEV_MODE':'1','PETQUEST_SEED_DEMO_DATA':'1','PETQUEST_ENV':'development','PETQUEST_REQUIRE_GUARDIAN_CONSENT':'0'})
p=subprocess.Popen([sys.executable,'api_server.py'],cwd=R,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
def req(path,method='GET',data=None,token=None):
    body=None if data is None else json.dumps(data).encode(); h={'Content-Type':'application/json'}
    if token:h['Authorization']='Bearer '+token
    r=urllib.request.Request('http://127.0.0.1:'+port+path,data=body,headers=h,method=method)
    with urllib.request.urlopen(r,timeout=8) as x:return x.status,json.loads(x.read())
def ck(name,ok,checks): checks.append((name,bool(ok))); print(('PASS' if ok else 'FAIL'),name)
try:
    for _ in range(80):
        try:
            if req('/api/health')[0]==200:break
        except:time.sleep(.1)
    _,login=req('/api/login','POST',{'email':'student@petquest.local','password':'Student123!'})
    tok=login['token']; sid=login['user']['id']; checks=[]
    # Listening: corrected information 1/5 = 20% (primary); times 2/5 = 40%; opinion 4/5 = 80%.
    groups=[('corrected_information',5,1),('times',5,2),('opinion',5,4)]
    n=0
    for pat,total,good in groups:
        for i in range(total):
            n+=1; req('/api/events','POST',{'event_type':'practice_bank_answer','skill':'listening','item_id':f'{pat}-{i}','success':i<good,'meta':{'diagnostic_patterns':[pat],'target':'detail','grammar':'past_simple' if pat=='times' else 'present_simple'}},tok)
    # Reading evidence: inference 3/5 = 60%, detail 4/5 = 80%, cohesion 2/5 = 40%.
    for pat,good in [('inference',3),('detail',4),('cohesion',2)]:
        for i in range(5): req('/api/events','POST',{'event_type':'practice_bank_answer','skill':'reading','item_id':f'r-{pat}-{i}','success':i<good,'meta':{'diagnostic_patterns':[pat],'target':pat,'grammar':'past_simple'}},tok)
    # Academic past-simple error + 3 recent correct remediation attempts => green mastery signal.
    ev={'skill':'writing','part':1,'competence':'Grammar','subcompetence':'Past Simple','error_code':'past_simple_form','severity':'high','original_text':'Yesterday I go','correction':'Yesterday I went','mastery_proxy':35,'source':'qa-v46.24'}
    for _ in range(3): req('/api/academic-errors','POST',{'events':[ev]},tok)
    for ans in ('went','went','went'): req('/api/academic-remediation','POST',{'error_code':'past_simple_form','prompt':'Yesterday I ___','answer':ans,'correct':True,'source':'qa-v46.24'},tok)
    ev2={'skill':'writing','part':1,'competence':'Grammar','subcompetence':'Present Perfect','error_code':'present_perfect_form','severity':'high','original_text':'I have went','correction':'I have gone','mastery_proxy':35,'source':'qa-v46.24'}
    for _ in range(3): req('/api/academic-errors','POST',{'events':[ev2]},tok)
    for ans in ('gone','gone','gone'): req('/api/academic-remediation','POST',{'error_code':'present_perfect_form','prompt':'I have ___','answer':ans,'correct':True,'source':'qa-v46.24'},tok)
    # Writing rubric saved in snapshot.
    snap={'writing':[
      {'date':'2026-09-03T10:00:00Z','rubric':{'content':4,'communication':3,'organisation':3,'language':2},'score':12},
      {'date':'2026-09-03T11:00:00Z','rubric':{'content':5,'communication':4,'organisation':4,'language':3},'score':16},
      {'date':'2026-09-03T12:00:00Z','rubric':{'content':5,'communication':4,'organisation':4,'language':3},'score':16}
    ]}
    req('/api/snapshot','POST',{'snapshot':snap},tok)
    # Speaking: 3 attempts so all three nodes can be coloured.
    for flu,pron,inter in [(68,45,82),(72,50,85),(74,55,88)]:
        req('/api/speaking-attempts','POST',{'part':3,'mode':'practice','transcript':'I think this could be a good idea because it is useful. What do you think?','duration_ms':12000,'metrics':{'fluency':flu,'pronunciation_proxy':pron,'interaction':inter},'rubric':{'grammar_vocabulary':4,'discourse_management':4,'pronunciation':3,'interactive_communication':4,'global_achievement':4},'score_pct':76,'source':'qa-v46.24'},tok)
    st,dna=req('/api/error-dna',token=tok)
    ck('endpoint_200',st==200,checks); ck('version_46_24',dna.get('version')=='46.24',checks); ck('five_domains',len(dna.get('domains',[]))==5,checks)
    nodes={n['key']:n for dom in dna['domains'] for n in dom['nodes']}
    ck('corrected_red_20',nodes['listening:corrected_information']['status']=='critical' and nodes['listening:corrected_information']['score']==20.0,checks)
    ck('opinion_green_80',nodes['listening:opinion']['status']=='mastered' and nodes['listening:opinion']['score']==80.0,checks)
    ck('reading_inference_orange',nodes['reading:inference']['status']=='progress' and nodes['reading:inference']['score']==60.0,checks)
    ck('reading_detail_green',nodes['reading:detail']['status']=='mastered' and nodes['reading:detail']['score']==80.0,checks)
    ck('present_perfect_mastery_green',nodes['grammar:present_perfect']['status']=='mastered',checks)
    ck('writing_content_green',nodes['writing:content']['status']=='mastered',checks)
    ck('writing_language_orange',nodes['writing:language']['status']=='progress',checks)
    ck('speaking_pron_red',nodes['speaking:pronunciation']['status']=='critical',checks)
    ck('speaking_interaction_green',nodes['speaking:interaction']['status']=='mastered',checks)
    ck('primary_corrected_information',dna['primary_issue']['key']=='listening:corrected_information',checks)
    ck('practice_match_present',bool(nodes['listening:corrected_information']['practice_match']),checks)
    ck('insufficient_articles_grey',nodes['grammar:articles']['status']=='insufficient',checks)
    ck('pronunciation_warning',bool(dna.get('automatic_pronunciation_note')),checks)
    print(f'{sum(v for _,v in checks)}/{len(checks)} PASS')
    raise SystemExit(0 if all(v for _,v in checks) else 1)
finally:
    p.terminate()
    try:p.wait(timeout=3)
    except:p.kill()
