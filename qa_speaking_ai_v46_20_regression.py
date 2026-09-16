from pathlib import Path
import os, subprocess, sys, time, json, urllib.request, urllib.error, socket, sqlite3
ROOT=Path(__file__).resolve().parent
checks=[]
def ck(name,cond,detail=''):
    checks.append((name,bool(cond),detail))
    if not cond: print('FAIL',name,detail)
js=(ROOT/'v46_14_speaking_ai_examiner.js').read_text()
api=(ROOT/'api_server.py').read_text()
idx=(ROOT/'index.html').read_text()
for term in ['MediaRecorder','getUserMedia','SpeechRecognition','long_pauses','hesitations','restarts','grammar','vocabulary_range','discourse_markers','pronunciation_proxy','intelligibility','stress_variation','intonation_variation','response_length','interaction','appropriate_fillers','words per minute' if False else 'wpm']:
    ck('js_metric:'+term,term in js)
for crit in ['grammar_vocabulary','discourse_management','pronunciation','interactive_communication','global_achievement']:
    ck('rubric:'+crit,crit in js)
ck('automatic_not_official','Automático ≠ oficial' in js and 'no equivale a una calificación oficial Cambridge' in js)
ck('audio_local_privacy','indexedDB' in js and 'solo en este dispositivo' in js)
ck('server_table','CREATE TABLE IF NOT EXISTS speaking_attempts' in api)
ck('server_post',"if p=='/api/speaking-attempts':" in api and 'INSERT INTO speaking_attempts' in api)
ck('server_get','SELECT id,part,mode,transcript,duration_ms,metrics_json,rubric_json,score_pct' in api)
ck('privacy_purge',"DELETE FROM speaking_attempts WHERE student_id=?" in api)
ck('privacy_export',"'speaking_attempts':[dict(x) for x in speaking]" in api)
ck('guardian_consent','guardian_consent_required' in api and "if p=='/api/speaking-attempts'" in api)
ck('loaded', 'v46_14_speaking_ai_examiner.js?v=46.20' in idx)
r=subprocess.run(['node','--check',str(ROOT/'v46_14_speaking_ai_examiner.js')],capture_output=True,text=True)
ck('node_syntax',r.returncode==0,r.stderr)
# Runtime persistence with consent disabled in isolated DB.
s=socket.socket(); s.bind(('127.0.0.1',0)); port=s.getsockname()[1]; s.close()
db=ROOT/'.qa_speaking_v4614.db'
try: db.unlink()
except FileNotFoundError: pass
env=os.environ.copy();env.update({'PORT':str(port),'PETQUEST_ENV':'test','PETQUEST_SQLITE_PATH':str(db),'SEED_DEMO_DATA':'1','PETQUEST_REQUIRE_GUARDIAN_CONSENT':'0'})
proc=subprocess.Popen([sys.executable,str(ROOT/'api_server.py')],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
def request(path,data=None,token=None):
    h={'Content-Type':'application/json'}
    if token:h['Authorization']='Bearer '+token
    q=urllib.request.Request(f'http://127.0.0.1:{port}{path}',data=json.dumps(data).encode() if data is not None else None,headers=h,method='POST' if data is not None else 'GET')
    with urllib.request.urlopen(q,timeout=4) as x:return x.status,json.loads(x.read())
try:
    ready=False
    for _ in range(30):
        try:
            st,h=request('/api/health');ready=True;break
        except Exception: time.sleep(.15)
    ck('server_ready',ready)
    ck('health_version',ready and h.get('version')=='46.20',str(h if ready else ''))
    st,login=request('/api/login',{'email':'student@petquest.local','password':'Student123!'})
    token=login['token']; ck('login',st==200)
    payload={'part':3,'mode':'exam','transcript':'Well, I think we could have a picnic because everyone can join. What about the sports hall if it rains? I agree, so let us choose that in the end.','duration_ms':42000,'metrics':{'fluency':84,'wpm':112.4,'long_pauses':1,'hesitations':1,'restarts':0,'grammar':86,'vocabulary_range':80,'discourse_markers':5,'pronunciation_proxy':82,'intelligibility':88,'stress_variation':70,'intonation_variation':75,'response_length':90,'interaction':92,'appropriate_fillers':1},'rubric':{'grammar_vocabulary':4,'discourse_management':4,'pronunciation':4,'interactive_communication':5,'global_achievement':4},'score_pct':84,'audio_local_key':'u1-p3-qa','source':'v46.14-speaking-ai'}
    st,p=request('/api/speaking-attempts',payload,token);ck('post_attempt',st==201 and p.get('id'),str(p))
    st,g=request('/api/speaking-attempts',None,token); a=(g.get('attempts') or [{}])[0];ck('readback',a.get('score_pct')==84.0 and a.get('metrics',{}).get('wpm')==112.4 and a.get('rubric',{}).get('interactive_communication')==5,str(a))
    st,prep=request('/api/my-preparation',None,token);ck('preparation_speaking',prep.get('skills',{}).get('speaking')==84.0,str(prep.get('skills')))
    con=sqlite3.connect(db); con.row_factory=sqlite3.Row; row=con.execute('select student_id,part,score_pct,source from speaking_attempts order by id desc limit 1').fetchone(); fk=con.execute('pragma foreign_key_check').fetchall(); con.close();ck('db_row',row and row['part']==3 and row['score_pct']==84.0 and row['source']=='v46.14-speaking-ai',str(dict(row) if row else None));ck('foreign_keys',not fk,str(fk))
finally:
    proc.terminate()
    try: proc.wait(timeout=3)
    except: proc.kill()
    try: db.unlink()
    except: pass
print(f'PET Quest V46.14 Speaking AI QA: {sum(o for _,o,_ in checks)}/{len(checks)} PASS')
if not all(o for _,o,_ in checks): raise SystemExit(1)
