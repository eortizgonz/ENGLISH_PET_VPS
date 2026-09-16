# PET Quest V46.30 — Data Store Map

## PostgreSQL PET — authoritative authentication store

### `pet_users`
Used by: self-registration, login by username/email, password reset, password change, identity deletion, last-login tracking.

Required uniqueness: `lower(username)`, `lower(email)`, and `local_user_id`.

## SQLite — application/academic runtime store

- `users`: local user/profile shadow and tenant (`school_id`) linkage.
- `sessions`: bearer sessions used by API authorization.
- `login_attempts`: lockout counters.
- `account_tokens`: reset/verification tokens.
- `schools`, `school_licenses`: school/individual-learner tenant context.
- `courses`, `enrollments`, `assignments`: classroom organization.
- `snapshots`: user-scoped application state/progress.
- `learning_events`: learning activity and practice outcomes.
- `academic_error_events`: Error DNA evidence.
- `academic_remediation_attempts`: error-correction attempts.
- `mock_attempts`, `mock_item_responses`: mock-exam results.
- `speaking_attempts`, `speaking_interaction_sessions`, `speaking_interaction_turns`: Speaking evidence.
- `calibration_outcomes`, `psychometric_reviews`: readiness calibration evidence.
- `audit_log`: security/administrative trace.

## Synchronization rules

- New self-registration creates the local `users` row and the matching PostgreSQL `pet_users` identity in one request; a PostgreSQL creation failure rolls back the local user row.
- Login validates credentials against PostgreSQL and resolves the application profile through `local_user_id` in SQLite.
- Password reset/change updates PostgreSQL first and then the local shadow hash, and reset invalidates existing sessions.
- User deletion removes the PostgreSQL identity and purges/anonymizes relevant SQLite educational records according to the privacy workflow.
