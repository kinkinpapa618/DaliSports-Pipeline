#!/usr/bin/env python3
import os
import sys
import time
import re
import json
import cv2
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
RAW_DATA_FILE = "raw_ocr_caulong.json"
TIMELINE_OUT = "cau_long_ttbc_timeline.txt"
TIMELINE_NORMS_OUT = "cau_long_ttbc_timeline_norms.txt"

TOURNAMENT_NAME = "GIẢI CẦU LÔNG THANH THIẾU NIÊN TRANH CÚP TTBC - LẦN THỨ I - 2026"

PROMPT = """Trích xuất thông tin trận đấu cầu lông từ ảnh bảng điểm/scoreboard:
Định dạng chính xác 1 dòng:
HẠNG MỤC | TÊN ĐỘI 1 vs TÊN ĐỘI 2

Ví dụ:
U15 ĐƠN NAM PT | NGUYỄN VĂN THUYẾT vs NGÔ VĂN MẠNH
U18 ĐÔI NAM PT | BÙI GIA THÀNH / NGUYỄN DUY KHÁNH vs DƯƠNG VĂN GIA HUY / BÙI DUY TÙNG
U15 ĐƠN NỮ PT | TRẦN MAI TRANG vs TẠ MINH THU

Quy tắc:
1. Nếu ảnh không có bảng điểm, hoặc đang khởi động / nghỉ / trao giải không có tên VĐV cụ thể, hãy trả về đúng chữ: KHONG_CO_TRAN
2. Nếu có số thứ tự (ví dụ "10. U15 ĐƠN NAM PT"), bỏ số thứ tự "10. ", chỉ giữ "U15 ĐƠN NAM PT".
3. Trả về đúng 1 dòng text, không markdown block (```), không thêm giải thích."""

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

def scan_and_save_raw():
    api_key = os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)

    cap = cv2.VideoCapture(VIDEO_PATH)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = int(total_frames / fps)
    
    # Sample every 30 seconds for higher precision
    step_sec = 30
    timestamps = list(range(0, duration, step_sec))
    print(f"[*] Trích xuất {len(timestamps)} frames (mỗi {step_sec}s)...", flush=True)

    frames_dict = {}
    for s in timestamps:
        cap.set(cv2.CAP_PROP_POS_MSEC, s * 1000)
        ret, frame = cap.read()
        if ret:
            frames_dict[s] = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    cap.release()
    print(f"[+] Đã trích xuất {len(frames_dict)} frames.", flush=True)

    print("[*] Đang gửi AI OCR song song (20 workers)...", flush=True)
    raw_results = {}

    def query(ts, img):
        for model in ["gemini-3.6-flash", "gemini-2.5-flash-lite"]:
            try:
                res = client.models.generate_content(model=model, contents=[img, PROMPT])
                txt = clean_title(res.text)
                return ts, txt
            except Exception:
                time.sleep(0.5)
        return ts, "KHONG_CO_TRAN"

    start_time = time.time()
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(query, ts, frames_dict[ts]) for ts in timestamps if ts in frames_dict]
        done = 0
        for f in as_completed(futures):
            ts, txt = f.result()
            raw_results[str(ts)] = txt
            done += 1
            if done % 50 == 0 or done == len(timestamps):
                print(f"    -> Đã xong {done}/{len(timestamps)} ({done/len(timestamps)*100:.0f}%)", flush=True)

    print(f"[+] AI OCR xong trong {time.time() - start_time:.1f}s!", flush=True)

    with open(RAW_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(raw_results, f, ensure_ascii=False, indent=2)
    print(f"[+] Đã lưu dữ liệu thô vào: {RAW_DATA_FILE}", flush=True)
    return raw_results

def process_timeline(raw_results=None):
    if raw_results is None:
        if not os.path.exists(RAW_DATA_FILE):
            print(f"[!] Không tìm thấy {RAW_DATA_FILE}")
            return
        with open(RAW_DATA_FILE, "r", encoding="utf-8") as f:
            raw_results = json.load(f)

    # Chuyển timestamp về int và sắp xếp
    data = []
    for k, v in raw_results.items():
        data.append((int(k), v))
    data.sort(key=lambda x: x[0])

    print("\n--- TẤT CẢ CÁC ĐIỂM CÓ BẢNG ĐIỂM ---")
    active_points = []
    for ts, txt in data:
        if "KHONG_CO_TRAN" not in txt and "KHONG_DOC_DUOC" not in txt and "vs" in txt.lower():
            active_points.append((ts, txt))
            print(f"{fmt(ts)} ({ts:05d}s): {txt}")

    # Nhóm các điểm thành từng trận đấu dựa trên tên VĐV tương tự và khoảng cách thời gian
    matches = []
    for ts, txt in active_points:
        # Tách tên cầu thủ
        parts = txt.split("|")
        cat = parts[0].strip()
        players = parts[-1].strip()

        # Chuẩn hóa tên VĐV để so sánh
        clean_p = re.sub(r"[^a-zA-Z0-9\s/]", "", players.lower()).strip()

        # Kiểm tra xem có thuộc trận đấu đang xét không
        matched = False
        if matches:
            last_m = matches[-1]
            last_p = re.sub(r"[^a-zA-Z0-9\s/]", "", last_m["players"].lower()).strip()
            
            # Nếu cách trận trước <= 5 phút (300s) và tên VĐV tương tự
            time_gap = ts - last_m["end_sec"]
            # So sánh từ khóa chính trong tên VĐV
            p_words_last = set(last_p.split()) - {"vs", "a", "b", "c"}
            p_words_cur = set(clean_p.split()) - {"vs", "a", "b", "c"}
            overlap = len(p_words_last.intersection(p_words_cur))

            if time_gap <= 300 and (overlap >= 2 or last_p in clean_p or clean_p in last_p):
                last_m["end_sec"] = ts
                last_m["samples"].append((ts, txt))
                if len(txt) > len(last_m["best_title"]):
                    last_m["best_title"] = txt
                    last_m["category"] = cat
                    last_m["players"] = players
                matched = True

        if not matched:
            matches.append({
                "start_sec": ts,
                "end_sec": ts,
                "best_title": txt,
                "category": cat,
                "players": players,
                "samples": [(ts, txt)]
            })

    print(f"\n==========================================")
    print(f"TỔNG SỐ TRẬN ĐẤU ĐƯỢC TỔNG HỢP: {len(matches)}")
    print(f"==========================================")

    try:
        from normalize import normalize_title
    except ImportError:
        def normalize_title(t): return t

    raw_lines = []
    norm_lines = []

    for idx, m in enumerate(matches, 1):
        st = max(0, m["start_sec"] - 15)
        en = m["end_sec"] + 30
        
        # Trận đầu nếu <= 3 phút thì kéo về 00:00:00
        if idx == 1 and st <= 180:
            st = 0

        st_s = fmt(st)
        en_s = fmt(en)
        dur = en - st

        full_raw = f"{TOURNAMENT_NAME} | {m['best_title']}"
        full_norm = normalize_title(full_raw)

        raw_line = f"{st_s} - {en_s} - {full_raw}"
        norm_line = f"{st_s} - {en_s} - {full_norm}"

        raw_lines.append(raw_line)
        norm_lines.append(norm_line)

        print(f"\nTRẬN {idx:02d}: {st_s} -> {en_s} (Thời lượng: {dur//60}m{dur%60:02d}s, {len(m['samples'])} frames)")
        print(f"  Tiêu đề gốc:      {full_raw}")
        print(f"  Tiêu đề chuẩn hóa: {full_norm}")

    with open(TIMELINE_OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(raw_lines) + "\n")

    with open(TIMELINE_NORMS_OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(norm_lines) + "\n")

    print(f"\n[+] ĐÃ LƯU FILE TIMELINE:")
    print(f"    - File gốc:       {TIMELINE_OUT}")
    print(f"    - File chuẩn hóa: {TIMELINE_NORMS_OUT}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--process-only":
        process_timeline()
    else:
        raw = scan_and_save_raw()
        process_timeline(raw)
