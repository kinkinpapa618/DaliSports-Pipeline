# upload_yt_nopublish.py - Upload video source len YouTube, dien title/chapters,
# NHUNG KHONG tu bam phan tich/publish. Giu cua so mo de nguoi dung tu xuong ban.
import os, sys, asyncio, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")
from playwright.async_api import async_playwright

import upload_source_youtube as u

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "upload_yt_nopublish_log.txt")


async def main():
    vid = [f for f in os.listdir(".") if f.lower().endswith(".mp4") and "caulong" in f.lower() and "timeline" not in f.lower()][0]
    norms = [f for f in os.listdir(".") if "caulong" in f.lower() and "_timeline_norms.txt" in f][0]
    video_path = os.path.abspath(vid)

    title, description = u.build_youtube_chapters_and_title(video_path, norms)
    print("=" * 60, flush=True)
    print("UPLOAD YOUTUBE (KHONG TU PUBLISH - GIU CUA SO MO)", flush=True)
    print(f"[*] Video: {video_path}", flush=True)
    print(f"[*] Tiêu đề: {title}", flush=True)
    print(f"[*] Mô tả kèm Chapters: {len(description)} ký tự", flush=True)
    print("=" * 60, flush=True)

    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            u.USER_DATA_DIR, channel="chrome", headless=False,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox",
                  "--disable-dev-shm-usage", "--start-maximized"],
            no_viewport=True, user_agent=user_agent,
        )
        page = await context.new_page()
        page.on("dialog", lambda d: asyncio.ensure_future(d.dismiss()))

        print("  [>] Mở trang YouTube Upload...", flush=True)
        await page.goto("https://www.youtube.com/upload", wait_until="domcontentloaded", timeout=90000)
        await asyncio.sleep(6)

        if "accounts.google" in page.url:
            print(">>> VUI LÒNG ĐĂNG NHẬP YOUTUBE TRONG TRÌNH DUYỆT...", flush=True)
            deadline = time.time() + 600
            while time.time() < deadline:
                if "accounts.google" not in page.url:
                    break
                await asyncio.sleep(4)

        print("  [>] Đang chọn tệp video source...", flush=True)
        btn = page.locator('button:has-text("Chọn tệp")')
        await btn.first.wait_for(state="visible", timeout=30000)
        async with page.expect_file_chooser(timeout=15000) as fc_info:
            await btn.first.click()
        fc = await fc_info.value
        await fc.set_files(video_path)
        print("  [+] Đã chọn tệp, chờ tải lên hoàn tất (video 6GB, có thể lâu)...", flush=True)

        # Chờ upload hoàn tất thật sự: phải KHÔNG còn "Đang tải lên"/"uploading" trong body
        # trong nhiều lần kiểm tra liên tiếp VÀ nút Next enabled (tránh nhầm khi chưa tải xong).
        upload_done = False
        upload_deadline = time.time() + 7200
        clean_streak = 0
        while time.time() < upload_deadline:
            try:
                txt = (await page.locator("body").inner_text(timeout=3000)) or ""
                uploading = ("Đang tải lên" in txt) or ("Đang xử lý" in txt) or ("uploading" in txt.lower())
                next_enabled = await page.locator("#next-button").is_enabled(timeout=1500)
                if not uploading and next_enabled:
                    clean_streak += 1
                    if clean_streak >= 6:
                        upload_done = True
                        break
                else:
                    clean_streak = 0
            except Exception:
                clean_streak = 0
            await asyncio.sleep(6)
        print("  [OK] Upload hoàn tất - BẮT ĐẦU ĐIỀN THÔNG TIN" if upload_done else "  [!] Hết thời gian chờ upload", flush=True)

        # 1. Tiêu đề
        try:
            ce = page.locator('[contenteditable="true"]').first
            await ce.wait_for(state="visible", timeout=10000)
            await ce.click()
            await page.keyboard.press("Control+a"); await asyncio.sleep(0.3)
            await ce.fill(""); await asyncio.sleep(0.2)
            await ce.type(title, delay=10)
            print("  [+] Đã điền tiêu đề", flush=True); await asyncio.sleep(1)
        except Exception as e:
            print(f"  [!] Tiêu đề lỗi: {e}", flush=True)

        # 2. Mô tả (chapters)
        try:
            de = page.locator('[contenteditable="true"]').nth(1)
            await de.click(); await asyncio.sleep(0.5)
            await de.fill(description)
            print("  [+] Đã điền mô tả kèm Chapters", flush=True); await asyncio.sleep(1)
        except Exception as e:
            print(f"  [!] Mô tả lỗi: {e}", flush=True)

        # 3. Not for kids
        try:
            await page.locator('tp-yt-paper-radio-button[name="VIDEO_MADE_FOR_KIDS_NOT_MFK"]').first.click(timeout=5000)
            print("  [+] Not for kids", flush=True); await asyncio.sleep(1)
        except Exception as e:
            print(f"  [!] Not for kids lỗi: {e}", flush=True)

        # 4. DỪNG - KHÔNG tự bấm Next/publish. Giu cua so mo cho nguoi dung tu xuong ban.
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n[{time.strftime('%Y-%m-%d %H:%M')}] {video_path} -> UPLOADED, await user publish\n")

        print("\n" + "=" * 60, flush=True)
        print("  ✅ ĐÃ UPLOAD + ĐIỀN THÔNG TIN. ", flush=True)
        print("  ▶ CỬA SỔ ĐANG ĐƯỢC GIỮ MỞ - BẠN TỰ BẤM:", flush=True)
        print("     1) Nút 'Tiếp theo' (Next) vài lần qua các bước", flush=True)
        print("     2) Cuối cùng chọn chế độ + bấm 'Xuất bản'", flush=True)
        print("  ▶ Script sẽ đợi 2 tiếng (giữ cửa sổ), bạn cứ thao tác.", flush=True)
        print("  ▶ Muốn tắt: đóng cửa sổ cmd hoặc Ctrl+C.", flush=True)
        print("=" * 60, flush=True)

        # Giu cua so mo: cho toi khi user dong (theo doi page co dong khong)
        while True:
            try:
                if page.is_closed():
                    print("[*] Trình duyệt đã đóng, kết thúc.", flush=True)
                    break
            except Exception:
                break
            await asyncio.sleep(30)


if __name__ == "__main__":
    asyncio.run(main())
