@echo off
color 0A
echo =========================================================
echo =    INICIANDO SERVIDOR LOCAL HOSPITAL MANAGEMENT      =
echo =========================================================
echo.
.\venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000
pause
