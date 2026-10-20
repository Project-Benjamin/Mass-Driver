@echo off
cd /d "%~dp0"
python project.py play definitive
if errorlevel 1 pause
