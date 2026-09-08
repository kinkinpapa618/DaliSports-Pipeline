import cv2, os, sys
from PIL import Image

sys.path.insert(0, r"E:\www\DaliSports-Pipeline\system")
import gemini_rotator

sys.stdout.reconfigure(encoding='utf-8')

video_path = r"C:\Temp\Mochi\mochi_full.mp4"
cap = cv2.VideoCapture(video_path)

fps = cap.get(cv2.CAP_PROP_FPS)
total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
dur_sec = int(total_frames / fps)

print(f"[+] Scanning card popups across 00:00:00 -> {dur_sec//3600:02d}:{(dur_sec%3600)//60:02d}:{dur_sec%60:02d}")

# Quét 2 giây / 1 frame để tìm chính xác mốc xuất hiện và biến mất của Intro Card "SẮP DIỄN RA"
# Card nằm ở chính giữa nửa dưới màn hình (y: 55% - 92%, x: 20% - 80%)

card_events = [] # list of (sec, status, text)

# Dùng prompt đơn giản để Gemini trả về đúng tên 2 đội nếu có card SẮP DIỄN RA
prompt = """Đây có phải là bảng card thông tin trận đấu 'SẮP DIỄN RA' nằm ở giữa nửa dưới màn hình không?
Nếu ĐÚNG, hãy ghi rõ: SẮP DIỄN RA | TÊN 2 ĐỘI / VĐV.
Nếu KHÔNG CÓ card, hãy trả về đúng chữ: KHONG_CÓ."""

# Quét từng 5 giây toàn bộ video để tìm các block card
step = 5
card_timestamps = []

for sec in range(0, dur_sec, step):
    cap.set(cv2.CAP_PROP_POS_MSEC, sec * 1000)
    ret, frame = cap.read()
    if not ret: continue
    
    h, w, _ = frame.shape
    crop = frame[int(h*0.55):int(h*0.92), int(w*0.25):int(w*0.75)]
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    std = float(gray.std())
    
    # Bảng card tối màu với viền sáng neon blue có std rất đặc trưng (std >= 48)
    if std >= 48:
        card_timestamps.append((sec, std))

print(f"[+] Tìm thấy {len(card_timestamps)} frame nghi ngờ có Intro Card.")

# Gom các frame liên tục thành các khoảng card xuất hiện
card_blocks = []
if card_timestamps:
    cur = [card_timestamps[0]]
    for pt in card_timestamps[1:]:
        if pt[0] - cur[-1][0] <= 15: # gom nếu gần nhau <= 15s
            cur.append(pt)
        else:
            card_blocks.append((cur[0][0], cur[-1][0]))
            cur = [pt]
    if cur:
        card_blocks.append((cur[0][0], cur[-1][0]))

print(f"[+] Phát hiện {len(card_blocks)} đợt hiển thị Intro Card (SẮP DIỄN RA):")

# Với mỗi đợt card xuất hiện, đọc tên cặp đấu từ frame ở giữa đợt bằng Gemini OCR
verified_cards = []
for i, (st, en) in enumerate(card_blocks, 1):
    mid_sec = (st + en) // 2
    cap.set(cv2.CAP_PROP_POS_MSEC, mid_sec * 1000)
    ret, frame = cap.read()
    if not ret: continue
    
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(rgb)
    
    text, meta = gemini_rotator.GeminiRotator.generate_vision_sync(
        prompt_text=prompt,
        image_input=img,
        preferred_model="gemini-3.6-flash"
    )
    res = text.strip() if text else "KHONG_CÓ"
    st_str = f"{st//3600:02d}:{(st%3600)//60:02d}:{st%60:02d}"
    en_str = f"{en//3600:02d}:{(en%3600)//60:02d}:{en%60:02d}"
    
    if "SẮP DIỄN RA" in res or ("vs" in res.lower() and "KHONG" not in res):
        print(f"  Card {i:02d} [{st_str} -> {en_str}] : {res}")
        verified_cards.append((st, en, res))
    else:
        print(f"  [Ignored {i:02d}] [{st_str} -> {en_str}] : {res}")

cap.release()

with open(r"E:\www\DaliSports-Pipeline\intro_card_timestamps.txt", "w", encoding="utf-8") as f:
    for st, en, info in verified_cards:
        st_str = f"{st//3600:02d}:{(st%3600)//60:02d}:{st%60:02d}"
        en_str = f"{en//3600:02d}:{(en%3600)//60:02d}:{en%60:02d}"
        f.write(f"{st} | {en} | {st_str} -> {en_str} | {info}\n")

print("\n[+] Đã lưu tất cả các mốc Intro Card vào intro_card_timestamps.txt")
