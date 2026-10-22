@echo off
title AI Health Risk System

cd /d "%~dp0backend"

start "AI Health Risk System - Backend" cmd /k "python app.py"

ping 127.0.0.1 -n 4 >nul

start "" "http://127.0.0.1:5000"

exit
