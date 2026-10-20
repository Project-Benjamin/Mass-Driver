@echo off
setlocal
set "SOYLENT_PYTHON=%~dp0.venv\Scripts\python.exe"
if not exist "%SOYLENT_PYTHON%" (
    echo Project error: The project Python environment is missing: "%SOYLENT_PYTHON%"
    pause
    exit /b 1
)
"%SOYLENT_PYTHON%" "%~dp0project.py" play soylent_system %*
set "RESULT=%ERRORLEVEL%"
if not "%RESULT%"=="0" pause
exit /b %RESULT%
