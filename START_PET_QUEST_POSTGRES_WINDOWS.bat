@echo off
setlocal
cd /d "%~dp0"
title PET Quest - PostgreSQL PET

set "PETQUEST_PG_HOST=localhost"
set "PETQUEST_PG_PORT=5432"
set "PETQUEST_PG_DB=PET"
set "PETQUEST_PG_USER=postgres"
set "PETQUEST_PG_PASSWORD=12345"
set "PETQUEST_REQUIRE_POSTGRES_AUTH=1"
set "PETQUEST_SEED_DEMO_DATA=0"

where python >nul 2>nul
if %errorlevel%==0 set "PY=python"
if not defined PY (
  where py >nul 2>nul
  if %errorlevel%==0 set "PY=py -3"
)
if not defined PY (
  echo ERROR: Python 3 no esta instalado o no esta disponible en PATH.
  pause
  exit /b 1
)

echo [0/5] Verificando integridad y longitud de rutas de Windows...
%PY% verify_windows_runtime.py
if errorlevel 1 goto :path_error

echo [1/5] Verificando driver PostgreSQL...
%PY% -c "import psycopg" >nul 2>nul
if errorlevel 1 (
  echo Instalando psycopg para PostgreSQL...
  %PY% -m pip install -r requirements-postgres.txt
  if errorlevel 1 goto :pg_error
)

echo [2/5] Preparando PostgreSQL PET y cargando contenido maestro...
%PY% setup_postgres_pet.py
if errorlevel 1 goto :pg_error

echo [3/5] Verificando tablas, login y contenido educativo...
%PY% postgres_check.py
if errorlevel 1 goto :pg_error

echo [4/5] Verificando recursos de la aplicacion...
%PY% verify_windows_runtime.py
if errorlevel 1 goto :path_error

echo [5/5] Iniciando PET Quest...
%PY% start_pet_quest.py
set "RC=%errorlevel%"
goto :finish

:path_error
echo.
echo NO SE PUEDE INICIAR DESDE ESTA UBICACION O EL PAQUETE ESTA INCOMPLETO.
echo Extrae la carpeta PET en C:\PET y vuelve a ejecutar este archivo.
pause
set "RC=3"
goto :finish

:pg_error
echo.
echo NO SE PUDO PREPARAR O VALIDAR POSTGRESQL.
echo Verifica que PostgreSQL este instalado e iniciado en localhost:5432.
echo Base: PET
echo Usuario: postgres
echo Clave configurada: 12345
pause
set "RC=2"
goto :finish

:finish
endlocal & exit /b %RC%
