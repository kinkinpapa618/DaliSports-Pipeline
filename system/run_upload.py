# run_upload.py - upload video source pickleball len YouTube (cong khai)
import glob, sys, os, asyncio
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")
import upload_source_youtube as u

vid = [f for f in glob.glob("*.mp4") if "PICKLEBALL" in f and "timeline" not in f.lower()][0]
norms = [f for f in glob.glob("*_timeline_norms.txt") if "PICKLEBALL" in f][0]
print("VIDEO:", vid)
print("NORMS:", norms, flush=True)
asyncio.run(u.upload_source_video(vid, norms_path=norms, dry_run=False))
print("UPLOAD DONE", flush=True)
