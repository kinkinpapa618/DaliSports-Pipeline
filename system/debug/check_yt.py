# check_yt.py - mo URL Studio user cung cap, doc trang thai video pickleball
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

        # dong dialog neu co, roi reload de cho bang hien
        for _ in range(6):
            await page.wait_for_timeout(3500)
            try:
                closed = await page.evaluate("""() => {
                    let ok = false;
                    document.querySelectorAll('ytcp-dialog, tp-yt-paper-dialog, ytcp-error').forEach(d=>{
                        if (d.offsetParent !== null) {
                            const btns = d.querySelectorAll('button, ytcp-button, [aria-label]');
                            for (const b of btns) {
                                const t=(b.textContent||'').toLowerCase();
                                if (t.includes('đóng') || t.includes('đồng ý') || t.includes('got it') ||
                                    t.includes('ok') || t.includes('tiếp tục') || t.includes('thử lại') ||
                                    t.includes('retry') || (b.getAttribute('aria-label')||'').toLowerCase().includes('đóng')) {
                                    b.click(); ok = true; return true;
                                }
                            }
                        }
                    });
                    return ok;
                }""")
                if closed:
                    await page.reload(wait_until="domcontentloaded")
                    await page.wait_for_timeout(4000)
                    break
            except Exception:
                pass

        # cho bang
        for _ in range(8):
            await page.wait_for_timeout(2500)
            n = await page.locator("ytcp-video-row").count()
            if n > 0:
                break

        all_text = await page.evaluate("""() => {
            const out=[];
            document.querySelectorAll('ytcp-video-row').forEach(el=>{
                const title=el.querySelector('a#video-title, yt-formatted-string#video-title');
                const t=title?title.textContent.trim().slice(0,150):'';
                out.push({text:(t||el.textContent.trim().slice(0,120)), badge:(title?title.closest('ytcp-video-row').textContent:'')});
            });
            return out;
        }""")

        lines = [f"URL: {page.url}", f"TOTAL: {len(all_text)}"]
        for o in all_text:
            if SEARCH in o["text"].upper():
                lines.append("MATCH >>> " + o["text"] + " | " + o["badge"][:200])
        if not any(SEARCH in o["text"].upper() for o in all_text):
            lines.append(f"(không thấy video chứa {SEARCH})")
            lines.append("--- first 5 rows ---")
            for o in all_text[:5]:
                lines.append(" * " + o["text"])
            body = await page.evaluate("() => document.body?document.body.innerText.slice(0,1200):''")
            lines.append("--- body ---")
            lines.append(body)

        with open(RESULT, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print("[*] wrote", RESULT, flush=True)
        await ctx.close()
    print("DONE", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
