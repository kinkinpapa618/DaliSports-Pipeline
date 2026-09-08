# check_yt_status.py - kiem tra trang thai video YouTube Studio (Playwright) v3
# Headless=False (cua so rieng). An nut bo qua overlay 'trinh duyet khong duoc ho tro'.
# Ghi ket qua ra yt_status_result.txt de doc lai.
import os, sys, asyncio, re
sys.stdout.reconfigure(encoding="utf-8")

from playwright.async_api import async_playwright

USER_DATA_DIR = os.path.join(os.environ.get("TEMP", "C:\\temp"), "yt_badv_profile")
SEARCH = "PICKLEBALL"
RESULT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "yt_status_result.txt")


def log(msg):
    print(msg, flush=True)


async def main():
    log("[*] Mở YouTube Studio Videos...")
    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            USER_DATA_DIR,
            headless=False,
            channel="chrome",
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()
        page.set_default_timeout(25000)
        await page.goto("https://studio.youtube.com/videos", wait_until="domcontentloaded")

        # click bo qua overlay trinh duyet khong duoc ho tro
        for attempt in range(8):
            await page.wait_for_timeout(3000)
            try:
                skipped = await page.evaluate("""() => {
                    const els = Array.from(document.querySelectorAll('button, a, ytcp-button'));
                    for (const el of els) {
                        const t = (el.textContent||'').trim().toLowerCase();
                        if (t.includes('youtube studio') || t.includes('chuyển thẳng') ||
                            t.includes('tiếp tục') || t.includes('continue')) {
                            if (el.offsetParent !== null) { el.click(); return el.textContent.trim(); }
                        }
                    }
                    return null;
                }""")
                if skipped:
                    log(f"[*] Đã bấm bỏ overlay: {skipped}")
                    break
            except Exception:
                pass
            # kiem tra xem da vao studio chua
            in_studio = await page.evaluate("() => !!document.querySelector('ytcp-video-row, ytcp-videos, ytcp-video-manager')")
            if in_studio:
                break

        # cho bang tai
        for _ in range(8):
            await page.wait_for_timeout(2500)
            n = await page.locator("ytcp-video-row").count()
            if n > 0:
                break

        # gom thong tin video
        all_text = await page.evaluate("""() => {
            const out = [];
            document.querySelectorAll('ytcp-video-row').forEach(el=>{
                const title = el.querySelector('a#video-title, yt-formatted-string#video-title');
                const badge = el.querySelector('#status-badge, ytcp-icon-badge');
                const t = title ? title.textContent.trim().slice(0,140) : '';
                const b = badge ? badge.textContent.trim() : '';
                out.push((t||el.textContent.trim().slice(0,100)) + ' [' + (b||'?') + ']');
            });
            return out;
        }""")
        total = len(all_text)

        lines = []
        lines.append(f"TOTAL: {total}")
        for t in all_text:
            lines.append(" - " + t)
            if SEARCH in t.upper():
                log(f"  -> {t}")
        lines += [f"(không thấy video chứa {SEARCH})"] if SEARCH not in " | ".join(all_text).upper() else []

        # ghi file
        with open(RESULT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        log(f"[*] Đã ghi {RESULT_FILE}")

        await page.wait_for_timeout(3000)
        await ctx.close()
    log("DONE CHECK")


if __name__ == "__main__":
    asyncio.run(main())
