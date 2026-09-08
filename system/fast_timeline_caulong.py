#!/usr/bin/env python3
import os
import sys
import time
import re
import cv2
import numpy as np
from PIL import Image
from concurrent.futures import ThreadPoolExecutor, as_completed

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

PROMPT = """Trích xuất thông tin trận đấu cầu lông từ ảnh bảng điểm/scoreboard:
Định dạng chính xác 1 dòng duy nhất:
HẠNG MỤC | TÊN ĐỘI 1 vs TÊN ĐỘI 2

Ví dụ:
U15 ĐƠN NAM PT | NGUYỄN VĂN THUYẾT vs NGÔ VĂN MẠNH
U18 ĐÔI NAM PT | BÙI GIA THÀNH / NGUYỄN DUY KHÁNH vs DƯƠNG VĂN GIA HUY / BÙI DUY TÙNG
U15 ĐƠN NỮ PT | TRẦN MAI TRANG vs TẠ MINH THU

Quy tắc:
1. Nếu ảnh không có bảng điểm, màn hình nghỉ giữa hiệp/quảng cáo/trao giải/khởi động không có bảng điểm rõ ràng, hãy trả về đúng chữ: KHONG_CO_TRAN
2. Nếu là số thứ tự trận (ví dụ "10. U15 ĐƠN NAM PT"), hãy bỏ số thứ tự "10. " đi, chỉ giữ "U15 ĐƠN NAM PT".
3. Trả về đúng 1 dòng text, không markdown block (```), không thêm giải thích."""

def fmt(s: int) -> str:
    h = s // 3600
    m = (s % 3600) // 60
    sec = s % 60
    return f"{h:02d}:{m:02d}:{sec:02d}"

def to_sec(t_str: str) -> int:
    parts = [int(p) for p in t_str.strip().split(":")]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    elif len(parts) == 2:
        return parts[0] * 60 + parts[1]
    return parts[0]

def clean_title(text: str) -> str:
    text = text.replace("```markdown", "").replace("```", "").strip()
    if "\n" in text:
        text = text.split("\n")[0].strip()
    # Remove match index numbers like "10. ", "14. ", "15. " at the start of category
    text = re.sub(r"^\d+\.\s*", "", text)
    # Also inside category if separated by |
    parts = text.split("|")
    if len(parts) >= 2:
        parts[0] = re.sub(r"^\d+\.\s*", "", parts[0].strip())
        text = " | ".join([p.strip() for p in parts])
    return text

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("[!] Không tìm thấy GEMINI_API_KEY trong .env")
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    cap = cv2.VideoCapture(VIDEO_PATH)
    if not cap.isOpened():
        print(f"[!] Không mở được video: {VIDEO_PATH}")
        sys.exit(1)

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = int(total_frames / fps)
    print(f"[*] Video: {VIDEO_PATH} | Thời lượng: {fmt(duration)} ({duration}s)")

    # 1. Trích xuất frames mỗi 45s
    step_sec = 45
    timestamps = list(range(0, duration, step_sec))
    print(f"[*] Trích xuất {len(timestamps)} frames (mỗi {step_sec}s)...")

    frames_dict = {}
    for s in timestamps:
        cap.set(cv2.CAP_PROP_POS_MSEC, s * 1000)
        ret, frame = cap.read()
        if ret:
            frames_dict[s] = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

    cap.release()
    print(f"[+] Đã trích xuất {len(frames_dict)} frames thành công.")

    # 2. Gọi Gemini 3.6 Flash song song (ThreadPoolExecutor 10 threads)
    print("[*] Đang nhận diện bảng điểm song song với Gemini 3.6 Flash...")
    results = {}

    def query_frame(ts, img):
        for model in ["gemini-3.6-flash", "gemini-2.5-flash-lite"]:
            try:
                res = client.models.generate_content(model=model, contents=[img, PROMPT])
                txt = clean_title(res.text)
                return ts, txt
            except Exception as e:
                time.sleep(1)
        return ts, "KHONG_CO_TRAN"

    start_time = time.time()
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(query_frame, ts, frames_dict[ts]) for ts in timestamps if ts in frames_dict]
        done_count = 0
        for f in as_completed(futures):
            ts, txt = f.result()
            results[ts] = txt
            done_count += 1
            if done_count % 25 == 0 or done_count == len(timestamps):
                print(f"    -> Đã xử lý {done_count}/{len(timestamps)} frames ({(done_count/len(timestamps))*100:.0f}%)", flush=True)

    elapsed = time.time() - start_time
    print(f"[+] Hoàn thành AI OCR trong {elapsed:.1f}s!", flush=True)

    # 3. Phân tích chuỗi kết quả và gom nhóm trận đấu
    sorted_ts = sorted(results.keys())
    
    current_match = None
    matches = [] # list of {"title": str, "start_sec": int, "end_sec": int, "samples": list}

    for ts in sorted_ts:
        txt = results[ts]
        if "KHONG_CO_TRAN" in txt or "KHONG_DOC_DUOC" in txt or "vs" not in txt.lower():
            key = None
        else:
            key = txt.strip()

        if key:
            if current_match is None:
                current_match = {"title": key, "start_sec": ts, "end_sec": ts, "samples": [ts]}
            else:
                p_cur = current_match["title"].split("|")[-1].strip().lower()
                p_new = key.split("|")[-1].strip().lower()
                
                # Check if same players
                if p_cur == p_new or (len(p_cur) > 5 and p_cur in p_new) or (len(p_new) > 5 and p_new in p_cur):
                    current_match["end_sec"] = ts
                    current_match["samples"].append(ts)
                    if len(key) > len(current_match["title"]):
                        current_match["title"] = key
                else:
                    matches.append(current_match)
                    current_match = {"title": key, "start_sec": ts, "end_sec": ts, "samples": [ts]}
        else:
            if current_match is not None:
                # If gap > 90s, close current match
                if ts - current_match["end_sec"] >= 90:
                    matches.append(current_match)
                    current_match = None

    if current_match is not None:
        matches.append(current_match)

    valid_matches = []
    for m in matches:
        dur = m["end_sec"] - m["start_sec"]
        if dur >= 90 or len(m["samples"]) >= 2:
            st = max(0, m["start_sec"] - 20)
            en = min(duration, m["end_sec"] + 30)
            valid_matches.append({
                "start_sec": st,
                "end_sec": en,
                "title": m["title"]
            })

    if valid_matches and valid_matches[0]["start_sec"] <= 120:
        valid_matches[0]["start_sec"] = 0

    print(f"\n[+] Phát hiện {len(valid_matches)} trận đấu hợp lệ:", flush=True)
    raw_lines = []
    norm_lines = []

    try:
        from normalize import normalize_title
    except ImportError:
        def normalize_title(t): return t

    for idx, m in enumerate(valid_matches, 1):
        st_s = fmt(m["start_sec"])
        en_s = fmt(m["end_sec"])
        dur = m["end_sec"] - m["start_sec"]
        
        full_title = f"{TOURNAMENT_NAME} | {m['title']}"
        raw_line = f"{st_s} - {en_s} - {full_title}"
        raw_lines.append(raw_line)

        norm_title = normalize_title(full_title)
        norm_line = f"{st_s} - {en_s} - {norm_title}"
        norm_lines.append(norm_line)

        print(f"[{idx:02d}] {st_s} -> {en_s} ({dur//60}m{dur%60:02d}s)", flush=True)
        print(f"     Raw:  {full_title}", flush=True)
        print(f"     Norm: {norm_title}", flush=True)

    with open(TIMELINE_OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(raw_lines) + "\n")
    print(f"\n[+] Đã lưu timeline gốc vào: {TIMELINE_OUT}", flush=True)

    with open(TIMELINE_NORMS_OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(norm_lines) + "\n")
    print(f"[+] Đã lưu timeline chuẩn hóa vào: {TIMELINE_NORMS_OUT}", flush=True)

if __name__ == "__main__":
    main()
