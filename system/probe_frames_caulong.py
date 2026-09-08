#!/usr/bin/env python3
# probe_frames_caulong.py - Trích xuất vài frame để xem vị trí bảng điểm cầu lông
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

import cv2

VIDEO = r"C:\Users\dalis\Desktop\Sân 2\🔴LIVE ｜ GIẢI CẦU LÔNG THANH THIẾU NIÊN TRANH CUP TTBC LẦN 1 - 2026.mp4"
OUT = r"C:\Users\dalis\AppData\Local\Temp\opencode\_probe_caulong"

os.makedirs(OUT, exist_ok=True)

cap = cv2.VideoCapture(VIDEO)
if not cap.isOpened():
    print("[!] Không mở được video")
    sys.exit(1)

fps = cap.get(cv2.CAP_PROP_FPS) or 30
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
duration = int(total_frames / fps)
W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
print(f"[*] {os.path.basename(VIDEO)} | dur={duration}s | {W}x{H} | fps={fps:.2f}")

# Các mốc thời gian để kiểm tra (giây): gần đầu, 20%, 40%, 60%, 80%, cuối
fracs = [0.02, 0.15, 0.30, 0.45, 0.60, 0.75, 0.90]

def fmt(s):
    h = s // 3600; m = (s % 3600) // 60; sec = s % 60
    return f"{h:02d}:{m:02d}:{sec:02d}"

for f in fracs:
    ts = int(duration * f)
    cap.set(cv2.CAP_PROP_POS_MSEC, ts * 1000)
    ret, frame = cap.read()
    if not ret:
        continue
    # xoay nếu vertical? giữ nguyên
    path = os.path.join(OUT, f"f_{f:.3f}_{ts:06d}.jpg")
    cv2.imwrite(path, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    print(f"[+] {fmt(ts)} -> {os.path.basename(path)}")

cap.release()
print(f"\n[+] Frame lưu tại: {OUT}")
