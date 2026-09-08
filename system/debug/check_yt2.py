# check_yt2.py - in ro badge trang thai cua video pickleball
import os, sys, asyncio
sys.stdout.reconfigure(encoding="utf-8")
from playwright.async_api import async_playwright

USER_DATA_DIR = os.path.join(os.environ.get("TEMP", "C:\\temp"), "yt_badv_profile")
SEARCH = "PICKLEBALL"
URL = "https://studio.youtube.com/channel/UCeJaMLWGwvlK1zgy9aeknTg/videos/upload?theme=dark&filter=%5B%5D&sort=%7B%22columnType%22%3A%22date%22%2C%22sortOrder%22%3A%22DESCENDING%22%7D"
RESULT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "yt_status_result.txt")


async def main():
    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            USER_DATA_DIR, headless=False, channel="chrome",
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()
        page.set_default_timeout(25000)
        await page.goto(URL, wait_until="domcontentloaded")

        for _ in range(6):
            await page.wait_for_timeout(3500)
            if await page.locator("ytcp-video-row").count() > 0:
                break

        # doc tung row, in title + toan bo text cua row (chua trang thai)
        rows = page.locator("ytcp-video-row")
        n = await rows.count()
        lines = [f"TOTAL rows: {n}"]
        pickleball = None
        for i in range(n):
            row = rows.nth(i)
            txt = (await row.inner_text()).replace("\n", " | ")
            title = (await row.locator("a#video-title").first.inner_text()) if await row.locator("a#video-title").count() else ""
            lines.append(f"ROW {i}: {title}")
            if SEARCH in title.upper() or SEARCH in txt.upper():
                pickleball = (i, title, txt)
        if pickleball:
            lines.append("\n=== PICKLEBALL ROW ===")
            lines.append("Index: " + str(pickleball[0]))
            lines.append("Title: " + pickleball[1])
            lines.append("Status text: " + pickleball[2])
        else:
            lines.append("\n(không thấy pickleball trong các row hiển thị)")

        with open(RESULT, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print("[*] wrote", RESULT, flush=True)
        await ctx.close()
    print("DONE", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
