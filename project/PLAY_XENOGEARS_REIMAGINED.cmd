@echo off
setlocal
python "%~dp0project.py" play combined
set "RESULT=%ERRORLEVEL%"
if not "%RESULT%"=="0" pause
exit /b %RESULT%
