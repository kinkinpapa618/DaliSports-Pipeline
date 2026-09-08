#!/usr/bin/env python3
# test_gemini_caulong.py - Gửi full frame cho Gemini đọc bảng điểm cầu lông
import os, sys
sys.stdout.reconfigure(encoding="utf-8")
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
import cv2
from PIL import Image
try:
    from google import genai
except ImportError:
    print("[!] Chua cai google-genai"); sys.exit(1)

VIDEO = r"C:\Users\dalis\Desktop\Sân 2\caulong_ttbc.mp4"
OUT = r"C:\Users\dalis\AppData\Local\Temp\opencode\_probe_caulong\test_full.jpg"
API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL = "gemini-3.6-flash"

# Trich frame tai giay 600 (00:10:00) - giua video dau
cap = cv2.VideoCapture(VIDEO)
cap.set(cv2.CAP_PROP_POS_MSEC, 600 * 1000)
ret, frame = cap.read()
cap.release()
if not ret:
    print("[!] Khong trich duoc frame"); sys.exit(1)
rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
img = Image.fromarray(rgb)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
cv2.imwrite(OUT, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
print(f"[*] Da trich frame tai 00:10:00 -> {OUT} ({img.size})")

# Goi Gemini full frame
client = genai.Client(api_key=API_KEY)
prompt = """Ban la chuyen gia trich xuat thong tin the thao cau long tu hinh anh.
Quan sat ky anh bang diem / banner thi dau cau long nay va trich xuat thong tin chinh xac:
1. Ten giai dau va Nam
2. Noi dung / Hanh muc thi dau (DON NAM, DOI NAM, DOI NAM NU, U15, U18, v.v.)
3. Ten hai doi / VDV thi dau:
   - Neu la doi: TEN 1 / TEN 2 vs TEN 3 / TEN 4
   - Neu la don: TEN 1 vs TEN 2

Quy tac xuat ket qua:
- Tra ve dung 1 dong text duy nhat theo dinh dang:
  TEN GIAI DAU - NAM | HANH MUC | TEN DOI 1 vs TEN DOI 2
- VDU: GIᴀI CAU LONGL THANH THIEU NIEN TRANH CUP TTBC - LAN THU 1 | U15 DON NAM | NGUYEN VAN THUYET vs NGO VAN MANH
- Neu hinh anh mo, thieu chu hoac khong doc duoc ro, hay tra ve dung chuoi: KHONG_DOC_DUOC
- Tuyet doi khong them giai thich, khong dung markdown block, chi tra ve 1 dong duy nhat."""

print(f"[*] Goi Gemini {MODEL} voi full frame...")
response = client.models.generate_content(model=MODEL, contents=[img, prompt])
text = response.text.strip().replace("```markdown","").replace("```","").strip()
if "\n" in text:
    text = text.split("\n")[0].strip()
print(f"[*] Ket qua Gemini:\n{text}")

# Test them crop goc trai tren nhu gemini_timeline.py
H, W = img.size[1], img.size[0]
y1, y2 = int(0.01 * H), int(0.20 * H)
x1, x2 = int(0.03 * W), int(0.35 * W)
crop = img.crop((x1, y1, x2, y2))
print(f"\n[*] Crop goc trai tren: ({x1},{y1})-({x2},{y2}), size={crop.size}")
response2 = client.models.generate_content(model=MODEL, contents=[crop, prompt])
text2 = response2.text.strip().replace("```markdown","").replace("```","").strip()
if "\n" in text2:
    text2 = text2.split("\n")[0].strip()
print(f"[*] Ket qua Gemini (crop goc trai tren):\n{text2}")
