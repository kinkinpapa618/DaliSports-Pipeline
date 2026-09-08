import os, sys, subprocess

sys.stdout.reconfigure(encoding='utf-8')

# 5 trận đấu có trong video D:\mochi_full_all.mp4
five_matches = [
    # 1. Đôi Hỗn Hợp 4.4
    {
        "cat": "doi-hon-hop-4-4",
        "matches": [
            ("09:16:36", "09:30:03", "GIẢI PICKLEBALL THỦY MOCHI LẦN 1 NĂM 2026 | Đôi Hỗn Hợp 4.4 | Bán Kết | Mạnh Thắng / Tuấn Minh vs Hưng Kai / Trịnh Tiến Thành"),
            ("12:41:56", "13:11:45", "GIẢI PICKLEBALL THỦY MOCHI LẦN 1 NĂM 2026 | Đôi Hỗn Hợp 4.4 | Chung Kết | Mạnh Thắng / Tuấn Minh vs Phạm Tuấn Hiệp / Minh Khoáng")
        ]
    },
    # 2. Đôi Hỗn Hợp 4.8
    {
        "cat": "doi-hon-hop-4-8",
        "matches": [
            ("13:17:10", "13:52:05", "GIẢI PICKLEBALL THỦY MOCHI LẦN 1 NĂM 2026 | Đôi Hỗn Hợp 4.8 | Bán Kết | Chinh Vũ Gia / Chiến Khói vs Nguyễn Văn Giáp / Nguyễn Văn Hà"),
            ("14:10:59", "14:39:01", "GIẢI PICKLEBALL THỦY MOCHI LẦN 1 NĂM 2026 | Đôi Hỗn Hợp 4.8 | Chung Kết | Chinh Vũ Gia / Chiến Khói vs Bin / Trần Quang Trung")
        ]
    },
    # 3. Đôi Nam Nữ 4.2
    {
        "cat": "doi-nam-nu-4-2",
        "matches": [
            ("14:40:08", "15:12:23", "GIẢI PICKLEBALL THỦY MOCHI LẦN 1 NĂM 2026 | Đôi Nam Nữ 4.2 | Chung Kết | Trần Phượng 68 / Vũ Ngọc Nghĩa vs Dương Nguyễn / Nguyễn Gia Nhi")
        ]
    }
]

video_path = r"D:\mochi_full_all.mp4"
tournament_dir = r"E:\www\DaliSports-Pipeline\2026-09-07_giai-pickleball-thuy-mochi-lan-1-nam-2026"
cut_clips_script = r"E:\www\DaliSports-Pipeline\system\cut_clips.py"

os.makedirs(tournament_dir, exist_ok=True)

# 1. Ghi file timeline tổng của 5 trận
all_lines = []
for group in five_matches:
    for st, en, title in group["matches"]:
        all_lines.append(f"{st} - {en} - {title}")

with open(os.path.join(tournament_dir, "timeline.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(all_lines) + "\n")

print(f"[+] Đã tạo file timeline tổng 5 trận tại: {os.path.join(tournament_dir, 'timeline.txt')}\n")

# 2. Cắt video cho từng nội dung tương ứng
for group in five_matches:
    cat_name = group["cat"]
    cat_dir = os.path.join(tournament_dir, cat_name)
    os.makedirs(cat_dir, exist_ok=True)
    
    tl_file = os.path.join(cat_dir, f"{cat_name}_timeline.txt")
    with open(tl_file, "w", encoding="utf-8") as f:
        for st, en, title in group["matches"]:
            f.write(f"{st} - {en} - {title}\n")
            
    clips_dir = os.path.join(cat_dir, "clips")
    print(f"[+] Cắt clip cho nội dung: {cat_name}")
    cmd = [sys.executable, cut_clips_script, video_path, tl_file, clips_dir]
    res = subprocess.run(cmd)
    print(f" -> Kết quả: {res.returncode}\n")

print("========== HOÀN THÀNH CẮT 5 TRẬN ĐẤU ==========")
