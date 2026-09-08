# explore_series.py - Kham pha trang Loạt video (Series) trong Meta Business Suite
# In ra cac button/text chinh de biet selector tao Series. KHONG tao/dang gi.
import os, sys, asyncio, time
sys.stdout.reconfigure(encoding="utf-8")
from playwright.async_api import async_playwright

FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
USER_DATA_DIR = os.path.join(os.environ.get("TEMP", "C:\\temp"), "fb_badv_profile")
HOME_URL = "https://business.facebook.com/"
SERIES_URL = ("https://business.facebook.com/latest/posts/all_series"
              "?asset_id=100941859608286&should_show_nux=false&focus_comments=false")
OUT = os.path.join(FOLDER, "explore_series_out.txt")


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

        await log("[>] Mo Business Suite...")
        await page.goto(HOME_URL, wait_until="domcontentloaded", timeout=90000)
        await asyncio.sleep(5)

        for _ in range(150):
            url = page.url
            if "login" not in url.lower() and "checkpoint" not in url.lower() and "facebook.com" in url.lower():
                break
            await asyncio.sleep(4)

        await log("[>] Dieu huong toi trang Loạt video (Series)...")
        await page.goto(SERIES_URL, wait_until="domcontentloaded", timeout=90000)
        await asyncio.sleep(8)
        await log("[*] URL: " + page.url)

        # thu body text
        try:
            body = await page.locator("body").inner_text(timeout=4000)
            await log("=== BODY TEXT (5000 chars) ===")
            await log(body.replace("\n", " | ")[:5000])
        except Exception as e:
            await log("[i] body loi: " + str(e))

        # tim cac button
        await log("=== BUTTONS ===")
        btns = page.locator("button, div[role=button]")
        n = await btns.count()
        count = 0
        for i in range(min(n, 60)):
            try:
                t = (await btns.nth(i).inner_text(timeout=800)).replace("\n", " ").strip()[:80]
                if t:
                    await log(f"BTN[{i}] {t}")
                    count += 1
            except Exception:
                pass
        await log(f"(tong button co text: {count})")

        await log("=== [DONE KHAM PHA] Giu cua so mo de ban quan sat ===")
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
