# QUY TRÌNH: TỰ ĐỘNG HÓA XỬ LÝ & ĐĂNG TẢI VIDEO THỂ THAO (DALI SPORTS)

Quy trình tự động hóa 100% từ video gốc / livestream (Facebook/YouTube) đến xử lý AI nhận diện trận đấu, cắt clip siêu tốc và đăng tải đa nền tảng (YouTube & Facebook).

---

## 🚀 1. Khởi chạy 1 lệnh tự động toàn bộ (Khuyên dùng)

Chỉ cần chạy lệnh từ thư mục gốc của dự án:

```bash
# 1. Đăng video gốc kèm Chapters lên YouTube (mặc định):
python auto_pipeline.py "https://www.facebook.com/dalisportss/videos/27910556711971209"

# 2. Đăng từng clip riêng lẻ lên YouTube:
python auto_pipeline.py "video.mp4" --yt-mode clips

# 3. Đăng trọn bộ clip thành 1 Album lên Facebook:
python auto_pipeline.py "video.mp4" --platform facebook

# 4. Đăng CẢ HAI nền tảng (YouTube Video Gốc + Facebook Album Clip):
python auto_pipeline.py "video.mp4" --platform both

# 5. Đăng Full toàn diện (YouTube Source + YouTube Clips + Facebook Album):
python auto_pipeline.py "video.mp4" --platform both --yt-mode both

# 6. Chạy thử nghiệm xem trước SEO, Caption, Chapters (Không đăng thật):
python auto_pipeline.py "video.mp4" --dry-run
```

### 💡 Bảng tham số `auto_pipeline.py`:
| Tham số | Giá trị mặc định | Mô tả |
| :--- | :--- | :--- |
| `input` | Video mới nhất | Đường dẫn URL Facebook hoặc file `.mp4` |
| `--platform` | `youtube` | Nền tảng đích: `youtube`, `facebook`, hoặc `both` |
| `--yt-mode` | `source` | Chế độ YouTube: `source` (Full video + Chapters), `clips` (từng clip), hoặc `both` |
| `--skip-download`| `False` | Bỏ qua bước tải video (dùng video đã có) |
| `--skip-timeline`| `False` | Bỏ qua quét AI nếu đã có file `*_timeline.txt` |
| `--skip-cut` | `False` | Bỏ qua cắt clip (tiết kiệm thời gian nếu chỉ đăng source video) |
| `--skip-upload` | `False` | Chỉ tải, quét timeline và cắt clip, không upload |
| `--dry-run` | `False` | Chạy mô phỏng toàn bộ quy trình và xem trước nội dung SEO/Chapters |
| `--review-timeline` | `False` | Dừng đếm ngược 10s cho phép người dùng kiểm tra mốc timeline |
| `--start N` | `0` | Bắt đầu upload từ clip thứ $N$ |
| `--model` | `gemini-2.5-flash-lite` | Model Gemini nhận diện scoreboard |

---

## 🏗️ 2. Cấu trúc thư mục & Dữ liệu chuẩn hóa

```text
DaliSports-Pipeline/
├── auto_pipeline.py                  # Launcher gốc (chạy lệnh từ thư mục này)
├── quy_trinh.md                      # Tài liệu quy trình chuẩn hóa
├── seo_config/                       # Bộ cấu hình SEO mẫu theo từng giải đấu & bộ môn
│   ├── _default_badminton.json       # Template SEO mặc định cho Cầu Lông
│   ├── _default_pickleball.json      # Template SEO mặc định cho Pickleball
│   └── <tournament-slug>.json        # Cấu hình riêng cho từng giải đấu cụ thể
├── system/                           # Toàn bộ mã nguồn xử lý trung tâm
│   ├── auto_pipeline.py              # Master pipeline điều phối toàn bộ luồng
│   ├── gemini_rotator.py             # Quản lý xoay tua 17+ API Keys & đa Models Gemini
│   ├── gemini_timeline.py            # AI phân tích Scoreboard -> xuất timeline
│   ├── normalize.py                  # Chuẩn hóa tên giải, VĐV, giới hạn <= 100 ký tự
│   ├── seo_helper.py                 # Tự động hóa tiêu đề, mô tả, hashtag, Chapters
│   ├── cut_clips.py                  # FFmpeg Stream Copy cắt video cực nhanh không suy hao
│   ├── upload_source_youtube.py      # Upload video dài lên YouTube kèm Chapters
│   ├── upload_clips.py               # Upload từng clip lên YouTube
│   ├── upload_facebook.py            # Upload Album các clip lên Facebook Page
│   └── debug/                        # Bộ công cụ kiểm thử & Unit Tests
└── YYYY-MM-DD_<tournament-slug>/     # Thư mục giải đấu tự động tạo
    └── <video-slug>/
        ├── <video>.mp4
        ├── <video>_timeline.txt
        ├── <video>_timeline_norms.txt
        └── clips/
            ├── 01 - <Trận 1>.mp4
            ├── 02 - <Trận 2>.mp4
            └── clips_info.txt
```

---

## 🔄 3. Chi tiết 5 Bước Trong Pipeline

### Bước 1: Xác định / Tải Video Nguồn (`yt-dlp`)
- Tự động nhận diện URL Facebook hoặc file cục bộ.
- Tải chất lượng cao nhất: `-f "bestvideo+bestaudio/best" --merge-output-format mp4`.

### Bước 2: AI Nhận diện Scoreboard & Xuất Timeline (`gemini_timeline.py`)
- Quét các khung hình vùng bảng điểm (Scoreboard) ở góc trên bên trái.
- Lọc frame tương phản cao nhất rồi gọi **Gemini API** (tự động xoay tua qua `gemini_rotator.py`).
- Xuất file `<video>_timeline.txt` với format: `START - END - RAW_TITLE`.

### Bước 3: Chuẩn hóa Tiêu đề & Tái cấu trúc Thư mục (`normalize.py`)
- **Tên giải**: VIẾT HOA TOÀN BỘ.
- **Tên VĐV**: Viết hoa chữ cái đầu, tên $\ge 3$ từ rút gọn lấy 2 từ cuối.
- **Độ dài**: Nghiêm ngặt $\le 100$ ký tự theo chuẩn SEO YouTube.
- Tự động di chuyển vào cây thư mục giải đấu chuẩn `YYYY-MM-DD_<slug>/<subslug>/`.

### Bước 4: Cắt Video Trận đấu Siêu tốc (`cut_clips.py`)
- Sử dụng FFmpeg Stream Copy (`-c copy`) không re-encode, tốc độ tối đa và giữ nguyên chất lượng gốc.
- Xuất vào thư mục `clips/` kèm danh mục `clips_info.txt`.

### Bước 5: Upload Tự động Đa Nền tảng (Playwright)
1. **YouTube Source (`upload_source_youtube.py`)**:
   - Đăng video dài kèm danh sách Chapters tự động sinh từ timeline.
   - Thêm SEO template, link mạng xã hội, hotline từ `seo_config/`.
2. **YouTube Clips (`upload_clips.py`)**:
   - Tự động upload từng clip ngắn, tối ưu tiêu đề cho từng trận đấu.
3. **Facebook Album (`upload_facebook.py`)**:
   - Đăng tải trọn bộ clip vào cùng một bài viết Album, tạo caption danh sách các trận thi đấu.
   - Tự động sử dụng phiên đăng nhập lưu tại profile cục bộ (chỉ cần đăng nhập lần đầu).

---

## 🧪 4. Kiểm thử & Đảm bảo Chất lượng Hệ thống

Chạy bộ kiểm thử tự động sau mỗi lần nâng cấp hoặc chỉnh sửa mã nguồn:

```bash
# Chạy bộ unit tests
python system/debug/test_pipeline_units.py

# Kiểm tra biên dịch không lỗi cú pháp
python -m compileall system/
```

---

## 🖥️ 5. Giao Diện Đồ Họa Ứng Dụng Desktop (DaliSports Studio)

Dành cho người dùng muốn điều khiển trực quan, kiểm tra tỷ số AI và chỉnh sửa mốc thời gian trước khi cắt clip:

1. **Khởi động nhanh**:
   - **Tệp thực thi độc lập (Portable EXE):** Double-click shortcut `DaliSports Studio.lnk` tại thư mục gốc hoặc mở trực tiếp `desktop/dist-app/DaliSports Studio 1.0.0.exe` (Dung lượng siêu gọn ~72MB, chạy ngay không cần cài đặt).
   - **Launcher script:** Double-click file `start_studio.bat` hoặc chạy PowerShell: `.\start_studio.ps1`.
   - **Môi trường lập trình:** Chạy `npm run dev` trong thư mục `desktop/`.
2. **Các tính năng trên giao diện**:
   - **🏆 Giải Đấu & Video:** Tự động quét và hiển thị tất cả các giải đấu trong thư mục làm việc, trạng thái video nguồn, số lượng clip và tình trạng upload.
   - **⏱️ Timeline & Tỷ Số:** Hiển thị chi tiết từng trận đấu được AI bóc tách; cho phép sửa tên VĐV, set điểm, căn chỉnh `start_time` / `end_time` và lưu đè file backup `.bak`.
   - **🚀 Pipeline Studio:** Bảng điều khiển kích hoạt pipeline (`Full`, `Chỉ chạy AI`, `Chỉ Cắt Clip`, `Chỉ Upload`), theo dõi tiến trình log real-time và nút **Dừng khẩn cấp**.
   - **📢 SEO & Metadata:** Tự động xem trước tiêu đề, mô tả và tags chuẩn SEO cho YouTube và Facebook, hỗ trợ copy nhanh.
   - **⚙️ Cài Đặt:** Kiểm tra trạng thái Google API Key, Facebook Token, YouTube Secrets và môi trường FFmpeg/Python.

