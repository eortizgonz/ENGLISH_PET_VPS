#!/usr/bin/env python3
"""Verify PET Quest PostgreSQL schema AND master educational content."""
import json
import postgres_auth, postgres_content
REQ={
'academic_error_events','academic_remediation_attempts','academic_review_snapshots','account_tokens','anonymous_calibration_candidates','assignments','audit_log','calibration_outcomes','courses','enrollments','governance_actions','governance_goals','governance_reviews','guardian_consents','intervention_run_members','intervention_runs','learning_events','login_attempts','mock_attempts','mock_item_responses','onboarding_items','pet_users','planning_scenarios','privacy_requests','psychometric_reviews','questions','recovery_checks','release_acceptance_runs','schedule_sessions','school_licenses','school_quality_snapshots','schools','sessions','snapshots','speaking_attempts','speaking_interaction_sessions','speaking_interaction_turns','strategic_targets','support_group_members','support_groups','teacher_availability','users',
'content_packages','practice_bank_items','curriculum_lessons','audio_assets','exam_packs','exam_items','content_seed_runs'}
postgres_auth.ensure_database_exists(); postgres_auth.init_schema()
with postgres_auth.connect() as conn:
  with conn.cursor() as cur:
    cur.execute('select current_database(), current_user, version()'); db,user,version=cur.fetchone()
    cur.execute("select table_name from information_schema.tables where table_schema='public' and table_type='BASE TABLE'"); tables={r[0] for r in cur.fetchall()}
    cur.execute("select column_name from information_schema.columns where table_schema='public' and table_name='pet_users'"); cols={r[0] for r in cur.fetchall()}
    cur.execute("select indexname from pg_indexes where schemaname='public' and tablename='pet_users'"); indexes={r[0] for r in cur.fetchall()}
    cur.execute('select count(*) from public.pet_users'); count=int(cur.fetchone()[0])
missing=sorted(REQ-tables)
required_cols={'id','local_user_id','username','email','password_hash','display_name','role','profile_mode','disabled','created_at','last_login_at'}
missing_cols=sorted(required_cols-cols); required_idx={'uq_pet_users_username_ci','uq_pet_users_email_ci'}; missing_idx=sorted(required_idx-indexes)
content=postgres_content.health()
ok=(db==postgres_auth.PG_DB and user==postgres_auth.PG_USER and not missing and not missing_cols and not missing_idx and content.get('ok'))
print(json.dumps({'ok':ok,'database':db,'expected_database':postgres_auth.PG_DB,'user':user,'expected_user':postgres_auth.PG_USER,'server':version.split(',')[0],'required_tables':len(REQ),'present_required_tables':len(REQ&tables),'missing_tables':missing,'pet_users_rows':count,'missing_pet_users_columns':missing_cols,'missing_pet_users_indexes':missing_idx,'master_content':content},ensure_ascii=False,indent=2))
raise SystemExit(0 if ok else 2)
