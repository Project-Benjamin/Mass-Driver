@echo off
setlocal
python "%~dp0project.py" play rico
set "RESULT=%ERRORLEVEL%"
if not "%RESULT%"=="0" pause
exit /b %RESULT%
