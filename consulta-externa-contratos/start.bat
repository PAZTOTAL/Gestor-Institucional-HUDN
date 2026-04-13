@echo off
cd /d "%~dp0"
py -m pip install -r requirements.txt >nul
py manage.py runserver 0.0.0.0:3030
