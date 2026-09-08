import cv2, os, sys
import numpy as np

video_path = r"C:\Temp\Mochi\mochi_full.mp4"
cap = cv2.VideoCapture(video_path)

fps = cap.get(cv2.CAP_PROP_FPS)
total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
duration_sec = int(total_frames / fps)

print(f"[+] Total duration: {duration_sec}s ({duration_sec//3600:02d}:{(duration_sec%3600)//60:02d}:{duration_sec%60:02d})")

# Quét với bước nhảy 5 giây
step_sec = 5
results = []

# Region of interest for scoreboard popup banner at bottom center
# y: 650 to 950, x: 450 to 1450 (assuming 1920x1080 resolution)

for sec in range(0, duration_sec, step_sec):
    cap.set(cv2.CAP_PROP_POS_MSEC, sec * 1000)
    ret, frame = cap.read()
    if not ret:
        continue
    
    h, w, _ = frame.shape
    # Dynamic ROI calculation based on resolution
    y1, y2 = int(h * 0.60), int(h * 0.90)
    x1, x2 = int(w * 0.20), int(w * 0.80)
    
    crop = frame[y1:y2, x1:x2]
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    std = float(np.std(gray))
    
    # Check color contrast / std threshold for scoreboard banner
    # Overlay banner has dark background, bright text (white/cyan/yellow), red badge, etc.
    results.append((sec, std))

cap.release()

print(f"[+] Scanned {len(results)} points.")
# In ra các khoảng thời gian có std bứt phá cao
detected = [r for r in results if r[1] >= 45]
print(f"[+] Detected {len(detected)} candidate banner frames (std >= 45)")

# Gom cụm theo giây
groups = []
if detected:
    cur = [detected[0]]
    for pt in detected[1:]:
        if pt[0] - cur[-1][0] <= 30: # gom nếu cách nhau <= 30s
            cur.append(pt)
        else:
            groups.append(cur)
            cur = [pt]
    if cur:
        groups.append(cur)

print(f"[+] Found {len(groups)} banner popup groups across the video:")
for i, g in enumerate(groups, 1):
    st = g[0][0]
    en = g[-1][0]
    best = max(g, key=lambda x: x[1])
    st_str = f"{st//3600:02d}:{(st%3600)//60:02d}:{st%60:02d}"
    en_str = f"{en//3600:02d}:{(en%3600)//60:02d}:{en%60:02d}"
    best_str = f"{best[0]//3600:02d}:{(best[0]%3600)//60:02d}:{best[0]%60:02d}"
    print(f"  Group {i:02d}: {st_str} -> {en_str} (Best @ {best_str}, std={best[1]:.1f})")

