@echo off
setlocal
cd /d "%~dp0"
set "PETQUEST_PG_HOST=localhost"
set "PETQUEST_PG_PORT=5432"
set "PETQUEST_PG_DB=PET"
set "PETQUEST_PG_USER=postgres"
set "PETQUEST_PG_PASSWORD=12345"
where python >nul 2>nul && set "PY=python"
if not defined PY where py >nul 2>nul && set "PY=py -3"
if not defined PY (
 echo ERROR: Python 3 no encontrado.
 pause
 exit /b 1
)
echo Cargando esquema y contenido maestro en PostgreSQL PET...
%PY% setup_postgres_pet.py
if errorlevel 1 goto :err
%PY% postgres_check.py
if errorlevel 1 goto :err
echo.
echo CONTENIDO POSTGRESQL VALIDADO.
echo Refresca PET ^> Schemas ^> public ^> Tables en pgAdmin.
pause
exit /b 0
:err
echo.
echo ERROR: no se pudo cargar o validar el contenido PostgreSQL.
pause
exit /b 2
