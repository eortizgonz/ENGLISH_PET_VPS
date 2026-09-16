@echo off
setlocal
cd /d "%~dp0"
call START_PET_QUEST_POSTGRES_WINDOWS.bat
set "RC=%errorlevel%"
endlocal & exit /b %RC%
