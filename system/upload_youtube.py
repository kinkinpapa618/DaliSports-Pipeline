import asyncio
import os
import time
import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.async_api import async_playwright

VIDEO_DIR = r"C:\Users\dalis\Desktop\Video 2"
DESCRIPTION_FILE = r"C:\Users\dalis\Desktop\Video 2\mota.txt.txt"
PLAYLIST_ID = "PLQ8nt-b1N3JM"
COOKIE_FILE = r"C:\Users\dalis\Desktop\Video 2\cookies.txt"
LOG_FILE = os.path.join(VIDEO_DIR, "upload_log.txt")

BASE_TITLE = "GIẢI TÚ HÀ BADMINTON - 2026 | San 2 |"

TITLE_MAP = {
    "San2_tran_01_MinhNhat_VS_GiaBao.mp4": "Minh Nhat vs Gia Bao",
    "San2_tran_02_NguyenPhuongNam_VS_PhamGiaHuy.mp4": "Nguyen Phuong Nam vs Pham Gia Huy",
    "San2_tran_03_NguyenQuyDuong_VS_BuiDoanHoangMinh.mp4": "Nguyen Quy Duong vs Bui Doan Hoang Minh",
    "San2_tran_04_DinhTrongCuong_LeQuyBao_VS_NgoVuPhong_NguyenTienToan.mp4": "Dinh Trong Cuong, Le Quy Bao vs Ngo Vu Phong, Nguyen Tien Toan",
    "San2_tran_05_LuuVanDuy_TranThanhHung_VS_LeGiaHung_PhamDucAnh.mp4": "Luu Van Duy, Tran Thanh Hung vs Le Gia Hung, Pham Duc Anh",
    "San2_tran_06_BuiDucHieu_TranPhuongThao_VS_DaoNhatMinh_LeThanhHang.mp4": "Bui Duc Hieu, Phuong Thao vs Dao Nhat Minh, Le Thanh Hang",
    "San2_tran_07_NguyenDinhPhat_LaiPhuongAnh_VS_NguyenMinhQuan_PhamPhuongMinh.mp4": "Nguyen Dinh Phat, Lai Phuong Anh vs Nguyen Minh Quan, Pham Phuong Minh",
    "San2_tran_08_PhamDucAnh_TranPhuongThao_VS_NgoAnhDuc_NguyenKhanhLinh.mp4": "Pham Duc Anh, Phuong Thao vs Ngo Anh Duc, Nguyen Khanh Linh",
    "San2_tran_09_PhamTienDung_DoanhThanhBinh_VS_NguyenTatTuan_PhiDucTri.mp4": "Pham Tien Dung, Doanh Thanh Binh vs Nguyen Tat Tuan, Phi Duc Tri",
    "San2_tran_10_DinhTrongCuong_VS_VuMinhHieu.mp4": "Dinh Trong Cuong vs Vu Minh Hieu",
    "San2_tran_11_DoHuuTai_PhamManhHung_VS_BuiTien_NgocTuan.mp4": "Do Huu Tai, Pham Manh Hung vs Bui Tien, Ngoc Tuan",
    "San2_tran_12_PhamTienDung_VS_NguyenKhang.mp4": "Pham Tien Dung vs Nguyen Khang",
    "San2_tran_13_BuiAnhDuc_VS_NguyenQuocDung.mp4": "Bui Anh Duc vs Nguyen Quoc Dung",
    "San2_tran_14_NguyenDinhPhat_BinhMinh_VS_NgoVuPhong_NguyenTienToan.mp4": "Nguyen Dinh Phat, Binh Minh vs Ngo Vu Phong, Nguyen Tien Toan",
}


def parse_netscape_cookies(cookie_file):
    cookies = []
    with open(cookie_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) < 7:
                continue
            domain, _, path, secure, expires, name, value = parts[:7]
            cookie = {"name": name, "value": value, "domain": domain, "path": path, "secure": secure.upper() == "TRUE", "httpOnly": False}
            if expires and expires != "0":
                cookie["expires"] = int(expires)
            cookies.append(cookie)
    return cookies


def read_description():
    with open(DESCRIPTION_FILE, "r", encoding="utf-8") as f:
        return f.read().strip()


async def click_publish(page):
    for sel in ['#publish-button', 'ytcp-button#publish-button', 'publish-button']:
        try:
            btn = page.locator(sel)
            if await btn.count() > 0 and await btn.first.is_visible(timeout=2000):
                await btn.first.click(timeout=5000)
                return True
        except:
            pass
    try:
        clicked = await page.evaluate("""() => {
            const buttons = document.querySelectorAll('ytcp-button, button');
            for (const b of buttons) {
                const text = b.textContent.trim().toLowerCase();
                if (text.includes('xuất bản') || text.includes('publish')) {
                    b.click();
                    return true;
                }
            }
            return false;
        }""")
        if clicked:
            return True
    except:
        pass
    try:
        buttons = await page.evaluate("""() => {
            const r = [];
            document.querySelectorAll('ytcp-button, button').forEach(b => {
                if (b.offsetParent !== null)
                    r.push({tag: b.tagName, id: b.id, text: b.textContent.trim().substring(0,50)});
            });
            return r;
        }""")
        for b in buttons:
            print(f"    BTN: {b['tag']}#{b['id']} '{b['text']}'")
    except:
        pass
    return False


async def main():
    description = read_description()
    cookies = parse_netscape_cookies(COOKIE_FILE)
    print(f"Loaded {len(cookies)} cookies")

    video_files = sorted([
        f for f in os.listdir(VIDEO_DIR)
        if f.startswith("San2_tran_") and f.endswith(".mp4")
    ])
    print(f"Found {len(video_files)} videos\n")

    log_lines = [f"=== UPLOAD LOG === {time.strftime('%Y-%m-%d %H:%M')}"]
    all_contexts = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )

        success_count = 0
        for i, filename in enumerate(video_files):
            video_path = os.path.join(VIDEO_DIR, filename)
            title_match = TITLE_MAP.get(filename, filename)
            full_title = f"{BASE_TITLE} {title_match}"

            print(f"\n>>> [{i+1}/{len(video_files)}] {filename}")
            log_lines.append(f"\n--- {filename} ---")

            # NEW context = NEW window per video
            context = await browser.new_context(
                viewport={"width": 1280, "height": 900},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            )
            await context.add_cookies(cookies)
            page = await context.new_page()
            page.on("dialog", lambda dialog: asyncio.ensure_future(dialog.dismiss()))

            try:
                # 1) Open upload page
                await page.goto("https://www.youtube.com/upload", wait_until="domcontentloaded", timeout=90000)
                await asyncio.sleep(8)
                if "accounts.google" in page.url:
                    print("  NOT LOGGED IN")
                    log_lines.append("  NOT LOGGED IN")
                    await context.close()
                    continue

                # 2) Select file
                print("  Waiting for upload button...")
                btn = page.locator('button:has-text("Chọn tệp")')
                await btn.first.wait_for(state="visible", timeout=30000)
                async with page.expect_file_chooser(timeout=15000) as fc_info:
                    await btn.first.click()
                fc = await fc_info.value
                await fc.set_files(video_path)
                print("  File selected")

                # 3) Wait for details page
                print("  Waiting for details page...")
                await asyncio.sleep(35)

                # 4) Title
                try:
                    title_ce = page.locator('[contenteditable="true"]').first
                    await title_ce.wait_for(state="visible", timeout=10000)
                    await title_ce.click()
                    await page.keyboard.press("Control+a")
                    await asyncio.sleep(0.3)
                    await title_ce.fill("")
                    await asyncio.sleep(0.2)
                    await title_ce.type(full_title, delay=10)
                    print(f"  Title set")
                    await asyncio.sleep(1)
                except Exception as e:
                    print(f"  Title error: {e}")

                # 5) Description
                try:
                    desc_ce = page.locator('[contenteditable="true"]').nth(1)
                    await desc_ce.click()
                    await asyncio.sleep(0.5)
                    await desc_ce.fill(description)
                    print("  Description set")
                    await asyncio.sleep(1)
                except Exception as e:
                    print(f"  Description error: {e}")

                # 6) Audience
                try:
                    await page.locator('tp-yt-paper-radio-button[name="VIDEO_MADE_FOR_KIDS_NOT_MFK"]').first.click(timeout=5000)
                    print("  Audience: Not for kids")
                    await asyncio.sleep(1)
                except Exception as e:
                    print(f"  Audience error: {e}")

                # 7) Next x3
                for step_name in ["Video elements", "Checks", "Visibility"]:
                    await asyncio.sleep(3)
                    try:
                        await page.locator('#next-button').first.click(timeout=8000)
                        print(f"  Next: {step_name}")
                    except Exception as e:
                        print(f"  Next error ({step_name}): {e}")
                    await asyncio.sleep(3)

                # 8) Visibility: Public
                try:
                    await page.locator('tp-yt-paper-radio-button[name="PUBLIC"]').first.click(timeout=5000)
                    print("  Visibility: Public")
                    await asyncio.sleep(2)
                except:
                    print("  Visibility: failed")

                # 9) Publish
                await asyncio.sleep(2)
                published = await click_publish(page)
                if published:
                    print("  PUBLISHED!")
                    await asyncio.sleep(12)
                else:
                    print("  PUBLISH FAILED")
                    log_lines.append("  PUBLISH BUTTON NOT FOUND")

                # Close success dialog
                try:
                    for txt in ["Đóng", "Close", "Xong"]:
                        close = page.locator('ytcp-button').filter(has_text=txt)
                        if await close.count() > 0:
                            await close.first.click(timeout=3000)
                            await asyncio.sleep(1)
                            break
                except:
                    pass

                log_lines.append("  SUCCESS")
                success_count += 1

                # KEEP context open - don't close
                all_contexts.append(context)
                print(f"  Window kept open")

            except Exception as e:
                print(f"  ERROR: {e}")
                log_lines.append(f"  ERROR: {e}")
                try:
                    await context.close()
                except:
                    pass

            # Save log after each video
            with open(LOG_FILE, "w", encoding="utf-8") as f:
                f.write("\n".join(log_lines))

            if i < len(video_files) - 1:
                print("  Waiting 5s before next...")
                await asyncio.sleep(5)

        print(f"\n=== DONE: {success_count}/{len(video_files)} uploaded ===")
        print(f"Keeping {len(all_contexts)} browser windows open")
        log_lines.append(f"\nSUMMARY: {success_count}/{len(video_files)} uploaded")
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(log_lines))

        # Keep browser alive
        print("\nBrowser windows still open. Press Ctrl+C to exit.")
        try:
            while True:
                await asyncio.sleep(60)
        except (KeyboardInterrupt, asyncio.CancelledError):
            pass
        finally:
            print("Closing browser...")
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
