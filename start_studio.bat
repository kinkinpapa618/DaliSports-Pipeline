@echo off
title DaliSports Studio Launcher
echo ========================================================
echo         KHOI DONG DALISPORTS STUDIO DESKTOP
echo ========================================================
cd /d "%~dp0desktop"
npm run dev
if errorlevel 1 (
    echo.
    echo [LOI] Khong the khoi dong DaliSports Studio.
    echo Vui long kiem tra Node.js hoac chay 'npm install' trong thu muc desktop.
    pause
)

