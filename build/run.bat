@echo off
cd /d "%~dp0"
pythonw -m desktop
if %errorlevel% neq 0 (
    python -m desktop
    pause
)
