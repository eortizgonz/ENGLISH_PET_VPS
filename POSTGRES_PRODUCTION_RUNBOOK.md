# PET Quest V41 — PostgreSQL production decision

The current executable runtime remains SQLite for local/pilot QA. V41 no longer represents SQLite as the final international SaaS architecture: if `PETQUEST_ENV=production` and `PETQUEST_REQUIRE_POSTGRES_IN_PRODUCTION=1`, readiness/release checks fail until a PostgreSQL runtime is implemented and validated.

`postgres_schema.sql`, `postgres_check.py`, and `postgres_migrate.py` remain migration assets, not proof that the live server is using PostgreSQL. Do not set a flag to pretend otherwise.
