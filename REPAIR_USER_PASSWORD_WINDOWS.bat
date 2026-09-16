@echo off
setlocal
cd /d "%~dp0"
set PETQUEST_PG_HOST=localhost
set PETQUEST_PG_PORT=5432
set PETQUEST_PG_DB=PET
set PETQUEST_PG_USER=postgres
set PETQUEST_PG_PASSWORD=12345
python repair_user_password.py
pause
