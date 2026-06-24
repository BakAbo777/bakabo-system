@echo off
title BKS Verse — Deploy Hetzner
color 0E

set SERVER=95.217.232.186
set REMOTE=/opt/bks-verse

echo ============================================================
echo   BKS Verse — Deploy su Hetzner CX22
echo   IP: %SERVER%   Servizio: bks-verse
echo ============================================================
echo.
echo Inserisci la password SSH una sola volta.
echo.

REM Crea un archivio tar con i 3 file da pushare
cd /d "I:\BAKABO SYSTEM"
tar -cf "%TEMP%\bks_verse_patch.tar" api/main.py api/routes/leaderboard.py data/schema.sql verse_engine/db.py data/poets.json scripts/init_db.py
if errorlevel 1 (
    echo [ERRORE] tar non trovato. Prova con Windows 10+ o installa Git Bash.
    pause
    exit /b 1
)

REM Upload tar + unpack + init + restart in UNA connessione SSH
type "%TEMP%\bks_verse_patch.tar" | ssh -o StrictHostKeyChecking=no root@%SERVER% "cat > /tmp/patch.tar && tar -xf /tmp/patch.tar -C %REMOTE% && echo '[OK] File aggiornati' && cd %REMOTE% && .venv/bin/python scripts/init_db.py && systemctl restart bks-verse && sleep 2 && systemctl status bks-verse --no-pager | grep -E 'Active|Main PID' && curl -s http://localhost:8001/health && echo ''"

if errorlevel 1 (
    echo.
    echo [ERRORE] Deploy fallito.
) else (
    echo.
    echo ============================================================
    echo   Deploy OK. Test: https://verse.bakabo.club/health
    echo   Leaderboard: https://verse.bakabo.club/leaderboard/global
    echo ============================================================
)

del "%TEMP%\bks_verse_patch.tar" 2>nul
pause
