@echo off
title BKS VERSE — Sistema Operativo
color 0A

echo ============================================================
echo   BKS VERSE — Dalla Poesia all'Oggetto
echo   Sistema operativo v1.0  ^|  porta 8001
echo ============================================================
echo.

cd /d "I:\BAKABO SYSTEM"

if not exist ".venv" (
    echo [SETUP] Creo ambiente virtuale Python 3.13...
    py -3.13 -m venv .venv
    echo [SETUP] Installo dipendenze...
    .venv\Scripts\pip install -r requirements.txt --quiet
)

if not exist ".env" (
    echo [ATTENZIONE] .env non trovato.
    echo Copia .env.template in .env e compila le chiavi API.
    echo.
    pause
    exit /b 1
)

if not exist "data\verse.db" (
    echo [SETUP] Inizializzo database...
    .venv\Scripts\python scripts\init_db.py
)

echo [OK] BKS Verse API su http://localhost:8001
echo [OK] Docs: http://localhost:8001/docs
echo.

.venv\Scripts\uvicorn api.main:app --host 0.0.0.0 --port 8001 --reload

pause
