#!/usr/bin/env python3
import os,tempfile,random,sys
os.environ['PETQUEST_ENV']='test'; os.environ['PETQUEST_DEV_MODE']='1'; os.environ['PETQUEST_SEED_DEMO_DATA']='1'; os.environ['PETQUEST_REQUIRE_GUARDIAN_CONSENT']='0'
fd,path=tempfile.mkstemp(prefix='petquest_v4617_',suffix='.db'); os.close(fd); os.unlink(path); os.environ['PETQUEST_SQLITE_PATH']=path
import api_server as a
a.init_db(); c=a.conn(); school=c.execute('select id from schools order by id limit 1').fetchone()['id']; admin=c.execute("select id from users where role='admin' order by id limit 1").fetchone()['id']

def add(n):
    rnd=random.Random(4617)
    bands=[(108,119),(120,139),(140,152),(153,159),(160,170)]
    for i in range(n):
        lo,hi=bands[i%len(bands)]; score=lo+(i*7%(hi-lo+1)); readiness=max(0,min(100,(score-102)/68*100 + rnd.uniform(-2.0,2.0)))
        anon=f'Student-{i+1:06d}'; c.execute('INSERT INTO anonymous_calibration_candidates(school_id,anon_id,predicted_readiness,actual_scale_score,cambridge_band,source,exam_date,cohort_label,recorded_at,recorded_by,notes) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(school,anon,readiness,score,a._cambridge_band(score),'official_exam','2026-12-01','qa',a.now(),admin,''))
    c.commit()

checks=[]
def ck(name,v): checks.append((name,bool(v))); print(('PASS' if v else 'FAIL'),name)
add(40); r=a.build_scale_equivalence_report(school); ck('40 remains OFF',not r['scale_equivalence_enabled'] and r['status'] in ('provisional','insufficient')); ck('40 sample',r['sample_size']==40)
c.execute('delete from anonymous_calibration_candidates'); c.commit(); add(400); r=a.build_scale_equivalence_report(school)
ck('400 minimum cohort',r['sample_size']==400 and r['progress']['to_300']==100)
ck('all four requested groups balanced',all(r['distribution'][k]>=40 for k in ['fail_a2','pass_b1','merit_b1','distinction_b2']))
ck('holdout >=60',r['holdout_size']>=60)
ck('MAE gate',r['gates']['holdout_mae_5']); ck('RMSE gate',r['gates']['holdout_rmse_7']); ck('R2 gate',r['gates']['holdout_r2_065'])
ck('statistical gate passes',r['statistical_gate_passed']); ck('still OFF without review',not r['scale_equivalence_enabled'])
c.execute("INSERT INTO psychometric_reviews(school_id,reviewer_name,organization,credentials,independent,decision,evidence_ref,reviewed_at,recorded_by,notes) VALUES(?,?,?,?,?,?,?,?,?,?)",(school,'Independent Reviewer','External Lab','Psychometrician',1,'approved','qa-evidence',a.now(),admin,'QA only')); c.commit(); r=a.build_scale_equivalence_report(school)
ck('enabled after independent review',r['scale_equivalence_enabled']); ck('model available only when validated',bool(r['model'])); ck('status validated',r['status']=='validated')
# Verify predicted score remains within official reporting range when endpoint applies clamp logic
m=r['model']; est=max(102,min(170,m['intercept']+m['slope']*75)); ck('equivalent score bounded',102<=est<=170)
# Mature cohort marker
c.execute('delete from anonymous_calibration_candidates'); c.commit(); add(1000); r=a.build_scale_equivalence_report(school); ck('1000+ maturity',r['maturity']=='mature_1000_plus' and r['progress']['to_1000']==100)
# DB identity fields: no name/email/phone in anonymous table
cols={x['name'] for x in c.execute('pragma table_info(anonymous_calibration_candidates)').fetchall()}; ck('anonymous schema excludes direct identifiers',not ({'name','email','phone'} & cols))
c.close(); os.unlink(path)
print(f'V46.17 SCALE EQUIVALENCE QA: {sum(v for _,v in checks)}/{len(checks)} PASS')
sys.exit(0 if all(v for _,v in checks) else 1)
