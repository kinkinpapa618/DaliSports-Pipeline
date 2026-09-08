import cv2, os, sys
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image

sys.path.insert(0, r"E:\www\DaliSports-Pipeline\system")
import gemini_rotator

# 12 trận đấu cần tìm và thông tin định vị mong muốn
target_matches = [
    # Đôi Hỗn Hợp 4.4
    {"cat": "doi-hon-hop-4-4", "round": "Bán Kết 1", "players": "Mạnh Thắng / Tuấn Minh vs Hưng Kai / Trịnh Tiến Thành"},
    {"cat": "doi-hon-hop-4-4", "round": "Bán Kết 2", "players": "Phạm Tuấn Hiệp / Minh Khoáng vs Dương Nguyễn / Tiến Đạt"},
    {"cat": "doi-hon-hop-4-4", "round": "Chung Kết", "players": "Mạnh Thắng / Tuấn Minh vs Phạm Tuấn Hiệp / Minh Khoáng"},

    # Đôi Nữ 4.0
    {"cat": "doi-nu-4-0", "round": "Bán Kết 1", "players": "Hoa Đấm / Lê Minh Phương vs Đào Hà ( Hà Nhi) / Ngô Hiền"},
    {"cat": "doi-nu-4-0", "round": "Bán Kết 2", "players": "Mừng Baby / Khánh Hà vs Minh Phương / Kiều Oanh"},
    {"cat": "doi-nu-4-0", "round": "Chung Kết", "players": "Hoa Đấm / Lê Minh Phương vs Minh Phương / Kiều Oanh"},

    # Đôi Nam Nữ 4.2
    {"cat": "doi-nam-nu-4-2", "round": "Bán Kết 1", "players": "Lê Ngọc Anh / Bùi Hồng Vân vs Trần Phượng 68 / Vũ Ngọc Nghĩa"},
    {"cat": "doi-nam-nu-4-2", "round": "Bán Kết 2", "players": "Phạm Văn Cường / Phạm Thị Thu vs Dương Nguyễn / Nguyễn Gia Nhi"},
    {"cat": "doi-nam-nu-4-2", "round": "Chung Kết", "players": "Trần Phượng 68 / Vũ Ngọc Nghĩa vs Dương Nguyễn / Nguyễn Gia Nhi"},

    # Đôi Hỗn Hợp 4.8
    {"cat": "doi-hon-hop-4-8", "round": "Bán Kết 1", "players": "Chinh Vũ Gia / Chiến Khói vs Nguyễn Văn Giáp / Nguyễn Văn Hà"},
    {"cat": "doi-hon-hop-4-8", "round": "Bán Kết 2", "players": "Bin / Trần Quang Trung vs Thắng PA / Lê Tấn Phát 2012"},
    {"cat": "doi-hon-hop-4-8", "round": "Chung Kết", "players": "Chinh Vũ Gia / Chiến Khói vs Bin / Trần Quang Trung"},
]

# Các timestamp có std cao (banner popup) thu thập từ scan_banners
candidate_timestamps = [
    # [s, format_time, std]
    (30, "00:00:30"), (1190, "00:19:50"), (1465, "00:24:25"), (1915, "00:31:55"), (3400, "00:56:40"),
    (4790, "01:19:50"), (4970, "01:22:50"), (5445, "01:30:45"), (6515, "01:48:35"), (7600, "02:06:40"),
    (8690, "02:24:50"), (9940, "02:45:40"), (11340, "03:09:00"), (12450, "03:27:30"), (15270, "04:14:30"),
    (16725, "04:38:45"), (18555, "05:09:15"), (20660, "05:44:20"), (21745, "06:02:25"), (24830, "06:53:50"),
    (26345, "07:15:35"), (26585, "07:19:05"), (27375, "07:36:15")
]

video_path = r"C:\Temp\Mochi\mochi_full.mp4"
cap = cv2.VideoCapture(video_path)

print("[+] Đang dùng Gemini OCR nhận diện thông tin trận từ các banner...")

prompt = """Đọc bảng điểm / banner giới thiệu trận đấu ở nửa dưới hoặc trên hình ảnh này.
Hãy trả về duy nhất 1 dòng text ghi rõ: NỘI DUNG THI ĐẤU | VÒNG ĐẤU | TÊN ĐỘI 1 vs TÊN ĐỘI 2
Nếu không có bảng điểm, ghi KHONG_THAY."""

ocr_results = []
for sec, ts_str in candidate_timestamps:
    cap.set(cv2.CAP_PROP_POS_MSEC, sec * 1000)
    ret, frame = cap.read()
    if not ret: continue
    
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(rgb)
    
    text, meta = gemini_rotator.GeminiRotator.generate_vision_sync(
        prompt_text=prompt,
        image_input=img,
        preferred_model="gemini-3.6-flash"
    )
    res_text = text.strip() if text else "KHONG_THAY"
    print(f"[{ts_str}] -> {res_text}")
    ocr_results.append((sec, ts_str, res_text))

cap.release()

with open(r"E:\www\DaliSports-Pipeline\banner_ocr_results.txt", "w", encoding="utf-8") as f:
    for sec, ts_str, res in ocr_results:
        f.write(f"{sec} | {ts_str} | {res}\n")

print("\n[+] Đã hoàn thành OCR các banner!")
