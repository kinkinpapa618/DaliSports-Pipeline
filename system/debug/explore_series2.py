# explore_series2.py - Click "Loạt video mới" va in cau truc modal tao Series
import os, sys, asyncio, time
sys.stdout.reconfigure(encoding="utf-8")
from playwright.async_api import async_playwright

FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
USER_DATA_DIR = os.path.join(os.environ.get("TEMP", "C:\\temp"), "fb_badv_profile")
HOME_URL = "https://business.facebook.com/"
SERIES_URL = ("https://business.facebook.com/latest/posts/all_series"
              "?asset_id=100941859608286&should_show_nux=false&focus_comments=false")
OUT = os.path.join(FOLDER, "explore_series2_out.txt")


async def log(msg):
    print(msg, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(msg + "\n")


async def main():
    try:
        os.remove(OUT)
    except Exception:
        pass

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

        await page.goto(HOME_URL, wait_until="domcontentloaded", timeout=90000)
        await asyncio.sleep(5)
        for _ in range(150):
            url = page.url
            if "login" not in url.lower() and "checkpoint" not in url.lower() and "facebook.com" in url.lower():
                break
            await asyncio.sleep(4)

        await page.goto(SERIES_URL, wait_until="domcontentloaded", timeout=90000)
        await asyncio.sleep(8)
        await log("[*] URL: " + page.url)

        # Click nut "Loạt video mới"
        clicked = False
        for sel in [
            'div[role="button"]:has-text("Lo\u1ea1t video m\u1edbi")',
            'button:has-text("Lo\u1ea1t video m\u1edbi")',
            'span:has-text("Lo\u1ea1t video m\u1edbi")',
            '[aria-label*="Lo\u1ea1t video m\u1edbi"]'
        ]:
            try:
                el = page.locator(sel).first
                if await el.count() > 0 and await el.is_visible(timeout=2000):
                    await el.click()
                    clicked = True
                    await log("[+] Click: " + sel)
                    await asyncio.sleep(5)
                    break
            except Exception:
                pass
        if not clicked:
            await log("[!] Khong click duoc 'Loạt video mới'")

        # In body cua modal/dialog hien tai
        await log("=== BODY (6000 chars) ===")
        try:
            body = await page.locator("body").inner_text(timeout=4000)
            await log(body.replace("\n", " | ")[:6000])
        except Exception as e:
            await log("[i] body loi: " + str(e))

        await log("=== DIALOG HEADERS ===")
        for dsel in ['[role="dialog"]', '[role="document"]', 'div[aria-label*="Lo\u1ea1t video"]']:
            try:
                d = page.locator(dsel).first
                if await d.count() > 0 and await d.is_visible(timeout=1500):
                    txt = (await d.inner_text(timeout=2000)).replace("\n", " | ")[:2500]
                    await log(f"[{dsel}] -> {txt}")
            except Exception:
                pass

        await log("=== BUTTONS/INPUTS in modal ===")
        for el_sel in ['input', 'textarea', 'div[contenteditable=true]', 'button', 'div[role=button]']:
            els = page.locator(el_sel)
            n = await els.count()
            for i in range(min(n, 40)):
                try:
                    t = (await els.nth(i).inner_text(timeout=600)).replace("\n", " ").strip()[:60]
                    ph = ""
                    try:
                        ph = await els.nth(i).get_attribute("placeholder") or ""
                    except Exception:
                        pass
                    if t or ph:
                        await log(f"EL[{el_sel}][{i}] text='{t}' ph='{ph}'")
                except Exception:
                    pass

        await log("=== [DONE] Giu cua so mo de ban quan sat ===")
        while True:
            try:
                if page.is_closed():
                    await log("[*] Closed.")
                    break
            except Exception:
                break
            await asyncio.sleep(30)


if __name__ == "__main__":
    asyncio.run(main())
