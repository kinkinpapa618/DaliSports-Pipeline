@echo off
title DaliSports Studio - Build Setup
echo ========================================================
echo        DONG GOI BO CAI DAT DALISPORTS STUDIO
echo ========================================================
echo.
cd /d "%~dp0desktop"

echo [1/2] Dang bien dich va dong goi bo cai dat Windows...
call npm run dist

if errorlevel 1 (
    echo.
    echo [LOI] Dong goi that bai. Vui long kiem tra lai log loi ben tren.
    pause
    exit /b 1
)

echo.
echo ========================================================
echo [THANH CONG] File cai dat da duoc tao tai:
echo %~dp0desktop\dist-app
echo.
echo   - DaliSports Studio Setup 1.0.0.exe (Bo cai dat Windows)
echo   - DaliSports Studio 1.0.0.exe       (Ban chay ngay Portable)
echo ========================================================
echo.
pause
