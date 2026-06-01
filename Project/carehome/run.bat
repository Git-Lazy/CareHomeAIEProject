@echo off
REM Double-click to launch the CareHome app using the project's virtual environment.
cd /d "%~dp0"
".venv\Scripts\python.exe" app.py
pause
