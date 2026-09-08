# upload_fb_business.py - Upload 22 clip pickleball len Page qua Meta Business Suite
# Luot: vao Page dalisportss -> Tao bai viet -> Them anh/video (1 lan, expect_file_chooser)
# -> set 22 clip -> cho upload xong -> dien caption -> Dang.
import os, sys, asyncio, time
sys.stdout.reconfigure(encoding="utf-8")
from playwright.async_api import async_playwright

FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CLIPS_DIR = os.path.join(FOLDER, "clips")
INFO_FILE = os.path.join(CLIPS_DIR, "clips_info.txt")
DESCRIPTION_FILE = os.path.join(FOLDER, "mota.txt.txt")
USER_DATA_DIR = os.path.join(os.environ.get("TEMP", "C:\\temp"), "fb_badv_profile")
HOME_URL = "https://business.facebook.com/"
PAGE_URL = "https://business.facebook.com/latest/posts"
LOG_FILE = os.path.join(FOLDER, "upload_fb_business_log.txt")

SELECTOR_ADD_MEDIA = [
    'div[role="button"]:has-text("Th\u00eam \u1ea3nh/video")',
    'div[role="button"]:has-text("Add photos/videos")',
    'div[role="button"]:has-text("Th\u00eam \u1ea3nh")',
    'div[role="button"]:has-text("Add photos")',
    'input[type="file"]',
    '[data-testid*="add-photos"]',
    '[aria-label*="Th\u00eam \u1ea3nh/video"]',
    'div[role="button"]:has-text("\u1ea2nh/video")',
    'div[role="button"]:has-text("Photo/video")',
]


def read_info():
    mapping = {}
    if not os.path.exists(INFO_FILE):
        return mapping
    with open(INFO_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.strip() or " | " not in line:
                continue
            fname, title = line.split(" | ", 1)
            mapping[fname.strip()] = title.strip()
    return mapping


def read_base_description():
    if os.path.exists(DESCRIPTION_FILE):
        with open(DESCRIPTION_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""


def build_caption(mapping):
    base = read_base_description()
    lines = [base, "\n\U0001F3C6 ALBUM TR\u1eccN B\u1ed8 C\u00c1C TR\u1eacN \u0110\u1ea4U PICKLEBALL (CLIPS):"]
    for i, (fname, title) in enumerate(mapping.items(), 1):
        lines.append(f"\U0001F3F8 Tr\u1eadn {i:02d}: {title}")
    return "\n".join(lines).strip()


async def log(msg):
    print(msg, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(time.strftime("%H:%M:%S ") + msg + "\n")


async def main():
    try:
        os.remove(LOG_FILE)
    except Exception:
        pass

    mapping = read_info()
    clips = sorted([f for f in os.listdir(CLIPS_DIR) if f.endswith(".mp4")])
    clips = [f for f in clips if f in mapping]
    if not clips:
        await log("[!] Khong co clip nao trong clips/")
        return
    video_paths = [os.path.join(CLIPS_DIR, f) for f in clips]
    caption = build_caption(mapping)
    await log(f"UPLOAD {len(clips)} CLIP L\u00caN PAGE QUA META BUSINESS SUITE")
    await log("Caption:\n" + caption)

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

        # login
        for _ in range(150):
            url = page.url
            if "login" not in url.lower() and "checkpoint" not in url.lower() and "facebook.com" in url.lower():
                break
            await log(">>> VUI LONG DANG NHAP BUSINESS SUITE (con cho)...")
            await asyncio.sleep(4)

        await log("[>] Dieu huong toi " + PAGE_URL)
        await page.goto(PAGE_URL, wait_until="domcontentloaded", timeout=90000)
        await asyncio.sleep(8)
        await log("[*] URL page: " + page.url)

        # Tao bai viet
        created = False
        for sel in [
            'div[role="button"]:has-text("T\u1ea1o b\u00e0i vi\u1ebft")',
            'div[role="button"]:has-text("Create post")',
            'button:has-text("T\u1ea1o b\u00e0i vi\u1ebft")',
            '[data-testid*="create"]'
        ]:
            try:
                el = page.locator(sel).first
                if await el.count() > 0 and await el.is_visible(timeout=2000):
                    await el.click()
                    created = True
                    await log("[+] Da mo khung Tao bai viet: " + sel)
                    await asyncio.sleep(4)
                    break
            except Exception:
                pass
        if not created:
            await log("[!] Khong mo duoc khung Tao bai viet.")

        # Dinh toan bo clip: bam Them anh/video 1 lan trong expect_file_chooser
        await log("[>] Dinh " + str(len(video_paths)) + " clip (bat File Chooser 1 lan)...")
        attached = False
        try:
            fi = page.locator('input[type="file"]').first
            if await fi.count() > 0:
                await fi.wait_for(state="attached", timeout=6000)
                await fi.set_input_files(video_paths)
                attached = True
                await log("[+] Da dinh qua input[type=file]")
        except Exception as e:
            await log("[i] Tat input[type=file]: " + str(e))

        if not attached:
            try:
                async with page.expect_file_chooser(timeout=25000) as fc_info:
                    done = False
                    for sel in SELECTOR_ADD_MEDIA:
                        el = page.locator(sel).first
                        if await el.count() > 0 and await el.is_visible(timeout=1500):
                            await el.click()
                            done = True
                            await log("[+] Da bam mo file dialog: " + sel)
                            break
                    if not done:
                        await log("[!] Khong co phan tu de mo file dialog")
                fc = await fc_info.value
                await fc.set_files(video_paths)
                attached = True
                await log("[+] Da dinh " + str(len(video_paths)) + " clip qua File Chooser")
            except Exception as e2:
                await log("[!] File Chooser loi: " + str(e2))

        if not attached:
            await log("[!] KHONG DINH DUOC clip - dung.")
            await context.close()
            return

        # Cho 22 video upload/encode xong (toi da 60 phut)
        await log("[>] Cho 22 video upload/encode xong (co the lau)...")
        up_done = False
        up_deadline = time.time() + 3600
        while time.time() < up_deadline:
            try:
                txt = (await page.locator("body").inner_text(timeout=2500)) or ""
                if ("\u0111ang t\u1ea3i l\u00ean" not in txt.lower()
                        and "uploading" not in txt.lower()
                        and "\u0111ang x\u1eed l\u00fd" not in txt.lower()
                        and "processing" not in txt.lower()):
                    # cho them 10 giay de chan chac
                    await asyncio.sleep(10)
                    up_done = True
                    break
            except Exception:
                pass
            await asyncio.sleep(6)
        await log("[OK] Upload/encode xong" if up_done else "[!] Het thoi gian cho upload - van thu tiep")

        # Dien caption
        await log("[>] Dien caption...")
        try:
            te = page.locator('div[contenteditable="true"], [role="textbox"]').first
            if await te.count() > 0:
                await te.click()
                await page.keyboard.press("Control+a")
                await asyncio.sleep(0.3)
                await te.fill(caption)
                await log("[+] Da dien caption (" + str(len(caption)) + " ky tu)")
                await asyncio.sleep(2)
        except Exception as e:
            await log("[!] Dien caption loi: " + str(e))

        # BAM DANG
        await log("[>] Tim va bam nut Dang...")
        published = False
        for txt in ["\u0110\u0103ng", "Post", "Publish", "Chia s\u1ebb ngay", "Xu\u1ea5t b\u1ea3n"]:
            deadline = time.time() + 900
            while time.time() < deadline:
                try:
                    btn = page.locator(f'div[role="button"]:has-text("{txt}"), button:has-text("{txt}"), [data-testid*="publish"]').first
                    if await btn.count() > 0 and await btn.is_visible(timeout=1500):
                        disabled = await btn.get_attribute("aria-disabled")
                        if disabled not in ("true",):
                            await btn.click(timeout=6000)
                            published = True
                            await log("[+] DA BAM DANG: " + txt)
                            break
                except Exception:
                    pass
                await asyncio.sleep(3)
            if published:
                break

        if published:
            # cho modal dong
            c_deadline = time.time() + 360
            while time.time() < c_deadline:
                try:
                    if await page.locator('div[role="dialog"]').count() == 0:
                        await log("[+] Bai viet da dang xong!")
                        break
                except Exception:
                    pass
                await asyncio.sleep(2)

        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n[{time.strftime('%Y-%m-%d %H:%M')}] FACEBOOK BUSINESS ({len(clips)} videos) -> {'SUCCESS' if published else 'FAILED'}\n")
        await log("KET QUA: " + ("SUCCESS" if published else "FAILED"))
        await asyncio.sleep(2)
        await context.close()


if __name__ == "__main__":
    asyncio.run(main())

