#!/usr/bin/env python3
import os
import sys
import time
import re
import cv2
import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from google import genai

VIDEO_PATH = "caulong_ttbc.mp4"
TIMELINE_OUT = "cau_long_ttbc_timeline.txt"
TIMELINE_NORMS_OUT = "cau_long_ttbc_timeline_norms.txt"

TOURNAMENT_NAME = "GIẢI CẦU LÔNG THANH THIẾU NIÊN TRANH CÚP TTBC - LẦN THỨ I - 2026"

AVAILABLE_MODELS = [
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.6-flash",
    "gemini-3.7-flash",
    "gemini-flash-latest",
    "gemini-flash-lite-latest",
    "gemini-3.1-flash-lite"
]

PROMPT = """Bạn là chuyên gia thể thao trích xuất thông tin trận đấu cầu lông từ hình ảnh scoreboard / banner:
Định dạng kết quả chính xác 1 dòng duy nhất:
HẠNG MỤC | TÊN ĐỘI 1 vs TÊN ĐỘI 2

Ví dụ:
U15 ĐƠN NAM PT | NGUYỄN VĂN THUYẾT vs NGÔ VĂN MẠNH
U18 ĐÔI NAM PT | BÙI GIA THÀNH / NGUYỄN DUY KHÁNH vs DƯƠNG VĂN GIA HUY / BÙI DUY TÙNG
U15 ĐƠN NỮ PT | TRẦN MAI TRANG vs TẠ MINH THU

Quy tắc:
1. Nếu có số thứ tự đầu hạng mục (ví dụ "10. U15 ĐƠN NAM PT"), bỏ số thứ tự "10. ", chỉ lấy "U15 ĐƠN NAM PT".
2. Nếu ảnh không có bảng điểm rõ ràng hoặc không đọc được, trả về: KHONG_DOC_DUOC
3. Chỉ trả về đúng 1 dòng text, không markdown, không giải thích."""

def fmt(s: int) -> str:
    h = s // 3600
    m = (s % 3600) // 60
    sec = s % 60
    return f"{h:02d}:{m:02d}:{sec:02d}"

def clean_title(text: str) -> str:
    text = text.replace("```markdown", "").replace("```", "").strip()
    if "\n" in text:
        text = text.split("\n")[0].strip()
    text = re.sub(r"^\d+\.\s*", "", text)
    parts = text.split("|")
    if len(parts) >= 2:
        parts[0] = re.sub(r"^\d+\.\s*", "", parts[0].strip())
        text = " | ".join([p.strip() for p in parts])
    return text

def detect_segments(video_path, step_sec=5, min_dur=50, merge_gap=35):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"[!] Không mở được video: {video_path}")
        return []

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = int(total_frames / fps)
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Top-left region
    y1, y2 = int(0.01 * H), int(0.20 * H)
    x1, x2 = int(0.03 * W), int(0.35 * W)

    print(f"[*] Quét phát hiện bảng điểm: {video_path} (Thời lượng: {fmt(duration)})...", flush=True)
    active_points = []

    for s in range(0, duration, step_sec):
        cap.set(cv2.CAP_PROP_POS_MSEC, s * 1000)
        ret, frame = cap.read()
        if not ret: break
        crop = frame[y1:y2, x1:x2]
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        std = np.std(gray)
        if std >= 45:
            active_points.append((s, std))

    cap.release()

    if not active_points:
        return []

    # Gom nhóm
    raw_groups = []
    cur = [active_points[0]]
    for pt in active_points[1:]:
        s, std = pt
        if s - cur[-1][0] <= merge_gap:
            cur.append(pt)
        else:
            st = cur[0][0]
            en = cur[-1][0]
            if en - st >= min_dur:
                best_sec = max(cur, key=lambda x: x[1])[0]
                raw_groups.append((st, en, best_sec))
            cur = [pt]

    if cur:
        st = cur[0][0]
        en = cur[-1][0]
        if en - st >= min_dur:
            best_sec = max(cur, key=lambda x: x[1])[0]
            raw_groups.append((st, en, best_sec))

    return raw_groups

def query_gemini(client, img):
    from gemini_rotator import GeminiRotator
    text, meta = GeminiRotator.generate_vision_sync(PROMPT, img)
    if text:
        txt = clean_title(text)
        if txt and "không thể" not in txt.lower() and "KHONG_DOC_DUOC" not in txt:
            return txt
    return "KHONG_DOC_DUOC"

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)

    segments = detect_segments(VIDEO_PATH, step_sec=5, min_dur=50, merge_gap=35)
    print(f"[+] Phát hiện {len(segments)} phân đoạn bảng điểm tiềm năng:")
    for i, (st, en, best_sec) in enumerate(segments, 1):
        print(f"    [{i:02d}] {fmt(st)} -> {fmt(en)} (best={fmt(best_sec)})")

    # Mở video để trích xuất frame cho từng phân đoạn
    cap = cv2.VideoCapture(VIDEO_PATH)
    matches = []

    print("\n[*] Đang gửi AI nhận diện bảng điểm cho từng phân đoạn...")
    for idx, (st, en, best_sec) in enumerate(segments, 1):
        # Trích frame tại best_sec
        cap.set(cv2.CAP_PROP_POS_MSEC, best_sec * 1000)
        ret, frame = cap.read()
        if not ret:
            print(f"    [{idx:02d}] Lỗi đọc frame tại {fmt(best_sec)}")
            continue

        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        title = query_gemini(client, img)

        # Nếu không đọc được, thử thêm 1/3 và 2/3 phân đoạn
        if title == "KHONG_DOC_DUOC" or "vs" not in title.lower():
            for frac in [0.33, 0.66]:
                mid = st + int((en - st) * frac)
                cap.set(cv2.CAP_PROP_POS_MSEC, mid * 1000)
                ret2, f2 = cap.read()
                if ret2:
                    img2 = Image.fromarray(cv2.cvtColor(f2, cv2.COLOR_BGR2RGB))
                    t2 = query_gemini(client, img2)
                    if t2 != "KHONG_DOC_DUOC" and "vs" in t2.lower():
                        title = t2
                        break

        print(f"    [{idx:02d}] {fmt(st)} -> {fmt(en)}: {title}", flush=True)
        time.sleep(0.5)

        if title != "KHONG_DOC_DUOC" and "vs" in title.lower():
            # Tinh chỉnh thời gian bắt đầu và kết thúc
            adj_st = 0 if (idx == 1 and st <= 180) else max(0, st - 5)
            adj_en = en + 10
            matches.append({
                "start": adj_st,
                "end": adj_en,
                "title": title
            })

    cap.release()

    # Nhóm các đoạn trùng tên (nếu có trận bị tách đôi)
    merged_matches = []
    for m in matches:
        if merged_matches:
            prev = merged_matches[-1]
            p_prev = prev["title"].split("|")[-1].strip().lower()
            p_cur = m["title"].split("|")[-1].strip().lower()
            if p_prev == p_cur and (m["start"] - prev["end"] <= 180):
                prev["end"] = m["end"]
                continue
        merged_matches.append(m)

    print(f"\n=======================================================")
    print(f"DANH SÁCH {len(merged_matches)} TRẬN ĐẤU HOÀN CHỈNH:")
    print(f"=======================================================")

    try:
        from normalize import normalize_title
    except ImportError:
        def normalize_title(t): return t

    raw_lines = []
    norm_lines = []

    for idx, m in enumerate(merged_matches, 1):
        st_s = fmt(m["start"])
        en_s = fmt(m["end"])
        dur = m["end"] - m["start"]

        full_raw = f"{TOURNAMENT_NAME} | {m['title']}"
        full_norm = normalize_title(full_raw)

        raw_line = f"{st_s} - {en_s} - {full_raw}"
        norm_line = f"{st_s} - {en_s} - {full_norm}"

        raw_lines.append(raw_line)
        norm_lines.append(norm_line)

        print(f"\nTRẬN {idx:02d}: {st_s} -> {en_s} ({dur//60}m{dur%60:02d}s)")
        print(f"  Gốc:       {full_raw}")
        print(f"  Chuẩn hóa: {full_norm}")

    with open(TIMELINE_OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(raw_lines) + "\n")

    with open(TIMELINE_NORMS_OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(norm_lines) + "\n")

    print(f"\n[+] ĐÃ XUẤT TIMELINE THÀNH CÔNG:")
    print(f"    - {TIMELINE_OUT}")
    print(f"    - {TIMELINE_NORMS_OUT}")

if __name__ == "__main__":
    main()
