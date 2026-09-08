import os, sys, subprocess

sys.stdout.reconfigure(encoding='utf-8')

# BẢNG TÍNH TOÁN TIMELINE CHUẨN XÁC DỰA TRÊN INTRO CARD SẮP DIỄN RA:
# Quy tắc:
# - Start time: Trước khi Intro Card biến mất 5s (t_card_disappear - 5s)
# - End time: Trước khi Intro Card trận kế tiếp xuất hiện 5s (t_next_card_appear - 5s)

timeline_data = [
    # 1. Đôi Hỗn Hợp 4.4
    {
        "cat": "doi-hon-hop-4-4",
        "matches": [
            # Bán Kết 1: Mạnh Thắng / Tuấn Minh vs Hưng Kai / Trịnh Tiến Thành
            # Card biến mất lúc 01:32:15 -> Start = 01:32:10. Next card xuất hiện lúc 01:46:20 -> End = 01:46:15
            ("01:32:10", "01:46:15", "GIẢI PICKLEBALL THỦY MOCHI LẦN 1 NĂM 2026 | Đôi Hỗn Hợp 4.4 | Bán Kết 1 | Mạnh Thắng / Tuấn Minh vs Hưng Kai / Trịnh Tiến Thành"),
            
            # Bán Kết 2: Phạm Tuấn Hiệp / Minh Khoáng vs Dương Nguyễn / Tiến Đạt
            # Card biến mất lúc 02:33:00 -> Start = 02:32:55. Next card xuất hiện lúc 02:45:25 -> End = 02:45:20
            ("02:32:55", "02:45:20", "GIẢI PICKLEBALL THỦY MOCHI LẦN 1 NĂM 2026 | Đôi Hỗn Hợp 4.4 | Bán Kết 2 | Phạm Tuấn Hiệp / Minh Khoáng vs Dương Nguyễn / Tiến Đạt"),
            
            # Chung Kết: Mạnh Thắng / Tuấn Minh vs Phạm Tuấn Hiệp / Minh Khoáng
            # Card biến mất lúc 03:13:45 -> Start = 03:13:40. Next card xuất hiện lúc 03:26:55 -> End = 03:26:50
            ("03:13:40", "03:26:50", "GIẢI PICKLEBALL THỦY MOCHI LẦN 1 NĂM 2026 | Đôi Hỗn Hợp 4.4 | Chung Kết | Mạnh Thắng / Tuấn Minh vs Phạm Tuấn Hiệp / Minh Khoáng"),
        ]
    },
    # 2. Đôi Nữ 4.0
    {
        "cat": "doi-nu-4-0",
        "matches": [
            # Bán Kết 1: Hoa Đấm / Lê Minh Phương vs Đào Hà ( Hà Nhi) / Ngô Hiền
            # Card biến mất lúc 01:19:50 -> Start = 01:19:45. Next card xuất hiện lúc 01:29:55 -> End = 01:29:50
            ("01:19:45", "01:29:50", "GIẢI PICKLEBALL THỦY MOCHI LẦN 1 NĂM 2026 | Đôi Nữ 4.0 | Bán Kết 1 | Hoa Đấm / Lê Minh Phương vs Đào Hà ( Hà Nhi) / Ngô Hiền"),
            
            # Bán Kết 2: Mừng Baby / Khánh Hà vs Minh Phương / Kiều Oanh
            # Card biến mất lúc 04:08:05 -> Start = 04:08:00. Next card xuất hiện lúc 04:08:30 -> End = 04:08:25
            ("04:08:00", "04:08:25", "GIẢI PICKLEBALL THỦY MOCHI LẦN 1 NĂM 2026 | Đôi Nữ 4.0 | Bán Kết 2 | Mừng Baby / Khánh Hà vs Minh Phương / Kiều Oanh"),
            
            # Chung Kết: Hoa Đấm / Lê Minh Phương vs Minh Phương / Kiều Oanh
            # Card biến mất lúc 04:22:30 -> Start = 04:22:25. Next card xuất hiện lúc 04:37:55 -> End = 04:37:50
            ("04:22:25", "04:37:50", "GIẢI PICKLEBALL THỦY MOCHI LẦN 1 NĂM 2026 | Đôi Nữ 4.0 | Chung Kết | Hoa Đấm / Lê Minh Phương vs Minh Phương / Kiều Oanh"),
        ]
    },
    # 3. Đôi Nam Nữ 4.2
    {
        "cat": "doi-nam-nu-4-2",
        "matches": [
            # Bán Kết 1: Lê Ngọc Anh / Bùi Hồng Vân vs Trần Phượng 68 / Vũ Ngọc Nghĩa
            # Card biến mất lúc 03:32:00 -> Start = 03:31:55. Next card xuất hiện lúc 03:43:40 -> End = 03:43:35
            ("03:31:55", "03:43:35", "GIẢI PICKLEBALL THỦY MOCHI LẦN 1 NĂM 2026 | Đôi Nam Nữ 4.2 | Bán Kết 1 | Lê Ngọc Anh / Bùi Hồng Vân vs Trần Phượng 68 / Vũ Ngọc Nghĩa"),
            
            # Bán Kết 2: Phạm Văn Cường / Phạm Thị Thu vs Dương Nguyễn / Nguyễn Gia Nhi
            # Card biến mất lúc 01:00:30 -> Start = 01:00:25. Next card xuất hiện lúc 01:18:30 -> End = 01:18:25
            ("01:00:25", "01:18:25", "GIẢI PICKLEBALL THỦY MOCHI LẦN 1 NĂM 2026 | Đôi Nam Nữ 4.2 | Bán Kết 2 | Phạm Văn Cường / Phạm Thị Thu vs Dương Nguyễn / Nguyễn Gia Nhi"),
            
            # Chung Kết: Trần Phượng 68 / Vũ Ngọc Nghĩa vs Dương Nguyễn / Nguyễn Gia Nhi
            # Card biến mất lúc 07:20:40 -> Start = 07:20:35. Next card xuất hiện lúc 07:33:30 -> End = 07:33:25
            ("07:20:35", "07:33:25", "GIẢI PICKLEBALL THỦY MOCHI LẦN 1 NĂM 2026 | Đôi Nam Nữ 4.2 | Chung Kết | Trần Phượng 68 / Vũ Ngọc Nghĩa vs Dương Nguyễn / Nguyễn Gia Nhi"),
        ]
    },
    # 4. Đôi Hỗn Hợp 4.8
    {
        "cat": "doi-hon-hop-4-8",
        "matches": [
            # Bán Kết 1: Chinh Vũ Gia / Chiến Khói vs Nguyễn Văn Giáp / Nguyễn Văn Hà
            # Card biến mất lúc 05:17:30 -> Start = 05:17:25. Next card xuất hiện lúc 05:43:35 -> End = 05:43:30
            ("05:17:25", "05:43:30", "GIẢI PICKLEBALL THỦY MOCHI LẦN 1 NĂM 2026 | Đôi Hỗn Hợp 4.8 | Bán Kết 1 | Chinh Vũ Gia / Chiến Khói vs Nguyễn Văn Giáp / Nguyễn Văn Hà"),
            
            # Bán Kết 2: Bin / Trần Quang Trung vs Thắng PA / Lê Tấn Phát 2012
            # Card biến mất lúc 07:37:55 -> Start = 07:37:50. Kết thúc video = 07:39:40
            ("07:37:50", "07:39:40", "GIẢI PICKLEBALL THỦY MOCHI LẦN 1 NĂM 2026 | Đôi Hỗn Hợp 4.8 | Bán Kết 2 | Bin / Trần Quang Trung vs Thắng PA / Lê Tấn Phát 2012"),
            
            # Chung Kết: Chinh Vũ Gia / Chiến Khói vs Bin / Trần Quang Trung
            # Card biến mất lúc 06:54:45 -> Start = 06:54:40. Next card xuất hiện lúc 07:18:10 -> End = 07:18:05
            ("06:54:40", "07:18:05", "GIẢI PICKLEBALL THỦY MOCHI LẦN 1 NĂM 2026 | Đôi Hỗn Hợp 4.8 | Chung Kết | Chinh Vũ Gia / Chiến Khói vs Bin / Trần Quang Trung"),
        ]
    }
]

video_path = r"C:\Temp\Mochi\mochi_full.mp4"
tournament_dir = r"E:\www\DaliSports-Pipeline\2026-09-07_giai-pickleball-thuy-mochi-lan-1-nam-2026"
cut_clips_script = r"E:\www\DaliSports-Pipeline\system\cut_clips.py"

os.makedirs(tournament_dir, exist_ok=True)

# 1. Ghi file timeline chính của giải
full_tl_lines = []
for group in timeline_data:
    for start, end, title in group["matches"]:
        full_tl_lines.append(f"{start} - {end} - {title}")

with open(os.path.join(tournament_dir, "timeline.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(full_tl_lines) + "\n")

print(f"[+] Đã tạo file timeline tổng tại: {os.path.join(tournament_dir, 'timeline.txt')}\n")

# 2. Cắt video cho từng nội dung
for group in timeline_data:
    cat_name = group["cat"]
    cat_dir = os.path.join(tournament_dir, cat_name)
    os.makedirs(cat_dir, exist_ok=True)
    
    tl_file = os.path.join(cat_dir, f"{cat_name}_timeline.txt")
    with open(tl_file, "w", encoding="utf-8") as f:
        for start, end, title in group["matches"]:
            f.write(f"{start} - {end} - {title}\n")
            
    clips_dir = os.path.join(cat_dir, "clips")
    print(f"[+] Cắt clip cho nội dung: {cat_name}")
    cmd = [sys.executable, cut_clips_script, video_path, tl_file, clips_dir]
    res = subprocess.run(cmd)
    print(f" -> Kết quả: {res.returncode}\n")

print("========== HOÀN THÀNH TOÀN BỘ QUY TRÌNH CẮT VIDEO ==========")
