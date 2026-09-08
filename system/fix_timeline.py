#!/usr/bin/env python3
# fix_timeline.py - Đọc lại title cho các dòng timeline bị placeholder rác (VĐV 1 / VĐV 2 ...)
# với nhiều mốc frame khác nhau trong mỗi trận, dùng Gemini để bắt đúng bảng điểm.
#
# Cách dùng:
#   python fix_timeline.py "<video>.mp4" "<timeline>.txt"
#
# Chỉ sửa những dòng có title rác; các dòng đã có title hợp lệ được giữ nguyên.
import os
import sys
import re
import concurrent.futures

sys.stdout.reconfigure(encoding="utf-8")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import cv2
from PIL import Image
import gemini_timeline as gt

# Chuẩn hoá dòng timeline: "START - END - RAW_TITLE"
TL_RE = re.compile(r"^\s*(\d{1,2}:\d{2}(?::\d{2})?)\s*-\s*(\d{1,2}:\d{2}(?::\d{2})?)\s*-\s*(.+?)\s*$")

TRASH_MARKERS = ["VĐV 1", "VĐV 2", "VĐV 3", "VĐV 4", "V\u0110V 1", "vdv 1", "khong_doc_duoc"]
# Một title được coi là rác nếu chứa marker placeholder.
def is_trash(title: str) -> bool:
    return any(m.lower() in title.lower() for m in TRASH_MARKERS)


def to_sec(t: str) -> int:
    p = [int(x) for x in t.split(":")]
    if len(p) == 3:
        h, m, s = p
    elif len(p) == 2:
        h, m, s = 0, p[0], p[1]
    else:
        h, m, s = 0, 0, p[0]
    return h * 3600 + m * 60 + s


def plausible(title: str) -> bool:
    t = title.strip().lower()
    if not t:
        return False
    if "khong_doc_duoc" in t:
        return False
    if any(m.lower() in t for m in TRASH_MARKERS):
        return False
    # phải có dấu "vs" (2 đội) hoặc ít nhất dấu "|" ghép đủ phần
    if "vs" not in t:
        return False
    return True


def extract_full_frame(video_path: str, timestamp_sec: float):
    """Trích xuất FULL frame (cả cảnh, không crop) để Gemini tự định vị bảng điểm ở bất kỳ đâu."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None
    cap.set(cv2.CAP_PROP_POS_MSEC, timestamp_sec * 1000)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        return None
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb)


def probe_match(video_path, client, start_sec, end_sec, model, total_duration):
    """Thử nhiều mốc frame khác nhau trong trận để Gemini đọc bảng điểm.
    Mỗi lần gọi Gemini được bọc bởi timeout cứng để không kẹt vĩnh viễn."""
    dur = end_sec - start_sec
    fracs = [0.05, 0.5, 0.5, 0.9, 0.25, 0.75, 0.02, 0.98]
    # thêm các mốc phía sau start một chút (bảng điểm có thể hiện ngay sau khi vào trận)
    cands = [start_sec + int(f * dur) for f in fracs]
    cands = [min(max(c, start_sec + 0), end_sec - 1) for c in cands]
    # loại trùng và sắp xếp
    seen = set()
    order = []
    for c in cands:
        if c not in seen:
            seen.add(c)
            order.append(c)

    def _call(ts):
        img = extract_full_frame(video_path, ts)
        if img is None:
            return None
        return gt.extract_title_with_gemini(client, img, preferred_model=model, sport="pickleball")

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
        for ts in order:
            fut = ex.submit(_call, ts)
            try:
                title = fut.result(timeout=45)
            except concurrent.futures.TimeoutError:
                # huỷ bỏ gọi lần này và thử mốc khác
                fut.cancel()
                continue
            except Exception:
                continue
            if plausible(title):
                return title, ts
    return None, None


def main():
    if len(sys.argv) < 3:
        print("Cách dùng: python fix_timeline.py <video.mp4> <timeline.txt>")
        sys.exit(1)
    video_path = sys.argv[1]
    tl_path = sys.argv[2]
    model = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")

    if not os.path.exists(video_path):
        print(f"[!] Không tìm thấy video: {video_path}")
        sys.exit(1)
    if not os.path.exists(tl_path):
        print(f"[!] Không tìm thấy timeline: {tl_path}")
        sys.exit(1)

    client = gt.get_gemini_client()
    if not client:
        sys.exit(1)

    # Lấy tổng duration từ video
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    total_duration = int(total_frames / (fps if fps > 0 else 30))
    cap.release()

    lines = open(tl_path, "r", encoding="utf-8").read().splitlines()
    out_lines = []
    fixed = 0
    trash_count = 0

    for i, line in enumerate(lines, 1):
        m = TL_RE.match(line)
        if not m:
            out_lines.append(line)
            continue
        start, end, raw = m.group(1), m.group(2), m.group(3)
        if not is_trash(raw):
            out_lines.append(line)
            continue

        trash_count += 1
        print(f"\n[{i}] TRÁN RÁC: {start} -> {end}", flush=True)
        st, en = to_sec(start), to_sec(end)
        title, used_ts = probe_match(video_path, client, st, en, model, total_duration)
        if title is None:
            print(f"    [!] Vẫn không đọc được. GIỮ NGUYÊN dòng rác.", flush=True)
            out_lines.append(line)
        else:
            print(f"    [OK] @ {gt.format_timestamp(used_ts)} : {title}", flush=True)
            out_lines.append(f"{start} - {end} - {title}")
            fixed += 1

    # Ghi đè lại timeline (giữ BOM nếu có? mở utf-8-sig để đọc, ghi utf-8-sig để bảo toàn)
    with open(tl_path, "r", encoding="utf-8-sig", newline="") as f:
        had_bom = f.read(1) == "\ufeff"
    newline_style = "\r\n" if "\r\n" in "\n".join(lines) else "\n"
    with open(tl_path, "w", encoding="utf-8-sig", newline="") as f:
        f.write("\ufeff" if had_bom else "")
        f.write(newline_style.join(out_lines))
        f.write("\n")

    print(f"\n=== XONG: {fixed}/{trash_count} dòng rác đã sửa ===")


if __name__ == "__main__":
    main()
