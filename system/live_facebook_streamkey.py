#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
live_facebook_streamkey.py
Tự động mở Facebook Live Producer qua Playwright (Headful), tạo sự kiện Live với tiêu đề & mô tả SEO,
trích xuất Stream Key & RTMP Server URL.
"""

import os
import sys
import time
import json
import asyncio
import argparse
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "system"))

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("[!] Chưa cài Playwright. Vui lòng chạy: pip install playwright && playwright install chromium")
    sys.exit(1)

# Import helpers
try:
    import seo_helper
except ImportError:
    seo_helper = None

try:
    import gemini_rotator
except ImportError:
    gemini_rotator = None

DEFAULT_PAGE_URL = os.environ.get("FACEBOOK_PAGE_URL", "https://www.facebook.com/dalisportss")

def resolve_browser_data_dir() -> str:
    """Xác định thư mục profile trình duyệt."""
    candidates = [
        str(PROJECT_ROOT / "browser_data"),
        os.path.join(os.environ.get("TEMP", "C:\\temp"), "fb_badv_profile"),
        str(PROJECT_ROOT / "browser_profile")
    ]
    for c in candidates:
        if os.path.exists(c) and os.listdir(c):
            return c
    return candidates[0]

def clean_stale_chromium_instances(user_data_dir: str):
    """Đóng các tiến trình Chromium cũ bị treo đang giữ khóa thư mục profile."""
    try:
        import psutil
        norm_dir = os.path.abspath(user_data_dir).lower()
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                name = proc.info.get('name') or ""
                if 'chrome' in name.lower():
                    cmdline = " ".join(proc.cmdline()).lower()
                    if 'ms-playwright' in cmdline or norm_dir in cmdline:
                        print(f"[*] Giải phóng tiến trình Chromium nền (PID {proc.pid})...")
                        proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        time.sleep(1)
    except Exception:
        pass

    # Xóa lockfile nếu còn tồn tại
    lock_file = os.path.join(user_data_dir, "lockfile")
    if os.path.exists(lock_file):
        try:
            os.remove(lock_file)
        except Exception:
            pass

def generate_live_seo(tournament_info: dict) -> tuple[str, str]:
    """Sinh tiêu đề và mô tả tối ưu SEO cho buổi phát trực tiếp."""
    t_name = tournament_info.get("name", "Giải Thể Thao").strip()
    sport = (tournament_info.get("sportType") or tournament_info.get("sport") or "badminton").lower()
    desc = tournament_info.get("description", "").strip()
    court = tournament_info.get("court", "Sân thi đấu chính").strip()
    sponsor = tournament_info.get("sponsor", "").strip()

    sport_names = {
        "badminton": "Cầu Lông",
        "pickleball": "Pickleball",
        "tennis": "Tennis"
    }
    sport_vn = sport_names.get(sport, "Thể Thao")

    # 1. Thử dùng Gemini AI nếu có API Key
    if gemini_rotator:
        prompt = f"""Hãy viết 1 Tiêu đề (dưới 80 ký tự) và 1 Mô tả Facebook Live (khoảng 150-250 từ) cho buổi phát trực tiếp thể thao với các thông tin sau:
- Giải đấu: {t_name}
- Bộ môn: {sport_vn}
- Sân thi đấu: {court}
- Mô tả / Thông tin chi tiết: {desc}
- Nhà tài trợ: {sponsor}

Yêu cầu:
1. Tiêu đề: Giật tít, hấp dẫn, có chữ [TRỰC TIẾP], chứa từ khóa chính về giải và bộ môn.
2. Mô tả: Đầy đủ thông tin, hào hứng, kêu gọi xem và chia sẻ, có các hashtag liên quan: #DaliSports #{sport} #livestream #{sport_vn.replace(' ', '')}.
3. Trả về đúng định dạng JSON:
{{"title": "...", "description": "..."}}
Không thêm bất kỳ text nào ngoài JSON.
"""
        try:
            print("[*] Đang dùng Gemini AI tối ưu hóa Tiêu đề & Mô tả Live theo chuẩn SEO...")
            rotator = gemini_rotator.GeminiRotator()
            ai_res = rotator.call_gemini_json(prompt)
            if isinstance(ai_res, dict) and ai_res.get("title") and ai_res.get("description"):
                title = ai_res["title"].strip()
                description = ai_res["description"].strip()
                print(f"[✓] AI SEO Title: {title}")
                return title, description
        except Exception as e:
            print(f"[!] AI generation failed ({e}), chuyển sang template chuẩn.")

    # 2. Fallback Template chuẩn tối ưu SEO
    title = f"[TRỰC TIẾP] {t_name} - Tranh Tài Đỉnh Cao | {sport_vn} DaliSports"
    if len(title) > 95:
        title = f"[TRỰC TIẾP] {t_name} | {sport_vn} DaliSports"

    sponsor_line = f"\n- Đơn vị đồng hành & tài trợ: {sponsor}" if sponsor else ""
    description = f"""🔥 [TRỰC TIẾP] {t_name.upper()} 🔥
🏸 Bộ môn: {sport_vn}
📍 Địa điểm/Sân: {court}{sponsor_line}

{desc if desc else 'Đón xem những pha cầu kịch tính, những pha bóng mãn nhãn và các màn so tài nảy lửa tại giải đấu hôm nay!'}

👉 Hãy bấm Theo dõi và Chia sẻ livestream để cổ vũ cho các vận động viên nhé!
----------------------------------
DaliSports - Đơn vị truyền thông & phát sóng thể thao chuyên nghiệp.
#DaliSports #{sport} #{sport_vn.replace(' ', '')} #livestream #giaidau #tructiep
""".strip()

    return title, description

async def run_facebook_live_automation(
    page_url: str,
    title: str,
    description: str,
    user_data_dir: str
) -> dict:
    """Tự động điều hướng Facebook Live Producer, điền SEO và lấy Stream Key."""
    result = {
        "success": False,
        "streamKey": "",
        "serverUrl": "rtmps://live-api-s.facebook.com:443/rtmp/",
        "title": title,
        "description": description
    }

    # Chuẩn hóa Live Producer URL
    # Lưu ý: Facebook đã khai tử định dạng cũ '/<pagename>/live_producer' (gây lỗi 404 Not Found).
    # Đường dẫn chuẩn quốc tế của Facebook Live Producer là https://www.facebook.com/live/producer/
    live_url = "https://www.facebook.com/live/producer/"

    print(f"[*] Khởi chạy Playwright Chromium (Headful)...")
    print(f"[*] Profile: {user_data_dir}")
    print(f"[*] URL: {live_url}")

    clean_stale_chromium_instances(user_data_dir)
    playwright = await async_playwright().start()
    browser_context = await playwright.chromium.launch_persistent_context(
        user_data_dir=user_data_dir,
        headless=False,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--start-maximized"
        ],
        permissions=["clipboard-read", "clipboard-write"],
        viewport=None
    )

    page = browser_context.pages[0] if browser_context.pages else await browser_context.new_page()

    try:
        # BƯỚC 1: TRUY CẬP VÀO FANPAGE ĐỂ CHUYỂN SANG PROFILE PAGE
        clean_page_url = page_url.rstrip("/")
        if not clean_page_url.startswith("http"):
            clean_page_url = f"https://www.facebook.com/{clean_page_url}"

        print(f"[*] BƯỚC 1: Đang truy cập Fanpage: {clean_page_url}...")
        await page.goto(clean_page_url, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(4)
        print(f"[*] Đang ở URL: {page.url}")
        print(f"[*] Tiêu đề trang: {await page.title()}")
        try:
            await page.screenshot(path=str(PROJECT_ROOT / "fb_step1_page.png"))
        except Exception:
            pass

        # Kiểm tra nếu bị chuyển hướng trang đăng nhập hoặc màn hình yêu cầu đăng nhập
        if "login" in page.url.lower() or await page.locator('input[name="email"]').count() > 0:
            print("\n[!] CHÚ Ý: Trình duyệt chưa đăng nhập Facebook!")
            print("    👉 Vui lòng nhìn màn hình Chrome đang mở, đăng nhập tài khoản Facebook có quyền quản lý Page Dali Sports...")
            for i in range(90):
                await asyncio.sleep(2)
                if "login" not in page.url.lower() and await page.locator('input[name="email"]').count() == 0:
                    print("[✓] Đã nhận diện đăng nhập thành công!")
                    await asyncio.sleep(3)
                    break
            else:
                print("[!] Hết thời gian chờ đăng nhập (3 phút). Tiếp tục tiến trình...")

        # Nếu Facebook yêu cầu "Chuyển sang Trang" -> bấm "Chuyển ngay" / "Switch now"
        for label in [
            "Chuyển ngay", "Switch now", "Chuyển sang Trang", "Chuyển sang Dali Sports",
            "Switch to Dali Sports", "Chuyển", "Switch"
        ]:
            try:
                sw = page.get_by_role("button", name=label).first
                if await sw.count() == 0:
                    sw = page.get_by_text(label, exact=False).first
                if await sw.count() > 0 and await sw.is_visible(timeout=1500):
                    print(f"[*] Đang chuyển sang quyền Page (bấm '{label}')...")
                    await sw.click()
                    await asyncio.sleep(5)
                    break
            except Exception:
                pass

        # Thử tìm nút "Video trực tiếp" / "Live video" trực tiếp trên giao diện Page
        live_btn_clicked = False
        live_page_selectors = [
            'div[role="button"]:has-text("Video trực tiếp")',
            'button:has-text("Video trực tiếp")',
            'span:has-text("Video trực tiếp")',
            'div[role="button"]:has-text("Live video")',
            'button:has-text("Live video")',
            'span:has-text("Live video")',
            'div[role="button"]:has-text("Phát trực tiếp")',
            'span:has-text("Phát trực tiếp")',
            'a[href*="/live/producer"]'
        ]
        for sel in live_page_selectors:
            try:
                btn = page.locator(sel).first
                if await btn.count() > 0 and await btn.is_visible(timeout=2000):
                    print(f"[*] Đã tìm thấy nút tạo Live trên giao diện Page, đang click...")
                    await btn.click()
                    await asyncio.sleep(4)
                    live_btn_clicked = True
                    break
            except Exception:
                pass

        # Nếu mở tab mới, trỏ vào tab mới nhất
        if len(browser_context.pages) > 1:
            page = browser_context.pages[-1]
            await page.bring_to_front()
            await asyncio.sleep(2)

        # BƯỚC 2: NẾU CHƯA Ở TRANG LIVE PRODUCER, MỞ THẲNG LINK CHUẨN META LIVE PRODUCER
        if "live/producer" not in page.url.lower():
            print("[*] BƯỚC 2: Điều hướng tới phòng điều khiển Live Producer...")
            await page.goto("https://www.facebook.com/live/producer/", wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(4)

        print(f"[*] Đang ở URL Live: {page.url}")
        try:
            await page.screenshot(path=str(PROJECT_ROOT / "fb_step2_live.png"))
        except Exception:
            pass

        # 1. Chọn "Thiết lập video trực tiếp" / "Phát trực tiếp" / "Go live" nếu có màn hình chọn
        go_live_selectors = [
            'span:has-text("Thiết lập video trực tiếp")',
            'div[role="button"]:has-text("Thiết lập video trực tiếp")',
            'button:has-text("Thiết lập video trực tiếp")',
            'text="Thiết lập video trực tiếp"',
            'span:has-text("Set up live video")',
            'div[role="button"]:has-text("Set up live video")',
            'div[role="button"]:has-text("Phát trực tiếp")',
            'div[role="button"]:has-text("Go live")',
            'button:has-text("Phát trực tiếp")',
            'button:has-text("Go live")',
            'div[role="radio"]:has-text("Phát trực tiếp ngay")',
            'div:has-text("Phát trực tiếp ngay")'
        ]
        for sel in go_live_selectors:
            try:
                el = page.locator(sel).first
                if await el.is_visible(timeout=2500):
                    print(f"[*] Đang bấm: '{sel}'...")
                    await el.click()
                    print("[✓] Đã chọn 'Thiết lập video trực tiếp'!")
                    break
            except Exception:
                pass

        # Đợi phòng điều khiển Live Studio tải xong hoàn toàn (hết skeleton placeholders)
        print("[*] Đang chờ phòng điều khiển Live Producer Studio tải xong...")
        for _ in range(25):
            await asyncio.sleep(1)
            has_details = await page.locator('text="Chi tiết bài viết"').count() > 0
            has_key = await page.locator('input[type="password"]').count() > 0
            has_btn = await page.locator('div[role="button"]:has-text("Chỉnh sửa")').count() > 0
            if has_details or has_key or has_btn:
                print("[✓] Phòng điều khiển Live Producer Studio đã tải xong!")
                await asyncio.sleep(2)
                break

        try:
            await page.screenshot(path=str(PROJECT_ROOT / "fb_step3_studio.png"))
        except Exception:
            pass

        # 1b. Chọn nơi đăng: Đảm bảo phát trên Trang (Page) thay vì Dòng thời gian cá nhân
        post_target_selectors = [
            'div[role="combobox"]:has-text("Dòng thời gian")',
            'div[role="combobox"]:has-text("Timeline")',
            'div[role="button"]:has-text("Chọn nơi đăng")',
            'div[role="button"]:has-text("Đăng lên Trang")'
        ]
        for sel in post_target_selectors:
            try:
                el = page.locator(sel).first
                if await el.is_visible(timeout=1500):
                    await el.click()
                    await asyncio.sleep(1)
                    # Chọn trang Dali Sports nếu có trong menu
                    for target_name in ["Dali Sports", "dalisportss", "Trang bạn quản lý"]:
                        dali_opt = page.locator(f'text="{target_name}"').first
                        if await dali_opt.is_visible(timeout=1500):
                            await dali_opt.click()
                            print(f"[*] Đã chọn đích phát sóng: '{target_name}'...")
                            await asyncio.sleep(1)
                            break
                    break
            except Exception:
                pass

        # 2. Chọn nguồn phát: "Phần mềm phát trực tiếp" (Streaming software)
        software_selectors = [
            'text="Phần mềm phát trực tiếp"',
            'text="Streaming software"',
            'input[value="STREAMING_SOFTWARE"]',
            'div[role="radio"]:has-text("Phần mềm")'
        ]
        for sel in software_selectors:
            try:
                el = page.locator(sel).first
                if await el.is_visible(timeout=2000):
                    await el.click()
                    print("[*] Đã chọn 'Phần mềm phát trực tiếp'...")
                    await asyncio.sleep(1)
                    break
            except Exception:
                pass

        # 3. Bấm "Chỉnh sửa chi tiết bài viết" để điền Tiêu đề & Mô tả SEO
        print("[*] Đang mở 'Chỉnh sửa chi tiết bài viết' trên Facebook...")
        edit_detail_selectors = [
            'div[role="button"]:has-text("Chỉnh sửa chi tiết bài viết")',
            'button:has-text("Chỉnh sửa chi tiết bài viết")',
            'span:has-text("Chỉnh sửa chi tiết bài viết")',
            'div[role="button"]:has-text("Chi tiết bài viết")',
            'div[role="button"]:has-text("Chỉnh sửa")',
            'button:has-text("Chỉnh sửa")',
            'span:has-text("Chỉnh sửa")',
            'div[role="button"]:has-text("Thêm chi tiết bài viết")',
            'button:has-text("Thêm chi tiết bài viết")',
            'span:has-text("Thêm chi tiết bài viết")',
            'div[aria-label*="Chỉnh sửa" i]',
            'div[role="button"]:has-text("Edit post details")',
            'button:has-text("Edit post details")',
            'span:has-text("Edit post details")',
            'div[role="button"]:has-text("Edit details")',
            'div[role="button"]:has-text("Edit")'
        ]
        
        edit_clicked = False
        for sel in edit_detail_selectors:
            try:
                btns = page.locator(sel)
                count = await btns.count()
                for idx in range(count):
                    b = btns.nth(idx)
                    if await b.is_visible(timeout=1500):
                        print(f"[*] Đã bấm nút: '{sel}'...")
                        await b.click()
                        await asyncio.sleep(2)
                        edit_clicked = True
                        break
                if edit_clicked:
                    break
            except Exception:
                pass

        # Điền Tiêu đề
        print("[*] Đang điền Tiêu đề SEO...")
        title_selectors = [
            'div[role="dialog"] input[type="text"]',
            'div[role="dialog"] input',
            'input[aria-label*="tiêu đề" i]',
            'input[aria-label*="title" i]',
            'input[placeholder*="tiêu đề" i]',
            'input[placeholder*="title" i]',
            'input[name="title"]',
            'input[type="text"]'
        ]
        for sel in title_selectors:
            try:
                el = page.locator(sel).first
                if await el.count() > 0 and await el.is_visible(timeout=1500):
                    await el.click(timeout=1500)
                    await el.fill("")
                    await el.fill(title)
                    print(f"[✓] Đã điền Tiêu đề: {title[:45]}...")
                    break
            except Exception:
                pass

        # Điền Mô tả
        print("[*] Đang điền Mô tả SEO...")
        desc_selectors = [
            'div[role="dialog"] div[role="textbox"]',
            'div[role="dialog"] textarea',
            'div[aria-label*="mô tả" i]',
            'div[aria-label*="description" i]',
            'div[aria-label*="nói gì đó" i]',
            'div[role="textbox"]',
            'textarea[placeholder*="mô tả" i]',
            'textarea'
        ]
        for sel in desc_selectors:
            try:
                el = page.locator(sel).first
                if await el.count() > 0 and await el.is_visible(timeout=1500):
                    await el.click(timeout=1500)
                    await el.fill("")
                    await el.fill(description)
                    print("[✓] Đã điền Mô tả SEO!")
                    break
            except Exception:
                pass

        await asyncio.sleep(1)

        # Bấm nút "Lưu" / "Save" để lưu chi tiết bài viết
        save_selectors = [
            'div[role="dialog"] div[role="button"]:has-text("Lưu")',
            'div[role="dialog"] button:has-text("Lưu")',
            'div[role="dialog"] div[role="button"]:has-text("Save")',
            'div[role="dialog"] button:has-text("Save")',
            'div[role="button"]:has-text("Lưu")',
            'button:has-text("Lưu")',
            'div[role="button"]:has-text("Save")',
            'button:has-text("Save")',
            'div[aria-label*="Lưu" i]',
            'div[role="button"]:has-text("Xong")',
            'button:has-text("Xong")'
        ]
        for sel in save_selectors:
            try:
                el = page.locator(sel).first
                if await el.count() > 0 and await el.is_visible(timeout=1500):
                    print(f"[*] Đang bấm '{sel}' để lưu chi tiết bài viết...")
                    await el.click(timeout=2500)
                    print("[✓] Đã lưu chi tiết bài viết Facebook thành công!")
                    await asyncio.sleep(2)
                    break
            except Exception:
                pass

        # 4. Trích xuất Stream Key & URL
        print("[*] Đang tìm kiếm Khóa luồng (Stream Key)...")
        # Tìm input chứa Stream Key (hoặc nút sao chép)
        key_input_selectors = [
            'input[type="password"]',
            'input[value*="FB-"]',
            'input[value*="live"]',
            'input[aria-label*="khóa luồng" i]',
            'input[aria-label*="stream key" i]'
        ]

        found_key = ""
        for sel in key_input_selectors:
            try:
                inputs = page.locator(sel)
                count = await inputs.count()
                for i in range(count):
                    val = await inputs.nth(i).input_value()
                    if val and len(val) > 10:
                        found_key = val
                        break
                if found_key:
                    break
            except Exception:
                pass

        # Nếu không đọc được từ input, thử click nút Copy Stream Key
        if not found_key:
            copy_btn_selectors = [
                'div[aria-label*="Sao chép khóa luồng" i]',
                'button:has-text("Sao chép")',
                'div[role="button"]:has-text("Sao chép")',
                'button:has-text("Copy")'
            ]
            for sel in copy_btn_selectors:
                try:
                    btns = page.locator(sel)
                    if await btns.first.is_visible(timeout=2000):
                        await btns.first.click()
                        await asyncio.sleep(1)
                        # Đọc từ clipboard qua evaluate
                        clip_text = await page.evaluate("() => navigator.clipboard.readText()")
                        if clip_text and len(clip_text) > 10:
                            found_key = clip_text
                            break
                except Exception:
                    pass

        if found_key:
            result["streamKey"] = found_key
            result["success"] = True
            print(f"[✓] ĐÃ TÌM THẤY STREAM KEY: {found_key[:6]}******{found_key[-4:]}")
        else:
            print("[!] Chưa tự động lấy được Stream Key qua selector.")
            print("    Hệ thống đang mở sẵn trang Live Producer trên màn hình...")
            print("    👉 Bạn có thể copy thủ công Stream Key và dán vào bên dưới (hoặc Enter để tiếp tục):")
            # Tạo task chờ người dùng nhập stream key nếu cần
            # Trong môi trường automated, ta cũng chờ 1 khoảng thời gian
            result["streamKey"] = ""

        # Trả về kết quả, LƯU Ý: KHÔNG đóng browser_context để giữ tab Facebook Live mở!
        return {
            "result": result,
            "browser_context": browser_context,
            "playwright": playwright
        }

    except Exception as e:
        print(f"[!] Lỗi trong quá trình thao tác Facebook: {e}")
        return {
            "result": result,
            "browser_context": browser_context,
            "playwright": playwright
        }

def get_facebook_stream_info(tournament_path: str, page_url: str = DEFAULT_PAGE_URL) -> dict:
    """Wrapper đồng bộ để gọi từ CLI / Orchestrator."""
    t_path = Path(tournament_path).resolve()
    info_file = t_path / "dieu_hanh" / "tournament_info.json"
    if not info_file.exists():
        info_file = t_path / "tournament_info.json"

    t_info = {}
    if info_file.exists():
        try:
            with open(info_file, "r", encoding="utf-8") as f:
                t_info = json.load(f)
        except Exception:
            pass

    title, description = generate_live_seo(t_info)
    user_data_dir = resolve_browser_data_dir()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    res_obj = loop.run_until_complete(
        run_facebook_live_automation(page_url, title, description, user_data_dir)
    )
    return res_obj

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Facebook Live Producer Stream Key Automation")
    parser.add_argument("--tournament", "-t", type=str, default="", help="Đường dẫn thư mục giải đấu")
    parser.add_argument("--page", "-p", type=str, default=DEFAULT_PAGE_URL, help="URL Fanpage Facebook")
    args = parser.parse_args()

    t_dir = args.tournament or os.getcwd()
    out = get_facebook_stream_info(t_dir, args.page)
    res = out.get("result", {})
    print(f"\nKết quả:")
    print(f"Success: {res.get('success')}")
    print(f"Stream Key: {res.get('streamKey')}")
    print(f"Title: {res.get('title')}")
