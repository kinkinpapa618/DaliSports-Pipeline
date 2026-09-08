# upload_fb_series_step1.py - Phase 1: TAO SERIES (Loáº¡t video) tren Meta Business Suite
# Tao Series truoc (ten + mo ta + thu tu), khong dang 22 video o step nay.
import os, sys, asyncio, time
sys.stdout.reconfigure(encoding="utf-8")
from playwright.async_api import async_playwright

FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
USER_DATA_DIR = os.path.join(os.environ.get("TEMP", "C:\\temp"), "fb_badv_profile")
HOME_URL = "https://business.facebook.com/"
SERIES_URL = ("https://business.facebook.com/latest/posts/all_series"
              "?asset_id=100941859608286&should_show_nux=false&focus_comments=false")
LOG_FILE = os.path.join(FOLDER, "upload_fb_series_step1_log.txt")

TITLE = "GI\u1ea2I PICKLEBALL S\u00c2N \u0110\u1ed2NG H\u01afNG 2026"
DESC = ("T\u1ed5ng h\u1ee3p to\u00e0n b\u1ed9 c\u00e1c tr\u1eadn \u0111\u1ea5u PICKLEBALL n\u1ed9i b\u1ed9 S\u00e2n \u0110\u1ed3ng H\u01b0ng n\u0103m 2026. "
        "Tr\u1eadn \u0110\u00e1nh theo th\u1ee9 t\u1ef1.\nTheo d\u00f5i Dali Sports: "
        "YouTube https://www.youtube.com/@DaliSports2026 | TikTok https://www.tiktok.com/@dali.sports "
        "| Hotline 0984 387 999\n#Pickleball #PickleballVietnam #DaliSports")


async def log(msg):
    print(msg, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(time.strftime("%H:%M:%S ") + msg + "\n")


async def main():
    try:
        os.remove(LOG_FILE)
    except Exception:
        pass
    await log("TITLE=[" + TITLE + "] len=" + str(len(TITLE)))

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

        await log("[>] Mo Business Suite...")
        await page.goto(HOME_URL, wait_until="domcontentloaded", timeout=90000)
        await asyncio.sleep(5)
        for _ in range(150):
            url = page.url
            if "login" not in url.lower() and "checkpoint" not in url.lower() and "facebook.com" in url.lower():
                break
            await asyncio.sleep(4)

        await log("[>] Mo trang Loan video...")
        await page.goto(SERIES_URL, wait_until="domcontentloaded", timeout=90000)
        await asyncio.sleep(8)

        # Click "Loáº¡t video má»›i"
        clicked = False
        for sel in ['div[role="button"]:has-text("Lo\u1ea1t video m\u1edbi")',
                    'button:has-text("Lo\u1ea1t video m\u1edbi")',
                    'span:has-text("Lo\u1ea1t video m\u1edbi")']:
            try:
                el = page.locator(sel).first
                if await el.count() > 0 and await el.is_visible(timeout=2000):
                    await el.click()
                    clicked = True
                    await log("[+] Mo khung tao Series")
                    await asyncio.sleep(5)
                    break
            except Exception:
                pass

        # Dien tieu de
        try:
            ti = page.locator('input[placeholder*="ti\u00eau \u0111\u1ec1"], input[placeholder*="title"], input[placeholder*="ti\u00eau"]').first
            await ti.wait_for(state="visible", timeout=8000)
            await ti.click()
            await ti.fill(TITLE)
            await log("[+] Da dien tieu de")
            await asyncio.sleep(1)
        except Exception as e:
            await log("[!] Tieu de loi: " + str(e))

        # Dien mo ta
        try:
            ta = page.locator('textarea[placeholder*="M\u00f4 t\u1ea3"], textarea').first
            await ta.wait_for(state="visible", timeout=6000)
            await ta.click()
            await ta.fill(DESC)
            await log("[+] Da dien mo ta")
            await asyncio.sleep(1)
        except Exception as e:
            await log("[!] Mo ta loi: " + str(e))

        # Chon thu tu: "Theo trĂ¬nh tá»± thá»i gian"
        try:
            for sel in ['div[role="button"]:has-text("Theo tr\u00ecnh t\u1ef1 th\u1eddi gian")',
                        'div[role="button"]:has-text("Theo tr\u00ecnh t\u1ef1")',
                        '[aria-label*="Theo tr\u00ecnh t\u1ef1"]']:
                el = page.locator(sel).first
                if await el.count() > 0 and await el.is_visible(timeout=1500):
                    await el.click()
                    await log("[+] Chon thu tu theo trinh tu thoi gian")
                    await asyncio.sleep(1)
                    break
        except Exception as e:
            await log("[!] Chon thu tu loi: " + str(e))

        # BAM "Luu lam ban nhap" (ko co nut Dang trong modal tao Series cua Meta)
        await log("[>] Tim nut Luu lam ban nhap...")
        published = False
        for txt in ["L\u01b0u l\u00e0m b\u1ea3n nh\u00e1p", "Save draft", "L\u01b0u"]:
            try:
                btn = page.locator(f'div[role="dialog"] div[role="button"]:has-text("{txt}"), div[role="dialog"] button:has-text("{txt}"), div[role="button"]:has-text("{txt}")').first
                if await btn.count() > 0 and await btn.is_visible(timeout=1500):
                    disabled = await btn.get_attribute("aria-disabled")
                    if disabled not in ("true",):
                        await btn.click(timeout=6000)
                        published = True
                        await log("[+] DA LUU l\u00e0m b\u1ea3n nh\u00e1p: " + txt)
                        break
            except Exception:
                pass

        if published:
            await asyncio.sleep(6)
            try:
                body = await page.locator("body").inner_text(timeout=3000)
            except Exception:
                body = ""
            await log("=== BODY (1500) ===")
            await log(body.replace("\n", " | ")[:1500])

        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n[{time.strftime('%Y-%m-%d %H:%M')}] TAO SERIES -> {'SUCCESS' if published else 'FAILED'}\n")
        await log("KET QUA: " + ("SUCCESS" if published else "FAILED"))

        # giu cua so mo de quan sat
        await log("Giu cua so mo.")
        while True:
            try:
                if page.is_closed():
                    break
            except Exception:
                break
            await asyncio.sleep(30)


if __name__ == "__main__":
    asyncio.run(main())

