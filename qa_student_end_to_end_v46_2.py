from pathlib import Path
import re, json, subprocess, sys, tempfile, os, time, urllib.request, urllib.error
ROOT=Path(__file__).resolve().parent
fails=[]; checks=[]
def ck(name,cond,detail=''):
 checks.append((name,bool(cond),detail));
 if not cond:fails.append((name,detail))

# 1) Syntax all JS
for p in sorted(ROOT.glob('*.js')):
 r=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
 ck('js:'+p.name,r.returncode==0,r.stderr[-400:])

app=(ROOT/'app.js').read_text()
alljs='\n'.join(p.read_text() for p in ROOT.glob('*.js'))
# 2) Student journey terminal behavior
ck('assignment status reads .done', "assignmentProgress?.[String(a.id)]?.done" in app)
ck('assignment starts false', "done:false" in app and 'activeAssignmentId' in app)
ck('assignment completes on session end', "assignmentProgress[id]={" in app and "done:true" in app)
ck('final level has terminal CTA', 'data-finish-skill' in app and 'Finalizar y volver al panel' in app)
ck('level3 no self-loop', "Math.min(3,state.level+1)" not in app)
ck('course completion persisted', 'courseCompletions' in app and 'finishSkillCourse' in app)
ck('speaking session completion', "completeLearningSession('speaking_complete')" in app)
ck('writing two-part completion', 'data-finish-writing' in (ROOT/'v41_academic_intelligence.js').read_text())

# 3) Exercise bank structural answerability (extract object literals approximately)
for skill in ('reading','listening'):
 m=re.search(rf'{skill}:\[(.*?)\]\s*(?:,\s*listening:|\}};)',app,re.S)
 if not m and skill=='listening':
  m=re.search(r'listening:\[(.*?)\]\s*\n\]};',app,re.S)
 block=m.group(1) if m else ''
 ids=re.findall(r"id:'([^']+)'",block)
 levels=[int(x) for x in re.findall(r'level:(\d+)',block)]
 answers=[int(x) for x in re.findall(r',a:(\d+),',block)]
 opts=[x for x in re.findall(r'opts:\[(.*?)\],a:',block,re.S)]
 ck(f'{skill} bank nonempty',len(ids)>0,str(len(ids)))
 ck(f'{skill} ids unique',len(ids)==len(set(ids)))
 ck(f'{skill} levels 1-3',set(levels)=={1,2,3},str(sorted(set(levels))))
 ck(f'{skill} answers count',len(answers)==len(ids),f'{len(answers)}/{len(ids)}')
 valid=True
 for a,o in zip(answers,opts):
  n=len(re.findall(r"'(?:[^'\\]|\\.)*'",o))
  if not (0<=a<n):valid=False;break
 ck(f'{skill} every item selectable',valid)

# 4) Click-action coverage: every button's primary data-* action has a handler reference.
meta={'data-disabled','data-fix-level','data-skill','data-rate','data-v32-value','data-v39-status','data-v43-rem-answer'}
buttons=[]
for p in [ROOT/'index.html',*ROOT.glob('*.js')]:
 txt=p.read_text()
 for tag in re.findall(r'<button\b[^>]*>',txt,re.I):
  attrs=re.findall(r'\b(data-[a-zA-Z0-9_-]+)(?:=(?:"[^"]*"|\'[^\']*\'|[^\s>]+))?',tag)
  acts=[a for a in attrs if a not in meta]
  if acts: buttons.append((p.name,acts[0],tag[:180]))
missing=[]
for f,a,tag in buttons:
 # handler is evidenced by at least another occurrence or explicit dataset camel-case access
 occ=alljs.count(a)
 camel=''.join([a.split('-')[1]]+[x.title() for x in a.split('-')[2:]]) if a.startswith('data-') else ''
 if occ<2 and ('.dataset.'+camel) not in alljs:
  missing.append((f,a,tag))
ck('click actions have handlers',not missing,repr(missing[:10]))

# 5) Exact mock fidelity regressions if scripts available
for qa in ['qa_v41_academic.py','qa_v43_ui.py','qa_v44_psychometrics.py','qa_v46_release_gate.py']:
 p=ROOT/qa
 if p.exists():
  r=subprocess.run([sys.executable,str(p)],cwd=ROOT,capture_output=True,text=True,timeout=120)
  ck('regression:'+qa,r.returncode==0,(r.stdout+r.stderr)[-500:])

# 6) API real user: launch isolated server, login student, sync a completed journey snapshot, read it back.
port='18181'; db=ROOT/'qa_e2e_v462.db'
try: db.unlink()
except: pass
env=os.environ.copy(); env.update({'PORT':port,'PETQUEST_SQLITE_PATH':str(db),'PETQUEST_ENV':'test','PETQUEST_DEV_MODE':'1','PETQUEST_SEED_DEMO_DATA':'1','PETQUEST_REQUIRE_GUARDIAN_CONSENT':'0'})
proc=subprocess.Popen([sys.executable,'api_server.py'],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
def req(path,method='GET',body=None,token=None):
 data=None if body is None else json.dumps(body).encode()
 h={'Content-Type':'application/json'}
 if token:h['Authorization']='Bearer '+token
 q=urllib.request.Request(f'http://127.0.0.1:{port}'+path,data=data,headers=h,method=method)
 with urllib.request.urlopen(q,timeout=5) as x:return x.status,json.loads(x.read().decode())
try:
 ok=False
 for _ in range(60):
  try:
   st,j=req('/api/ready'); ok=st==200; break
  except Exception:time.sleep(.1)
 ck('server ready',ok)
 st,j=req('/api/login','POST',{'email':'student@petquest.local','password':'Student123!'})
 token=j.get('token'); ck('student login',st==200 and bool(token))
 # Complete every base Reading/Listening item as a deterministic end-to-end data snapshot.
 hist=[]
 for skill in ('reading','listening'):
  # source IDs and correct answers from app source
  mm=re.search(rf'{skill}:\[(.*?)\]\s*(?:,\s*listening:|\}};)',app,re.S)
  if not mm and skill=='listening': mm=re.search(r'listening:\[(.*?)\]\s*\n\]};',app,re.S)
  block=mm.group(1)
  for om in re.finditer(r"\{id:'([^']+)'.*?level:(\d+).*?focus:'([^']+)'.*?opts:\[(.*?)\],a:(\d+),",block,re.S):
   qid,lev,focus,optsraw,a=om.groups();
   opts2=re.findall(r"'([^']*)'",optsraw); ai=int(a)
   hist.append({'date':'2026-08-25T12:00:00Z','qid':qid,'skill':skill,'level':int(lev),'focus':focus,'correct':True,'answer':ai,'answerText':opts2[ai] if ai<len(opts2) else ''})
 snapshot={'profile':{'name':'Student','xp':999,'role':'student'},'history':hist,'writing':[{'part':1,'score':16,'words':101},{'part':2,'score':17,'words':104}],'speaking':[{'part':1,'score':3},{'part':2,'score':3},{'part':3,'score':3},{'part':4,'score':3}],'studySessions':[{'skill':'reading','level':1,'completed':True},{'skill':'reading','level':2,'completed':True},{'skill':'reading','level':3,'completed':True},{'skill':'listening','level':1,'completed':True},{'skill':'listening','level':2,'completed':True},{'skill':'listening','level':3,'completed':True},{'skill':'writing','completed':True},{'skill':'speaking','completed':True}],'courseCompletions':{'reading':{'level':3},'listening':{'level':3}},'assignmentProgress':{}}
 st,j=req('/api/snapshot','POST',{'snapshot':snapshot},token); ck('completed journey sync',st==200 and j.get('ok') is True)
 st,j=req('/api/snapshot',token=token); got=j.get('snapshot') or {}; ck('completed journey readback',len(got.get('history',[]))==len(hist) and len(got.get('studySessions',[]))==8)
finally:
 proc.terminate();
 try:proc.wait(3)
 except:proc.kill()
 try: db.unlink()
 except: pass

print('\n'.join(('PASS' if ok else 'FAIL')+' '+name+((' :: '+detail) if detail and not ok else '') for name,ok,detail in checks))
print(f'\nTOTAL {sum(1 for _,x,_ in checks if x)}/{len(checks)} PASS')
if fails:
 print('FAILURES',json.dumps(fails,ensure_ascii=False,indent=2)); sys.exit(1)
