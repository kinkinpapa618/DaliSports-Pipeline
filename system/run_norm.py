# run_norm.py - chay lai normalize tre src timeline (sinh lai _norms.txt)
import glob, sys, os
sys.stdout.reconfigure(encoding="utf-8")
import normalize

tl = [f for f in glob.glob("*_timeline.txt") if "PICKLEBALL" in f and "norms" not in f][0]
print("TL:", tl, flush=True)
normalize.process_file(tl)
print("DONE NORM", flush=True)
