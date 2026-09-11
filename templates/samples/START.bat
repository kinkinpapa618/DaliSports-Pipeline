@echo off
chcp 65001 >nul
title DaliSports - 1-Click Livestream Launcher
echo ================================================================
echo    🚀 DALISPORTS 1-CLICK LIVESTREAM: KHOI DONG TRUC TIEP
echo ================================================================
echo.
set TOURNAMENT_DIR=%~dp0
if "%TOURNAMENT_DIR:~-1%"=="\" set TOURNAMENT_DIR=%TOURNAMENT_DIR:~0,-1%

:: Tim duong dan toi script start_live_orchestrator.py
set SCRIPT_PATH=""
if exist "%TOURNAMENT_DIR%\..\system\start_live_orchestrator.py" (
    set SCRIPT_PATH="%TOURNAMENT_DIR%\..\system\start_live_orchestrator.py"
) else if exist "%TOURNAMENT_DIR%\..\..\system\start_live_orchestrator.py" (
    set SCRIPT_PATH="%TOURNAMENT_DIR%\..\..\system\start_live_orchestrator.py"
) else if exist "e:\www\DaliSports-Pipeline\system\start_live_orchestrator.py" (
    set SCRIPT_PATH="e:\www\DaliSports-Pipeline\system\start_live_orchestrator.py"
)

if %SCRIPT_PATH%=="" (
    echo [!] Khong tim thay script start_live_orchestrator.py!
    pause
    exit /b 1
)

echo [*] Thu muc giai: %TOURNAMENT_DIR%
echo [*] Dang khoi chay tien trinh tu dong hoa...
echo.

python %SCRIPT_PATH% --tournament "%TOURNAMENT_DIR%"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] Co loi xay ra trong qua trinh khoi chay!
    pause
)
