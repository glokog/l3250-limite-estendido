@echo off
setlocal
cd /d "%~dp0"
set "L375_POWERSHELL=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if exist "%SystemRoot%\Sysnative\WindowsPowerShell\v1.0\powershell.exe" set "L375_POWERSHELL=%SystemRoot%\Sysnative\WindowsPowerShell\v1.0\powershell.exe"
"%L375_POWERSHELL%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-L375.ps1" -Action Verify
set "L375_RESULT=0"
if errorlevel 1 set "L375_RESULT=1"
if errorlevel 2 set "L375_RESULT=2"
if errorlevel 3 set "L375_RESULT=1"
if not errorlevel 0 set "L375_RESULT=1"
echo.
echo Codigo %L375_RESULT%: 0 = concluido; 1 = erro; 2 = verificacao pendente ou limite nao confirmado.
pause
exit /b %L375_RESULT%
