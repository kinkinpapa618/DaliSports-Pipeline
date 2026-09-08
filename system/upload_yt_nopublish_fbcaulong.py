# upload_yt_nopublish_fbcaulong.py - Upload video FB cau long len YouTube
import os, sys, asyncio, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")
from playwright.async_api import async_playwright
import upload_source_youtube as u

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "upload_yt_fbcaulong_log.txt")
VIDEO_FILE = "fb_caulong.mp4"
NORMS_FILE = "fb_caulong_timeline_norms.txt"

async def main():
    video_path = os.path.abspath(VIDEO_FILE)
    norms_path = os.path.abspath(NORMS_FILE)
    if not os.path.exists(video_path):
        print(f"[!] Khong tim thay: {video_path}"); return
    if not os.path.exists(norms_path):
        print(f"[!] Khong tim thay: {norms_path}"); return

    title, description = u.build_youtube_chapters_and_title(video_path, norms_path)
    print("=" * 60, flush=True)
    print("UPLOAD YOUTUBE - FB CAU LONG (KHONG TU PUBLISH)", flush=True)
    print(f"[*] Video: {video_path} ({os.path.getsize(video_path)/1024/1024/1024:.2f} GB)", flush=True)
    print(f"[*] Tieu de: {title}", flush=True)
    print(f"[*] Mo ta: {len(description)} ky tu", flush=True)
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

        print("  [>] Mo trang YouTube Upload...", flush=True)
        await page.goto("https://www.youtube.com/upload", wait_until="domcontentloaded", timeout=90000)
        await asyncio.sleep(6)

        if "accounts.google" in page.url:
            print(">>> VUI LONG DANG NHAP YOUTUBE...", flush=True)
            deadline = time.time() + 600
            while time.time() < deadline:
                if "accounts.google" not in page.url:
                    break
                await asyncio.sleep(4)

        print("  [>] Chon tep video...", flush=True)
        btn = page.locator('button:has-text("Chọn tệp")')
        await btn.first.wait_for(state="visible", timeout=30000)
        async with page.expect_file_chooser(timeout=15000) as fc_info:
            await btn.first.click()
        fc = await fc_info.value
        await fc.set_files(video_path)
        print("  [+] Da chon tep, cho tai len...", flush=True)

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
        print("  [OK] Upload hoan tat" if upload_done else "  [!] Het thoi gian", flush=True)

        try:
            ce = page.locator('[contenteditable="true"]').first
            await ce.wait_for(state="visible", timeout=10000)
            await ce.click()
            await page.keyboard.press("Control+a"); await asyncio.sleep(0.3)
            await ce.fill(""); await asyncio.sleep(0.2)
            await ce.type(title, delay=10)
            print("  [+] Da dien tieu de", flush=True); await asyncio.sleep(1)
        except Exception as e:
            print(f"  [!] Tieu de loi: {e}", flush=True)

        try:
            de = page.locator('[contenteditable="true"]').nth(1)
            await de.click(); await asyncio.sleep(0.5)
            await de.fill(description)
            print("  [+] Da dien mo ta", flush=True); await asyncio.sleep(1)
        except Exception as e:
            print(f"  [!] Mo ta loi: {e}", flush=True)

        try:
            await page.locator('tp-yt-paper-radio-button[name="VIDEO_MADE_FOR_KIDS_NOT_MFK"]').first.click(timeout=5000)
            print("  [+] Not for kids", flush=True); await asyncio.sleep(1)
        except Exception as e:
            print(f"  [!] Not for kids loi: {e}", flush=True)

        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n[{time.strftime('%Y-%m-%d %H:%M')}] {video_path} -> UPLOADED\n")

        print("\n" + "=" * 60, flush=True)
        print("  DA UPLOAD + DIEN THONG TIN.", flush=True)
        print("  BAN TU BAM: Next -> Chon che do -> Xuat ban", flush=True)
        print("=" * 60, flush=True)

        while True:
            try:
                if page.is_closed(): break
            except Exception: break
            await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(main())
