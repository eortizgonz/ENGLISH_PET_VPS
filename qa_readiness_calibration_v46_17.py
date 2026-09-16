#!/usr/bin/env python3
import os,tempfile,importlib.util,sys,random
from pathlib import Path
root=Path(__file__).resolve().parent
tmp=Path(tempfile.mkdtemp())/'cal.db'
os.environ['PETQUEST_SQLITE_PATH']=str(tmp);os.environ['PETQUEST_SEED_DEMO_DATA']='0';os.environ['PETQUEST_DEV_MODE']='1';os.environ['PETQUEST_ENV']='test'
spec=importlib.util.spec_from_file_location('pq',root/'api_server.py');pq=importlib.util.module_from_spec(spec);spec.loader.exec_module(pq);pq.init_db()
c=pq.conn();c.execute("INSERT INTO schools(id,name,created_at) VALUES(1,'QA',?)",(pq.now(),));c.execute("INSERT INTO users(id,email,password_hash,name,role,school_id,created_at) VALUES(1,'reviewer@qa',?,'Reviewer','academic_reviewer',1,?)",(pq.hash_pw('x'),pq.now()))
# 40-case provisional set: probability must remain OFF
for i in range(2,42):
 c.execute("INSERT INTO users(id,email,password_hash,name,role,school_id,created_at) VALUES(?,?,?,?, 'student',1,?)",(i,f's{i}@qa',pq.hash_pw('x'),f'S{i}',pq.now())); r=85 if i%2==0 else 55; y=1 if i%2==0 else 0;c.execute("INSERT INTO calibration_outcomes(school_id,student_id,source,predicted_readiness,actual_pass,exam_date,recorded_at,recorded_by) VALUES(1,?,'official_exam',?,?,?,?,1)",(i,r,y,'2026-01-01',pq.now()))
c.commit();rep40=pq.build_calibration_report(1)
checks=[]
def ck(name,cond):checks.append((name,bool(cond)))
ck('40 sample provisional',rep40['status']=='provisional');ck('40 probability OFF',not rep40['probability_enabled']);ck('40 unique external',rep40['external_unique_students']==40)
# Add to 320 unique outcomes, intentionally strongly separable
for i in range(42,322):
 c.execute("INSERT INTO users(id,email,password_hash,name,role,school_id,created_at) VALUES(?,?,?,?, 'student',1,?)",(i,f's{i}@qa',pq.hash_pw('x'),f'S{i}',pq.now())); y=1 if i%2==0 else 0;r=(82+(i%7)) if y else (48+(i%9));c.execute("INSERT INTO calibration_outcomes(school_id,student_id,source,predicted_readiness,actual_pass,exam_date,recorded_at,recorded_by) VALUES(1,?,'external_mock',?,?,?,?,1)",(i,r,y,'2026-02-01',pq.now()))
# teacher mocks must not inflate scientific sample
for i in range(2,22):c.execute("INSERT INTO calibration_outcomes(school_id,student_id,source,predicted_readiness,actual_pass,exam_date,recorded_at,recorded_by) VALUES(1,?,'teacher_mock',70,1,'2026-02-02',?,1)",(i,pq.now()))
c.commit();rep=pq.build_calibration_report(1)
ck('teacher mocks excluded',rep['external_unique_students']==320);ck('holdout created',rep['holdout_size']>=50);ck('statistical gate passed',rep['statistical_gate_passed']);ck('review still required',not rep['gates']['independent_review_approved']);ck('probability OFF before review',not rep['probability_enabled']);ck('holdout AUC',rep['holdout_metrics'].get('auc',0)>=.70);ck('holdout Brier',rep['holdout_metrics'].get('brier',1)<=.20);ck('holdout ECE',rep['holdout_metrics'].get('ece',1)<=.10)
c.execute("INSERT INTO psychometric_reviews(school_id,reviewer_name,organization,credentials,independent,decision,evidence_ref,reviewed_at,recorded_by,notes) VALUES(1,'Independent Reviewer','External Lab','Psychometrician',1,'approved','report://qa',?,1,'QA')",(pq.now(),));c.commit();rep2=pq.build_calibration_report(1);c.close()
ck('external review gate',rep2['gates']['independent_review_approved']);ck('probability enabled after all gates',rep2['probability_enabled']);ck('validated status',rep2['status']=='validated');ck('model available only after validation',isinstance(rep2['model'],dict))
for n,v in checks:print(('PASS' if v else 'FAIL'),n)
print(f'READINESS CALIBRATION V46.17: {sum(v for _,v in checks)}/{len(checks)} PASS')
if not all(v for _,v in checks):sys.exit(1)
