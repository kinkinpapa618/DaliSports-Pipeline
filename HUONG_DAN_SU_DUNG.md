# HƯỚNG DẪN SỬ DỤNG HỆ THỐNG DALISPORTS STUDIO

**Tác giả & Bản quyền:** Hữu Mạnh - BMB  
**Email hỗ trợ:** [huumanh.info@aol.com](mailto:huumanh.info@aol.com)  
**Phiên bản:** DaliSports Studio v1.0.0 (Windows x64)  
**Engine xử lý:** Gemini 2.5 AI + FFmpeg GPU Accelerated + Electron + Python 3.12  

---

## 1. TỔNG QUAN HỆ THỐNG

**DaliSports Studio** là phần mềm quản lý và tự động hóa chuỗi xử lý video thể thao chuyên biệt cho **Cầu Lông** và **Pickleball**. Phần mềm giúp biên tập viên và quản trị viên:
- Tự động trích xuất thông tin giải đấu và trận đấu từ link video phát trực tiếp.
- Tự động phân tích mốc thời gian (Timeline) và tỷ số từng trận bằng AI.
- Cắt clip hàng loạt siêu tốc bằng công nghệ GPU Stream Copy (không cần render lại, giữ 100% chất lượng gốc).
- Tải video nguồn dài (Full Match / Livestream) lên YouTube với danh sách mốc thời gian (Chapters) tự động chèn trong phần mô tả.
- Tự động hóa đăng tải hàng loạt clip ngắn lên Facebook Fanpage và YouTube Shorts / Videos.

---

## 2. CÀI ĐẶT & KHỞI ĐỘNG ỨNG DỤNG

Hệ thống cung cấp 2 phương thức sử dụng trong thư mục `desktop/dist-app/`:

### Cách 1: Cài đặt qua trình hướng dẫn Setup Wizard (Khuyên dùng)
1. Chạy tệp **`DaliSports Studio Setup 1.0.0.exe`**.
2. Trình cài đặt sẽ hiển thị:
   - Cho phép chọn thư mục cài đặt (mặc định: `Program Files` hoặc thư mục người dùng).
   - Tự động tạo biểu tượng ngoài màn hình Desktop (**Desktop Shortcut**) kèm logo DaliSports chuẩn.
   - Tự động thêm vào menu Start của Windows.
3. Sau khi cài xong, có thể gỡ bỏ dễ dàng bất kỳ lúc nào trong Windows Settings (Add or remove programs).

### Cách 2: Bản Portable (Chạy ngay không cần cài đặt)
- Chạy trực tiếp tệp **`DaliSports Studio 1.0.0.exe`**.
- Có thể copy vào USB hoặc bất kỳ ổ đĩa nào để mở và làm việc ngay lập tức.

---

## 3. QUY TRÌNH SỬ DỤNG CHI TIẾT TỪNG BƯỚC

### BƯỚC 1: TẠO GIẢI ĐẤU TỰ ĐỘNG BẰNG LINK VIDEO (AGENT AI)
1. Tại màn hình **Giải Đấu & Video**, nhấn vào nút **`+ Nhập Link Video`** (có huy hiệu `Agent AI`).
2. Dán đường link video YouTube hoặc Facebook của trận đấu/livestream vào ô nhập.
3. Nhấn **`⚡ Phân Tích & Lọc Dữ Liệu`**:
   - Hệ thống tự động bóc tách tiêu đề, ngày tải, thời lượng và ảnh bìa gốc.
   - Bộ lọc AI tiếng Việt tự động loại bỏ các từ thừa livestream (`[TRỰC TIẾP]`, `LIVESTREAM |`, `FULL MATCH`, `1080P`,...), tự động nhận diện môn thể thao (**Cầu Lông** hoặc **Pickleball**), số sân và ngày diễn ra.
4. Kiểm tra lại thông tin trên thẻ xem trước, sau đó nhấn **`Xác Nhận & Chèn Vào Bảng Giải Đấu`**.
5. Hệ thống sẽ tự động tạo cấu trúc thư mục chuẩn:
   ```text
   YYYY-MM-DD_ten-giai-dau/
   ├── video/              (Chứa file video nguồn mp4/mkv)
   ├── clips/              (Chứa các clip trận đấu sau khi cắt)
   ├── thumbnails/         (Chứa ảnh bìa từng trận)
   ├── tournament_info.json(Thông tin giải, link video, nhà tài trợ)
   └── timeline.json       (Danh sách trận đấu và mốc thời gian)
   ```

---

### BƯỚC 2: CHỈNH SỬA THÔNG TIN GIẢI ĐẤU (NÚT EDIT)
- Trên mỗi thẻ giải đấu, ở góc trên bên phải cạnh nhãn bộ môn có:
  - **Nút Bút Chì (Icon Edit)**: Mở hộp thoại chỉnh sửa nhanh:
    - Tên Giải Đấu
    - Ngày Thi Đấu
    - Bộ Môn (Cầu Lông / Pickleball)
    - Link Video Nguồn
    - Sân Thi Đấu & Nội Dung Mặc Định
    - Đơn Vị Tổ Chức / Nhà Tài Trợ
  - **Nút Thư Mục (Icon Folder)**: Mở nhanh thư mục giải trong File Explorer của Windows.
- Khi lưu thay đổi, hệ thống sẽ tự động đồng bộ hóa sang cả `tournament_info.json` và `timeline.json`.

---

### BƯỚC 3: HIỆU ĐÍNH TIMELINE & TỶ SỐ (TIMELINE EDITOR)
1. Nhấn nút xanh dương **`TIMELINE`** trên thẻ giải đấu để chuyển sang tab **Timeline & Tỷ Số**.
2. Hệ thống tự động quét và phân tích thông minh các định dạng timeline có sẵn trong giải:
   - File chuẩn hóa: `*_timeline_norms.txt`
   - File văn bản: `timeline.txt`, `source_timeline.txt`
   - File JSON: `timeline.json`, `raw_ocr_*.json`
3. Tại bảng danh sách trận:
   - Xem và chỉnh sửa mốc thời gian bắt đầu (`Start`) và kết thúc (`End`).
   - Sửa thông tin Vòng đấu (Vòng bảng, Bán kết, Chung kết,...), Nội dung thi đấu và Tên VĐV/Đội tuyển.
   - Tích chọn hoặc bỏ chọn các trận đấu cụ thể cần xuất bản.
4. Nhấn **`Lưu Thay Đổi`** để cập nhật file `timeline.json`.

---

### BƯỚC 4: CHẠY QUY TRÌNH CẮT CLIP HÀNG LOẠT (CHẠY FULL)
1. Nhấn nút xanh lá **`CHẠY FULL`** trên thẻ giải đấu hoặc chuyển sang tab **Pipeline Studio**.
2. Cấu hình các tùy chọn:
   - **Nền tảng xuất bản**: Facebook Fanpage / YouTube / Cả hai.
   - **Chế độ cắt clip**: Tự động nhận diện mốc cắt theo `timeline.json`.
3. Nhấn **`Khởi Chạy Full Pipeline`**:
   - Cửa sổ Console sẽ hiển thị dòng thời gian log trực tiếp theo thời gian thực.
   - Engine FFmpeg GPU sẽ cắt các trận đấu với tốc độ cực đại (chỉ mất vài giây mỗi clip dài 30 phút).
   - Tự động gắn ảnh thumbnail, tạo tiêu đề/mô tả chuẩn SEO thể thao và tải lên kênh.

---

### BƯỚC 5: TẢI VIDEO DÀI NGUỒN LÊN YOUTUBE KÈM CHAPTERS (Y-UPLOAD)
Khi bạn muốn đăng toàn bộ video livestream/full match (dài 3 - 6 tiếng) lên YouTube để khán giả xem lại toàn bộ giải:
1. Nhấn nút đỏ **`Y-UPLOAD`** (hoặc nút **`SOURCE Y-UP`** trên thanh tiêu đề Pipeline Studio).
2. Hệ thống sẽ:
   - Tự động bỏ qua khâu cắt clip lẻ (`--skip-cut`).
   - Đọc danh sách các trận đấu từ `timeline.json`.
   - Tự động sinh danh sách **Chapters YouTube** chèn trực tiếp vào phần Mô Tả:
     ```text
     00:00:00 Trận 01: Vòng Bảng - Đôi Nam | VĐV Nguyễn A vs VĐV Trần B
     00:28:15 Trận 02: Bán Kết - Đôi Nữ | VĐV Lê C vs VĐV Phạm D
     01:05:40 Trận 03: Chung Kết - Đôi Nam Nữ | ...
     ```
   - Tải video nguồn lên kênh YouTube đã chứng thực OAuth.

---

## 4. CÀI ĐẶT HỆ THỐNG & API KEYS

Vào tab **Cài Đặt** trên thanh menu trái:
1. **Google Gemini API Key**: Dùng để bóc tách tỷ số OCR và tối ưu hóa tiêu đề/mô tả tự động. Hỗ trợ mô hình `gemini-2.5-flash-lite` tiết kiệm chi phí và tốc độ cao.
2. **Facebook Fanpage ID & Page Access Token**: Dùng để đăng video và Reels lên trang Facebook.
3. **Chứng thực YouTube OAuth**:
   - Đặt file `client_secrets.json` của Google Cloud vào thư mục gốc của hệ thống.
   - Token đăng nhập sẽ được lưu tại `yt_profile/upload_youtube_oauth.json`.
4. **cookies.txt**: Đặt file `cookies.txt` (xuất từ trình duyệt) ở thư mục gốc để tải video chất lượng cao từ các livestream Facebook/YouTube có giới hạn.

---

## 5. XỬ LÝ SỰ CỐ THƯỜNG GẶP (TROUBLESHOOTING)

| Hiện tượng | Nguyên nhân | Cách khắc phục |
| :--- | :--- | :--- |
| **Không tải được video từ link Facebook/YouTube** | `cookies.txt` bị hết hạn hoặc `yt-dlp` cũ | 1. Cập nhật `yt-dlp`: Chạy `pip install --upgrade yt-dlp`<br>2. Xuất lại file `cookies.txt` mới từ trình duyệt và copy vào thư mục gốc. |
| **Báo lỗi thiếu API Key Gemini** | Chưa nhập key trong tab Cài Đặt | Vào tab **Cài Đặt**, dán API key Gemini và nhấn **Lưu Cấu Hình**. |
| **Không tìm thấy file video trong giải** | File video đặt sai tên hoặc chưa copy vào | Đặt file video `.mp4` vào thư mục `video/` bên trong thư mục giải đấu tương ứng. |
| **Icon app bị lỗi hoặc không mở được** | Đang chạy bản build cũ | Sử dụng bản cài đặt **`DaliSports Studio Setup 1.0.0.exe`** mới nhất tại thư mục `desktop/dist-app/`. |

---

## 6. KIỂM TRA & CẬP NHẬT PHIÊN BẢN MỚI (APP UPDATES)

DaliSports Studio hỗ trợ hệ thống cập nhật phiên bản tự động và thủ công:
1. **Kiểm tra tự động khi khởi động**: Mỗi khi mở ứng dụng, hệ thống sẽ tự động kiểm tra phiên bản mới nhất trên máy chủ. Nếu có bản mới, huy hiệu `Update vX.X.X 🚀` sẽ sáng đèn trên thanh tiêu đề (TitleBar).
2. **Kiểm tra thủ công trong Cài Đặt**:
   - Vào tab **Cài Đặt** -> tìm khối **Cập Nhật & Phiên Bản Ứng Dụng (App Updates)**.
   - Nhấn nút **`Kiểm Tra Bản Mới`**.
   - Khi có bản mới: hệ thống sẽ hiển thị thẻ thông báo phiên bản mới, ngày phát hành, danh sách các tính năng/sửa lỗi mới và nút **`Tải Bản Cập Nhật Ngay`** để tải bộ cài.
3. **Cấu hình máy chủ cập nhật tùy chỉnh**: Bạn có thể chỉ định đường dẫn endpoint manifest JSON tại mục `URL Máy Chủ Cập Nhật (UPDATE_CHECK_URL)`.

---

## 7. BẢN QUYỀN & LIÊN HỆ HỖ TRỢ

Phần mềm được nghiên cứu và phát triển độc quyền bởi:
- **Tác giả:** Hữu Mạnh - BMB
- **Email:** [huumanh.info@aol.com](mailto:huumanh.info@aol.com)
- **Bản quyền:** Copyright © 2026 Hữu Mạnh - BMB. Mọi quyền được bảo lưu.
