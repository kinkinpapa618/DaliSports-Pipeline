# run_fix.py - wrapper ASCII để chạy fix_timeline với đường dẫn có ký tự đặc biệt
import glob, sys, os
sys.stdout.reconfigure(encoding="utf-8")
import fix_timeline

vid = [f for f in glob.glob("*.mp4") if "PICKLEBALL" in f and "timeline" not in f.lower()][0]
tl = [f for f in glob.glob("*_timeline.txt") if "PICKLEBALL" in f][0]
print("VIDEO:", vid)
print("TL:", tl, flush=True)
sys.argv = ["fix_timeline.py", vid, tl]
fix_timeline.main()
