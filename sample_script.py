import cv2, os, sys

video_path = r"C:\Temp\Mochi\mochi_full.mp4"
out_dir = r"C:\Temp\Mochi\sample_frames"
os.makedirs(out_dir, exist_ok=True)

cap = cv2.VideoCapture(video_path)
timestamps = [300, 1000, 3000, 5000, 7000, 10000, 15000, 20000, 25000]

for sec in timestamps:
    cap.set(cv2.CAP_PROP_POS_MSEC, sec * 1000)
    ret, frame = cap.read()
    if ret:
        fn = os.path.join(out_dir, f"frame_{sec}s.jpg")
        cv2.imwrite(fn, frame)
        print(f"Saved {fn}")

cap.release()
print("Done sampling.")
