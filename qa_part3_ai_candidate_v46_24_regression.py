from pathlib import Path
import os, subprocess, sys, time, json, urllib.request, socket, sqlite3
ROOT=Path(__file__).resolve().parent
checks=[]
def ck(n,c,d=''):
    checks.append((n,bool(c),d))
    if not c: print('FAIL',n,d)
js=(ROOT/'v46_15_part3_ai_candidate.js').read_text(); api=(ROOT/'api_server.py').read_text(); idx=(ROOT/'index.html').read_text()
for term in ['suggestion','agreement','disagreement','justification','turn_taking','negotiation','final_decision','AI Candidate','speechSynthesis','SpeechRecognition']:
    ck('feature:'+term,term in js)
ck('loaded','v46_15_part3_ai_candidate.js?v=46.24' in idx)
ck('version',"APP_VERSION='46.24'" in api)
ck('tables','speaking_interaction_sessions' in api and 'speaking_interaction_turns' in api)
ck('api_get',"if p=='/api/speaking-interactions':" in api)
ck('privacy','DELETE FROM speaking_interaction_sessions WHERE student_id=?' in api)
r=subprocess.run(['node','--check',str(ROOT/'v46_15_part3_ai_candidate.js')],capture_output=True,text=True);ck('node',r.returncode==0,r.stderr)
# runtime
sock=socket.socket();sock.bind(('127.0.0.1',0));port=sock.getsockname()[1];sock.close();db=ROOT/'.qa_v4615.db'
try: db.unlink()
except: pass
env=os.environ.copy();env.update({'PORT':str(port),'PETQUEST_ENV':'test','PETQUEST_SQLITE_PATH':str(db),'SEED_DEMO_DATA':'1','PETQUEST_REQUIRE_GUARDIAN_CONSENT':'0'})
proc=subprocess.Popen([sys.executable,str(ROOT/'api_server.py')],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
def req(path,data=None,token=None):
    h={'Content-Type':'application/json'}
    if token:h['Authorization']='Bearer '+token
    q=urllib.request.Request(f'http://127.0.0.1:{port}{path}',data=json.dumps(data).encode() if data is not None else None,headers=h,method='POST' if data is not None else 'GET')
    with urllib.request.urlopen(q,timeout=5) as x:return x.status,json.loads(x.read())
try:
    h={}
    for _ in range(40):
        try: st,h=req('/api/health');break
        except: time.sleep(.15)
    ck('health',h.get('version')=='46.24',str(h))
    st,l=req('/api/login',{'email':'student@petquest.local','password':'Student123!'});tok=l['token'];ck('login',st==200)
    turns=[
      {'role':'ai','text':'I think going to the cinema could be a good idea. What do you think?','functions':{}},
      {'role':'student','text':'I agree, but it could be expensive because tickets cost a lot.','functions':{'agreement':True,'disagreement':True,'justification':True}},
      {'role':'ai','text':'How about having a picnic instead?','functions':{}},
      {'role':'student','text':'That is a good idea. We could have a picnic in the park.','functions':{'agreement':True,'suggestion':True}},
      {'role':'ai','text':'Which is better for everyone?','functions':{}},
      {'role':'student','text':'The picnic is better because it is cheaper, although the cinema is good if it rains.','functions':{'justification':True,'disagreement':True}},
      {'role':'ai','text':'Shall we make a final decision?','functions':{}},
      {'role':'student','text':'So let us choose the picnic. We agree that it is the best option.','functions':{'final_decision':True,'agreement':True}}
    ]
    metrics={'coverage':{'suggestion':True,'agreement':True,'disagreement':True,'justification':True,'turn_taking':True,'negotiation':True,'final_decision':True},'score':100,'interactive_communication':5,'student_turns':4,'ai_turns':4}
    rubric={'interactive_communication':5}
    st,p=req('/api/speaking-interactions',{'scenario_id':'free_afternoon','scenario_title':'Plan a free afternoon','turns':turns,'metrics':metrics,'rubric':rubric,'score_pct':100,'source':'v46.15-part3-ai-candidate'},tok);ck('post',st==201 and p.get('id'),str(p));sid=p.get('id')
    st,g=req('/api/speaking-interactions',None,tok); sess=(g.get('sessions') or [{}])[0];ck('readback',sess.get('id')==sid and len(sess.get('turns') or [])==8 and sess.get('metrics',{}).get('score')==100,str(sess))
    con=sqlite3.connect(db);con.row_factory=sqlite3.Row
    sr=con.execute('select * from speaking_interaction_sessions where id=?',(sid,)).fetchone();tc=con.execute('select count(*) n from speaking_interaction_turns where session_id=?',(sid,)).fetchone()['n'];sp=con.execute("select score_pct,source from speaking_attempts where source='v46.15-part3-ai-candidate' order by id desc limit 1").fetchone();fk=con.execute('pragma foreign_key_check').fetchall();con.close()
    ck('session_row',sr and sr['student_id']>0 and sr['score_pct']==100,str(dict(sr) if sr else None));ck('turn_rows',tc==8,str(tc));ck('prep_evidence',sp and sp['score_pct']==100 and sp['source']=='v46.15-part3-ai-candidate',str(dict(sp) if sp else None));ck('fk',not fk,str(fk))
finally:
    proc.terminate()
    try:proc.wait(timeout=3)
    except:proc.kill()
    try:db.unlink()
    except:pass
print(f'PET Quest V46.15 Part 3 AI Candidate QA: {sum(x[1] for x in checks)}/{len(checks)} PASS')
if not all(x[1] for x in checks):raise SystemExit(1)
