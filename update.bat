@echo off
title DaliSports Studio - Tu Dong Cap Nhat
echo ========================================================
echo       DALISPORTS STUDIO - AUTO UPDATE MANAGER
echo ========================================================
echo.

cd /d "%~dp0"

echo [*] Buoc 1/3: Dang kiem tra va dong bo ma nguon moi nhat tu GitHub...
git --version >nul 2>&1
if errorlevel 1 (
    echo [CANH BAO] Khong tim thay Git trong PATH. Dang su dung PowerShell de tai ban cap nhat...
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://github.com/kinkinpapa618/DaliSports-Pipeline/archive/refs/heads/main.zip' -OutFile 'update_main.zip' -UseBasicParsing; Expand-Archive -Path 'update_main.zip' -DestinationPath 'temp_update' -Force; Copy-Item -Path 'temp_update\DaliSports-Pipeline-main\*' -Destination '.' -Recurse -Force; Remove-Item -Path 'temp_update' -Recurse -Force; Remove-Item -Path 'update_main.zip' -Force"
) else (
    git pull origin main
    if errorlevel 1 (
        echo [LOI] Khong the pull tu GitHub. Vui long kiem tra ket noi mang.
        pause
        exit /b 1
    )
)

echo.
echo [*] Buoc 2/3: Go bo co chan bao mat Windows SmartScreen (Unblock-File)...
powershell -Command "Get-ChildItem -Path '%~dp0*' -Recurse -ErrorAction SilentlyContinue | Unblock-File; Get-Item -Path '%~dp0*' -ErrorAction SilentlyContinue | Unblock-File"

echo.
echo [*] Buoc 3/3: Kiem tra va bien dich he thong Desktop Studio...
cd /d "%~dp0desktop"
if exist "package.json" (
    cmd /c "npm run build"
)

cd /d "%~dp0"
echo.
echo ========================================================
echo   [THANH CONG] DA CAP NHAT DALISPORTS STUDIO THANH CONG!
echo ========================================================
echo.
set /p RUN_NOW="Ban co muon khoi dong DaliSports Studio ngay bay gio? (Y/N): "
if /i "%RUN_NOW%"=="Y" (
    start "" "%~dp0start_studio.bat"
)
exit /b 0
