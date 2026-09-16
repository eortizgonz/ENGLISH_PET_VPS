PET QUEST - POSTGRESQL COMPLETO

Base: PET
Usuario: postgres
Password por defecto local solicitada: 12345

Al ejecutar START_PET_QUEST_WINDOWS.bat / START_PET_QUEST_POSTGRES_WINDOWS.bat:
1. Crea la base PET si falta.
2. Ejecuta postgres_full_schema.sql.
3. Verifica 42/42 tablas con postgres_check.py.
4. Inicia PET Quest solo si PostgreSQL esta listo.
5. Mantiene pet_users como tabla autoritativa de login.
6. Sincroniza el estado academico SQLite hacia las tablas PostgreSQL cada 10 segundos.

Archivos principales:
- postgres_full_schema.sql
- setup_postgres_pet.py
- postgres_check.py
- postgres_full_sync.py
- postgres_auth.py

Para ver las tablas en pgAdmin:
PET > Schemas > public > Tables > Refresh
