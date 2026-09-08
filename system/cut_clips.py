#!/usr/bin/env python3
# cut_clips.py - Cắt từng trận từ video gốc theo timeline
# Đọc dalisports_video2_timeline.txt (định dạng: START - END - TIÊU ĐỀ)
# Xuất từng trận vào thư mục clips/, kèm file clips_info.txt ánh xạ tên file -> tiêu đề chuẩn hóa.
import os
import re
import sys
import glob
import subprocess

try:
    import normalize
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import normalize

TL_RE = re.compile(r"^\s*(\d{1,2}:\d{2}(?::\d{2})?)\s*-\s*(\d{1,2}:\d{2}(?::\d{2})?)\s*-\s*(.+?)\s*$")
ILLEGAL = re.compile(r'[<>:"/\\|?*]')


def to_sec(t: str) -> int:
    p = [int(x) for x in t.split(":")]
    if len(p) == 3:
        h, m, s = p
    elif len(p) == 2:
        h, m, s = 0, p[0], p[1]
    else:
        h, m, s = 0, 0, p[0]
    return h * 3600 + m * 60 + s


def sanitize(name: str) -> str:
    name = name.replace("|", " - ")
    name = ILLEGAL.sub("", name)
    return name.strip().rstrip(".")[:120]


def find_video(folder: str) -> str:
    cands = glob.glob(os.path.join(folder, "*video2*.mp4"))
    cands = [c for c in cands if "timeline" not in os.path.basename(c).lower()]
    if cands:
        # lấy file mới nhất
        return max(cands, key=os.path.getmtime)
    # fallback: mọi mp4
    cands = glob.glob(os.path.join(folder, "*.mp4"))
    cands = [c for c in cands if "timeline" not in os.path.basename(c).lower()]
    return max(cands, key=os.path.getmtime) if cands else None


def find_timeline(folder: str, video_path: str = None) -> str:
    if video_path:
        base = os.path.splitext(video_path)[0]
        cand = base + "_timeline.txt"
        if os.path.exists(cand):
            return cand
    cands = glob.glob(os.path.join(folder, "*_timeline.txt"))
    cands = [c for c in cands if not c.endswith("_norms.txt")]
    return max(cands, key=os.path.getmtime) if cands else None


def main():
    folder = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    video = sys.argv[1] if len(sys.argv) > 1 else find_video(folder)
    timeline = sys.argv[2] if len(sys.argv) > 2 else find_timeline(folder, video)
    if not video or not os.path.exists(video):
        print("[!] Không tìm thấy video gốc."); return
    if not timeline or not os.path.exists(timeline):
        print(f"[!] Không tìm thấy file timeline."); return

    # Ưu tiên clips trong cùng thư mục với video (hỗ trợ tournament + video subfolder 2 cấp)
    video_dir = os.path.dirname(os.path.abspath(video))
    # Nếu video nằm trong tournament structure (không phải thư mục gốc Sân 2), dùng clips trong video_dir
    try:
        is_subpath = os.path.commonpath([os.path.abspath(video_dir), os.path.abspath(folder)]) == os.path.abspath(folder)
    except ValueError:
        is_subpath = False
    if os.path.abspath(video_dir) != os.path.abspath(folder) and is_subpath:
        out_dir = os.path.join(video_dir, "clips")
    else:
        out_dir = os.path.join(folder, "clips")
    # Cho phép ghi đè qua tham số thứ 3
    if len(sys.argv) > 3:
        out_dir = sys.argv[3]
    os.makedirs(out_dir, exist_ok=True)

    rows = []
    with open(timeline, encoding="utf-8-sig") as f:
        for line in f:
            m = TL_RE.match(line)
            if m:
                rows.append((m.group(1), m.group(2), m.group(3)))

    if not rows:
        print("[!] Timeline trống / sai định dạng."); return

    info_path = os.path.join(out_dir, "clips_info.txt")
    with open(info_path, "w", encoding="utf-8") as info:
        for i, (start, end, title) in enumerate(rows, 1):
            s_sec, e_sec = to_sec(start), to_sec(end)
            dur = max(1, e_sec - s_sec)
            norm = normalize.normalize(title)
            fname = f"{i:02d} - {sanitize(norm)}.mp4"
            out_path = os.path.join(out_dir, fname)
            cmd = [
                "ffmpeg", "-y", "-ss", start, "-i", video,
                "-t", str(dur), "-c", "copy", "-map", "0",
                "-avoid_negative_ts", "make_zero", out_path
            ]
            print(f"[+] Trận {i:02d}: {start} -> {end} ({dur}s) | {norm}")
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            info.write(f"{fname} | {norm}\n")
    print(f"[+] Xong. Clip lưu tại: {out_dir}")
    print(f"[+] Ánh xạ tiêu đề: {info_path}")


if __name__ == "__main__":
    main()
