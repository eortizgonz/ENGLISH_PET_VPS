#!/usr/bin/env python3
"""Mirror PET Quest academic SQLite state into PostgreSQL PET.
PostgreSQL keeps the complete relational schema for inspection/reporting while the
legacy V46.30 runtime remains SQLite-compatible. Safe to run repeatedly.
"""
from pathlib import Path
import os, sqlite3, time, threading
import postgres_auth

ROOT=Path(__file__).resolve().parent
SQLITE=Path(os.environ.get('PETQUEST_SQLITE_PATH', str(ROOT/'petquest.db')))
TABLES=[
 'schools','users','sessions','login_attempts','account_tokens','courses','enrollments','assignments',
 'support_groups','support_group_members','intervention_runs','intervention_run_members',
 'school_quality_snapshots','academic_review_snapshots','governance_goals','governance_actions','governance_reviews',
 'teacher_availability','schedule_sessions','school_licenses','onboarding_items','release_acceptance_runs','strategic_targets',
 'questions','snapshots','audit_log','guardian_consents','privacy_requests','calibration_outcomes',
 'anonymous_calibration_candidates','psychometric_reviews','academic_error_events','academic_remediation_attempts',
 'mock_attempts','mock_item_responses','speaking_attempts','speaking_interaction_sessions','speaking_interaction_turns',
 'learning_events','recovery_checks','planning_scenarios'
]

def _q(name):
    return '"'+str(name).replace('"','""')+'"'

def sync_once():
    if not SQLITE.exists():
        return {'ok':False,'reason':'sqlite_missing'}
    src=sqlite3.connect(SQLITE); src.row_factory=sqlite3.Row
    copied={}
    try:
        with postgres_auth.connect() as pg:
            with pg.cursor() as cur:
                for table in TABLES:
                    try:
                        info=src.execute(f'PRAGMA table_info({_q(table)})').fetchall()
                        if not info: continue
                        cols=[r['name'] for r in info]
                        pk=[r['name'] for r in sorted(info,key=lambda x:x['pk']) if r['pk']]
                        rows=src.execute(f'SELECT * FROM {_q(table)}').fetchall()
                        if not rows: copied[table]=0; continue
                        colsql=','.join(_q(c) for c in cols)
                        vals=','.join(['%s']*len(cols))
                        if pk:
                            conflict=','.join(_q(c) for c in pk)
                            upd=[c for c in cols if c not in pk]
                            tail=(' DO UPDATE SET '+','.join(f'{_q(c)}=EXCLUDED.{_q(c)}' for c in upd)) if upd else ' DO NOTHING'
                            sql=f'INSERT INTO public.{_q(table)} ({colsql}) VALUES ({vals}) ON CONFLICT ({conflict}){tail}'
                        else:
                            sql=f'INSERT INTO public.{_q(table)} ({colsql}) VALUES ({vals}) ON CONFLICT DO NOTHING'
                        for row in rows:
                            cur.execute(sql, tuple(row[c] for c in cols))
                        copied[table]=len(rows)
                    except Exception as exc:
                        pg.rollback(); raise RuntimeError(f'sync_failed:{table}:{exc}') from exc
            pg.commit()
        return {'ok':True,'tables':copied,'rows':sum(copied.values())}
    finally:
        src.close()

def start_background(interval=10):
    def worker():
        while True:
            try: sync_once()
            except Exception as exc: print('PostgreSQL mirror warning:', str(exc)[:240])
            time.sleep(max(5,int(interval)))
    t=threading.Thread(target=worker,name='pet-postgres-mirror',daemon=True); t.start(); return t

if __name__=='__main__':
    postgres_auth.ensure_database_exists(); postgres_auth.init_schema()
    print(sync_once())
