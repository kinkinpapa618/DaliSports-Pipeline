#!/usr/bin/env python3
# test_fix_khongdoc.py - Test truc tiep doc KHONG_DOC_DUOC o cac mốc thoi gian cu the
import os, sys
sys.stdout.reconfigure(encoding="utf-8")
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
import gemini_timeline as gt

VIDEO = r"C:\Users\dalis\Desktop\Sân 2\caulong_ttbc.mp4"
model = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")
client = gt.get_gemini_client()

# Cac khoang KHONG_DOC_DUOC chua fix duoc
intervals = [
    ("01:29:10", "01:30:20", "short 70s"),
    ("01:40:40", "01:42:05", "short 85s"),
    ("01:42:40", "01:44:05", "short 85s"),
    ("01:44:40", "01:58:20", "long 14min"),
    ("02:26:25", "02:29:05", "short 160s"),
    ("02:42:10", "02:52:20", "10min"),
    ("02:52:55", "02:53:50", "55s"),
    ("02:54:25", "03:03:20", "9min"),
    ("03:04:10", "03:34:20", "30min"),
    ("03:34:55", "03:35:50", "55s"),
    ("03:36:55", "03:37:50", "55s"),
    ("03:38:40", "03:45:05", "6min"),
    ("03:45:40", "03:51:50", "6min"),
]

def to_sec(t):
    p = [int(x) for x in t.split(":")]
    return p[0]*3600 + p[1]*60 + p[2]

for start, end, label in intervals:
    st, en = to_sec(start), to_sec(end)
    # Thu 3 mốc: 20%, 50%, 80%
    for frac, name in [(0.2, "20%"), (0.5, "50%"), (0.8, "80%")]:
        ts = st + int((en - st) * frac)
        img = gt.extract_match_frame(VIDEO, ts)
        if img is None:
            print(f"[{start}-{end}] {name} @ {gt.format_timestamp(ts)}: KHONG TRICH DUOC FRAME")
            continue
        try:
            response = client.models.generate_content(model=model, contents=[img, "Doc bang diem cau long trong anh. Tra ve 1 dong: TEN GIAI | HANH MUC | TEN DOI 1 vs TEN DOI 2. Neu khong doc duoc tra ve KHONG_DOC_DUOC"])
            text = response.text.strip().split("\n")[0].strip()
            print(f"[{start}-{end}] {name} @ {gt.format_timestamp(ts)}: {text}")
            if "KHONG_DOC_DUOC" not in text and "VĐV" not in text:
                break  # Doc duoc roi, khong can test tiep
        except Exception as e:
            print(f"[{start}-{end}] {name} @ {gt.format_timestamp(ts)}: ERROR {e}")
