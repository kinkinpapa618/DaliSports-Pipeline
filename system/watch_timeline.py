#!/usr/bin/env python3
# watch_timeline.py - Theo dõi file timeline, tự chạy pipeline khi có dữ liệu mới
# Usage: python watch_timeline.py <video_file> [timeline_file]
import os
import sys
import time
import subprocess

sys.stdout.reconfigure(encoding="utf-8")

def get_last_modified(path):
    try:
        return os.path.getmtime(path)
    except:
        return 0

def has_real_entries(path):
    """Kiểm tra file có dòng timeline thật (không chỉ comment)"""
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    return True
        return False
    except:
        return False

def main():
    folder = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    video = sys.argv[1] if len(sys.argv) > 1 else None
    timeline = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Tìm video file
    if not video:
        cands = [f for f in os.listdir(folder) if f.startswith("dalisportss_video") and f.endswith(".mp4") and "timeline" not in f]
        if not cands:
            print("[!] Không tìm thấy video file"); return
        video = max(cands, key=lambda x: os.path.getmtime(os.path.join(folder, x)))
    
    # Tìm timeline file
    if not timeline:
        base = os.path.splitext(video)[0]
        timeline = base + "_timeline.txt"
    
    timeline_path = os.path.join(folder, timeline)
    video_path = os.path.join(folder, video)
    
    if not os.path.exists(timeline_path):
        print(f"[!] Không tìm thấy {timeline}"); return
    
    print(f"[...] Đang theo dõi {timeline}")
    print(f"    Video: {video}")
    print(f"    Nhấn Ctrl+C để dừng")
    
    last_modified = get_last_modified(timeline_path)
    
    while True:
        time.sleep(2)  # Check mỗi 2 giây
        
        current_modified = get_last_modified(timeline_path)
        
        if current_modified > last_modified:
            last_modified = current_modified
            
            # Kiểm tra có dòng timeline thật không
            if has_real_entries(timeline_path):
                print(f"\n[+] Phát hiện dữ liệu mới trong {timeline}!")
                print("[...] Chạy normalize...")
                subprocess.run([sys.executable, os.path.join(folder, "normalize.py")], cwd=folder)
                
                print(f"[...] Chạy cut_clips...")
                subprocess.run([sys.executable, os.path.join(folder, "cut_clips.py"), video_path, timeline_path], cwd=folder)
                
                print(f"[...] Chạy upload_clips...")
                subprocess.run([sys.executable, os.path.join(folder, "upload_clips.py")], cwd=folder)
                
                print("[+] Pipeline hoàn tất!")
                print(f"[...] Tiếp tục theo dõi... (Ctrl+C để dừng)")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[+] Dừng theo dõi.")
