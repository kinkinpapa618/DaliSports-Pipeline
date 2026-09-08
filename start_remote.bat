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

echo [*] Dang khoi dong May Chu Web va ket noi Cloudflare Tunnel...
echo [*] Ban co the mo tren dien thoai hoac may tinh bang tu xa.
echo.

python "%~dp0system\remote_server.py" --tunnel --port 8000

if errorlevel 1 (
    echo.
    echo [LOI] Khong the khoi dong may chu tu xa.
    echo Vui long kiem tra lai Python va cac thu vien can thiet.
    pause
)
