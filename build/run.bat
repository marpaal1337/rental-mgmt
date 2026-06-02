@echo off
cd /d "%~dp0"
python -m desktop
if errorlevel 1 (
    echo.
    echo Error: Python no encontrado o dependencias faltantes.
    echo Asegurate de que Python 3.11+ esta instalado y en PATH.
    echo.
    pause
)
