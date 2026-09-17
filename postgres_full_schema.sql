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

-- Legacy public.pet_users is intentionally not created in PostgreSQL-only mode.
-- public.users is the single identity/credential table.

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


-- V46.30 content-master schema: educational material stored in PostgreSQL.
CREATE TABLE IF NOT EXISTS public.content_packages(
 package_key TEXT PRIMARY KEY,
 profile TEXT NOT NULL,
 content_type TEXT NOT NULL,
 version TEXT,
 title TEXT,
 source_file TEXT NOT NULL,
 item_count INTEGER NOT NULL DEFAULT 0,
 source_sha256 TEXT,
 metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
 loaded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_content_packages_type ON public.content_packages(profile,content_type);

CREATE TABLE IF NOT EXISTS public.practice_bank_items(
 content_key TEXT PRIMARY KEY,
 profile TEXT NOT NULL,
 item_id TEXT NOT NULL,
 skill TEXT,
 part INTEGER,
 cefr TEXT,
 difficulty DOUBLE PRECISION,
 competency TEXT,
 item_type TEXT,
 prompt TEXT NOT NULL,
 options_json JSONB,
 answer_index TEXT,
 explanation TEXT,
 audio_text TEXT,
 source TEXT,
 diagnostic_patterns_json JSONB,
 payload_json JSONB NOT NULL,
 package_key TEXT NOT NULL REFERENCES public.content_packages(package_key) ON DELETE CASCADE,
 loaded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
 UNIQUE(profile,item_id)
);

-- ---------------------------------------------------------------------------
-- Docker/upgrade migration for existing PostgreSQL volumes:
-- practice_bank_items.answer_index can contain mixed values.
-- ---------------------------------------------------------------------------
DO $$
DECLARE
    current_type TEXT;
BEGIN
    SELECT data_type
      INTO current_type
      FROM information_schema.columns
     WHERE table_schema = 'public'
       AND table_name = 'practice_bank_items'
       AND column_name = 'answer_index';

    IF current_type IN ('smallint', 'integer', 'bigint') THEN
        ALTER TABLE public.practice_bank_items
            ALTER COLUMN answer_index TYPE TEXT
            USING answer_index::TEXT;
    ELSIF current_type IS NULL THEN
        ALTER TABLE public.practice_bank_items
            ADD COLUMN answer_index TEXT;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_practice_items_profile_skill ON public.practice_bank_items(profile,skill,part,cefr);
CREATE INDEX IF NOT EXISTS idx_practice_items_competency ON public.practice_bank_items(profile,competency);

CREATE TABLE IF NOT EXISTS public.curriculum_lessons(
 lesson_id TEXT PRIMARY KEY,
 level TEXT NOT NULL,
 lesson_order INTEGER NOT NULL,
 difficulty DOUBLE PRECISION,
 skill TEXT,
 competency TEXT,
 title TEXT NOT NULL,
 objective TEXT,
 teach_text TEXT,
 examples_json JSONB,
 strategy TEXT,
 check_json JSONB,
 recheck_json JSONB,
 practice_filter_json JSONB,
 mastery_json JSONB,
 payload_json JSONB NOT NULL,
 package_key TEXT NOT NULL REFERENCES public.content_packages(package_key) ON DELETE CASCADE,
 loaded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_curriculum_level_order ON public.curriculum_lessons(level,lesson_order);

CREATE TABLE IF NOT EXISTS public.audio_assets(
 asset_path TEXT PRIMARY KEY,
 audio_id TEXT,
 profile TEXT NOT NULL DEFAULT 'schools',
 part INTEGER,
 item_index INTEGER,
 transcript TEXT,
 question TEXT,
 options_json JSONB,
 -- IMPORTANT: this field is intentionally TEXT. PET Listening answers are mixed:
 -- numeric option indexes (0/1/2/...) and literal answers such as '9:30'.
 -- Keeping the historical column name preserves compatibility with postgres_content.py.
 answer_index TEXT,
 focus TEXT,
 voice_profiles_json JSONB,
 training_speeds_json JSONB,
 exam_speed DOUBLE PRECISION,
 exam_max_plays INTEGER,
 synthetic BOOLEAN,
 human_recording BOOLEAN,
 duration_seconds DOUBLE PRECISION,
 bit_rate BIGINT,
 sample_rate INTEGER,
 channels INTEGER,
 sha256 TEXT,
 file_size BIGINT,
 source_manifest TEXT,
 metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
 loaded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
-- ---------------------------------------------------------------------------
-- Docker/upgrade migration for existing PostgreSQL volumes
-- ---------------------------------------------------------------------------
-- CREATE TABLE IF NOT EXISTS does not alter a table that already exists.
-- Previous PET builds created audio_assets.answer_index as INTEGER, which fails
-- when the seed contains literal Listening answers such as "9:30".
DO $$
DECLARE
    current_type TEXT;
BEGIN
    SELECT data_type
      INTO current_type
      FROM information_schema.columns
     WHERE table_schema = 'public'
       AND table_name = 'audio_assets'
       AND column_name = 'answer_index';

    IF current_type IN ('smallint', 'integer', 'bigint') THEN
        ALTER TABLE public.audio_assets
            ALTER COLUMN answer_index TYPE TEXT
            USING answer_index::TEXT;
    ELSIF current_type IS NULL THEN
        ALTER TABLE public.audio_assets
            ADD COLUMN answer_index TEXT;
    END IF;
END $$;

-- Optional forward-compatible columns. The current loader can ignore these;
-- they allow a later release to store the semantic answer separately without
-- changing the legacy answer_index field again.
ALTER TABLE public.audio_assets
    ADD COLUMN IF NOT EXISTS answer_text TEXT;

ALTER TABLE public.audio_assets
    ADD COLUMN IF NOT EXISTS answer_value JSONB;

CREATE INDEX IF NOT EXISTS idx_audio_assets_id ON public.audio_assets(audio_id);
CREATE INDEX IF NOT EXISTS idx_audio_assets_profile_part ON public.audio_assets(profile,part);
CREATE INDEX IF NOT EXISTS idx_audio_assets_human ON public.audio_assets(human_recording,synthetic);

CREATE TABLE IF NOT EXISTS public.exam_packs(
 pack_id TEXT PRIMARY KEY,
 profile TEXT NOT NULL,
 title TEXT NOT NULL,
 version TEXT,
 status TEXT,
 theme TEXT,
 source_file TEXT NOT NULL,
 reading_count INTEGER NOT NULL DEFAULT 0,
 listening_count INTEGER NOT NULL DEFAULT 0,
 writing_count INTEGER NOT NULL DEFAULT 0,
 speaking_count INTEGER NOT NULL DEFAULT 0,
 header_json JSONB NOT NULL DEFAULT '{}'::jsonb,
 loaded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_exam_packs_profile ON public.exam_packs(profile,pack_id);

CREATE TABLE IF NOT EXISTS public.exam_items(
 pack_id TEXT NOT NULL REFERENCES public.exam_packs(pack_id) ON DELETE CASCADE,
 item_id TEXT NOT NULL,
 skill TEXT NOT NULL,
 part INTEGER,
 item_order INTEGER NOT NULL,
 interaction TEXT,
 prompt TEXT,
 source_text TEXT,
 source_label TEXT,
 options_json JSONB,
 answer_index TEXT,
 audio_id TEXT,
 audio_file TEXT,
 transcript TEXT,
 target_words INTEGER,
 focus TEXT,
 audit_json JSONB,
 payload_json JSONB NOT NULL,
 loaded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
 PRIMARY KEY(pack_id,item_id)
);

-- ---------------------------------------------------------------------------
-- Docker/upgrade migration for existing PostgreSQL volumes:
-- exam_items.answer_index can contain A/B/C/D as well as numeric values.
-- ---------------------------------------------------------------------------
DO $$
DECLARE
    current_type TEXT;
BEGIN
    SELECT data_type
      INTO current_type
      FROM information_schema.columns
     WHERE table_schema = 'public'
       AND table_name = 'exam_items'
       AND column_name = 'answer_index';

    IF current_type IN ('smallint', 'integer', 'bigint') THEN
        ALTER TABLE public.exam_items
            ALTER COLUMN answer_index TYPE TEXT
            USING answer_index::TEXT;
    ELSIF current_type IS NULL THEN
        ALTER TABLE public.exam_items
            ADD COLUMN answer_index TEXT;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_exam_items_pack_skill ON public.exam_items(pack_id,skill,part,item_order);
CREATE INDEX IF NOT EXISTS idx_exam_items_audio ON public.exam_items(audio_id) WHERE audio_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS public.content_seed_runs(
 id BIGSERIAL PRIMARY KEY,
 started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
 finished_at TIMESTAMPTZ,
 status TEXT NOT NULL DEFAULT 'running',
 counts_json JSONB NOT NULL DEFAULT '{}'::jsonb,
 errors_json JSONB NOT NULL DEFAULT '[]'::jsonb,
 source_root TEXT
);

CREATE OR REPLACE VIEW public.v_content_inventory AS
SELECT 'practice_bank_items'::text AS content_table, COUNT(*)::bigint AS row_count FROM public.practice_bank_items
UNION ALL SELECT 'curriculum_lessons', COUNT(*) FROM public.curriculum_lessons
UNION ALL SELECT 'audio_assets', COUNT(*) FROM public.audio_assets
UNION ALL SELECT 'exam_packs', COUNT(*) FROM public.exam_packs
UNION ALL SELECT 'exam_items', COUNT(*) FROM public.exam_items
UNION ALL SELECT 'content_packages', COUNT(*) FROM public.content_packages;

-- ---------------------------------------------------------------------------
-- Schema sanity checks
-- ---------------------------------------------------------------------------
-- Fail early during Docker startup if an old PostgreSQL volume still has an
-- incompatible answer_index type. This prevents confusing seed errors such as:
--   invalid input syntax for type integer: "9:30"
--   invalid input syntax for type integer: "A"
-- ---------------------------------------------------------------------------
DO $$
DECLARE
    practice_type TEXT;
    audio_type TEXT;
    exam_type TEXT;
BEGIN
    SELECT data_type
      INTO practice_type
      FROM information_schema.columns
     WHERE table_schema = 'public'
       AND table_name = 'practice_bank_items'
       AND column_name = 'answer_index';

    SELECT data_type
      INTO audio_type
      FROM information_schema.columns
     WHERE table_schema = 'public'
       AND table_name = 'audio_assets'
       AND column_name = 'answer_index';

    SELECT data_type
      INTO exam_type
      FROM information_schema.columns
     WHERE table_schema = 'public'
       AND table_name = 'exam_items'
       AND column_name = 'answer_index';

    IF practice_type <> 'text' THEN
        RAISE EXCEPTION
            'PET schema error: practice_bank_items.answer_index must be TEXT, got %',
            practice_type;
    END IF;

    IF audio_type <> 'text' THEN
        RAISE EXCEPTION
            'PET schema error: audio_assets.answer_index must be TEXT, got %',
            audio_type;
    END IF;

    IF exam_type <> 'text' THEN
        RAISE EXCEPTION
            'PET schema error: exam_items.answer_index must be TEXT, got %',
            exam_type;
    END IF;
END $$;


-- ============================================================
-- PostgreSQL-only runtime: auto-increment compatibility
-- ============================================================
-- Earlier PET schemas mirrored SQLite IDs into BIGINT PRIMARY KEY columns
-- without sequence defaults. The PostgreSQL-only runtime inserts directly,
-- so every numeric `id` primary-key table needs an automatic sequence.
DO $$
DECLARE
    r record;
    seq text;
    mx bigint;
BEGIN
    FOR r IN
        SELECT c.table_name
        FROM information_schema.columns c
        JOIN information_schema.tables t
          ON t.table_schema=c.table_schema AND t.table_name=c.table_name
        WHERE c.table_schema='public'
          AND c.column_name='id'
          AND c.data_type IN ('smallint','integer','bigint')
          AND c.column_default IS NULL
          AND t.table_type='BASE TABLE'
    LOOP
        seq := r.table_name || '_id_seq';
        EXECUTE format('CREATE SEQUENCE IF NOT EXISTS public.%I', seq);
        EXECUTE format(
            'ALTER TABLE public.%I ALTER COLUMN id SET DEFAULT nextval(%L::regclass)',
            r.table_name, 'public.' || seq
        );
        EXECUTE format('SELECT COALESCE(MAX(id),0) FROM public.%I', r.table_name) INTO mx;
        IF mx > 0 THEN
            EXECUTE format('SELECT setval(%L::regclass,%s,true)', 'public.' || seq, mx);
        ELSE
            EXECUTE format('SELECT setval(%L::regclass,1,false)', 'public.' || seq);
        END IF;
    END LOOP;
END $$;

COMMIT;
