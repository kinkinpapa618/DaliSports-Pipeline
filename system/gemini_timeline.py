#!/usr/bin/env python3
# gemini_timeline.py - Tự động nhận diện mốc timeline trận đấu bằng Gemini Flash API (Cơ chế xoay tua 17 Keys & Đa Models)
# Quét video -> Phát hiện các khoảng thời gian thi đấu -> Trích xuất scoreboard -> Gọi Gemini AI -> Xuất file timeline.txt
import os
import sys
import argparse
import cv2
import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from gemini_rotator import GeminiRotator, RECOMMENDED_GEMINI_MODELS

FALLBACK_MODELS = RECOMMENDED_GEMINI_MODELS


def format_timestamp(sec: float) -> str:
    sec = int(round(sec))
    h = sec // 3600
    m = (sec % 3600) // 60
    s = sec % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def get_gemini_client(api_key: str = None):
    # Trả về GeminiRotator class
    return GeminiRotator


def detect_match_intervals_with_best_frames(video_path: str, step_sec: int = 6, min_duration: int = 600, merge_gap: int = 15):
    """
    Quét video theo chu kỳ step_sec để tìm các khoảng thời gian xuất hiện bảng điểm (Scoreboard),
    đồng thời lưu lại frame có độ nét/tương phản cao nhất cho mỗi trận.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"[!] Không thể mở video: {video_path}")
        return []

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = int(total_frames / (fps if fps > 0 else 30))
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Tọa độ vùng bảng điểm góc trên bên trái
    y1, y2 = int(0.01 * H), int(0.20 * H)
    x1, x2 = int(0.03 * W), int(0.35 * W)

    print(f"[*] Quét video: {os.path.basename(video_path)} | Thời lượng: {format_timestamp(duration)} ({duration}s)")
    active_points = [] # list of (sec, std)

    for s in range(0, duration, step_sec):
        cap.set(cv2.CAP_PROP_POS_MSEC, s * 1000)
        ret, frame = cap.read()
        if not ret:
            break
        crop = frame[y1:y2, x1:x2]
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        std = np.std(gray)

        # Bảng điểm có độ tương phản cao (chữ trắng, khung đen, điểm xanh) -> std >= 42
        if std >= 42:
            active_points.append((s, std))

    cap.release()

    if not active_points:
        return []

    # Gom các giây liên tục thành khoảng thời gian từng trận
    intervals = [] # list of (start_sec, end_sec, best_sec)
    cur_group = [active_points[0]]

    for pt in active_points[1:]:
        s, std = pt
        prev_s, _ = cur_group[-1]
        if s - prev_s <= merge_gap:
            cur_group.append(pt)
        else:
            st = cur_group[0][0]
            en = cur_group[-1][0]
            if en - st >= min_duration:
                best_sec = max(cur_group, key=lambda x: x[1])[0]
                intervals.append((st, en, best_sec))
            cur_group = [pt]

    if cur_group:
        st = cur_group[0][0]
        en = cur_group[-1][0]
        if en - st >= min_duration:
            best_sec = max(cur_group, key=lambda x: x[1])[0]
            intervals.append((st, en, best_sec))

    # Tinh chỉnh: nếu trận đầu tiên bắt đầu gần đầu video (< 5 phút), mở rộng về 00:00:00
    refined = []
    for idx, (st, en, best_sec) in enumerate(intervals):
        adj_st = 0 if (idx == 0 and st <= 300) else max(0, st - 5)
        adj_en = min(duration, en + 5)
        refined.append((adj_st, adj_en, best_sec))

    # Tách block lớn (>35 phút) thành nhiều trận nhỏ ~20 phút (vì mỗi trận 15-25p, bảng điểm hiển thị liên tục nên std không tách được)
    final = []
    for st, en, best_sec in refined:
        dur = en - st
        if dur > 35*60:
            # Chia thành n phần ~20 phút
            n = max(2, round(dur / (20*60)))
            seg_len = dur / n
            print(f"  [SPLIT] Block {format_timestamp(st)}-{format_timestamp(en)} ({dur//60}p) quá lớn -> chia {n} trận ~{int(seg_len//60)}p")
            for i in range(n):
                seg_st = int(st + i*seg_len)
                seg_en = int(st + (i+1)*seg_len) if i < n-1 else en
                # best_sec là giữa đoạn
                seg_best = (seg_st + seg_en)//2
                final.append((seg_st, seg_en, seg_best))
        else:
            final.append((st, en, best_sec))

    return final


def extract_match_frame(video_path: str, timestamp_sec: float) -> Image.Image:
    """Trich xuat FULL frame (khong crop) de Gemini tu doc bang diem o bat ky vi tri nao"""
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_MSEC, timestamp_sec * 1000)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        return None

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb)


def extract_title_with_gemini(client, image: Image.Image, preferred_model: str = None, sport: str = "cầu lông", api_key: str = None) -> str:
    """Gọi Gemini Flash API đọc nội dung banner scoreboard qua cơ chế xoay tua 17 Keys"""
    if sport == "pickleball":
        sport_vn = "pickleball"
    else:
        sport_vn = "cầu lông"
    prompt = f"""Bạn là chuyên gia trích xuất thông tin thể thao {sport_vn} từ hình ảnh.
Hãy quan sát kỹ ảnh bảng điểm / banner thi đấu {sport_vn} này và trích xuất thông tin chính xác:
1. Tên giải đấu và Năm (ví dụ: GIẢI {sport_vn.upper()} NỘI BỘ SÂN ĐỒNG HƯNG - SEN VÀNG 2026)
2. Nội dung / Hạng mục thi đấu (ví dụ: ĐÔI NAM, ĐÔI NỮ, ĐÔI NAM NỮ, ĐÔI NAM TRUNG, BẢNG A, TỨ KẾT, BÁN KẾT, CHUNG KẾT,...)
3. Tên hai đội / VĐV thi đấu:
   - Nếu là đôi: TÊN 1 / TÊN 2 vs TÊN 3 / TÊN 4
   - Nếu là đơn: TÊN 1 vs TÊN 2

Quy tắc xuất kết quả:
- Trả về đúng 1 dòng text duy nhất theo định dạng:
  TÊN GIẢI ĐẤU - NĂM | HẠNG MỤC | TÊN ĐỘI 1 vs TÊN ĐỘI 2
- Ví dụ: GIẢI {sport_vn.upper()} NỘI BỘ SÂN ĐỒNG HƯNG - SEN VÀNG | ĐÔI NAM | A VINH / THƯỞNG vs A ĐỨC / A ĐÔNG
- Nếu hình ảnh mờ, thiếu chữ hoặc không đọc được rõ, hãy trả đúng chuỗi: KHONG_DOC_DUOC
- Tuyệt đối không thêm giải thích, không dùng markdown block (```), chỉ trả về 1 dòng duy nhất."""

    content_text, meta = GeminiRotator.generate_vision_sync(
        prompt_text=prompt,
        image_input=image,
        preferred_model=preferred_model or "gemini-3.6-flash",
        custom_key=api_key
    )

    if content_text:
        text = content_text.strip()
        text = text.replace("```markdown", "").replace("```", "").strip()
        if "\n" in text:
            text = text.split("\n")[0].strip()
        if text and "không thể" not in text.lower():
            model_used = meta.get("model_used", "gemini")
            key_used = meta.get("key_used", "")
            print(f"        [OK model={model_used} | key={key_used}] {text}")
            return text
        else:
            print(f"        [WARN] empty/cannot: {text}")

    print(f"        [FAIL] Tất cả keys & models thất bại: {meta.get('last_error', 'Lỗi không xác định')}")
    return "KHONG_DOC_DUOC"


def generate_timeline(video_path: str, output_path: str = None, api_key: str = None, model: str = None, step_sec: int = 10):
    """Quy trình chính: Scan video -> Trích xuất mốc -> Đọc thông tin AI -> Ghi file timeline.txt"""
    if not os.path.exists(video_path):
        print(f"[!] Không tìm thấy video: {video_path}")
        return None

    if not output_path:
        base = os.path.splitext(video_path)[0]
        output_path = base + "_timeline.txt"

    client = get_gemini_client(api_key)

    intervals = detect_match_intervals_with_best_frames(video_path, step_sec=step_sec)
    if not intervals:
        print("[!] Không phát hiện được trận đấu nào từ video.")
        return None

    print(f"[+] Phát hiện {len(intervals)} trận đấu:")
    timeline_lines = []

    for idx, (st, en, best_sec) in enumerate(intervals, 1):
        st_str = format_timestamp(st)
        en_str = format_timestamp(en)
        dur = en - st

        # Dùng frame có chất lượng bảng điểm tốt nhất trong trận
        img = extract_match_frame(video_path, best_sec)

        title = "GIẢI CẦU LÔNG | ĐÔI NAM | VĐV A vs VĐV B"
        if img is not None:
            title = extract_title_with_gemini(client, img, preferred_model=model, api_key=api_key)

        line = f"{st_str} - {en_str} - {title}"
        timeline_lines.append(line)
        print(f"    [{idx:02d}] {st_str} -> {en_str} ({dur}s | sample @ {format_timestamp(best_sec)})\n         {title}")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(timeline_lines) + "\n")

    print(f"\n[+] Đã lưu timeline vào: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Tự động trích xuất timeline trận đấu bằng Gemini Flash API (Cơ chế xoay tua 17 Keys)")
    parser.add_argument("video", help="Đường dẫn file video .mp4")
    parser.add_argument("output", nargs="?", default=None, help="File timeline output (mặc định: <video>_timeline.txt)")
    parser.add_argument("--api-key", default=None, help="Gemini API Key (Tùy chọn, mặc định xoay tua 17 Keys)")
    parser.add_argument("--model", default="gemini-3.6-flash", help="Model Gemini sử dụng (mặc định: gemini-3.6-flash)")
    parser.add_argument("--step", type=int, default=10, help="Chu kỳ lấy mẫu frame (giây)")

    args = parser.parse_args()
    generate_timeline(args.video, args.output, api_key=args.api_key, model=args.model, step_sec=args.step)


if __name__ == "__main__":
    main()
