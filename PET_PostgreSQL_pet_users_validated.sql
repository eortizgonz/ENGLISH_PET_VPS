-- PET Quest B1 - PostgreSQL authentication table
-- Target database: PET
-- Target role/user: postgres
-- Safe/idempotent schema hardening script.
-- IMPORTANT: Run this script while connected to database PET.

BEGIN;

CREATE TABLE IF NOT EXISTS public.pet_users (
    id BIGSERIAL PRIMARY KEY,
    local_user_id BIGINT NOT NULL,
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

-- Ensure unique link to the local academic user.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'public.pet_users'::regclass
          AND conname = 'pet_users_local_user_id_key'
    ) THEN
        ALTER TABLE public.pet_users
            ADD CONSTRAINT pet_users_local_user_id_key UNIQUE (local_user_id);
    END IF;
END $$;

-- Case-insensitive username/email uniqueness used by login.
CREATE UNIQUE INDEX IF NOT EXISTS uq_pet_users_username_ci
    ON public.pet_users (lower(username));

CREATE UNIQUE INDEX IF NOT EXISTS uq_pet_users_email_ci
    ON public.pet_users (lower(email));

-- The UNIQUE(local_user_id) constraint already creates an index, so this old
-- duplicate index is unnecessary and can safely be removed if present.
DROP INDEX IF EXISTS public.idx_pet_users_local_user;

-- Prevent blank authentication/profile values.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'public.pet_users'::regclass
          AND conname = 'pet_users_username_not_blank'
    ) THEN
        ALTER TABLE public.pet_users
            ADD CONSTRAINT pet_users_username_not_blank
            CHECK (btrim(username) <> '') NOT VALID;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'public.pet_users'::regclass
          AND conname = 'pet_users_email_not_blank'
    ) THEN
        ALTER TABLE public.pet_users
            ADD CONSTRAINT pet_users_email_not_blank
            CHECK (btrim(email) <> '') NOT VALID;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'public.pet_users'::regclass
          AND conname = 'pet_users_password_hash_not_blank'
    ) THEN
        ALTER TABLE public.pet_users
            ADD CONSTRAINT pet_users_password_hash_not_blank
            CHECK (btrim(password_hash) <> '') NOT VALID;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'public.pet_users'::regclass
          AND conname = 'pet_users_display_name_not_blank'
    ) THEN
        ALTER TABLE public.pet_users
            ADD CONSTRAINT pet_users_display_name_not_blank
            CHECK (btrim(display_name) <> '') NOT VALID;
    END IF;
END $$;

-- Restrict known profile modes used by PET Quest.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'public.pet_users'::regclass
          AND conname = 'pet_users_profile_mode_check'
    ) THEN
        ALTER TABLE public.pet_users
            ADD CONSTRAINT pet_users_profile_mode_check
            CHECK (profile_mode IN ('schools','adult')) NOT VALID;
    END IF;
END $$;

-- Restrict roles currently supported by PET Quest.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'public.pet_users'::regclass
          AND conname = 'pet_users_role_check'
    ) THEN
        ALTER TABLE public.pet_users
            ADD CONSTRAINT pet_users_role_check
            CHECK (role IN (
                'student',
                'guardian',
                'teacher',
                'school',
                'platform_support',
                'admin',
                'academic_reviewer',
                'content_author'
            )) NOT VALID;
    END IF;
END $$;

-- Validate constraints only when existing data already satisfies them.
-- If any VALIDATE fails, PostgreSQL will report the offending constraint/data
-- instead of deleting or modifying user records.
ALTER TABLE public.pet_users VALIDATE CONSTRAINT pet_users_username_not_blank;
ALTER TABLE public.pet_users VALIDATE CONSTRAINT pet_users_email_not_blank;
ALTER TABLE public.pet_users VALIDATE CONSTRAINT pet_users_password_hash_not_blank;
ALTER TABLE public.pet_users VALIDATE CONSTRAINT pet_users_display_name_not_blank;
ALTER TABLE public.pet_users VALIDATE CONSTRAINT pet_users_profile_mode_check;
ALTER TABLE public.pet_users VALIDATE CONSTRAINT pet_users_role_check;

COMMIT;

-- ---------------------------------------------------------------------------
-- VALIDATION QUERIES
-- ---------------------------------------------------------------------------

-- 1) Table columns
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'pet_users'
ORDER BY ordinal_position;

-- 2) Indexes
SELECT indexname, indexdef
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename = 'pet_users'
ORDER BY indexname;

-- 3) Case-insensitive duplicate usernames: expected 0 rows
SELECT lower(username) AS username_ci, COUNT(*) AS qty
FROM public.pet_users
GROUP BY lower(username)
HAVING COUNT(*) > 1;

-- 4) Case-insensitive duplicate emails: expected 0 rows
SELECT lower(email) AS email_ci, COUNT(*) AS qty
FROM public.pet_users
GROUP BY lower(email)
HAVING COUNT(*) > 1;

-- 5) Blank required values: expected 0 rows
SELECT id, local_user_id, username, email, display_name
FROM public.pet_users
WHERE btrim(username) = ''
   OR btrim(email) = ''
   OR btrim(password_hash) = ''
   OR btrim(display_name) = '';

-- 6) Login-facing view of accounts. password_hash is intentionally omitted.
SELECT
    id,
    local_user_id,
    username,
    email,
    display_name,
    role,
    profile_mode,
    disabled,
    created_at,
    last_login_at
FROM public.pet_users
ORDER BY id;
