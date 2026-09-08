import cv2, os, sys
from PIL import Image

sys.path.insert(0, r"E:\www\DaliSports-Pipeline\system")
import gemini_rotator

sys.stdout.reconfigure(encoding='utf-8')

video_path = r"C:\Temp\Mochi\mochi_full.mp4"
cap = cv2.VideoCapture(video_path)

# Danh sách 12 trận đấu cần định vị mốc thời gian bắt đầu & kết thúc
matches_to_find = [
    # Đôi Hỗn Hợp 4.4
    ("doi-hon-hop-4-4", "Bán Kết 1", "Mạnh Thắng / Tuấn Minh vs Hưng Kai / Trịnh Tiến Thành"),
    ("doi-hon-hop-4-4", "Bán Kết 2", "Phạm Tuấn Hiệp / Minh Khoáng vs Dương Nguyễn / Tiến Đạt"),
    ("doi-hon-hop-4-4", "Chung Kết", "Mạnh Thắng / Tuấn Minh vs Phạm Tuấn Hiệp / Minh Khoáng"),

    # Đôi Nữ 4.0
    ("doi-nu-4-0", "Bán Kết 1", "Hoa Đấm / Lê Minh Phương vs Đào Hà ( Hà Nhi) / Ngô Hiền"),
    ("doi-nu-4-0", "Bán Kết 2", "Mừng Baby / Khánh Hà vs Minh Phương / Kiều Oanh"),
    ("doi-nu-4-0", "Chung Kết", "Hoa Đấm / Lê Minh Phương vs Minh Phương / Kiều Oanh"),

    # Đôi Nam Nữ 4.2
    ("doi-nam-nu-4-2", "Bán Kết 1", "Lê Ngọc Anh / Bùi Hồng Vân vs Trần Phượng 68 / Vũ Ngọc Nghĩa"),
    ("doi-nam-nu-4-2", "Bán Kết 2", "Phạm Văn Cường / Phạm Thị Thu vs Dương Nguyễn / Nguyễn Gia Nhi"),
    ("doi-nam-nu-4-2", "Chung Kết", "Trần Phượng 68 / Vũ Ngọc Nghĩa vs Dương Nguyễn / Nguyễn Gia Nhi"),

    # Đôi Hỗn Hợp 4.8
    ("doi-hon-hop-4-8", "Bán Kết 1", "Chinh Vũ Gia / Chiến Khói vs Nguyễn Văn Giáp / Nguyễn Văn Hà"),
    ("doi-hon-hop-4-8", "Bán Kết 2", "Bin / Trần Quang Trung vs Thắng PA / Lê Tấn Phát 2012"),
    ("doi-hon-hop-4-8", "Chung Kết", "Chinh Vũ Gia / Chiến Khói vs Bin / Trần Quang Trung"),
]

# Quét kỹ từng 3 phút để tìm đúng banner hiển thị tên các cặp đấu trên
prompt = """Bạn là chuyên gia soi bảng điểm trận đấu Pickleball.
Hãy kiểm tra màn hình xem có bảng điểm / banner hiển thị tên VĐV thi đấu hay không.
Nếu có, ghi rõ tên các VĐV hiển thị trên màn hình.
Nếu không có, ghi KHONG_THAY."""

print("[+] Quét chi tiết các mốc 3 phút...")
results = []
for sec in range(60, 27300, 180): # 3 phút 1 lần
    cap.set(cv2.CAP_PROP_POS_MSEC, sec * 1000)
    ret, frame = cap.read()
    if not ret: continue
    
    t_str = f"{sec//3600:02d}:{(sec%3600)//60:02d}:{sec%60:02d}"
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(rgb)
    
    text, meta = gemini_rotator.GeminiRotator.generate_vision_sync(
        prompt_text=prompt,
        image_input=img,
        preferred_model="gemini-3.6-flash"
    )
    res = text.strip() if text else "KHONG_THAY"
    if "KHONG_THAY" not in res and "không" not in res.lower():
        print(f"[{t_str}] -> {res}\n")
        results.append((sec, t_str, res))

cap.release()

with open(r"E:\www\DaliSports-Pipeline\fine_match_scan.txt", "w", encoding="utf-8") as f:
    for sec, t_str, res in results:
        f.write(f"{sec} | {t_str} | {res}\n")

print("Done fine match scan.")
