@echo off
setlocal
cd /d "%~dp0"
set "L3250_POWERSHELL=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if exist "%SystemRoot%\Sysnative\WindowsPowerShell\v1.0\powershell.exe" set "L3250_POWERSHELL=%SystemRoot%\Sysnative\WindowsPowerShell\v1.0\powershell.exe"
"%L3250_POWERSHELL%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-L3250.ps1" -Action Verify
set "L3250_RESULT=0"
if errorlevel 1 set "L3250_RESULT=1"
if errorlevel 2 set "L3250_RESULT=2"
if errorlevel 3 set "L3250_RESULT=1"
if not errorlevel 0 set "L3250_RESULT=1"
echo.
echo Codigo %L3250_RESULT%: 0 = concluido; 1 = erro; 2 = verificacao pendente ou limite nao confirmado.
pause
exit /b %L3250_RESULT%
