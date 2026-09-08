#!/usr/bin/env python3
import os, shutil, glob, re, sys
sys.stdout.reconfigure(encoding="utf-8")
FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SYSTEM = os.path.join(FOLDER, "system")
DEBUG = os.path.join(SYSTEM, "debug")
LOGS = os.path.join(FOLDER, "logs")
TRASH = os.path.join(FOLDER, "_trash")

os.makedirs(SYSTEM, exist_ok=True)
os.makedirs(DEBUG, exist_ok=True)
os.makedirs(LOGS, exist_ok=True)
os.makedirs(TRASH, exist_ok=True)

# 1. Core system files (move to system/)
core = [
 "auto_pipeline.py","cut_clips.py","normalize.py","gemini_timeline.py","gemini_rotator.py","seo_helper.py",
 "upload_source_youtube.py","upload_clips.py","upload_facebook.py","upload_fb_business.py","upload_youtube.py",
 "upload_yt_nopublish.py","upload_yt_nopublish_caulong.py","upload_yt_nopublish_fbcaulong.py","upload_yt_nopublish_pickleball.py",
 "download_fb.bat","watch_timeline.py","generate_full_timeline.py","fix_timeline.py",
 "fix_caulong_timeline.py","probe_frames_caulong.py","smart_timeline_caulong.py","fast_timeline_caulong.py",
 "run_cut.py","run_fix.py","run_norm.py","run_upload.py",
 "migrate_to_tournament_folders.py","migrate_to_video_subfolders.py","_reorg.py"
]
# Debug files (move to system/debug)
debug_files = ["check_yt.py","check_yt2.py","check_yt_status.py","debug_yt.py","explore_series.py","explore_series2.py","test_fix_khongdoc.py","test_gemini_caulong.py"]

# Junk to trash/delete
junk_patterns = [
 "_check_*.py","_debug_*.py","_fix_*.py","_process_*.py","_resume*.py","_reup*.py","_wait_*.py","_reupload_*.py",
 "*.log","*.err","*_out.txt","*_log.txt","fast_scan.json","fb_run_out.txt","yt_debug.txt","yt_status_result.txt","listvideo.txt"
]
junk_dirs = ["__pycache__","_probe_caulong","output_timeline","timeline_auto","scratch_frames","snap_toi"]

print("=== 1. Move core to system/ ===")
for f in core:
    src=os.path.join(FOLDER, f)
    if os.path.exists(src):
        dst=os.path.join(SYSTEM, f)
        if os.path.abspath(src)!=os.path.abspath(dst):
            print(f"  MOVE {f} -> system/")
            shutil.move(src, dst)

print("\n=== 2. Move debug to system/debug/ ===")
for f in debug_files:
    src=os.path.join(FOLDER, f)
    if os.path.exists(src):
        dst=os.path.join(DEBUG, f)
        print(f"  MOVE {f} -> system/debug/")
        shutil.move(src, dst)

print("\n=== 3. Move junk to _trash/ (for review before delete) ===")
for pat in junk_patterns:
    for src in glob.glob(os.path.join(FOLDER, pat)):
        if os.path.isfile(src):
            base=os.path.basename(src)
            # Đừng trash file vừa move vào system
            if os.path.exists(os.path.join(SYSTEM, base)) or os.path.exists(os.path.join(DEBUG, base)):
                continue
            dst=os.path.join(TRASH, base)
            print(f"  TRASH {base}")
            try: shutil.move(src, dst)
            except: pass
for d in junk_dirs:
    src=os.path.join(FOLDER, d)
    if os.path.exists(src):
        dst=os.path.join(TRASH, d)
        print(f"  TRASH DIR {d}/")
        try: shutil.move(src, dst)
        except: pass

# Dọn dalisportss_video10 timeline (data cũ) -> move vào tournament TTBC hoặc trash?
for f in ["dalisportss_video10_timeline.txt","dalisportss_video10_timeline_norms.txt"]:
    src=os.path.join(FOLDER, f)
    if os.path.exists(src):
        # Move vào _trash vì là data cũ không thuộc 2 giải chính
        dst=os.path.join(TRASH, f)
        print(f"  TRASH data {f}")
        shutil.move(src, dst)

# clips/ legacy ở root: nếu rỗng thì trash, nếu có file thì giữ nhưng báo
clips_path=os.path.join(FOLDER, "clips")
if os.path.exists(clips_path):
    files=os.listdir(clips_path)
    if not files:
        print(f"  TRASH empty clips/")
        shutil.move(clips_path, os.path.join(TRASH, "clips"))
    else:
        print(f"  KEEP clips/ ({len(files)} files) - legacy, sẽ dùng tournament subfolders cho mới")

print("\n=== 4. Update FOLDER references in system/ ===")
for root, dirs, files in os.walk(SYSTEM):
    for fname in files:
        if fname.endswith(".py"):
            fpath=os.path.join(root, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                content=f.read()
            orig=content
            # Thay FOLDER = dirname(__file__) -> parent
            content=re.sub(r'FOLDER\s*=\s*os\.path\.dirname\(os\.path\.abspath\(__file__\)\)',
                           'FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))', content)
            content=re.sub(r'folder\s*=\s*os\.path\.dirname\(os\.path\.abspath\(__file__\)\)',
                           'folder = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))', content)
            # Đặc biệt cho cut_clips, watch_timeline dùng folder biến
            if content!=orig:
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"  PATCHED {os.path.relpath(fpath, FOLDER)}")

# Tạo launcher tại root để backward compat
launcher=os.path.join(FOLDER, "auto_pipeline.py")
if not os.path.exists(launcher):
    with open(launcher, "w", encoding="utf-8") as f:
        f.write('''#!/usr/bin/env python3
import sys, subprocess, os
sys.stdout.reconfigure(encoding="utf-8")
# Launcher giữ tương thích sau khi move vào system/
subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "system", "auto_pipeline.py")] + sys.argv[1:])
''')
    print("  CREATED launcher auto_pipeline.py at root")

print("\n=== DONE ===")
for root, dirs, files in os.walk(FOLDER):
    level=root.replace(FOLDER,"").count(os.sep)
    if level>2: continue
    indent="  "*level
    print(f"{indent}{os.path.basename(root) or 'Sân 2'}/")
    for fn in sorted(files)[:8]:
        print(f"{indent}  {fn}")
    if len(files)>8:
        print(f"{indent}  ... +{len(files)-8}")
