# upload_fb_business_test.py - TEST 1 clip tren Meta Business Suite
# M\u1edf business.facebook.com, ch\u1edd dang nhap, vao Page dalisportss,
# mo khung tao bai viet, dinh 1 clip, DUNG (khong dang).
import os, sys, asyncio, time
sys.stdout.reconfigure(encoding="utf-8")
from playwright.async_api import async_playwright

FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CLIPS_DIR = os.path.join(FOLDER, "clips")
USER_DATA_DIR = os.path.join(os.environ.get("TEMP", "C:\\temp"), "fb_badv_profile")
PAGE_URL = "https://business.facebook.com/latest/posts"
HOME_URL = "https://business.facebook.com/"


async def log(msg):
    print(msg, flush=True)
    with open(os.path.join(FOLDER, "fb_business_test_out.txt"), "a", encoding="utf-8") as f:
        f.write(msg + "\n")


async def main():
    # xoa file out cu
    try:
        os.remove(os.path.join(FOLDER, "fb_business_test_out.txt"))
    except Exception:
        pass

    # lay 1 clip dau tien
    clips = sorted([f for f in os.listdir(CLIPS_DIR) if f.endswith(".mp4")])
    if not clips:
        await log("[!] Khong co clip nao trong clips/")
        return
    one_clip = os.path.join(CLIPS_DIR, clips[0])
    await log("TEST 1 CLIP: " + one_clip)

    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            USER_DATA_DIR, channel="chrome", headless=False,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox",
                  "--disable-dev-shm-usage", "--start-maximized"],
            no_viewport=True, user_agent=user_agent,
        )
        page = await context.new_page()
        page.set_default_timeout(20000)

        await log("[>] Mo Meta Business Suite...")
        await page.goto(HOME_URL, wait_until="domcontentloaded", timeout=90000)
        await asyncio.sleep(6)

        url = page.url
        await log("[*] URL: " + url)

        # Dang nhap
        if "login" in url.lower() or "checkpoint" in url.lower():
            await log(">>> VUI LONG DANG NHAP META BUSINESS SUITE (toi da 10 phut)...")
            deadline = time.time() + 600
            while time.time() < deadline:
                url = page.url
                if "login" not in url.lower() and "checkpoint" not in url.lower() and "facebook.com" in url.lower():
                    break
                await asyncio.sleep(4)
            await log("[*] Sau khi dang nhap, URL: " + page.url)
            await asyncio.sleep(5)

        # Dieu huong toi trang Posts cua Business Suite
        await log("[>] Dieu huong toi " + PAGE_URL)
        await page.goto(PAGE_URL, wait_until="domcontentloaded", timeout=90000)
        await asyncio.sleep(8)

        # Neu can chon Page/Dropdown
        await log("[*] URL page: " + page.url)

        # Mo nut tao bai viet
        await log("[>] Tim nut tao bai viet (Create post)...")
        created = False
        for sel in [
            'div[role="button"]:has-text("T\u1ea1o b\u00e0i vi\u1ebft")',
            'div[role="button"]:has-text("Create post")',
            'span:has-text("T\u1ea1o b\u00e0i vi\u1ebft")',
            'span:has-text("Create post")',
            '[data-testid*="create"]',
            'button:has-text("T\u1ea1o b\u00e0i vi\u1ebft")',
            'button:has-text("Create post")'
        ]:
            try:
                el = page.locator(sel).first
                if await el.count() > 0 and await el.is_visible(timeout=2000):
                    await el.click()
                    created = True
                    await log("[+] Da click tao bai viet: " + sel)
                    await asyncio.sleep(4)
                    break
            except Exception:
                pass
        if not created:
            await log("[!] Khong tim thay nut tao bai viet - dung test de quan sat.")

        # D\u00ednh t\u1ec7p: th\u1eed input[type=file] tr\u01b0\u1edbc; n\u1ebfu kh\u00f4ng c\u00f3,
        # b\u1eaft File Chooser b\u1eb1ng c\u00e1ch b\u1ea5m n\u00fat th\u00eam \u1ea3nh/video M\u1ed8T L\u1ea6N DUY NH\u1ea4T.
        await log("[>] Tim va dinh 1 clip (bat File Chooser 1 lan duy nhat)...")
        attached = False
        # 2a. th\u1eed set tr\u1ef1c ti\u1ebfp v\u00e0o input[type=file] n\u1ebfu c\u00f3
        try:
            fi = page.locator('input[type="file"]').first
            if await fi.count() > 0:
                await fi.wait_for(state="attached", timeout=8000)
                await fi.set_input_files(one_clip)
                attached = True
                await log("[+] Da dinh 1 clip vao input[type=file]")
        except Exception as e:
            await log("[i] Khong dat duoc input[type=file]: " + str(e))

        # 2b. n\u1ebfu v\u1eabn ch\u01b0a \u0111\u00ednh, b\u1eaft File Chooser b\u1eb1ng c\u00e1ch b\u1ea5m n\u00fat l\u1ea1i
        if not attached:
            await log("[>] Bat File Chooser bang cach bam lai nut them anh/video...")
            try:
                async with page.expect_file_chooser(timeout=20000) as fc_info:
                    done = False
                    for sel in [
                        'div[role="button"]:has-text("Th\u00eam \u1ea3nh/video")',
                        'div[role="button"]:has-text("Add photos/videos")',
                        'div[role="button"]:has-text("Th\u00eam \u1ea3nh")',
                        'input[type="file"]',
                        '[data-testid*="add-photos"]',
                        'div[role="button"]:has-text("\u1ea2nh/video")',
                        'div[role="button"]:has-text("Photo/video")'
                    ]:
                        el = page.locator(sel).first
                        if await el.count() > 0 and await el.is_visible(timeout=1200):
                            await el.click()
                            done = True
                            await log("[+] Da bam de mo file dialog: " + sel)
                            break
                    if not done:
                        await log("[!] Khong co phan tu de bam mo file dialog")
                fc = await fc_info.value
                await fc.set_files(one_clip)
                attached = True
                await log("[+] Da dinh 1 clip qua File Chooser")
            except Exception as e2:
                await log("[!] File Chooser loi: " + str(e2))

        # Khong dang - de nguoi dung xac nhan clip da dinh
        await log("=" * 60)
        await log("[DUNG TEST] Clip da dinh: " + str(attached))
        await log("Kiem tra tren man hinh: clip co hien khong? Neu OK, noi toi de chay du 22.")
        await log("Gi\u1eef c\u1eeda s\u1ed5 m\u1edf (script \u0111\u1ee3i \u0111\u1ebfn khi b\u1ea1n \u0111\u00f3ng).")
        await log("=" * 60)

        while True:
            try:
                if page.is_closed():
                    await log("[*] Trinh duyet da dong.")
                    break
            except Exception:
                break
            await asyncio.sleep(30)


if __name__ == "__main__":
    asyncio.run(main())

