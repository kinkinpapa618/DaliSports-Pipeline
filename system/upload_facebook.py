#!/usr/bin/env python3
# upload_facebook.py - Tự động Upload các clip từ thư mục clips/ hoặc file chỉ định lên Facebook
# Tiêu đề & danh sách trận lấy từ clips/clips_info.txt, mô tả lấy từ mota.txt.txt.
# Sử dụng profile Playwright persistent (fb_badv_profile trong %TEMP%) để lưu phiên đăng nhập.
#
# Cách dùng:
#   python upload_facebook.py --file "C:\path\to\video.mp4"    (đăng 1 file video cụ thể)
#   python upload_facebook.py                                 (đăng toàn bộ clip thành 1 album lên Facebook)
#   python upload_facebook.py --dry-run                       (xem trước nội dung không đăng)
import asyncio
import os
import sys
import time
import re
import glob
import argparse

sys.stdout.reconfigure(encoding="utf-8")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("[!] Chưa cài playwright. Chạy: pip install playwright && playwright install chromium")
    sys.exit(1)

FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CLIPS_DIR = os.path.join(FOLDER, "clips")
INFO_FILE = os.path.join(CLIPS_DIR, "clips_info.txt")
DESCRIPTION_FILE = os.path.join(FOLDER, "mota.txt.txt")
USER_DATA_DIR = os.path.join(os.environ.get("TEMP", "C:\\temp"), "fb_badv_profile")
LOG_FILE = os.path.join(FOLDER, "upload_fb_log.txt")
PAGE_URL = "https://www.facebook.com/dalisportss"


def resolve_clips_dir(cli_arg: str = None) -> str:
    """Tìm thư mục clips thực tế: ưu tiên cli_arg, rồi tournament/video subfolder, rồi root clips"""
    if cli_arg and os.path.isdir(cli_arg):
        return cli_arg
    if os.path.exists(CLIPS_DIR) and glob.glob(os.path.join(CLIPS_DIR, "*.mp4")):
        return CLIPS_DIR
    candidates = []
    for pat in [os.path.join(FOLDER, "20*_*", "clips"), os.path.join(FOLDER, "20*_*", "*", "clips")]:
        for entry in glob.glob(pat):
            if os.path.isdir(entry) and glob.glob(os.path.join(entry, "*.mp4")):
                candidates.append(entry)
    if candidates:
        return max(candidates, key=lambda p: os.path.getmtime(p) if os.path.exists(p) else 0)
    return CLIPS_DIR


def read_base_description() -> str:
    if os.path.exists(DESCRIPTION_FILE):
        with open(DESCRIPTION_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""


def read_info(info_path: str = None) -> dict:
    mapping = {}
    target_info = info_path or INFO_FILE
    if not os.path.exists(target_info):
        return mapping
    with open(target_info, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.strip() or " | " not in line:
                continue
            fname, title = line.split(" | ", 1)
            mapping[fname.strip()] = title.strip()
    return mapping


def build_album_caption(mapping: dict) -> str:
    """Tạo nội dung bài viết Album tổng hợp toàn bộ các trận đấu"""
    base_desc = read_base_description()
    lines = [base_desc, "\n🏆 ALBUM TRỌN BỘ CÁC TRẬN ĐẤU (CLIPS):"]
    for i, (fname, title) in enumerate(mapping.items(), 1):
        lines.append(f"🏸 Trận {i:02d}: {title}")
    return "\n".join(lines).strip()


async def is_facebook_logged_in(page) -> bool:
    """Kiểm tra chính xác tài khoản đã đăng nhập Facebook chưa"""
    try:
        cookies = await page.context.cookies()
        for c in cookies:
            if c.get("name") == "c_user":
                return True

        if await page.locator('input[name="email"], input[id="email"], button[name="login"]').count() > 0:
            return False

        if await page.locator('div[role="navigation"], div[role="feed"], div[aria-label*="Tài khoản"], div[aria-label*="Account"]').count() > 0:
            return True
    except Exception:
        pass
    return False


async def wait_for_facebook_login(page, timeout: int = 600) -> bool:
    """Chờ người dùng đăng nhập Facebook thủ công 1 lần đầu"""
    deadline = time.time() + timeout

    while time.time() < deadline:
        if await is_facebook_logged_in(page):
            return True

        remaining = int(deadline - time.time())
        sys.stdout.write(f"\r>>> Vui lòng đăng nhập Facebook trong cửa sổ trình duyệt (còn {remaining}s)... ")
        sys.stdout.flush()
        await asyncio.sleep(3)

    print()
    return await is_facebook_logged_in(page)


async def upload_to_facebook_browser(page, video_paths: list, caption: str) -> bool:
    """Tự động đăng 1 hoặc nhiều video lên Facebook"""
    print(f"  [>] Chuẩn bị tải lên {len(video_paths)} video...")
    print(f"  [>] Mở Facebook...")

    await page.goto("https://www.facebook.com", wait_until="domcontentloaded", timeout=90000)
    await asyncio.sleep(4)

    # 1. Kiểm tra trạng thái đăng nhập
    if not await is_facebook_logged_in(page):
        print("\n" + "=" * 60)
        print(">>> VUI LÒNG ĐĂNG NHẬP FACEBOOK TRONG CỬA SỔ TRÌNH DUYỆT ĐANG MỞ...")
        print("    (Script sẽ tự động lưu phiên trong %TEMP%/fb_badv_profile)")
        print("=" * 60)
        logged_in = await wait_for_facebook_login(page, timeout=600)
        if not logged_in:
            print("[!] Hết thời gian chờ đăng nhập Facebook.")
            return False
        print("\n>>> ĐÃ ĐĂNG NHẬP FACEBOOK THÀNH CÔNG! Đang tiếp tục...")

    # 1b. Điều hướng tới TRANG PAGE (dalisportss) để tạo bài viết dưới danh nghĩa Page
    print(f"  [>] Điều hướng tới Page: {PAGE_URL}")
    await page.goto(PAGE_URL, wait_until="domcontentloaded", timeout=90000)
    await asyncio.sleep(6)

    # 1c. Nếu Facebook yêu cầu "Chuyển sang Trang" -> bấm "Chuyển ngay" / "Chuyển"
    #     Dùng get_by_text thay vì CSS selector để match Unicode tốt hơn
    switched = False
    for label in ["Chuyển ngay", "Switch now", "Chuyển", "Switch"]:
        try:
            sw = page.get_by_text(label, exact=False).first
            if await sw.count() > 0 and await sw.is_visible(timeout=2000):
                print(f"  [>] Đang chuyển sang chế độ Page (bấm '{label}')...")
                await sw.click()
                await asyncio.sleep(6)
                switched = True
                break
        except Exception:
            pass

    # 2. Mở khung tạo bài viết (Create Post modal)
    print("  [>] Đang mở khung tạo bài viết trên Page...")
    post_box_opened = False

    # Thử click "Bạn đang nghĩ gì?" bằng get_by_role (handle Unicode tốt)
    for label in ["Bạn đang nghĩ gì", "What's on your mind", "Tạo bài viết", "Create post", "Viết gì đó"]:
        try:
            btn = page.get_by_role("button", name=label, exact=False).first
            if await btn.count() > 0 and await btn.is_visible(timeout=2000):
                print(f"  [>] Click button: '{label}'")
                await btn.click()
                post_box_opened = True
                await asyncio.sleep(3)
                break
        except Exception:
            pass

    # Fallback: thử CSS selector
    if not post_box_opened:
        for sel in [
            '[role="button"]', 'div[role="button"]',
            'span:has-text("ngh")', 'div:has-text("ngh")',
        ]:
            try:
                btn = page.locator(sel).first
                txt = (await btn.inner_text(timeout=800)).strip()
                if "ngh" in txt.lower() and await btn.is_visible(timeout=1000):
                    await btn.click()
                    post_box_opened = True
                    await asyncio.sleep(3)
                    break
            except Exception:
                pass

    if not post_box_opened:
        print("  [!] Không tìm thấy nút tạo bài viết - thử reload...")
        await page.reload(wait_until="domcontentloaded")
        await asyncio.sleep(5)
        for label in ["Chuyển ngay", "Chuyển"]:
            try:
                sw = page.get_by_text(label, exact=False).first
                if await sw.count() > 0 and await sw.is_visible(timeout=2000):
                    print(f"  [>] Re-switch: '{label}'")
                    await sw.click()
                    await asyncio.sleep(6)
                    break
            except Exception:
                pass
        for label in ["Bạn đang nghĩ gì", "Tạo bài viết", "Create post"]:
            try:
                btn = page.get_by_role("button", name=label, exact=False).first
                if await btn.count() > 0 and await btn.is_visible(timeout=1500):
                    await btn.click()
                    post_box_opened = True
                    await asyncio.sleep(3)
                    break
            except Exception:
                pass

    print(f"  [*] Trạng thái tạo bài: {'Mo da mo' if post_box_opened else 'Chua mo'}")

    # 3. Đính kèm các tệp video - dùng icon "Ảnh/video" trong modal
    print(f"  [>] Đang đính kèm {len(video_paths)} tệp video...")

    # Flow mới: click icon "Ảnh/video" trong "Thêm vào bài viết của bạn" -> File Chooser
    attached = False
    for label in ["Ảnh/video", "Photo/video", "Anh/video"]:
        try:
            # Tìm trong dialog trước
            av_btn = page.locator('div[role="dialog"]').get_by_role("button", name=label, exact=False).first
            if await av_btn.count() == 0:
                av_btn = page.get_by_role("button", name=label, exact=False).first
            if await av_btn.count() > 0 and await av_btn.is_visible(timeout=2000):
                print(f"  [>] Click '{label}' de chon video...")
                async with page.expect_file_chooser(timeout=15000) as fc_info:
                    await av_btn.click()
                fc = await fc_info.value
                await fc.set_files(video_paths)
                attached = True
                print("  [+] Da chon tep video thanh cong!")
                break
        except Exception as ex:
            print(f"  [*] Thu '{label}' loi: {ex}")

    # Fallback: thử input[type=file] trực tiếp
    if not attached:
        try:
            file_input = page.locator('input[type="file"]').first
            await file_input.wait_for(state="attached", timeout=8000)
            await file_input.set_input_files(video_paths)
            attached = True
            print("  [+] Da dinh kem qua input file!")
        except Exception as e:
            print(f"  [!] Khong dinh kem duoc video: {e}")
            return False

    if not attached:
        print("  [!] Khong dinh kem duoc video bat ky cach nao.")
        return False

    # 4. Chờ video upload/encode xong, rồi click "Tiếp"
    print("  [+] Dang tai video len, cho hoan tat...")
    upload_deadline = time.time() + 1800
    while time.time() < upload_deadline:
        try:
            body_txt = (await page.locator("body").inner_text(timeout=2000)) or ""
            lower = body_txt.lower()
            if "dang tai len" not in lower and "uploading" not in lower:
                if await page.locator('div[role="dialog"] img, div[role="dialog"] video').count() > 0:
                    print("  [+] Video da tai xong (co preview)")
                    break
        except Exception:
            pass
        await asyncio.sleep(5)
    await asyncio.sleep(3)

    # 5. Click "Tiếp" (Next) de sang buoc tiep theo
    print("  [>] Dang tim va bam nut 'Tiep'...")
    next_clicked = False
    for label in ["Tiếp", "Next"]:
        try:
            # Thu nhieu cach: get_by_role, get_by_text, CSS filter
            tiep_btn = None
            for finder in [
                lambda: page.locator('div[role="dialog"]').get_by_text(label, exact=True).first,
                lambda: page.get_by_text(label, exact=True).first,
                lambda: page.locator(f'div[role="dialog"] div[role="button"]:has-text("{label}")').first,
            ]:
                try:
                    candidate = finder()
                    if await candidate.count() > 0 and await candidate.is_visible(timeout=1500):
                        tiep_btn = candidate
                        break
                except:
                    pass

            if tiep_btn is None:
                continue

            # Chờ enable (tối đa 5 phút)
            tiep_deadline = time.time() + 300
            while time.time() < tiep_deadline:
                try:
                    if await tiep_btn.is_visible(timeout=1500):
                        disabled = await tiep_btn.get_attribute("aria-disabled")
                        if disabled != "true":
                            await tiep_btn.click(timeout=8000)
                            next_clicked = True
                            print(f"  [+] Da bam 'Tiep' thanh cong!")
                            await asyncio.sleep(4)
                            break
                except Exception:
                    pass
                await asyncio.sleep(3)
            if next_clicked:
                break
        except Exception:
            pass

    if not next_clicked:
        print("  [!] Khong bam duoc nut 'Tiep' - thu dang bai truc tiep...")
        # Có thể nút "Tiếp" không cần thiết, thử tìm "Đăng" luôn

    # 6. Điền Caption bài viết (neu chua dien o buoc 2)
    print("  [>] Dang dien noi dung Caption...")
    try:
        text_editor = None
        for sel in [
            'div[role="dialog"] [contenteditable="true"][role="textbox"]',
            'div[role="dialog"] [contenteditable="true"]',
            'div[role="dialog"] [role="textbox"]',
            '[contenteditable="true"][role="textbox"]',
        ]:
            el = page.locator(sel).first
            if await el.count() > 0 and await el.is_visible(timeout=2000):
                text_editor = el
                break
        if text_editor:
            await text_editor.click()
            await page.keyboard.press("Control+a")
            await asyncio.sleep(0.3)
            await text_editor.fill(caption)
            print("  [+] Da dien xong Caption bai viet")
            await asyncio.sleep(2)
        else:
            print("  [!] Khong tim thay text editor de dien caption")
    except Exception as e:
        print(f"  [!] Dien caption loi: {e}")

    # 7. Bấm nút Đăng (Post / Publish)
    print("  [>] Dang tim va bam nut 'Dang'...")
    published = False
    for txt in ["Đăng", "Post", "Chia sẻ ngay", "Share now", "Publish"]:
        try:
            # Thu nhieu cach tim nut
            pub_btn = None
            for finder in [
                lambda: page.locator('div[role="dialog"]').get_by_text(txt, exact=True).first,
                lambda: page.get_by_text(txt, exact=True).first,
                lambda: page.locator(f'div[role="dialog"] div[role="button"]:has-text("{txt}")').first,
            ]:
                try:
                    candidate = finder()
                    if await candidate.count() > 0 and await candidate.is_visible(timeout=1500):
                        pub_btn = candidate
                        break
                except:
                    pass

            if pub_btn is None:
                continue

            post_deadline = time.time() + 1800
            found_enabled = False
            while time.time() < post_deadline:
                try:
                    if await pub_btn.is_visible(timeout=1500):
                        disabled = await pub_btn.get_attribute("aria-disabled")
                        if disabled != "true":
                            found_enabled = True
                            break
                except Exception:
                    pass
                await asyncio.sleep(3)
            if found_enabled:
                await pub_btn.click(timeout=8000)
                published = True
                print(f"  [+] Da bam nut '{txt}' thanh cong!")
                break
        except Exception:
            pass

    if published:
        print("  [*] Dang cho Facebook xu ly va tai len hoan tat...")
        close_deadline = time.time() + 360
        while time.time() < close_deadline:
            try:
                if await page.locator('div[role="dialog"]').count() == 0:
                    print("  [+] Bai viet da xuat ban va dong modal!")
                    break
            except Exception:
                pass
            await asyncio.sleep(2)
        return True

    print("  [!] Khong tim thay nut Dang bai viet (hoac nut bi disabled qua lau).")
    return False


async def main():
    parser = argparse.ArgumentParser(description="Upload video lên Facebook dạng Album hoặc video đơn")
    parser.add_argument("--clips-dir", default=None, help="Đường dẫn đến thư mục clips")
    parser.add_argument("--file", default=None, help="Đường dẫn đến 1 file video cụ thể cần upload")
    parser.add_argument("--caption", default=None, help="Nội dung caption cho bài viết")
    parser.add_argument("--dry-run", action="store_true", help="Chạy thử không đăng")
    parser.add_argument("--delete-after", action="store_true", help="Tự động xóa clip sau khi đăng")

    args = parser.parse_args()

    # Xác định danh sách video và caption
    if args.file:
        video_path = os.path.abspath(args.file)
        if not os.path.exists(video_path):
            print(f"[!] Không tìm thấy file: {video_path}")
            return
        video_paths = [video_path]
        filename = os.path.basename(video_path)
        base_desc = read_base_description()
        caption = args.caption or f"{base_desc}\n\n🏸 {os.path.splitext(filename)[0]}".strip()
        print(f"Target Single Video: {video_path}")
    else:
        global CLIPS_DIR, INFO_FILE
        CLIPS_DIR = resolve_clips_dir(args.clips_dir)
        INFO_FILE = os.path.join(CLIPS_DIR, "clips_info.txt")
        print(f"[*] Facebook Clips dir: {CLIPS_DIR}")
        mapping = read_info(INFO_FILE)
        if not os.path.exists(CLIPS_DIR):
            print(f"[!] Thư mục clips không tồn tại: {CLIPS_DIR}")
            return
        video_files = sorted([f for f in os.listdir(CLIPS_DIR) if f.endswith(".mp4")])
        if mapping:
            video_files = [f for f in video_files if f in mapping]
        video_paths = [os.path.join(CLIPS_DIR, f) for f in video_files]
        caption = build_album_caption(mapping)
        print(f"Loaded {len(video_files)} clip videos for Facebook upload\n")

    if not video_paths:
        print("[!] Không có video nào để upload.")
        return

    if args.dry_run:
        print("============================================================")
        print("=== DRY-RUN FACEBOOK (Xem trước nội dung đăng) ===")
        print("============================================================")
        print(f"[*] Số lượng video đính kèm: {len(video_paths)}")
        print(f"[*] Danh sách file:\n" + "\n".join(f"    - {f}" for f in video_paths))
        print(f"\n[*] Caption bài viết:\n{caption}")
        print("============================================================")
        return

    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            USER_DATA_DIR,
            channel="chrome",
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--start-maximized"
            ],
            no_viewport=True,
            user_agent=user_agent
        )

        page = await context.new_page()
        ok = await upload_to_facebook_browser(page, video_paths, caption)

        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n[{time.strftime('%Y-%m-%d %H:%M')}] FACEBOOK ({len(video_paths)} videos) -> {'SUCCESS' if ok else 'FAILED'}\n")

        if ok and args.delete_after:
            for vp in video_paths:
                try:
                    os.remove(vp)
                except Exception:
                    pass
            print(f"  [+] Đã dọn dẹp các file clip sau khi đăng")

        await page.close()
        await context.close()


if __name__ == "__main__":
    asyncio.run(main())
