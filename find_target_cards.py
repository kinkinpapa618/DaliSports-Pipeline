import cv2, os, sys
from PIL import Image

sys.path.insert(0, r"E:\www\DaliSports-Pipeline\system")
import gemini_rotator

sys.stdout.reconfigure(encoding='utf-8')

video_path = r"C:\Temp\Mochi\mochi_full.mp4"
cap = cv2.VideoCapture(video_path)

# Danh sách 12 trận đấu cần cắt và từ khóa nhận diện VĐV
targets = [
    # Đôi Hỗn Hợp 4.4
    {"cat": "doi-hon-hop-4-4", "round": "Bán Kết 1", "title": "GIẢI PICKLEBALL THỦY MOCHI LẦN 1 NĂM 2026 | Đôi Hỗn Hợp 4.4 | Bán Kết 1 | Mạnh Thắng / Tuấn Minh vs Hưng Kai / Trịnh Tiến Thành", "kw": ["mạnh thắng", "tuấn minh", "hưng kai", "tiến thành"]},
    {"cat": "doi-hon-hop-4-4", "round": "Bán Kết 2", "title": "GIẢI PICKLEBALL THỦY MOCHI LẦN 1 NĂM 2026 | Đôi Hỗn Hợp 4.4 | Bán Kết 2 | Phạm Tuấn Hiệp / Minh Khoáng vs Dương Nguyễn / Tiến Đạt", "kw": ["tuấn hiệp", "minh khoáng", "dương nguyễn", "tiến đạt"]},
    {"cat": "doi-hon-hop-4-4", "round": "Chung Kết", "title": "GIẢI PICKLEBALL THỦY MOCHI LẦN 1 NĂM 2026 | Đôi Hỗn Hợp 4.4 | Chung Kết | Mạnh Thắng / Tuấn Minh vs Phạm Tuấn Hiệp / Minh Khoáng", "kw": ["mạnh thắng", "tuấn minh", "tuấn hiệp", "minh khoáng"]},

    # Đôi Nữ 4.0
    {"cat": "doi-nu-4-0", "round": "Bán Kết 1", "title": "GIẢI PICKLEBALL THỦY MOCHI LẦN 1 NĂM 2026 | Đôi Nữ 4.0 | Bán Kết 1 | Hoa Đấm / Lê Minh Phương vs Đào Hà ( Hà Nhi) / Ngô Hiền", "kw": ["hoa đấm", "minh phương", "đào hà", "hà nhi", "ngô hiền"]},
    {"cat": "doi-nu-4-0", "round": "Bán Kết 2", "title": "GIẢI PICKLEBALL THỦY MOCHI LẦN 1 NĂM 2026 | Đôi Nữ 4.0 | Bán Kết 2 | Mừng Baby / Khánh Hà vs Minh Phương / Kiều Oanh", "kw": ["mừng baby", "khánh hà", "minh phương", "kiều oanh"]},
    {"cat": "doi-nu-4-0", "round": "Chung Kết", "title": "GIẢI PICKLEBALL THỦY MOCHI LẦN 1 NĂM 2026 | Đôi Nữ 4.0 | Chung Kết | Hoa Đấm / Lê Minh Phương vs Minh Phương / Kiều Oanh", "kw": ["hoa đấm", "minh phương", "kiều oanh"]},

    # Đôi Nam Nữ 4.2
    {"cat": "doi-nam-nu-4-2", "round": "Bán Kết 1", "title": "GIẢI PICKLEBALL THỦY MOCHI LẦN 1 NĂM 2026 | Đôi Nam Nữ 4.2 | Bán Kết 1 | Lê Ngọc Anh / Bùi Hồng Vân vs Trần Phượng 68 / Vũ Ngọc Nghĩa", "kw": ["ngọc anh", "hồng vân", "trần phượng 68", "phượng 68", "ngọc nghĩa"]},
    {"cat": "doi-nam-nu-4-2", "round": "Bán Kết 2", "title": "GIẢI PICKLEBALL THỦY MOCHI LẦN 1 NĂM 2026 | Đôi Nam Nữ 4.2 | Bán Kết 2 | Phạm Văn Cường / Phạm Thị Thu vs Dương Nguyễn / Nguyễn Gia Nhi", "kw": ["văn cường", "phạm thị thu", "dương nguyễn", "gia nhi"]},
    {"cat": "doi-nam-nu-4-2", "round": "Chung Kết", "title": "GIẢI PICKLEBALL THỦY MOCHI LẦN 1 NĂM 2026 | Đôi Nam Nữ 4.2 | Chung Kết | Trần Phượng 68 / Vũ Ngọc Nghĩa vs Dương Nguyễn / Nguyễn Gia Nhi", "kw": ["trần phượng 68", "phượng 68", "ngọc nghĩa", "dương nguyễn", "gia nhi"]},

    # Đôi Hỗn Hợp 4.8
    {"cat": "doi-hon-hop-4-8", "round": "Bán Kết 1", "title": "GIẢI PICKLEBALL THỦY MOCHI LẦN 1 NĂM 2026 | Đôi Hỗn Hợp 4.8 | Bán Kết 1 | Chinh Vũ Gia / Chiến Khói vs Nguyễn Văn Giáp / Nguyễn Văn Hà", "kw": ["chinh vũ gia", "chiến khói", "văn giáp", "văn hà"]},
    {"cat": "doi-hon-hop-4-8", "round": "Bán Kết 2", "title": "GIẢI PICKLEBALL THỦY MOCHI LẦN 1 NĂM 2026 | Đôi Hỗn Hợp 4.8 | Bán Kết 2 | Bin / Trần Quang Trung vs Thắng PA / Lê Tấn Phát 2012", "kw": ["bin", "quang trung", "thắng pa", "tấn phát 2012"]},
    {"cat": "doi-hon-hop-4-8", "round": "Chung Kết", "title": "GIẢI PICKLEBALL THỦY MOCHI LẦN 1 NĂM 2026 | Đôi Hỗn Hợp 4.8 | Chung Kết | Chinh Vũ Gia / Chiến Khói vs Bin / Trần Quang Trung", "kw": ["chinh vũ gia", "chiến khói", "bin", "quang trung"]},
]

print("[+] Deep scanning intro cards for target matches...")

# Quét kỹ từng 10s khu vực nghi ngờ card SẮP DIỄN RA
prompt = """Đọc bảng card 'SẮP DIỄN RA' ở giữa dưới màn hình. Ghi rõ TÊN 4 VĐV hiển thị. Nếu không có card, ghi KHONG_THAY."""

found_matches = []

# Quét toàn bộ video theo từng 5s xem có card Intro không
for sec in range(0, 27500, 5):
    cap.set(cv2.CAP_PROP_POS_MSEC, sec * 1000)
    ret, frame = cap.read()
    if not ret: continue
    
    h, w, _ = frame.shape
    crop = frame[int(h*0.6):int(h*0.9), int(w*0.25):int(w*0.75)]
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    
    # Kiểm tra std màu card viền xanh sáng
    if gray.std() >= 48:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb)
        text, _ = gemini_rotator.GeminiRotator.generate_vision_sync(
            prompt_text=prompt,
            image_input=img,
            preferred_model="gemini-3.6-flash"
        )
        res = text.lower() if text else ""
        
        # So khớp với từng trận target
        for t in targets:
            match_score = sum(1 for k in t["kw"] if k in res)
            if match_score >= 2: # Tìm thấy ít nhất 2 từ khóa trùng khớp
                t_str = f"{sec//3600:02d}:{(sec%3600)//60:02d}:{sec%60:02d}"
                print(f"[MATCH CARD FOUND] {t['cat']} | {t['round']} @ {t_str} ({sec}s) -> {text.strip()}")
                found_matches.append((sec, t_str, t['cat'], t['round'], t['title'], text.strip()))

cap.release()

with open(r"E:\www\DaliSports-Pipeline\target_intro_cards.txt", "w", encoding="utf-8") as f:
    for item in found_matches:
        f.write(f"{item[0]} | {item[1]} | {item[2]} | {item[3]} | {item[4]} | {item[5]}\n")

print("\n[+] Done scanning target intro cards.")
