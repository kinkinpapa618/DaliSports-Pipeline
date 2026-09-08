@echo off
title DaliSports Studio Launcher
echo ========================================================
echo         KHOI DONG DALISPORTS STUDIO DESKTOP
echo ========================================================

:: Tat cac tien trinh electron chay ngam cu neu co
taskkill /f /im electron.exe >nul 2>&1

:: Xoa bo nho dem GPU bi khoa neu co
if exist "%APPDATA%\dalisports-studio\GPUCache" (
    rmdir /s /q "%APPDATA%\dalisports-studio\GPUCache" >nul 2>&1
)

cd /d "%~dp0desktop"
npm run dev
if errorlevel 1 (
    echo.
    echo [LOI] Khong the khoi dong DaliSports Studio.
    echo Vui long kiem tra Node.js hoac chay 'npm install' trong thu muc desktop.
    pause
)


