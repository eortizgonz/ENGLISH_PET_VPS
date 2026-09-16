-- PET Quest V46.30 - Full PostgreSQL schema for database PET
-- Safe/idempotent: creates missing objects; never drops user data.
BEGIN;

CREATE TABLE IF NOT EXISTS public.schools(
 id BIGINT PRIMARY KEY, name TEXT NOT NULL, created_at TEXT
);
CREATE TABLE IF NOT EXISTS public.users(
 id BIGINT PRIMARY KEY, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
 name TEXT NOT NULL, role TEXT NOT NULL, school_id BIGINT REFERENCES public.schools(id),
 created_at TEXT NOT NULL, disabled INTEGER DEFAULT 0, verified_at TEXT,
 last_login_at TEXT, username TEXT, profile_mode TEXT DEFAULT 'schools'
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_users_username_ci ON public.users(lower(username)) WHERE username IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_users_email_ci ON public.users(lower(email));

CREATE TABLE IF NOT EXISTS public.pet_users(
 id BIGSERIAL PRIMARY KEY,
 local_user_id BIGINT NOT NULL UNIQUE,
 username VARCHAR(32) NOT NULL,
 email VARCHAR(180) NOT NULL,
 password_hash TEXT NOT NULL,
 display_name VARCHAR(120) NOT NULL,
 role VARCHAR(32) NOT NULL DEFAULT 'student',
 profile_mode VARCHAR(16) NOT NULL DEFAULT 'schools',
 disabled BOOLEAN NOT NULL DEFAULT FALSE,
 created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
 last_login_at TIMESTAMPTZ NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_pet_users_username_ci ON public.pet_users(lower(username));
CREATE UNIQUE INDEX IF NOT EXISTS uq_pet_users_email_ci ON public.pet_users(lower(email));

CREATE TABLE IF NOT EXISTS public.sessions(token TEXT PRIMARY KEY,user_id BIGINT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,created_at TEXT NOT NULL,expires_at TEXT NOT NULL,last_seen_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS public.login_attempts(email TEXT PRIMARY KEY,failures INTEGER NOT NULL DEFAULT 0,locked_until TEXT,updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS public.account_tokens(token TEXT PRIMARY KEY,user_id BIGINT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,kind TEXT NOT NULL,created_at TEXT NOT NULL,expires_at TEXT NOT NULL,used_at TEXT);
CREATE TABLE IF NOT EXISTS public.courses(id BIGINT PRIMARY KEY,school_id BIGINT NOT NULL REFERENCES public.schools(id),name TEXT NOT NULL,teacher_id BIGINT REFERENCES public.users(id),created_at TEXT);
CREATE TABLE IF NOT EXISTS public.enrollments(course_id BIGINT NOT NULL REFERENCES public.courses(id),user_id BIGINT NOT NULL REFERENCES public.users(id),PRIMARY KEY(course_id,user_id));
CREATE TABLE IF NOT EXISTS public.assignments(id BIGINT PRIMARY KEY,course_id BIGINT NOT NULL REFERENCES public.courses(id),title TEXT NOT NULL,skill TEXT NOT NULL,due_date TEXT,status TEXT DEFAULT 'active',created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS public.support_groups(id BIGINT PRIMARY KEY,school_id BIGINT NOT NULL REFERENCES public.schools(id),course_id BIGINT REFERENCES public.courses(id),name TEXT NOT NULL,skill TEXT NOT NULL,focus TEXT,status TEXT DEFAULT 'active',created_by BIGINT REFERENCES public.users(id),created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS public.support_group_members(group_id BIGINT NOT NULL REFERENCES public.support_groups(id) ON DELETE CASCADE,user_id BIGINT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,PRIMARY KEY(group_id,user_id));
CREATE TABLE IF NOT EXISTS public.intervention_runs(id BIGINT PRIMARY KEY,group_id BIGINT NOT NULL UNIQUE REFERENCES public.support_groups(id) ON DELETE CASCADE,course_id BIGINT NOT NULL REFERENCES public.courses(id),school_id BIGINT NOT NULL REFERENCES public.schools(id),skill TEXT NOT NULL,status TEXT DEFAULT 'active',baseline_average DOUBLE PRECISION DEFAULT 0,current_average DOUBLE PRECISION DEFAULT 0,delta DOUBLE PRECISION DEFAULT 0,recommendation TEXT DEFAULT 'collect_more_data',success_criteria TEXT,created_at TEXT NOT NULL,last_evaluated_at TEXT,closed_at TEXT,created_by BIGINT REFERENCES public.users(id));
CREATE TABLE IF NOT EXISTS public.intervention_run_members(run_id BIGINT NOT NULL REFERENCES public.intervention_runs(id) ON DELETE CASCADE,user_id BIGINT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,baseline_score DOUBLE PRECISION DEFAULT 0,current_score DOUBLE PRECISION DEFAULT 0,delta DOUBLE PRECISION DEFAULT 0,PRIMARY KEY(run_id,user_id));
CREATE TABLE IF NOT EXISTS public.school_quality_snapshots(id BIGINT PRIMARY KEY,school_id BIGINT NOT NULL REFERENCES public.schools(id),period_label TEXT NOT NULL,metrics_json TEXT NOT NULL,created_at TEXT NOT NULL,created_by BIGINT REFERENCES public.users(id));
CREATE TABLE IF NOT EXISTS public.academic_review_snapshots(id BIGINT PRIMARY KEY,school_id BIGINT NOT NULL REFERENCES public.schools(id),period_label TEXT NOT NULL,window_type TEXT NOT NULL DEFAULT 'monthly',payload_json TEXT NOT NULL,created_at TEXT NOT NULL,created_by BIGINT REFERENCES public.users(id));
CREATE TABLE IF NOT EXISTS public.governance_goals(id BIGINT PRIMARY KEY,school_id BIGINT NOT NULL REFERENCES public.schools(id),title TEXT NOT NULL,metric TEXT NOT NULL,target_value DOUBLE PRECISION NOT NULL,baseline_value DOUBLE PRECISION DEFAULT 0,current_value DOUBLE PRECISION DEFAULT 0,owner_user_id BIGINT,due_date TEXT,status TEXT DEFAULT 'active',created_at TEXT NOT NULL,updated_at TEXT NOT NULL,created_by BIGINT);
CREATE TABLE IF NOT EXISTS public.governance_actions(id BIGINT PRIMARY KEY,goal_id BIGINT NOT NULL REFERENCES public.governance_goals(id) ON DELETE CASCADE,school_id BIGINT NOT NULL REFERENCES public.schools(id),title TEXT NOT NULL,owner_user_id BIGINT,due_date TEXT,status TEXT DEFAULT 'open',expected_impact TEXT,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,created_by BIGINT);
CREATE TABLE IF NOT EXISTS public.governance_reviews(id BIGINT PRIMARY KEY,goal_id BIGINT NOT NULL REFERENCES public.governance_goals(id) ON DELETE CASCADE,school_id BIGINT NOT NULL REFERENCES public.schools(id),observed_value DOUBLE PRECISION NOT NULL,decision TEXT NOT NULL,note TEXT,created_at TEXT NOT NULL,created_by BIGINT);
CREATE TABLE IF NOT EXISTS public.teacher_availability(id BIGINT PRIMARY KEY,school_id BIGINT NOT NULL REFERENCES public.schools(id),teacher_id BIGINT NOT NULL REFERENCES public.users(id),weekday INTEGER NOT NULL,start_min INTEGER NOT NULL,end_min INTEGER NOT NULL,created_at TEXT NOT NULL,UNIQUE(teacher_id,weekday,start_min,end_min));
CREATE TABLE IF NOT EXISTS public.schedule_sessions(id BIGINT PRIMARY KEY,school_id BIGINT NOT NULL REFERENCES public.schools(id),course_id BIGINT REFERENCES public.courses(id),support_group_id BIGINT REFERENCES public.support_groups(id),teacher_id BIGINT NOT NULL REFERENCES public.users(id),weekday INTEGER NOT NULL,start_min INTEGER NOT NULL,duration_min INTEGER NOT NULL,status TEXT DEFAULT 'planned',label TEXT,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS public.school_licenses(id BIGINT PRIMARY KEY,school_id BIGINT NOT NULL REFERENCES public.schools(id),plan TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'active',student_seats INTEGER NOT NULL,teacher_seats INTEGER NOT NULL DEFAULT 25,starts_at TEXT NOT NULL,expires_at TEXT,created_at TEXT NOT NULL,created_by BIGINT);
CREATE TABLE IF NOT EXISTS public.onboarding_items(id BIGINT PRIMARY KEY,school_id BIGINT NOT NULL REFERENCES public.schools(id),item_key TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'pending',completed_at TEXT,updated_by BIGINT,updated_at TEXT NOT NULL,UNIQUE(school_id,item_key));
CREATE TABLE IF NOT EXISTS public.release_acceptance_runs(id BIGINT PRIMARY KEY,school_id BIGINT REFERENCES public.schools(id),score DOUBLE PRECISION NOT NULL,blockers_json TEXT NOT NULL,warnings_json TEXT NOT NULL,checks_json TEXT NOT NULL,created_at TEXT NOT NULL,created_by BIGINT);
CREATE TABLE IF NOT EXISTS public.strategic_targets(id BIGINT PRIMARY KEY,school_id BIGINT NOT NULL REFERENCES public.schools(id),year INTEGER NOT NULL,metric TEXT NOT NULL,target_value DOUBLE PRECISION NOT NULL,owner_user_id BIGINT,status TEXT DEFAULT 'active',note TEXT,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,created_by BIGINT);
CREATE TABLE IF NOT EXISTS public.questions(id BIGINT PRIMARY KEY,external_id TEXT UNIQUE,skill TEXT NOT NULL,part INTEGER,level INTEGER,focus TEXT,prompt TEXT NOT NULL,options_json TEXT,answer_index INTEGER,explanation TEXT,tip TEXT,status TEXT DEFAULT 'draft',created_by BIGINT REFERENCES public.users(id),created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS public.snapshots(user_id BIGINT PRIMARY KEY REFERENCES public.users(id) ON DELETE CASCADE,payload TEXT NOT NULL,updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS public.audit_log(id BIGINT PRIMARY KEY,user_id BIGINT REFERENCES public.users(id),action TEXT NOT NULL,entity TEXT,entity_id TEXT,meta_json TEXT,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS public.guardian_consents(id BIGINT PRIMARY KEY,student_id BIGINT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,guardian_name TEXT NOT NULL,guardian_email TEXT NOT NULL,consent_version TEXT NOT NULL,accepted_at TEXT NOT NULL,revoked_at TEXT,recorded_by BIGINT REFERENCES public.users(id));
CREATE TABLE IF NOT EXISTS public.privacy_requests(id BIGINT PRIMARY KEY,user_id BIGINT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,request_type TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'open',note TEXT,requested_at TEXT NOT NULL,resolved_at TEXT,resolved_by BIGINT REFERENCES public.users(id));
CREATE TABLE IF NOT EXISTS public.calibration_outcomes(id BIGINT PRIMARY KEY,school_id BIGINT NOT NULL REFERENCES public.schools(id),student_id BIGINT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,source TEXT NOT NULL,predicted_readiness DOUBLE PRECISION NOT NULL,actual_scale_score DOUBLE PRECISION,actual_pass INTEGER,exam_date TEXT,recorded_at TEXT NOT NULL,recorded_by BIGINT REFERENCES public.users(id),notes TEXT);
CREATE TABLE IF NOT EXISTS public.anonymous_calibration_candidates(id BIGINT PRIMARY KEY,school_id BIGINT NOT NULL REFERENCES public.schools(id),anon_id TEXT NOT NULL,predicted_readiness DOUBLE PRECISION NOT NULL,actual_scale_score DOUBLE PRECISION NOT NULL,cambridge_band TEXT NOT NULL,source TEXT NOT NULL,exam_date TEXT,cohort_label TEXT,recorded_at TEXT NOT NULL,recorded_by BIGINT REFERENCES public.users(id),notes TEXT,UNIQUE(school_id,anon_id));
CREATE TABLE IF NOT EXISTS public.psychometric_reviews(id BIGINT PRIMARY KEY,school_id BIGINT NOT NULL REFERENCES public.schools(id),reviewer_name TEXT NOT NULL,organization TEXT NOT NULL,credentials TEXT NOT NULL,independent INTEGER NOT NULL DEFAULT 0,decision TEXT NOT NULL,evidence_ref TEXT NOT NULL,reviewed_at TEXT NOT NULL,recorded_by BIGINT NOT NULL REFERENCES public.users(id),notes TEXT);
CREATE TABLE IF NOT EXISTS public.academic_error_events(id BIGINT PRIMARY KEY,student_id BIGINT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,skill TEXT NOT NULL,part INTEGER,competence TEXT,subcompetence TEXT,error_code TEXT,severity TEXT,original_text TEXT,correction TEXT,mastery_proxy DOUBLE PRECISION,occurred_at TEXT NOT NULL,source TEXT);
CREATE TABLE IF NOT EXISTS public.academic_remediation_attempts(id BIGINT PRIMARY KEY,student_id BIGINT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,error_code TEXT NOT NULL,prompt TEXT,answer TEXT,correct INTEGER NOT NULL DEFAULT 0,attempted_at TEXT NOT NULL,source TEXT);
CREATE TABLE IF NOT EXISTS public.mock_attempts(id BIGINT PRIMARY KEY,student_id BIGINT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,pack_id TEXT NOT NULL,skill TEXT NOT NULL,total_items INTEGER NOT NULL,correct_items INTEGER NOT NULL,pct DOUBLE PRECISION NOT NULL,started_at TEXT,finished_at TEXT NOT NULL,source TEXT);
CREATE TABLE IF NOT EXISTS public.mock_item_responses(id BIGINT PRIMARY KEY,attempt_id BIGINT NOT NULL REFERENCES public.mock_attempts(id) ON DELETE CASCADE,student_id BIGINT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,pack_id TEXT NOT NULL,skill TEXT NOT NULL,part INTEGER NOT NULL,item_id TEXT NOT NULL,answer_text TEXT,answer_option INTEGER,is_correct INTEGER NOT NULL,response_ms INTEGER,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS public.speaking_attempts(id BIGINT PRIMARY KEY,student_id BIGINT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,part INTEGER NOT NULL,mode TEXT NOT NULL,transcript TEXT,duration_ms INTEGER NOT NULL DEFAULT 0,metrics_json TEXT NOT NULL,rubric_json TEXT NOT NULL,score_pct DOUBLE PRECISION NOT NULL DEFAULT 0,audio_local_key TEXT,created_at TEXT NOT NULL,source TEXT);
CREATE TABLE IF NOT EXISTS public.speaking_interaction_sessions(id BIGINT PRIMARY KEY,student_id BIGINT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,scenario_id TEXT NOT NULL,scenario_title TEXT,metrics_json TEXT NOT NULL,rubric_json TEXT NOT NULL,score_pct DOUBLE PRECISION NOT NULL DEFAULT 0,created_at TEXT NOT NULL,source TEXT);
CREATE TABLE IF NOT EXISTS public.speaking_interaction_turns(id BIGINT PRIMARY KEY,session_id BIGINT NOT NULL REFERENCES public.speaking_interaction_sessions(id) ON DELETE CASCADE,turn_no INTEGER NOT NULL,role TEXT NOT NULL,text TEXT NOT NULL,functions_json TEXT NOT NULL DEFAULT '{}',created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS public.learning_events(id BIGINT PRIMARY KEY,user_id BIGINT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,event_type TEXT NOT NULL,skill TEXT,item_id TEXT,success INTEGER,minutes DOUBLE PRECISION DEFAULT 0,meta_json TEXT,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS public.recovery_checks(id BIGINT PRIMARY KEY,backup_name TEXT NOT NULL,ok INTEGER NOT NULL,integrity_result TEXT,checked_at TEXT NOT NULL,checked_by BIGINT REFERENCES public.users(id));
CREATE TABLE IF NOT EXISTS public.planning_scenarios(id BIGINT PRIMARY KEY,school_id BIGINT NOT NULL REFERENCES public.schools(id),scenario_type TEXT NOT NULL,inputs_json TEXT NOT NULL,result_json TEXT NOT NULL,created_at TEXT NOT NULL,created_by BIGINT NOT NULL REFERENCES public.users(id));

CREATE INDEX IF NOT EXISTS idx_sessions_user ON public.sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_learning_events_user ON public.learning_events(user_id,created_at);
CREATE INDEX IF NOT EXISTS idx_error_events_student ON public.academic_error_events(student_id,skill,error_code,occurred_at);
CREATE INDEX IF NOT EXISTS idx_remediation_student ON public.academic_remediation_attempts(student_id,error_code,attempted_at);
CREATE INDEX IF NOT EXISTS idx_mock_attempts_student ON public.mock_attempts(student_id,finished_at);
CREATE INDEX IF NOT EXISTS idx_speaking_attempts_student ON public.speaking_attempts(student_id,created_at);
CREATE INDEX IF NOT EXISTS idx_audit_created ON public.audit_log(created_at);
CREATE INDEX IF NOT EXISTS idx_privacy_requests_status ON public.privacy_requests(status,requested_at);
CREATE INDEX IF NOT EXISTS idx_calibration_school ON public.calibration_outcomes(school_id,exam_date,recorded_at);
CREATE INDEX IF NOT EXISTS idx_recovery_checks_time ON public.recovery_checks(checked_at);

COMMIT;
