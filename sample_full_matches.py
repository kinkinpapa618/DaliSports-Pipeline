import cv2, os, sys
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image

sys.path.insert(0, r"E:\www\DaliSports-Pipeline\system")
import gemini_rotator

video_path = r"C:\Temp\Mochi\mochi_full.mp4"
cap = cv2.VideoCapture(video_path)

# Lấy 1 frame ở giữa mỗi khoảng 15 phút từ 00:00:00 -> 07:30:00 (tổng cộng 30 frames)
prompt = """Hãy quan sát hình ảnh sân Pickleball này và trả lời:
1. Có bảng điểm overlay hiển thị ở màn hình hay không? Nếu có, ghi rõ TÊN NỘI DUNG, VÒNG ĐẤU và TÊN 4 VĐV.
2. Nếu không có bảng overlay, nhìn vào biển hiệu / backdrop sân hoặc VĐV đang thi đấu trên sân để nhận diện tên 2 đội nếu có.
Nếu không có bất kỳ thông tin nào, ghi KHONG_THAY."""

print("[+] Sampling 30 frames across full video...")
for sec in range(300, 27000, 900): # 15p 1 frame
    cap.set(cv2.CAP_PROP_POS_MSEC, sec * 1000)
    ret, frame = cap.read()
    if not ret: continue
    
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(rgb)
    t_str = f"{sec//3600:02d}:{(sec%3600)//60:02d}:{sec%60:02d}"
    
    text, meta = gemini_rotator.GeminiRotator.generate_vision_sync(
        prompt_text=prompt,
        image_input=img,
        preferred_model="gemini-3.6-flash"
    )
    res = text.strip() if text else "KHONG_THAY"
    print(f"[{t_str}] -> {res}\n")

cap.release()
