import cv2, os, sys
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image

sys.path.insert(0, r"E:\www\DaliSports-Pipeline\system")
import gemini_rotator

# Quét bước nhảy 30 giây trong 2 tiếng rưỡi đầu (00:00:00 -> 02:00:00)
# để tìm các trận Bán kết/Chung kết chưa thấy banner ở đoạn sau
video_path = r"C:\Temp\Mochi\mochi_full.mp4"
cap = cv2.VideoCapture(video_path)

prompt = """Nếu trên hình ảnh này có bảng điểm hay banner giới thiệu trận đấu thể thao ( Pickleball ), hãy ghi rõ: NỘI DUNG | VÒNG ĐẤU | TÊN VĐV 1 / TÊN VĐV 2 vs TÊN VĐV 3 / TÊN VĐV 4.
Nếu không có bảng điểm / banner, hãy trả đúng chuỗi: KHONG_THAY"""

results = []
for sec in range(0, 7200, 30): # quét 2 tiếng đầu
    cap.set(cv2.CAP_PROP_POS_MSEC, sec * 1000)
    ret, frame = cap.read()
    if not ret: continue
    
    # Kiểm tra nhanh std ở nửa dưới xem có banner không
    h, w, _ = frame.shape
    crop = frame[int(h*0.6):int(h*0.9), int(w*0.2):int(w*0.8)]
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    std = gray.std()
    
    if std >= 45:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb)
        text, meta = gemini_rotator.GeminiRotator.generate_vision_sync(
            prompt_text=prompt,
            image_input=img,
            preferred_model="gemini-3.6-flash"
        )
        t_str = f"{sec//3600:02d}:{(sec%3600)//60:02d}:{sec%60:02d}"
        res = text.strip() if text else "KHONG_THAY"
        if "KHONG_THAY" not in res and "không" not in res.lower():
            print(f"[{t_str}] (std={std:.1f}) -> {res}")
            results.append((sec, t_str, res))

cap.release()

with open(r"E:\www\DaliSports-Pipeline\scan_early_matches.txt", "w", encoding="utf-8") as f:
    for sec, t_str, res in results:
        f.write(f"{sec} | {t_str} | {res}\n")

print("Done scanning early matches.")
