@echo off
title BKS Verse — Admin Panel
color 0B

cd /d "I:\BAKABO SYSTEM"
echo Apro pannello admin...
echo.
start http://localhost:8099
.venv\Scripts\python scripts\admin_panel.py

pause
