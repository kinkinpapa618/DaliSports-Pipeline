#!/usr/bin/env python3
# upload_source_youtube.py - Upload video SOURCE (dài) lên YouTube kèm Timeline Chapters trong Description
# Tự động đọc file norms.txt để tạo các mốc Chapter (00:00:00 Trận 1: ...)
#
# Cách dùng:
#   python upload_source_youtube.py "dalisportss_video10.mp4" --dry-run
#   python upload_source_youtube.py "dalisportss_video10.mp4"
import asyncio
import os
import sys
import time
import re
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
DESCRIPTION_FILE = os.path.join(FOLDER, "mota.txt.txt")
USER_DATA_DIR = os.path.join(os.environ.get("TEMP", "C:\\temp"), "yt_badv_profile")
LOG_FILE = os.path.join(FOLDER, "upload_source_log.txt")


def read_base_description() -> str:
    if os.path.exists(DESCRIPTION_FILE):
        with open(DESCRIPTION_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""


def build_youtube_chapters_and_title(video_path: str, norms_path: str = None, sport: str = None) -> tuple:
    """Tự động sinh Tiêu đề và Mô tả chuẩn SEO chứa Timeline Chapters - đọc seo_config theo giải"""
    try:
        import seo_helper
    except ImportError:
        seo_helper = None

    if not norms_path:
        base = os.path.splitext(video_path)[0]
        norms_path = base + "_timeline_norms.txt"
        if not os.path.exists(norms_path):
            norms_path = base + "_timeline.txt"

    norms_file = norms_path
    if "_timeline.txt" in norms_path and not norms_path.endswith("_norms.txt"):
        tl_candidate = norms_path.replace("_timeline.txt", "_timeline_norms.txt")
        if os.path.exists(tl_candidate):
            norms_file = tl_candidate

    tournament_name = ""
    court_info = "SÂN 2"
    chapters = ["\n⏰ TIMELINE CÁC TRẬN ĐẤU (CHAPTERS):"]
    match_num = 0
    
    if os.path.exists(norms_file):
        with open(norms_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = [p.strip() for p in line.split(" | ")]
                time_part = parts[0].split(" - ")[0].strip()
                if not tournament_name and len(parts) >= 2:
                    # parts[1] là tên giải (đã chuẩn hóa VIẾT HOA)
                    tournament_name = parts[1] if len(parts) >= 4 else parts[1]
                match_num += 1
                if len(parts) >= 4:
                    cat = parts[2]
                    players = parts[3]
                    chapter_label = f"Trận {match_num:02d}: {cat} | {players}"
                elif len(parts) == 3:
                    chapter_label = f"Trận {match_num:02d}: {parts[2]}"
                else:
                    chapter_label = f"Trận {match_num:02d}: " + " | ".join(parts[1:])
                chapters.append(f"{time_part} {chapter_label}")

    # Load SEO config theo giải
    config = {}
    if seo_helper:
        config = seo_helper.load_seo_config(tournament_name, video_path, sport=sport)
        if config:
            court_info = config.get("court", court_info)
            # Ưu tiên tên giải gốc từ timeline (Hồng Loan, TTBC...); chỉ dùng config khi timeline rỗng
            effective_tournament = tournament_name if tournament_name else config.get("tournament_full", "")
            # Build title/description chuẩn SEO - truyền effective_tournament để giữ tên gốc
            video_title = seo_helper.build_source_title(config, match_num, effective_tournament)
            # build_dynamic_description vẫn dùng config cho intro/hashtags, nhưng chapters đã đúng
            full_description = seo_helper.build_dynamic_description(config, chapters, match_num)
            # Nếu effective_tournament khác config tournament_full, thay thế trong description intro cho đúng tên
            if effective_tournament and effective_tournament != config.get("tournament_full"):
                full_description = full_description.replace(config.get("tournament_full", ""), effective_tournament)
            return video_title, full_description

    # Fallback cũ nếu không có seo_helper/config
    if tournament_name:
        video_title = f"{tournament_name} | {court_info} | TRỌN BỘ {match_num} TRẬN | Full HD".strip()
    else:
        video_title = f"GIẢI CẦU LÔNG - 2026 | {court_info} | TRỌN BỘ {match_num} TRẬN | Full HD".strip()
    if len(video_title) > 100:
        video_title = video_title[:100].rsplit(" ", 1)[0]
    base_desc = read_base_description()
    full_description = f"{base_desc}\n" + "\n".join(chapters)
    return video_title, full_description


def get_seo_tags(video_path: str, norms_path: str = None, sport: str = None) -> list:
    """Lấy danh sách tags ẩn YouTube từ seo_config"""
    try:
        import seo_helper
        # Reuse logic lấy tournament_name
        if not norms_path:
            base = os.path.splitext(video_path)[0]
            norms_path = base + "_timeline_norms.txt"
            if not os.path.exists(norms_path):
                norms_path = base + "_timeline.txt"
        tname = ""
        if os.path.exists(norms_path):
            with open(norms_path, "r", encoding="utf-8") as f:
                for line in f:
                    parts = [p.strip() for p in line.strip().split(" | ")]
                    if len(parts) >= 2:
                        tname = parts[1]
                        break
        cfg = seo_helper.load_seo_config(tname, video_path, sport=sport)
        return cfg.get("tags", [])
    except Exception:
        return []


async def handle_publish_flow(page, timeout: int = 40) -> bool:
    """Bấm Xuất bản và xử lý tự động bấm 'Vẫn xuất bản' nếu có popup cảnh báo"""
    print("  [>] Đang bấm nút 'Xuất bản'...")
    publish_clicked = False
    for _ in range(5):
        try:
            btn = page.locator('#publish-button, ytcp-button#publish-button, button:has-text("Xuất bản"), button:has-text("Publish")')
            if await btn.count() > 0 and await btn.first.is_visible(timeout=1500):
                await btn.first.click(timeout=4000)
                publish_clicked = True
                print("  [+] Đã bấm 'Xuất bản'")
                break
        except Exception:
            pass

        try:
            clicked = await page.evaluate("""() => {
                const btns = document.querySelectorAll('ytcp-button, button');
                for (const b of btns) {
                    const t = b.textContent.trim().toLowerCase();
                    if ((t === 'xuất bản' || t === 'publish' || t.includes('xuất bản')) && b.offsetParent !== null) {
                        b.click(); return true;
                    }
                }
                return false;
            }""")
            if clicked:
                publish_clicked = True
                print("  [+] Đã bấm 'Xuất bản' (qua JS)")
                break
        except Exception:
            pass
        await asyncio.sleep(0.8)

    if not publish_clicked:
        print("  [!] Không tìm thấy nút Xuất bản")
        return False

    start_time = time.time()
    still_publish_clicked = False

    while time.time() - start_time < timeout:
        if not still_publish_clicked:
            try:
                btn_still = page.get_by_role("button", name=re.compile(r"Vẫn\s*xuất\s*bản|Publish\s*anyway|Still\s*publish", re.I))
                if await btn_still.count() > 0 and await btn_still.first.is_visible(timeout=500):
                    await btn_still.first.click(timeout=3000)
                    still_publish_clicked = True
                    print("  [🔥] ĐÃ TỰ ĐỘNG BẤM 'VẪN XUẤT BẢN'!")
                    await asyncio.sleep(1)
            except Exception:
                pass

            if not still_publish_clicked:
                try:
                    clicked_js = await page.evaluate("""() => {
                        function queryAll(root) {
                            let nodes = Array.from(root.querySelectorAll('*'));
                            let all = [...nodes];
                            for (let n of nodes) {
                                if (n.shadowRoot) all = all.concat(queryAll(n.shadowRoot));
                            }
                            return all;
                        }
                        for (let el of queryAll(document)) {
                            if (el.tagName && (el.tagName.toLowerCase() === 'ytcp-button' || el.tagName.toLowerCase() === 'button')) {
                                const text = (el.textContent || '').trim().toLowerCase();
                                if (text.includes('vẫn xuất bản') || text.includes('publish anyway') || (text.includes('vẫn') && text.includes('bản'))) {
                                    if (el.offsetParent !== null || el.clientHeight > 0) {
                                        el.click(); return true;
                                    }
                                }
                            }
                        }
                        return false;
                    }""")
                    if clicked_js:
                        still_publish_clicked = True
                        print("  [🔥] ĐÃ TỰ ĐỘNG BẤM 'VẪN XUẤT BẢN' (Shadow DOM JS)!")
                        await asyncio.sleep(1)
                except Exception:
                    pass

        # Bấm nút Đóng nếu hoàn tất
        try:
            btn_close = page.get_by_role("button", name=re.compile(r"^(Đóng|Close|Xong)$", re.I))
            if await btn_close.count() > 0 and await btn_close.first.is_visible(timeout=500):
                await btn_close.first.click(timeout=3000)
                print("  [+] Đã bấm 'Đóng' hộp thoại hoàn tất")
                await asyncio.sleep(1)
                break
        except Exception:
            pass

        await asyncio.sleep(0.8)

    return True


async def upload_source_video(video_path: str, norms_path: str = None, dry_run: bool = False) -> bool:
    """Tự động tải video source dài lên YouTube kèm Chapter Timeline"""
    if not os.path.exists(video_path):
        print(f"[!] Không tìm thấy video: {video_path}")
        return False

    title, description = build_youtube_chapters_and_title(video_path, norms_path)
    
    print(f"\n============================================================")
    print(f"  UPLOAD SOURCE VIDEO (FULL) LÊN YOUTUBE")
    print(f"============================================================")
    print(f"[*] File video: {video_path}")
    print(f"[*] Tiêu đề: {title}")
    print(f"[*] Mô tả kèm Chapters:\n{description}")
    print(f"============================================================\n")

    if dry_run:
        print("[=== DRY-RUN YOUTUBE SOURCE: Không đăng thật ===]")
        return True

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
        page.on("dialog", lambda d: asyncio.ensure_future(d.dismiss()))

        print("  [>] Mở trang YouTube Upload...")
        await page.goto("https://www.youtube.com/upload", wait_until="domcontentloaded", timeout=90000)
        await asyncio.sleep(6)

        if "accounts.google" in page.url:
            print(">>> VUI LÒNG ĐĂNG NHẬP YOUTUBE TRONG TRÌNH DUYỆT (tối đa 10 phút)...")
            deadline = time.time() + 600
            while time.time() < deadline:
                if "accounts.google" not in page.url:
                    break
                await asyncio.sleep(4)

        print("  [>] Đang chọn tệp video source...")
        btn = page.locator('button:has-text("Chọn tệp")')
        await btn.first.wait_for(state="visible", timeout=30000)
        async with page.expect_file_chooser(timeout=15000) as fc_info:
            await btn.first.click()
        fc = await fc_info.value
        await fc.set_files(video_path)
        print("  [+] Đã chọn tệp video source, chờ tải lên hoàn tất (video 3-4GB có thể mất 30-90 phút)...")
        # === FIX: Chờ upload 100% thực sự - không đóng trình duyệt sớm ===
        # YouTube hiển thị "Đang tải lên XX%" trong shadow DOM, phải quét cả Shadow DOM + clean_streak
        upload_done = False
        upload_deadline = time.time() + 7200  # tối đa 2 tiếng cho video source lớn (>2GB)
        clean_streak = 0
        last_percent = ""
        while time.time() < upload_deadline:
            try:
                # Lấy toàn bộ text kể cả Shadow DOM để bắt "Đang tải lên 87%" / "Uploading 87%"
                shadow_text = await page.evaluate("""() => {
                    function getAllText(root) {
                        let t = root.innerText || '';
                        root.querySelectorAll('*').forEach(el => {
                            if (el.shadowRoot) t += ' ' + getAllText(el.shadowRoot);
                        });
                        return t;
                    }
                    return getAllText(document.body);
                }""")
                body_text = (shadow_text or "") + " " + ((await page.locator("body").inner_text(timeout=2000)) or "")
                # Tìm phần trăm upload nếu có
                m = re.search(r"(\d{1,3})\s*%", body_text)
                cur_percent = m.group(1) + "%" if m else ""
                if cur_percent and cur_percent != last_percent:
                    print(f"  [..] Đang tải lên: {cur_percent} - vui lòng đợi, KHÔNG đóng trình duyệt...")
                    last_percent = cur_percent

                is_uploading = (
                    "Đang tải lên" in body_text
                    or "Đang xử lý" in body_text
                    or "uploading" in body_text.lower()
                    or "processing" in body_text.lower()
                    or ("%" in body_text and re.search(r"\d+\s*%", body_text))
                )
                # Chỉ coi là xong khi KHÔNG còn dấu hiệu uploading VÀ nút Next đã enable, duy trì 6 lần liên tiếp (~36s)
                try:
                    next_enabled = await page.locator("#next-button").is_enabled(timeout=1500)
                except Exception:
                    next_enabled = False

                if not is_uploading and next_enabled:
                    clean_streak += 1
                    if clean_streak >= 6:
                        upload_done = True
                        break
                else:
                    clean_streak = 0
            except Exception as e:
                # Lỗi transient - reset streak
                clean_streak = 0
            await asyncio.sleep(6)
        if upload_done:
            print("  [OK] Upload 100% hoàn tất - bắt đầu điền thông tin...")
        else:
            print("  [!] Hết thời gian chờ 2 tiếng - vẫn thử tiếp (có thể mạng chậm, nhưng sẽ KHÔNG đóng trình duyệt)")

        # 1. Điền Tiêu đề
        try:
            ce = page.locator('[contenteditable="true"]').first
            await ce.wait_for(state="visible", timeout=10000)
            await ce.click()
            await page.keyboard.press("Control+a"); await asyncio.sleep(0.3)
            await ce.fill(""); await asyncio.sleep(0.2)
            await ce.type(title, delay=10)
            print("  [+] Đã điền tiêu đề"); await asyncio.sleep(1)
        except Exception as e:
            print(f"  [!] Điền tiêu đề lỗi: {e}")

        # 2. Điền Mô tả (Chứa Chapters)
        try:
            de = page.locator('[contenteditable="true"]').nth(1)
            await de.click(); await asyncio.sleep(0.5)
            await de.fill(description)
            print("  [+] Đã điền mô tả kèm Chapters"); await asyncio.sleep(1)
        except Exception as e:
            print(f"  [!] Điền mô tả lỗi: {e}")

        # 3. Đối tượng khán giả: Not for kids
        try:
            await page.locator('tp-yt-paper-radio-button[name="VIDEO_MADE_FOR_KIDS_NOT_MFK"]').first.click(timeout=5000)
            print("  [+] Đối tượng: Not for kids"); await asyncio.sleep(1)
        except Exception as e:
            print(f"  [!] Lỗi đối tượng: {e}")

        # 4. Next qua các bước
        for step in ["Video elements", "Checks", "Visibility"]:
            await asyncio.sleep(3)
            try:
                await page.locator('#next-button').first.click(timeout=8000)
                print(f"  [>] Bước tiếp theo: {step}")
            except Exception as e:
                print(f"  [!] Next error ({step}): {e}")
            await asyncio.sleep(3)

        # 5. Quyền riêng tư: Public
        try:
            await page.locator('tp-yt-paper-radio-button[name="PUBLIC"]').first.click(timeout=5000)
            print("  [+] Chế độ: Công khai (Public)"); await asyncio.sleep(2)
        except Exception:
            pass

        # 6. Xuất bản và xác nhận
        ok = await handle_publish_flow(page, timeout=40)
        if ok:
            print(f"\n[🎉] ĐÃ XUẤT BẢN THÀNH CÔNG VIDEO SOURCE LÊN YOUTUBE (KÈM CHAPTERS)!")
        else:
            print(f"\n[!] Xuất bản video source thất bại.")

        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n[{time.strftime('%Y-%m-%d %H:%M')}] {video_path} -> {'SUCCESS' if ok else 'FAILED'}\n")

        # === FIX: KHÔNG đóng trình duyệt ngay sau khi bấm Xuất bản ===
        # Video 3-4GB cần thêm thời gian YouTube xử lý server-side sau khi bấm publish.
        # Giữ cửa sổ mở ít nhất 10 phút để đảm bảo upload không bị hủy.
        if ok:
            print("\n  [OK] Đã bấm Xuất bản - GIỮ TRÌNH DUYỆT MỞ 10 PHÚT để YouTube xử lý xong...")
            print("  [INFO] Bạn có thể kiểm tra trong YouTube Studio. Script sẽ tự đóng sau 10 phút,")
            print("         hoặc bạn có thể đóng thủ công khi thấy video đã 'Đã xử lý xong'.")
            try:
                # Đợi 600s (10 phút) nhưng vẫn kiểm tra nếu user đã đóng page thì thoát sớm
                for _ in range(60):
                    if page.is_closed():
                        print("  [*] Trình duyệt đã được đóng thủ công.")
                        break
                    await asyncio.sleep(10)
            except Exception:
                pass
        else:
            print("\n  [!] Xuất bản chưa chắc thành công - giữ trình duyệt mở 5 phút để bạn kiểm tra thủ công...")
            try:
                for _ in range(30):
                    if page.is_closed():
                        break
                    await asyncio.sleep(10)
            except Exception:
                pass

        # Chỉ đóng context/page sau khi đã giữ đủ thời gian, KHÔNG dùng taskkill (tránh giết nhầm Chrome khác)
        try:
            if not page.is_closed():
                await page.close()
        except Exception:
            pass
        try:
            await context.close()
        except Exception:
            pass
        return ok


def main():
    parser = argparse.ArgumentParser(description="Upload video source dài lên YouTube kèm Chapter Timeline")
    parser.add_argument("video", nargs="?", default=None, help="Đường dẫn file video .mp4")
    parser.add_argument("norms", nargs="?", default=None, help="Đường dẫn file *_timeline_norms.txt")
    parser.add_argument("--dry-run", action="store_true", help="Chạy thử không đăng")

    args = parser.parse_args()

    vid = args.video
    if not vid:
        # Tìm video mp4 source trong thư mục
        cands = [f for f in os.listdir(FOLDER) if f.endswith(".mp4") and "clip" not in f.lower()]
        if cands:
            vid = os.path.join(FOLDER, max(cands, key=lambda x: os.path.getmtime(os.path.join(FOLDER, x))))
        else:
            vid = input("Nhập đường dẫn file video source: ").strip()

    asyncio.run(upload_source_video(vid, norms_path=args.norms, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
