from pathlib import Path
import py_compile, re
R=Path(__file__).resolve().parent
api=(R/'api_server.py').read_text()
pg=(R/'postgres_auth.py').read_text()
ux=(R/'v46_30_registration_ux.js').read_text()
bat=(R/'START_PET_QUEST_POSTGRES_WINDOWS.bat').read_text()
checks={
'db_name_pet': "PG_DB = os.environ.get('PETQUEST_PG_DB', 'PET')" in pg,
'user_postgres': "PG_USER = os.environ.get('PETQUEST_PG_USER', 'postgres')" in pg,
'password_12345': "PG_PASSWORD = os.environ.get('PETQUEST_PG_PASSWORD', '12345')" in pg,
'postgres_required': "PETQUEST_REQUIRE_POSTGRES_AUTH" in api,
'postgres_init': 'postgres_auth.ensure_database_exists()' in api and 'postgres_auth.init_schema()' in api,
'username_registration': "username=clean_text(b.get('username',''),32)" in api,
'postgres_create_identity': 'postgres_auth.create_identity' in api,
'postgres_login_identity': 'postgres_auth.find_identity' in api,
'reset_sync_pg': 'postgres_auth.update_password_by_local_user' in api,
'delete_sync_pg': 'postgres_auth.delete_identity_by_local_user' in api,
'ux_username': 'registerUsername' in ux,
'ux_password_generator': 'Generar contraseña segura' in ux,
'ux_recovery': 'Recuperar contraseña' in ux,
'windows_launcher_db': 'set "PETQUEST_PG_DB=PET"' in bat,
'windows_launcher_user': 'set "PETQUEST_PG_USER=postgres"' in bat,
'windows_launcher_password': 'set "PETQUEST_PG_PASSWORD=12345"' in bat,
'launcher_setup': 'setup_postgres_pet.py' in bat,
'init_sql': (R/'init_pet.sql').exists(),
'env_file': (R/'.env.postgres.pet').exists(),
'docs': (R/'POSTGRES_PET_SETUP.md').exists(),
}
py_compile.compile(str(R/'api_server.py'),doraise=True)
py_compile.compile(str(R/'postgres_auth.py'),doraise=True)
py_compile.compile(str(R/'setup_postgres_pet.py'),doraise=True)
failed=[k for k,v in checks.items() if not v]
print(f'PostgreSQL PET contract QA: {len(checks)-len(failed)}/{len(checks)} PASS')
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
if failed: raise SystemExit(1)
