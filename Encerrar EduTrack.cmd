@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\stop-postgres.ps1" -Cluster All
set "EDUTRACK_EXIT=%ERRORLEVEL%"
if not "%EDUTRACK_EXIT%"=="0" (
  echo.
  echo Nao foi possivel encerrar o PostgreSQL. Consulte a mensagem acima.
  pause
)
exit /b %EDUTRACK_EXIT%
