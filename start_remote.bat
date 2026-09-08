@echo off
title DaliSports Studio - Remote Tunnel Launcher
chcp 65001 >nul
echo ========================================================
echo       DALISPORTS STUDIO - TRUY CẬP TỪ XA QUA TUNNEL
echo ========================================================
echo.

:: Kiểm tra nếu chưa có bản build web thì biên dịch
if not exist "%~dp0desktop\dist\index.html" (
    echo [*] Đang chuẩn bị giao diện Web Studio...
    cd /d "%~dp0desktop"
    call npm run build
    cd /d "%~dp0"
)

echo [*] Đang khởi động Máy Chủ Web và kết nối Cloudflare Tunnel...
echo [*] Bạn có thể mở trên điện thoại, máy tính bảng hoặc laptop từ xa.
echo.

python "%~dp0system\remote_server.py" --tunnel --port 8000

if errorlevel 1 (
    echo.
    echo [LỖI] Không thể khởi động máy chủ từ xa.
    echo Vui lòng kiểm tra lại Python và thư viện cần thiết.
    pause
)
