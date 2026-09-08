#!/usr/bin/env python3
# upload_clips.py - Upload các clip từ thư mục clips/ lên YouTube (Playwright)
# Tiêu đề lấy từ clips/clips_info.txt (format: <filename> | <tiêu đề chuẩn hóa>)
# Mô tả lấy từ mota.txt.txt, đăng nhập bằng profile Playwright persistent (yt_profile/).
# Lần đầu chạy bạn đăng nhập YouTube thủ công 1 lần, các lần sau tự động dùng lại.
# Chạy thử không đăng:  python upload_clips.py --dry-run
import asyncio
import os
import sys
import time
import re
import glob

sys.stdout.reconfigure(encoding="utf-8")

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("[!] Chưa cài playwright. Chạy: pip install playwright && playwright install chromium")
    sys.exit(1)

FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# Hỗ trợ tournament folder: nếu chạy từ pipeline với video trong tournament folder, CLIPS_DIR sẽ được override
CLIPS_DIR = os.path.join(FOLDER, "clips")
INFO_FILE = os.path.join(CLIPS_DIR, "clips_info.txt")
DESCRIPTION_FILE = os.path.join(FOLDER, "mota.txt.txt")

def resolve_clips_dir(cli_arg: str = None) -> str:
    """Tìm thư mục clips thực tế: ưu tiên --clips-dir, rồi tournament/video subfolder, rồi root clips"""
    if cli_arg and os.path.isdir(cli_arg):
        return cli_arg
    # Kiểm tra root clips có file không
    if os.path.exists(CLIPS_DIR) and glob.glob(os.path.join(CLIPS_DIR, "*.mp4")):
        return CLIPS_DIR
    # Quét tournament 2 cấp: Sân 2/YYYY-MM-DD_*/clips (legacy) và Sân 2/YYYY-MM-DD_*/*/clips (mới)
    candidates = []
    for pat in [os.path.join(FOLDER, "20*_*", "clips"), os.path.join(FOLDER, "20*_*", "*", "clips")]:
        for entry in glob.glob(pat):
            if os.path.isdir(entry) and glob.glob(os.path.join(entry, "*.mp4")):
                candidates.append(entry)
    if candidates:
        return max(candidates, key=lambda p: os.path.getmtime(p) if os.path.exists(p) else 0)
    return CLIPS_DIR
# dùng thư mục tạm ASCII để tránh lock do đường dẫn Unicode
USER_DATA_DIR = os.path.join(os.environ.get("TEMP", "C:\\temp"), "yt_badv_profile")
LOG_FILE = os.path.join(FOLDER, "upload_log.txt")

PLAYLIST_ID = "PLQ8nt-b1N3JM"   # để trống ("") nếu không dùng
BASE_TITLE = ""                  # prefix thêm vào trước tiêu đề, để trống nếu không cần


def read_description(norm_title: str = "") -> str:
    base = ""
    if os.path.exists(DESCRIPTION_FILE):
        with open(DESCRIPTION_FILE, "r", encoding="utf-8") as f:
            base = f.read().strip()
    try:
        import seo_helper
        if norm_title:
            parts = [p.strip() for p in norm_title.split("|")]
            tname = parts[0] if parts else ""
            cfg = seo_helper.load_seo_config(tname)
            if cfg:
                hashtags = " ".join(cfg.get("hashtags", []))
                if hashtags and hashtags not in base:
                    base = base + "\n\n" + hashtags
                # Thêm intro ngắn cho clip lẻ (thay {match_count} = 1)
                intro = cfg.get("description_intro", "")
                if intro:
                    try:
                        intro_filled = intro.format(
                            match_count=1,
                            tournament_full=cfg.get("tournament_full", tname),
                            location=cfg.get("location", ""),
                            date=cfg.get("date", ""),
                            organizer=cfg.get("organizer", ""),
                            court=cfg.get("court", ""),
                            short_keyword=cfg.get("short_keyword", "")
                        )
                    except Exception:
                        intro_filled = intro.replace("{match_count}", "1")
                    # Lấy câu đầu làm intro clip
                    intro_clip = intro_filled.split(".")[0].strip() + "."
                    if intro_clip not in base and len(intro_clip) < 200:
                        base = intro_clip + "\n\n" + base
    except Exception:
        pass
    return base.strip()


def read_info():
    mapping = {}
    if not os.path.exists(INFO_FILE):
        return mapping
    with open(INFO_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.strip():
                continue
            if " | " not in line:
                continue
            fname, title = line.split(" | ", 1)
            mapping[fname.strip()] = title.strip()
    return mapping


def build_title(norm_title, sport: str = None):
    # Nếu có seo_config, thử sinh title chuẩn SEO từ norm_title (đã có category + players)
    try:
        import seo_helper
        # norm_title dạng: "GIẢI ... | Hạng mục | VĐV vs VĐV"
        parts = [p.strip() for p in norm_title.split("|")]
        if len(parts) >= 3:
            tname = parts[0]
            cat = parts[1]
            players = parts[2]
            cfg = seo_helper.load_seo_config(tname, sport=sport)
            seo_title = seo_helper.build_clip_title(cfg, cat, players, tname)
            if seo_title and len(seo_title) <= 100:
                return seo_title
    except Exception:
        pass
    return f"{BASE_TITLE} {norm_title}".strip() if BASE_TITLE else norm_title


async def handle_publish_flow(page, timeout: int = 35) -> bool:
    """
    Xử lý trọn vẹn quy trình Xuất bản:
    1. Bấm nút 'Xuất bản' (Publish).
    2. Theo dõi liên tục ngay lập tức:
       - Nếu xuất hiện hộp thoại 'Chúng tôi vẫn đang kiểm tra...' -> Tự động bấm 'Vẫn xuất bản' ngay.
       - Nếu xuất hiện hộp thoại thành công -> Bấm 'Đóng' / 'Close'.
    """
    print("  [>] Đang bấm nút 'Xuất bản'...")

    # 1. Bấm nút Xuất bản chính
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

    # 2. Vòng lặp giám sát hộp thoại xác nhận "Vẫn xuất bản" và hộp thoại "Đóng"
    start_time = time.time()
    still_publish_clicked = False

    while time.time() - start_time < timeout:
        # A. Kiểm tra nút "Vẫn xuất bản" / "Publish anyway"
        if not still_publish_clicked:
            # 1. Dùng get_by_role (xuyên qua Shadow DOM và ARIA labels)
            try:
                btn_still = page.get_by_role("button", name=re.compile(r"Vẫn\s*xuất\s*bản|Publish\s*anyway|Still\s*publish", re.I))
                if await btn_still.count() > 0 and await btn_still.first.is_visible(timeout=500):
                    await btn_still.first.click(timeout=3000)
                    still_publish_clicked = True
                    print("  [🔥] ĐÃ TỰ ĐỘNG BẤM 'VẪN XUẤT BẢN'!")
                    await asyncio.sleep(1)
            except Exception:
                pass

            # 2. Dùng CSS selector
            if not still_publish_clicked:
                try:
                    btn_css = page.locator('ytcp-confirmation-dialog ytcp-button, ytcp-uploads-still-processing-dialog ytcp-button, tp-yt-paper-dialog ytcp-button, [role="dialog"] ytcp-button').filter(has_text=re.compile(r"Vẫn\s*xuất\s*bản|Publish\s*anyway|Vẫn", re.I))
                    if await btn_css.count() > 0 and await btn_css.first.is_visible(timeout=500):
                        await btn_css.first.click(timeout=3000)
                        still_publish_clicked = True
                        print("  [🔥] ĐÃ TỰ ĐỘNG BẤM 'VẪN XUẤT BẢN' (CSS)!")
                        await asyncio.sleep(1)
                except Exception:
                    pass

            # 3. Dùng Shadow DOM traversal JS
            if not still_publish_clicked:
                try:
                    clicked_js = await page.evaluate("""() => {
                        function queryAll(root) {
                            let nodes = Array.from(root.querySelectorAll('*'));
                            let all = [...nodes];
                            for (let n of nodes) {
                                if (n.shadowRoot) {
                                    all = all.concat(queryAll(n.shadowRoot));
                                }
                            }
                            return all;
                        }
                        const allEls = queryAll(document);
                        for (let el of allEls) {
                            if (el.tagName && (el.tagName.toLowerCase() === 'ytcp-button' || el.tagName.toLowerCase() === 'button' || el.getAttribute('role') === 'button')) {
                                const text = (el.textContent || '').trim().toLowerCase();
                                if (text.includes('vẫn xuất bản') || text.includes('publish anyway') || (text.includes('vẫn') && text.includes('bản'))) {
                                    if (el.offsetParent !== null || el.clientHeight > 0) {
                                        el.click();
                                        return true;
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

        # B. Kiểm tra nút "Đóng" / "Close" / "Xong" khi hoàn tất
        try:
            btn_close = page.get_by_role("button", name=re.compile(r"^(Đóng|Close|Xong)$", re.I))
            if await btn_close.count() > 0 and await btn_close.first.is_visible(timeout=500):
                await btn_close.first.click(timeout=3000)
                print("  [+] Đã bấm 'Đóng' hộp thoại hoàn tất")
                await asyncio.sleep(1)
                break
        except Exception:
            pass

        # C. Kiểm tra nếu dialog upload đã đóng hoàn toàn
        try:
            upload_dialog = page.locator('ytcp-uploads-dialog')
            if await upload_dialog.count() == 0 or not await upload_dialog.first.is_visible(timeout=300):
                if still_publish_clicked or time.time() - start_time > 8:
                    print("  [+] Hộp thoại upload đã đóng thành công")
                    break
        except Exception:
            pass

        await asyncio.sleep(0.8)

    return True


async def main():
    dry_run = "--dry-run" in sys.argv
    # Hỗ trợ tournament folder: --clips-dir / --dir
    clips_dir_arg = None
    for _i, _a in enumerate(sys.argv):
        if _a in ("--clips-dir", "--dir", "--clips") and _i + 1 < len(sys.argv):
            clips_dir_arg = sys.argv[_i + 1]
    global CLIPS_DIR, INFO_FILE
    CLIPS_DIR = resolve_clips_dir(clips_dir_arg)
    INFO_FILE = os.path.join(CLIPS_DIR, "clips_info.txt")
    print(f"[*] Clips dir: {CLIPS_DIR}")
    mapping = read_info()
    print(f"Loaded {len(mapping)} clip titles")

    if not os.path.isdir(CLIPS_DIR):
        print(f"[!] Không tìm thấy thư mục clips: {CLIPS_DIR}")
        return
    video_files = sorted([f for f in os.listdir(CLIPS_DIR) if f.endswith(".mp4")])
    video_files = [f for f in video_files if f in mapping]
    # Fallback: nếu không có mapping, vẫn upload tất cả mp4 trong clips
    if not video_files:
        video_files = sorted([f for f in os.listdir(CLIPS_DIR) if f.endswith(".mp4")])
        print(f"[!] Không có mapping, fallback upload tất cả {len(video_files)} file trong clips")
    print(f"Found {len(video_files)} videos to upload\n")

    if dry_run:
        print("=== DRY-RUN (không đăng) - SEO Preview ===")
        for f in video_files:
            t = build_title(mapping[f])
            d = read_description(mapping[f])
            print(f"  {f}\n    Title ({len(t)} chars): {t}\n    Desc preview: {d[:120]}...")
        return

    start = 0
    for _i, _a in enumerate(sys.argv):
        if _a == "--start" and _i + 1 < len(sys.argv):
            try:
                start = int(sys.argv[_i + 1])
            except ValueError:
                pass
    if start:
        print(f"Bat dau tu clip thu {start + 1} (bo qua {start} clip dau)")

    log_lines = [f"=== UPLOAD LOG === {time.strftime('%Y-%m-%d %H:%M')}"]

    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    async with async_playwright() as p:
        async def wait_for_login(page, timeout=600):
            deadline = time.time() + timeout
            while time.time() < deadline:
                try:
                    url = page.url
                except Exception:
                    url = ""
                if "accounts.google" not in url:
                    try:
                        if await page.locator('button:has-text("Chọn tệp")').count() > 0:
                            return True
                    except Exception:
                        pass
                    return True
                await asyncio.sleep(5)
            return False

        async def new_context_and_gate():
            return await p.chromium.launch_persistent_context(
                USER_DATA_DIR,
                headless=False,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--no-first-run",
                    "--no-default-browser-check",
                ],
                viewport={"width": 1280, "height": 900},
                user_agent=user_agent,
            )

        context = await new_context_and_gate()
        # Cổng đăng nhập thủ công (lần đầu, hoặc khi phiên hết hạn)
        gate = await context.new_page()
        await gate.goto("https://www.youtube.com/upload", wait_until="domcontentloaded", timeout=90000)
        await asyncio.sleep(6)
        if "accounts.google" in gate.url:
            print(">>> VUI LONG DANG NHAP YOUTUBE TRONG CUA SO BROWSER (co the can 2FA).")
            print("    Script se tu dong tiep tuc ngay khi phat hien da dang nhap (cho toi 10 phut).")
            ok = await wait_for_login(gate, timeout=600)
            if not ok:
                print(">>> HET THOI GIAN DANG NHAP. Thu lai hoac Ctrl+C.")
        await gate.close()

        # Tạo 1 trang duy nhất, tái sử dụng cho mọi clip (tránh lỗi context đóng)
        page = await context.new_page()
        page.on("dialog", lambda d: asyncio.ensure_future(d.dismiss()))

        success = 0
        for i, filename in enumerate(video_files):
            if i < start:
                print(f"(bo qua {i+1}/{len(video_files)}: {filename})")
                continue
            video_path = os.path.join(CLIPS_DIR, filename)
            full_title = build_title(mapping[filename])
            print(f"\n>>> [{i+1}/{len(video_files)}] {filename}\n    TITLE: {full_title}")
            log_lines.append(f"\n--- {filename} ---\nTITLE: {full_title}")

            try:
                await page.goto("https://www.youtube.com/upload", wait_until="domcontentloaded", timeout=90000)
                await asyncio.sleep(8)
            except Exception as e:
                print(f"  goto loi ({e}) - thu tao lai context")
                try:
                    await context.close()
                except Exception:
                    pass
                context = await new_context_and_gate()
                page = await context.new_page()
                page.on("dialog", lambda d: asyncio.ensure_future(d.dismiss()))
                await page.goto("https://www.youtube.com/upload", wait_until="domcontentloaded", timeout=90000)
                await asyncio.sleep(8)

            if "accounts.google" in page.url:
                print("  NOT LOGGED IN - yeu cau dang nhap lai trong cua so browser")
                await wait_for_login(page, timeout=600)
                await page.reload(wait_until="domcontentloaded"); await asyncio.sleep(6)
                if "accounts.google" in page.url:
                    print("  VAN CHUA DANG NHAP"); log_lines.append("  NOT LOGGED IN")
                    continue

            try:

                print("  Chọn tệp...")
                btn = page.locator('button:has-text("Chọn tệp")')
                await btn.first.wait_for(state="visible", timeout=30000)
                async with page.expect_file_chooser(timeout=15000) as fc_info:
                    await btn.first.click()
                fc = await fc_info.value
                await fc.set_files(video_path)
                print("  File selected")
                await asyncio.sleep(10)

                # === FIX: Chờ upload 100% thực sự (áp dụng cho cả clip nhỏ và video lớn) ===
                upload_done = False
                upload_deadline = time.time() + 3600  # tối đa 60 phút
                clean_streak = 0
                last_percent = ""
                while time.time() < upload_deadline:
                    try:
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
                        txt = (shadow_text or "") + " " + ((await page.locator("body").inner_text(timeout=2000)) or "")
                        m = re.search(r"(\d{1,3})\s*%", txt)
                        cur_percent = m.group(1) + "%" if m else ""
                        if cur_percent and cur_percent != last_percent:
                            print(f"  [..] Đang tải lên: {cur_percent} - KHÔNG đóng trình duyệt...")
                            last_percent = cur_percent
                        is_uploading = (
                            "Đang tải lên" in txt or "Đang xử lý" in txt
                            or "uploading" in txt.lower() or "processing" in txt.lower()
                            or ("%" in txt and re.search(r"\d+\s*%", txt))
                        )
                        try:
                            next_enabled = await page.locator("#next-button").is_enabled(timeout=1500)
                        except Exception:
                            next_enabled = False
                        if not is_uploading and next_enabled:
                            clean_streak += 1
                            if clean_streak >= 4:
                                upload_done = True
                                break
                        else:
                            clean_streak = 0
                    except Exception:
                        clean_streak = 0
                    await asyncio.sleep(5)
                if upload_done:
                    print("  Upload hoàn tất (đã ổn định)")
                else:
                    print("  [!] Hết thời gian chờ upload - vẫn thử tiếp (sẽ KHÔNG đóng trình duyệt sớm)")

                try:
                    ce = page.locator('[contenteditable="true"]').first
                    await ce.wait_for(state="visible", timeout=10000)
                    await ce.click()
                    await page.keyboard.press("Control+a"); await asyncio.sleep(0.3)
                    await ce.fill(""); await asyncio.sleep(0.2)
                    await ce.type(full_title, delay=10)
                    print("  Title set"); await asyncio.sleep(1)
                except Exception as e:
                    print(f"  Title error: {e}")

                try:
                    # Mô tả động theo từng clip (SEO hashtag riêng)
                    description = read_description(mapping[filename])
                    de = page.locator('[contenteditable="true"]').nth(1)
                    await de.click(); await asyncio.sleep(0.5)
                    await de.fill(description)
                    print("  Description set (SEO)"); await asyncio.sleep(1)
                except Exception as e:
                    print(f"  Description error: {e}")

                try:
                    await page.locator('tp-yt-paper-radio-button[name="VIDEO_MADE_FOR_KIDS_NOT_MFK"]').first.click(timeout=5000)
                    print("  Audience: Not for kids"); await asyncio.sleep(1)
                except Exception as e:
                    print(f"  Audience error: {e}")

                for step in ["Video elements", "Checks", "Visibility"]:
                    await asyncio.sleep(3)
                    try:
                        await page.locator('#next-button').first.click(timeout=8000)
                        print(f"  Next: {step}")
                    except Exception as e:
                        print(f"  Next error ({step}): {e}")
                    await asyncio.sleep(3)

                try:
                    await page.locator('tp-yt-paper-radio-button[name="PUBLIC"]').first.click(timeout=5000)
                    print("  Visibility: Public"); await asyncio.sleep(2)
                except Exception:
                    print("  Visibility: failed")

                await asyncio.sleep(2)
                published_ok = await handle_publish_flow(page, timeout=35)
                if published_ok:
                    print("  PUBLISHED & CONFIRMED!")
                    success += 1
                    log_lines.append("  SUCCESS")
                else:
                    print("  PUBLISH FAILED")
                    log_lines.append("  PUBLISH FAILED")

                # Xóa file clip đã upload thành công
                if published_ok:
                    try:
                        os.remove(video_path)
                        print(f"  Đã xóa file: {filename}")
                        log_lines.append(f"  DELETED: {filename}")
                    except Exception as e:
                        print(f"  Xóa file lỗi: {e}")
            except Exception as e:
                print(f"  ERROR: {e}"); log_lines.append(f"  ERROR: {e}")
                try:
                    await page.goto("https://www.youtube.com/upload", wait_until="domcontentloaded", timeout=90000)
                    await asyncio.sleep(3)
                except Exception:
                    pass

            with open(LOG_FILE, "w", encoding="utf-8") as f:
                f.write("\n".join(log_lines))

            if i < len(video_files) - 1:
                print("  Chờ 5s..."); await asyncio.sleep(5)

        print(f"\n=== DONE: {success}/{len(video_files)} uploaded ===")
        log_lines.append(f"\nSUMMARY: {success}/{len(video_files)} uploaded")
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(log_lines))
        print("\nĐóng browser...")
        try:
            await page.close()
        except Exception:
            pass
        try:
            await context.close()
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(main())
