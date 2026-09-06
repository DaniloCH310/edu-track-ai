@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start-app.ps1"
set "EDUTRACK_EXIT=%ERRORLEVEL%"
if not "%EDUTRACK_EXIT%"=="0" (
  echo.
  echo O EduTrack nao foi iniciado. Consulte a mensagem acima.
  pause
)
exit /b %EDUTRACK_EXIT%
