#!/usr/bin/env python3
# migrate_to_tournament_folders.py - Gom file 2 giải Hồng Loan & TTBC vào thư mục riêng YYYY-MM-DD_slug trong Sân 2/
# Option A: Di chuyển HẾT file sinh ra (mp4 gốc + timeline + norms + clips) vào thư mục giải
# Giữ lại ở Sân 2/: seo_config/, cookies.txt, .env, scripts .py, yt_profile/, browser_data/
import os
import shutil
import glob
import re

import sys
sys.stdout.reconfigure(encoding="utf-8")
FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Định nghĩa 2 giải
TOURNAMENTS = {
    "hong_loan": {
        "folder_name": "2026-08-30_giai-cau-long-hong-loan-mo-rong-2026",
        "patterns": [
            "*HỒNG LOAN*",
            "*Hong Loan*",
            "*HONG_LOAN*",
            # Live Hồng Loan mp4 + timeline (chứa emoji + ngày)
            "*30╸8*",
            "*30⧸8*",
        ],
        # File clips chứa HONG LOAN
        "clip_keyword": "HỒNG LOAN",
    },
    "ttbc": {
        "folder_name": "2026-08-30_giai-cau-long-ttbc-lan-1-2026",
        "patterns": [
            "*ttbc*",
            "*TTBC*",
            "*caulong*",
            "*caulong*",
            "*fb_caulong*",
            "*TTBC*",
            # raw_ocr_caulong, smart_timeline_caulong etc sẽ được gom theo từ khóa caulong
        ],
        "clip_keyword": "TTBC",
    }
}

# Các file luôn giữ lại ở gốc (không move)
KEEP_AT_ROOT = {
    "seo_config", "browser_data", "yt_profile", "__pycache__", "output_timeline",
    "timeline_auto", "scratch_frames", "snap_toi", "_probe_caulong",
    ".env", ".env.example", "cookies.txt", "mota.txt.txt",
    "seo_helper.py", "normalize.py", "cut_clips.py", "upload_source_youtube.py",
    "upload_clips.py", "upload_facebook.py", "gemini_timeline.py", "gemini_rotator.py",
    "auto_pipeline.py", "quy_trinh.md", "migrate_to_tournament_folders.py",
}

def should_keep_at_root(name: str) -> bool:
    for keep in KEEP_AT_ROOT:
        if name == keep or name.startswith(keep):
            return True
    # Giữ lại các script .py chung
    if name.endswith(".py") and not any(k in name.lower() for k in ["caulong", "ttbc", "hong"]):
        # Nhưng giữ lại .py là script chung, không move
        if name in ["migrate_to_tournament_folders.py"]:
            return True
    return False

def find_files_for_tournament(patterns, clip_keyword=None):
    matched = set()
    for pat in patterns:
        for f in glob.glob(os.path.join(FOLDER, pat)):
            if os.path.isfile(f):
                matched.add(f)
        # case-insensitive glob via python
        for f in glob.glob(os.path.join(FOLDER, "*")):
            base = os.path.basename(f)
            for pat in patterns:
                # chuyển pattern *xxx* thành substring check
                sub = pat.strip("*").lower()
                if sub and sub.lower() in base.lower():
                    if os.path.isfile(f):
                        matched.add(f)
    return matched

def migrate():
    print("=== MIGRATE TO TOURNAMENT FOLDERS (Option B + folder trong Sân 2/) ===")
    for key, cfg in TOURNAMENTS.items():
        tournament_dir = os.path.join(FOLDER, cfg["folder_name"])
        os.makedirs(tournament_dir, exist_ok=True)
        clips_dir = os.path.join(tournament_dir, "clips")
        # clips_dir sẽ được tạo khi move clips
        print(f"\n[{key}] -> {cfg['folder_name']}/")
        files = find_files_for_tournament(cfg["patterns"])
        # Lọc bỏ file thuộc KEEP_AT_ROOT
        files = [f for f in files if not should_keep_at_root(os.path.basename(f))]
        # Đặc biệt: không move các .py script chung
        files = [f for f in files if not f.endswith(".py") or "caulong" in os.path.basename(f).lower() or "ttbc" in os.path.basename(f).lower()]
        for f in sorted(files):
            base = os.path.basename(f)
            # Nếu đã ở trong tournament folder thì skip
            if tournament_dir in f:
                continue
            dest = os.path.join(tournament_dir, base)
            if os.path.exists(dest):
                print(f"  [SKIP] {base} đã tồn tại ở đích")
                continue
            print(f"  [MOVE] {base} -> {cfg['folder_name']}/")
            try:
                shutil.move(f, dest)
            except Exception as e:
                print(f"    [!] Lỗi move {base}: {e}")

        # Xử lý clips riêng: move clips chứa keyword
        if cfg.get("clip_keyword"):
            keyword = cfg["clip_keyword"].lower()
            clips_src = os.path.join(FOLDER, "clips")
            if os.path.exists(clips_src):
                for clip in glob.glob(os.path.join(clips_src, "*.mp4")):
                    b = os.path.basename(clip).lower()
                    if keyword in b or (key == "hong_loan" and "hong" in b):
                        dest_clips = os.path.join(tournament_dir, "clips")
                        os.makedirs(dest_clips, exist_ok=True)
                        dest = os.path.join(dest_clips, os.path.basename(clip))
                        if os.path.exists(dest):
                            continue
                        print(f"  [MOVE CLIP] {os.path.basename(clip)} -> {cfg['folder_name']}/clips/")
                        try:
                            shutil.move(clip, dest)
                        except Exception as e:
                            print(f"    [!] Lỗi move clip: {e}")
                # Move clips_info.txt nếu có clips được move
                info_src = os.path.join(clips_src, "clips_info.txt")
                if os.path.exists(info_src):
                    # Nếu đã move ít nhất 1 clip hồng loan thì copy info
                    if key == "hong_loan":
                        dest_info = os.path.join(tournament_dir, "clips", "clips_info.txt")
                        if not os.path.exists(dest_info):
                            try:
                                shutil.copy2(info_src, dest_info)
                                print(f"  [COPY] clips_info.txt -> {cfg['folder_name']}/clips/")
                            except Exception as e:
                                print(f"    [!] Copy info lỗi: {e}")
                # Move output_timeline, timeline_auto nếu liên quan
                for extra_dir in ["output_timeline", "timeline_auto"]:
                    src_extra = os.path.join(FOLDER, extra_dir)
                    if os.path.exists(src_extra):
                        for ef in glob.glob(os.path.join(src_extra, "*")):
                            if keyword in os.path.basename(ef).lower() or "hong" in os.path.basename(ef).lower() or "ttbc" in os.path.basename(ef).lower():
                                dest_extra = os.path.join(tournament_dir, extra_dir)
                                os.makedirs(dest_extra, exist_ok=True)
                                dest = os.path.join(dest_extra, os.path.basename(ef))
                                if not os.path.exists(dest):
                                    try:
                                        shutil.move(ef, dest)
                                        print(f"  [MOVE] {extra_dir}/{os.path.basename(ef)} -> {cfg['folder_name']}/{extra_dir}/")
                                    except Exception as e:
                                        print(f"    [!] Lỗi: {e}")

    print("\n=== HOÀN TẤT MIGRATE ===")
    for key, cfg in TOURNAMENTS.items():
        td = os.path.join(FOLDER, cfg["folder_name"])
        print(f"\n[{cfg['folder_name']}]")
        if os.path.exists(td):
            for root, dirs, files in os.walk(td):
                level = root.replace(td, "").count(os.sep)
                indent = " " * 2 * level
                print(f"{indent}{os.path.basename(root)}/")
                subindent = " " * 2 * (level + 1)
                for f in files[:10]:
                    print(f"{subindent}{f}")
                if len(files) > 10:
                    print(f"{subindent}... +{len(files)-10} files")
        else:
            print("  (không tồn tại)")

if __name__ == "__main__":
    migrate()
