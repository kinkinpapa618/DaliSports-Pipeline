# run_cut.py - wrapper ASCII chay lai cut_clips voi duong dan co ky tu dac biet
import glob, sys, os
sys.stdout.reconfigure(encoding="utf-8")
import cut_clips

vid = [f for f in glob.glob("*.mp4") if "PICKLEBALL" in f and "timeline" not in f.lower()][0]
tl = [f for f in glob.glob("*_timeline.txt") if "PICKLEBALL" in f and "norms" not in f][0]
print("VIDEO:", vid)
print("TL:", tl, flush=True)
sys.argv = ["cut_clips.py", vid, tl]
cut_clips.main()
print("DONE CUT", flush=True)
