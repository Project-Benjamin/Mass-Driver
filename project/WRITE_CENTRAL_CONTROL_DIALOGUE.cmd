@echo off
setlocal
title Xenogears Mass Driver Dialogue Writer

set "EDITOR=%~dp0tools\central_control_dialogue_writer.html"

if not exist "%EDITOR%" goto missing_editor

start "" "%EDITOR%"
exit /b 0

:missing_editor
echo ERROR: The dialogue writer was not found:
echo   %EDITOR%
echo.
pause
exit /b 1
