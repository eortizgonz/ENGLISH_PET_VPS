# PET Quest — users-only identity + durable progress fix

Changes in this package:

- `public.users` is the only PostgreSQL identity/credential table.
- Legacy `public.pet_users` is merged into `users` by `local_user_id` and dropped transactionally at startup.
- `MIGRATE_DROP_PET_USERS.sql` is included for a manual DBA migration.
- Practice progress is saved immediately to `/api/snapshot` after a successful answer.
- The snapshot now carries a `resume` object with skill, level, question index, selection/check state, session and assignment context.
- Login/bootstrap restores an active practice/writing/speaking session from the PostgreSQL snapshot.
- Moving to the next step also persists the new resume position immediately.
- Writing evaluation and speaking recording persist immediately as critical academic progress.
- If immediate server sync fails, local storage remains as a fallback and the UI warns the user.

The progress charts were intentionally left unchanged for a later phase.
