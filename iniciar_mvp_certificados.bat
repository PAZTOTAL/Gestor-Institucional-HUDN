@echo off
color 0B
echo =========================================================
echo =    INICIANDO SERVIDOR MVP - CERTIFICADOS LABORALES  =
echo =========================================================
echo.
cd mvp
..\venv\Scripts\python.exe manage.py runserver 0.0.0.0:3001
pause
