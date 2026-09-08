@echo off
REM --- Tải video Facebook chất lượng tốt nhất bằng yt-dlp ---
REM Cách dùng: kéo thả link vào file này, hoặc chạy rồi dán link.

setlocal
set "OUT_DIR=%~dp0"
set "URL=%~1"

if "%URL%"=="" (
    set /p URL=Nhap link video Facebook: 
)

echo [+] Dang tai: %URL%
yt-dlp -f "bestvideo+bestaudio/best" -N 4 -o "%OUT_DIR%%%(title)s.%%(ext)s" --no-playlist --merge-output-format mp4 --remux-video mp4 --retry-sleep 3 --retries 10 "%URL%"

echo [+] Xong! File luu tai: %OUT_DIR%
pause
