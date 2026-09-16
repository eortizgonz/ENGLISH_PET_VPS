import os,tempfile,importlib.util,json,sys
from pathlib import Path
R=Path(__file__).resolve().parent
fd,db=tempfile.mkstemp(prefix='pq4627_',suffix='.db'); os.close(fd); os.unlink(db)
os.environ['PETQUEST_SQLITE_PATH']=db
os.environ['PETQUEST_APP_ENV']='test'
os.environ['PETQUEST_SEED_DEMO_DATA']='1'
spec=importlib.util.spec_from_file_location('api4627',R/'api_server.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); m.init_db()
c=m.conn(); st=c.execute("SELECT id,school_id FROM users WHERE role='student' ORDER BY id LIMIT 1").fetchone(); sid,school=st['id'],st['school_id']
payload={'profile':{'examProfile':'adult','masteryGoal':'excellent','examDate':'2026-09-22'},'history':[
 {'qid':'r1','skill':'reading','correct':False},{'qid':'r1','skill':'reading','correct':False},{'qid':'r1','skill':'reading','correct':True},
 {'qid':'r2','skill':'reading','correct':True},{'qid':'l1','skill':'listening','correct':False},{'qid':'l1','skill':'listening','correct':False},{'qid':'l2','skill':'listening','correct':True}
], 'writing':[{'score':16}], 'speaking':[{'score':4}]}
c.execute('INSERT OR REPLACE INTO snapshots(user_id,payload,updated_at) VALUES(?,?,?)',(sid,json.dumps(payload),m.now()))
for i in range(2): c.execute('INSERT INTO academic_error_events(student_id,skill,part,competence,subcompetence,error_code,severity,original_text,correction,mastery_proxy,occurred_at,source) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(sid,'listening',2,'detail','corrected information','L-CORRECTED','high','x','y',0.2,m.now(),'qa'))
c.execute('INSERT INTO academic_remediation_attempts(student_id,error_code,prompt,answer,correct,attempted_at,source) VALUES(?,?,?,?,?,?,?)',(sid,'L-CORRECTED','p','a',1,m.now(),'qa'))
c.execute('INSERT INTO learning_events(user_id,event_type,skill,item_id,success,minutes,meta_json,created_at) VALUES(?,?,?,?,?,?,?,?)',(sid,'practice_bank_answer','listening','x',0,7.5,'{}',m.now()))
c.execute('INSERT INTO learning_events(user_id,event_type,skill,item_id,success,minutes,meta_json,created_at) VALUES(?,?,?,?,?,?,?,?)',(sid,'practice_bank_answer','reading','y',1,4.5,'{}',m.now()))
c.execute('INSERT INTO speaking_attempts(student_id,part,mode,transcript,duration_ms,metrics_json,rubric_json,score_pct,audio_local_key,created_at,source) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(sid,1,'learn','sample',20000,'{}','{}',80.0,'',m.now(),'qa'))
c.commit(); c.close()
r=m.student_preparation_summary(sid,school)
checks={
 'today_minutes':abs(r['activity']['today_minutes']-12.0)<0.01,
 'recurrent_present':r['errors']['recurrent']>=2,
 'goal_echo':r['learner_target']['mastery_goal']=='excellent',
 'profile_echo':r['learner_target']['exam_profile']=='adult',
 'exam_date_echo':r['learner_target']['exam_date']=='2026-09-22',
 'writing_normalized':r['skills']['writing']==80.0,
 'speaking_normalized':r['skills']['speaking']==80.0,
 'errors_counts_consistent':r['errors']['corrected']<=r['errors']['total_error_targets'] and r['errors']['pending']<=r['errors']['total_error_targets'],
}
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
try: os.unlink(db)
except OSError: pass
sys.exit(0 if all(checks.values()) else 1)
