# debug_yt.py - ghi toan bo trang de biet dang o dau
import os, sys, asyncio
sys.stdout.reconfigure(encoding="utf-8")
from playwright.async_api import async_playwright

USER_DATA_DIR = os.path.join(os.environ.get("TEMP", "C:\\temp"), "yt_badv_profile")
RESULT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "yt_debug.txt")


async def main():
    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            USER_DATA_DIR, headless=False, channel="chrome",
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()
        page.set_default_timeout(25000)
        await page.goto("https://studio.youtube.com/videos", wait_until="domcontentloaded")
        await page.wait_for_timeout(4000)

        out = []
        out.append("URL: " + page.url)
        try:
            title = await page.title()
            out.append("TITLE: " + title)
        except Exception as e:
            out.append("TITLE ERR: " + str(e))
        try:
            body = await page.evaluate("() => document.body ? document.body.innerText : '(no body)'")
            out.append("BODY:\n" + body[:4000])
        except Exception as e:
            out.append("BODY ERR: " + str(e))
        # dem cac loai element
        for sel in ["ytcp-video-row", "a#video-title", "ytcp-dialog", "ytcp-uploads-dialog", "ytcp-toast", "iron-pages"]:
            c = await page.evaluate("sel => document.querySelectorAll(sel).length", sel)
            out.append(f"count[{sel}] = {c}")
        # screenshot
        try:
            await page.screenshot(path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "yt_debug.png"))
            out.append("screenshot saved")
        except Exception as e:
            out.append("shot ERR: " + str(e))

        with open(RESULT, "w", encoding="utf-8") as f:
            f.write("\n".join(out))
        print("[*] wrote", RESULT, flush=True)
        await ctx.close()
    print("DONE", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
