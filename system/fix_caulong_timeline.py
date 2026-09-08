#!/usr/bin/env python3
# fix_caulong_timeline.py - Fix cac dong KHONG_DOC_DUOC trong timeline cau long
# Doc timeline hien tai, lay full frame tai giua moi khoang KHONG_DOC_DUOC, goi Gemini doc
import os, sys, re, time
sys.stdout.reconfigure(encoding="utf-8")
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
import gemini_timeline as gt

TL_RE = re.compile(r"^\s*(\d{1,2}:\d{2}(?::\d{2})?)\s*-\s*(\d{1,2}:\d{2}(?::\d{2})?)\s*-\s*(.+?)\s*$")
VIDEO = r"C:\Users\dalis\Desktop\Sân 2\fb_caulong.mp4"
TL_FILE = r"C:\Users\dalis\Desktop\Sân 2\fb_caulong_timeline.txt"

def to_sec(t):
    p = [int(x) for x in t.split(":")]
    if len(p)==3: return p[0]*3600+p[1]*60+p[2]
    elif len(p)==2: return p[0]*60+p[1]
    return p[0]

def main():
    client = gt.get_gemini_client()
    if not client:
        sys.exit(1)
    model = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")

    with open(TL_FILE, encoding="utf-8-sig") as f:
        lines = f.readlines()

    out_lines = []
    fixed = 0
    total = 0

    for i, line in enumerate(lines):
        m = TL_RE.match(line)
        if not m:
            out_lines.append(line)
            continue
        start, end, title = m.group(1), m.group(2), m.group(3)
        total += 1

        if "KHONG_DOC_DUOC" not in title:
            out_lines.append(line)
            continue

        # Lay full frame tai giua khoang
        st_sec, en_sec = to_sec(start), to_sec(end)
        mid_sec = (st_sec + en_sec) // 2
        print(f"\n[{i+1}] KHONG_DOC_DUOC: {start} -> {end} (mid={gt.format_timestamp(mid_sec)})")

        img = gt.extract_match_frame(VIDEO, mid_sec)
        if img is None:
            print(f"    [!] Khong trich duoc frame, giu nguyen")
            out_lines.append(line)
            continue

        title_new = gt.extract_title_with_gemini(client, img, preferred_model=model)
        if "KHONG_DOC_DUOC" in title_new or "VĐV 1" in title_new or "VĐV A" in title_new:
            # Thu them o 20% va 80% cua khoang
            for frac in [0.2, 0.8]:
                ts2 = st_sec + int((en_sec - st_sec) * frac)
                img2 = gt.extract_match_frame(VIDEO, ts2)
                if img2:
                    t2 = gt.extract_title_with_gemini(client, img2, preferred_model=model)
                    if "KHONG_DOC_DUOC" not in t2 and "VĐV 1" not in t2 and "VĐV A" not in t2:
                        title_new = t2
                        break

        if "KHONG_DOC_DUOC" in title_new:
            print(f"    [!] Van KHONG_DOC_DUOC, giu nguyen")
            out_lines.append(line)
        else:
            print(f"    [OK] {title_new}")
            out_lines.append(f"{start} - {end} - {title_new}")
            fixed += 1
        time.sleep(0.5)

    with open(TL_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(out_lines) + "\n")
    print(f"\n=== XONG: {fixed}/{total} dong KHONG_DOC_DUOC da fix ===")

if __name__ == "__main__":
    main()
