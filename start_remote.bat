@echo off
title DaliSports Studio - Remote Tunnel Launcher
echo ========================================================
echo       DALISPORTS STUDIO - TRUY CAP TU XA QUA TUNNEL
echo ========================================================
echo.

:: Kiem tra neu chua co ban build web thi bien dich
if not exist "%~dp0desktop\dist\index.html" (
    echo [*] Dang bien dich giao dien Web Studio...
    cd /d "%~dp0desktop"
    call npm run build
    cd /d "%~dp0"
)

:: Kiem tra neu port 8000 da duoc mo boi PM2 hoac tien trinh khac
netstat -ano | findstr :8000 | findstr LISTENING >nul 2>&1
if not errorlevel 1 (
    echo [*] May chu DaliSports Studio da duoc khoi dong va dang chay!
    echo.
    echo ========================================================
    echo  DOMAIN TU XA:  https://stu.trongtaiso.com
    echo  MANG NOI BO:   http://localhost:8000
    echo ========================================================
    echo.
    echo [*] Dang mo trinh duyet toi: https://stu.trongtaiso.com
    start https://stu.trongtaiso.com
    goto :end
)

:: Neu chua chay, khoi dong qua PM2 neu co hoac python truc tiep
where pm2 >nul 2>&1
if not errorlevel 1 (
    echo [*] Khoi dong bang PM2 daemon...
    pm2 start "%~dp0system\remote_server.py" --name dalisports-remote --interpreter python
    pm2 save
    timeout /t 2 >nul
    start https://stu.trongtaiso.com
    goto :end
)

echo [*] Dang khoi dong May Chu Web...
python "%~dp0system\remote_server.py" --port 8000

:end
echo.
echo ========================================================
echo  Nhan phim bat ky de dong cua so nay...
echo ========================================================
pause >nul
