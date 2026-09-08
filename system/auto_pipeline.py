#!/usr/bin/env python3
# auto_pipeline.py - Master Pipeline: Tự động hóa 100% xử lý video từ Link/File đến YouTube
# Quy trình: Download (nếu là URL) -> Scan Timeline (Gemini Flash) -> Normalize -> Cut Clips -> Upload YouTube
#
# Cách dùng:
#   python auto_pipeline.py "https://www.facebook.com/dalisportss/videos/..."
#   python auto_pipeline.py "dalisportss_video10.mp4"
#   python auto_pipeline.py "dalisportss_video10.mp4" --review-timeline
#   python auto_pipeline.py "dalisportss_video10.mp4" --skip-upload
import os
import sys
import time
import argparse
import subprocess
import glob
import re

sys.stdout.reconfigure(encoding="utf-8")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import gemini_timeline
import normalize
import shutil

try:
    import seo_helper
except ImportError:
    seo_helper = None

FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def print_banner(text: str, char="="):
    line = char * 60
    print(f"\n{line}\n  {text}\n{line}")


def parse_date_to_iso(date_str: str) -> str:
    """Chuyển '30/08/2026' hoặc '30-08-2026' hoặc '2026-08-30' -> '2026-08-30'"""
    if not date_str:
        return time.strftime("%Y-%m-%d")
    date_str = date_str.strip()
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%Y/%m/%d", "%d.%m.%Y"):
        try:
            t = time.strptime(date_str, fmt)
            return time.strftime("%Y-%m-%d", t)
        except Exception:
            continue
    # Fallback: tìm chuỗi ngày trong text
    m = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", date_str)
    if m:
        try:
            d, mo, y = m.groups()
            return f"{y}-{int(mo):02d}-{int(d):02d}"
        except Exception:
            pass
    return time.strftime("%Y-%m-%d")


def get_tournament_folder(tournament_name: str, date_str: str = "") -> str:
    """Tạo tên thư mục YYYY-MM-DD_slug trong Sân 2/"""
    iso = parse_date_to_iso(date_str)
    if seo_helper:
        slug = seo_helper.slugify(tournament_name or "unknown-tournament")
    else:
        slug = re.sub(r"[^a-z0-9]+", "-", (tournament_name or "unknown-tournament").lower()).strip("-")
    # Giới hạn slug 50 ký tự để path không quá dài
    slug = slug[:50].strip("-")
    folder_name = f"{iso}_{slug}"
    return os.path.join(FOLDER, folder_name)


def get_video_subfolder_name(video_path: str, tournament_name: str = "") -> str:
    """Tạo slug ngắn cho video con trong tournament folder.
    Ưu tiên phần sau '📅' hoặc suffix ngắn gọn, ví dụ 'Sáng 30/8' -> 'sang-30-8'"""
    base = os.path.splitext(os.path.basename(video_path))[0]
    # Loại bỏ prefix tournament nếu có để tránh trùng lặp
    if tournament_name and tournament_name.lower() in base.lower():
        # Cắt bỏ phần tournament
        idx = base.lower().find(tournament_name.lower()) + len(tournament_name)
        suffix = base[idx:].strip(" -|📍").strip()
        if suffix:
            base = suffix
    # Ưu tiên phần sau emoji 📅
    if "📅" in base:
        base = base.split("📅")[-1].strip()
    elif "📍" in base:
        # Lấy sau 📍 nhưng trước 📅 nếu có
        parts = base.split("📍")
        if len(parts) > 1:
            # Giữ phần sau cùng sau 📅 nếu có, không thì sau 📍
            base = parts[-1].strip()
    # Làm sạch ký tự thừa
    base = re.sub(r"^[🔴\s\[\]LIVE\s]+", "", base, flags=re.IGNORECASE).strip(" -")
    if not base or len(base) < 3:
        base = os.path.splitext(os.path.basename(video_path))[0][:30]
    if seo_helper:
        slug = seo_helper.slugify(base)
    else:
        slug = re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-")
    slug = slug[:40].strip("-") or "video"
    # Thêm prefix số nếu slug quá chung (tránh trùng)
    return slug


def is_url(path: str) -> bool:
    return path.startswith("http://") or path.startswith("https://")


def _resolve_local_for_url(url: str, output_dir: str = None) -> str:
    """Resolve chính xác file mp4 đã tải cho 1 URL bằng yt-dlp (không tải về).

    Dùng `yt-dlp --print filename` để lấy đúng tên file theo tiêu đề như khi tải,
    rồi kiểm tra file đó có tồn tại trên đĩa hay không. Tránh chọn nhầm file mới
    nhất của một video khác khi dùng --skip-download với URL.
    """
    output_dir = output_dir or FOLDER
    try:
        out = subprocess.run(
            [os.environ.get("YTDLP", "yt-dlp"), "--print", "filename",
             "-o", os.path.join(output_dir, "%(title)s.%(ext)s"), url],
            capture_output=True, timeout=60
        )
        if out.returncode == 0:
            raw = out.stdout or b""
            # Giải mã dung sai: yt-dlp trên Windows có thể xuất tên file theo
            # encoding console (cp1258) thay vì UTF-8 khi tên có tiếng Việt.
            name = None
            for enc in ("utf-8", "cp1258", "latin-1"):
                try:
                    name = raw.decode(enc).strip().splitlines()
                    if name:
                        break
                except Exception:
                    name = None
            if name:
                cand = name[0].strip()
                if os.path.exists(cand):
                    print(f"[+] Khớp file đã tải cho URL: {os.path.basename(cand)}")
                    return cand
                print(f"[!] URL tương ứng file '{os.path.basename(cand)}' chưa có trên đĩa.")
    except Exception as e:
        print(f"[!] Không resolve được URL bằng yt-dlp: {e}")

    # Fallback: liệt kê các file đã tải để người dùng chọn đúng
    cands = glob.glob(os.path.join(FOLDER, "*.mp4"))
    cands = [c for c in cands if "clip" not in os.path.basename(c).lower()
             and "timeline" not in os.path.basename(c).lower()]
    if cands:
        print("[*] Các file source đã có trên máy (hãy truyền đúng đường dẫn nếu cần):")
        for c in sorted(cands, key=os.path.getmtime, reverse=True):
            print(f"    - {os.path.basename(c)}")
    return None


def download_video(url: str, output_dir: str) -> str:
    """Tải video bằng yt-dlp và trả về đường dẫn file mp4 tải về"""
    print_banner(f"BƯỚC 1: TẢI VIDEO TỪ URL ({url})")
    
    # Lấy danh sách file mp4 trước khi tải để phát hiện file mới
    before_files = set(glob.glob(os.path.join(output_dir, "*.mp4")))
    
    cmd = [
        "yt-dlp",
        "-f", "bestvideo+bestaudio/best",
        "-N", "4",
        "-o", os.path.join(output_dir, "%(title)s.%(ext)s"),
        "--no-playlist",
        "--merge-output-format", "mp4",
        "--remux-video", "mp4",
        "--retry-sleep", "3",
        "--retries", "10",
        url
    ]
    
    print("[*] Đang tải với yt-dlp đa luồng...")
    res = subprocess.run(cmd)
    if res.returncode != 0:
        print("[!] Lỗi khi tải video bằng yt-dlp.")
        return None
    
    after_files = set(glob.glob(os.path.join(output_dir, "*.mp4")))
    new_files = list(after_files - before_files)
    if new_files:
        return max(new_files, key=os.path.getmtime)
    
    # Fallback: lấy file mp4 mới nhất
    all_mp4 = glob.glob(os.path.join(output_dir, "*.mp4"))
    all_mp4 = [f for f in all_mp4 if "clip" not in f.lower() and "timeline" not in f.lower()]
    return max(all_mp4, key=os.path.getmtime) if all_mp4 else None


def review_timeline_prompt(timeline_path: str, timeout_sec: int = 10):
    """Hiển thị timeline và đếm ngược cho phép người dùng kiểm tra hoặc tạm dừng"""
    print_banner("KIỂM TRA TIMELINE TRƯỚC KHI CẮT & UPLOAD", char="-")
    with open(timeline_path, "r", encoding="utf-8") as f:
        print(f.read().strip())
    print("-" * 60)
    print(f"[?] Hệ thống sẽ tự động tiếp tục sau {timeout_sec} giây...")
    print("    - Nhấn [Enter] để tiếp tục ngay")
    print("    - Nhấn [Ctrl + C] để dừng lại nếu muốn sửa file timeline")
    
    try:
        # Đếm ngược đơn giản
        for remaining in range(timeout_sec, 0, -1):
            sys.stdout.write(f"\rTiếp tục sau: {remaining:02d}s (Enter: chạy ngay | Ctrl+C: dừng)... ")
            sys.stdout.flush()
            time.sleep(1)
        print("\r" + " " * 70 + "\r[+] Tiếp tục pipeline!")
    except KeyboardInterrupt:
        print(f"\n[!] Đã dừng pipeline. Bạn có thể mở file '{os.path.basename(timeline_path)}' để chỉnh sửa.")
        print(f"    Sau đó chạy lại với: python auto_pipeline.py \"{timeline_path}\" --skip-timeline")
        sys.exit(0)


def run_pipeline(
    input_target: str,
    platform: str = "youtube",
    yt_mode: str = "source",
    api_key: str = None,
    model: str = "gemini-2.5-flash-lite",
    skip_download: bool = False,
    skip_timeline: bool = False,
    skip_cut: bool = False,
    skip_upload: bool = False,
    dry_run: bool = False,
    review_timeline: bool = False,
    upload_start: int = 0,
    court: str = None,
    tournament: str = None,
    category: str = None,
    sponsor: str = None,
    yt_url: str = None
):
    start_total_time = time.time()
    video_path = None

    if tournament or court or category or sponsor or yt_url:
        print("[*] THÔNG TIN BỔ SUNG TỪ STUDIO:")
        if tournament: print(f"    - Giải đấu: {tournament}")
        if court: print(f"    - Sân thi đấu: {court}")
        if category: print(f"    - Nội dung: {category}")
        if sponsor: print(f"    - Nhà tài trợ: {sponsor}")
        if yt_url: print(f"    - YouTube URL: {yt_url}")

    
    # -------------------------------------------------------------
    # BƯỚC 1: XÁC ĐỊNH HOẶC TẢI FILE VIDEO
    # -------------------------------------------------------------
    if is_url(input_target):
        if skip_download:
            print("[*] Bỏ qua bước download (--skip-download).")
            # Với URL, resolve chính xác file tương ứng bằng yt-dlp (không tải),
            # tránh chọn nhầm file mới nhất của video khác.
            video_path = _resolve_local_for_url(input_target)
        else:
            video_path = download_video(input_target, FOLDER)
    else:
        video_path = os.path.abspath(input_target)
        if os.path.isdir(video_path):
            folder_target = video_path
            vid_candidates = []
            for v_sub in [os.path.join(folder_target, "video"), folder_target]:
                if os.path.exists(v_sub):
                    for ext in ("*.mp4", "*.mkv", "*.mov", "*.ts", "*.avi"):
                        vid_candidates.extend(glob.glob(os.path.join(v_sub, ext)))
            vid_candidates = [v for v in vid_candidates if "timeline" not in os.path.basename(v).lower()]
            if vid_candidates:
                video_path = vid_candidates[0]
                print(f"[*] Tự động chọn video nguồn trong thư mục giải: {os.path.basename(video_path)}")
            elif yt_url and is_url(yt_url):
                print(f"[*] Thư mục chưa có video, tải từ URL YouTube: {yt_url}")
                video_subdir = os.path.join(folder_target, "video")
                os.makedirs(video_subdir, exist_ok=True)
                if skip_download:
                    video_path = _resolve_local_for_url(yt_url)
                else:
                    video_path = download_video(yt_url, video_subdir)
            else:
                print(f"[!] Không tìm thấy file video trong thư mục: {folder_target}")
                return False
    
    if not video_path or not os.path.exists(video_path):
        print(f"[!] Không tìm thấy video hợp lệ: {video_path}")
        return False
    
    video_name = os.path.basename(video_path)
    video_dir = os.path.dirname(video_path)
    base_name = os.path.splitext(video_path)[0]
    timeline_path = base_name + "_timeline.txt"

    # Tự động tìm kiếm file timeline thông minh (root, thư mục giải, hoặc thư mục con)
    tournament_dir = os.path.dirname(video_dir) if os.path.basename(video_dir).lower() in ("video", "clips") else video_dir
    search_dirs = [video_dir, tournament_dir]
    # Tìm thêm trong các thư mục con 1 cấp của tournament_dir
    for sub in glob.glob(os.path.join(tournament_dir, "*")):
        if os.path.isdir(sub) and os.path.basename(sub).lower() not in ("video", "clips", "thumbnails"):
            search_dirs.append(sub)

    if not os.path.exists(timeline_path):
        detected_tl = None
        # 1. Ưu tiên file norms.txt
        for d in search_dirs:
            norms_files = [f for f in glob.glob(os.path.join(d, "*_timeline_norms.txt"))]
            if norms_files:
                detected_tl = norms_files[0]
                break
        # 2. Ưu tiên timeline.txt
        if not detected_tl:
            for d in search_dirs:
                tl_exact = os.path.join(d, "timeline.txt")
                if os.path.exists(tl_exact):
                    detected_tl = tl_exact
                    break
        # 3. Ưu tiên *_timeline.txt
        if not detected_tl:
            for d in search_dirs:
                raw_cands = [f for f in glob.glob(os.path.join(d, "*_timeline.txt")) if "_norms" not in f]
                if raw_cands:
                    detected_tl = raw_cands[0]
                    break
        # 4. Ưu tiên file timeline.json (tự động xuất ra file txt nếu cần)
        if not detected_tl:
            for d in search_dirs:
                json_f = os.path.join(d, "timeline.json")
                if os.path.exists(json_f):
                    try:
                        import json
                        with open(json_f, "r", encoding="utf-8") as jf:
                            jdata = json.load(jf)
                            m_list = jdata if isinstance(jdata, list) else jdata.get("matches", [])
                            if m_list:
                                out_txt = os.path.join(tournament_dir, "timeline.txt")
                                lines = []
                                for m in m_list:
                                    s = m.get("start_time", "00:00:00")
                                    e = m.get("end_time", "00:00:00")
                                    rnd = m.get("round", "")
                                    cat = m.get("category", "")
                                    pa = m.get("player_a", "Đội A")
                                    pb = m.get("player_b", "Đội B")
                                    lines.append(f"{s} - {e} | {cat} | {rnd} | {pa} vs {pb}")
                                with open(out_txt, "w", encoding="utf-8") as tf:
                                    tf.write("\n".join(lines))
                                detected_tl = out_txt
                                print(f"[*] Đã chuyển đổi timeline.json thành: {out_txt}")
                                break
                    except Exception as err_json:
                        print(f"[!] Lỗi đọc timeline.json: {err_json}")

        if detected_tl:
            timeline_path = detected_tl
            print(f"[*] Tự động phát hiện timeline có sẵn: {os.path.basename(timeline_path)} ({timeline_path})")

    norms_path = os.path.splitext(timeline_path)[0] + "_norms.txt" if "_timeline" in timeline_path else base_name + "_timeline_norms.txt"

    print(f"\n[+] Video mục tiêu: {video_name}")
    print(f"[+] Đường dẫn: {video_path}")
    print(f"[+] File Timeline: {timeline_path}")

    # -------------------------------------------------------------
    # BƯỚC 2: TRÍCH XUẤT TIMELINE BẰNG GEMINI FLASH API
    # -------------------------------------------------------------
    if skip_timeline:
        if os.path.exists(timeline_path):
            print_banner(f"BƯỚC 2: DÙNG FILE TIMELINE CÓ SẴN ({os.path.basename(timeline_path)})")
        else:
            print(f"[!] --skip-timeline được bật nhưng không tìm thấy file timeline tại: {timeline_path}")
            return False
    else:
        print_banner("BƯỚC 2: TỰ ĐỘNG SCAN TIMELINE VỚI GEMINI FLASH API")
        res_timeline = gemini_timeline.generate_timeline(
            video_path=video_path,
            output_path=timeline_path,
            api_key=api_key,
            model=model,
            step_sec=10
        )
        if not res_timeline or not os.path.exists(timeline_path):
            print("[!] Quét timeline thất bại. Dừng pipeline.")
            return False

    if review_timeline:
        review_timeline_prompt(timeline_path, timeout_sec=10)

    # -------------------------------------------------------------
    # BƯỚC 3: CHUẨN HÓA TIÊU ĐỀ
    # -------------------------------------------------------------
    print_banner("BƯỚC 3: CHUẨN HÓA TIÊU ĐỀ VIDEO")
    normalize.process_file(timeline_path)
    if not os.path.exists(norms_path):
        print(f"[!] Không tìm thấy file norms sau khi chuẩn hóa: {norms_path}")

    # -------------------------------------------------------------
    # BƯỚC 3B: TÁI CẤU TRÚC VÀO THƯ MỤC GIẢI (YYYY-MM-DD_slug/)
    # -------------------------------------------------------------
    try:
        # Đọc tournament_name từ norms để tạo thư mục giải
        tournament_name_for_folder = tournament.strip() if tournament else ""
        date_for_folder = ""
        cfg_for_folder = None
        if not tournament_name_for_folder and os.path.exists(norms_path):
            with open(norms_path, "r", encoding="utf-8") as f:
                for line in f:
                    parts = [p.strip() for p in line.strip().split(" | ")]
                    if len(parts) >= 2:
                        tournament_name_for_folder = parts[1]
                        break
        # Lấy date + tournament_full chuẩn từ seo_config
        if seo_helper and tournament_name_for_folder:
            cfg_for_folder = seo_helper.load_seo_config(tournament_name_for_folder, video_path)
            if cfg_for_folder:
                date_for_folder = cfg_for_folder.get("date", "")
                raw = tournament_name_for_folder
                clean = cfg_for_folder.get("tournament_full", "")
                if clean and raw.startswith(clean):
                    tournament_name_for_folder = clean
                elif clean and len(raw) > len(clean) + 10 and clean.lower() in raw.lower():
                    tournament_name_for_folder = clean
        tournament_dir = get_tournament_folder(tournament_name_for_folder or os.path.splitext(os.path.basename(video_path))[0], date_for_folder)
        os.makedirs(tournament_dir, exist_ok=True)
        # Tạo video subfolder riêng cho mỗi link (nếu cùng giải thì chung tournament_dir, khác video subfolder)
        video_slug = get_video_subfolder_name(video_path, tournament_name_for_folder)
        video_subdir = os.path.join(tournament_dir, video_slug)
        # Kiểm tra đã ở đúng video subfolder chưa
        video_dir = os.path.dirname(os.path.abspath(video_path))
        if os.path.abspath(video_dir) == os.path.abspath(video_subdir):
            print(f"[+] Video đã trong thư mục video: {os.path.basename(tournament_dir)}/{os.path.basename(video_subdir)}/ (không cần di chuyển)")
        else:
            # Nếu video đang ở tournament root (cấu trúc cũ), cần chuyển vào subfolder
            os.makedirs(video_subdir, exist_ok=True)
            if os.path.abspath(video_dir) == os.path.abspath(tournament_dir):
                print_banner(f"TÁI CẤU TRÚC VÀO VIDEO SUBFOLDER: {os.path.basename(tournament_dir)}/{os.path.basename(video_subdir)}/", char="-")
            else:
                print_banner(f"TÁI CẤU TRÚC VÀO THƯ MỤC GIẢI: {os.path.basename(tournament_dir)}/{os.path.basename(video_subdir)}/", char="-")
            for src in [video_path, timeline_path, norms_path]:
                if src and os.path.exists(src):
                    dest = os.path.join(video_subdir, os.path.basename(src))
                    if os.path.abspath(src) == os.path.abspath(dest):
                        print(f"  [SKIP] {os.path.basename(src)} đã ở đúng vị trí")
                        continue
                    if os.path.exists(dest):
                        print(f"  [SKIP] {os.path.basename(src)} đã tồn tại ở đích")
                    else:
                        print(f"  [MOVE] {os.path.basename(src)} -> {os.path.basename(tournament_dir)}/{os.path.basename(video_subdir)}/")
                        shutil.move(src, dest)
            # Cập nhật lại path sau khi move
            video_path = os.path.join(video_subdir, os.path.basename(video_path))
            timeline_path = os.path.join(video_subdir, os.path.basename(timeline_path))
            norms_path = os.path.join(video_subdir, os.path.basename(norms_path))
            print(f"[+] Đã chuyển vào: {video_subdir}")
            # Di chuyển clips cũ nếu có (từ tournament root) vào video subfolder nếu chưa có clips
            legacy_clips = os.path.join(tournament_dir, "clips")
            new_clips = os.path.join(video_subdir, "clips")
            if os.path.isdir(legacy_clips) and not os.path.exists(new_clips):
                # Không move hết, chỉ copy nếu legacy có clips (giữ lại cho backward compat)
                pass
    except Exception as e:
        import traceback
        print(f"[!] Lỗi tái cấu trúc thư mục giải (bỏ qua, tiếp tục ở thư mục gốc): {e}")
        traceback.print_exc()

    video_dir = os.path.dirname(os.path.abspath(video_path))
    clips_dir = os.path.join(video_dir, "clips")

    # -------------------------------------------------------------
    # BƯỚC 4: CẮT CLIP TỪNG TRẬN ĐẤU (FFmpeg Stream Copy)
    # -------------------------------------------------------------
    if skip_cut:
        print_banner("BƯỚC 4: BỎ QUA CẮT CLIP (--skip-cut)")
    else:
        print_banner("BƯỚC 4: CẮT TỪNG TRẬN THÀNH CLIP (FFmpeg Stream Copy)")
        _sys_dir = os.path.dirname(os.path.abspath(__file__))
        cut_cmd = [sys.executable, os.path.join(_sys_dir, "cut_clips.py"), video_path, timeline_path]
        res_cut = subprocess.run(cut_cmd)
        if res_cut.returncode != 0:
            print("[!] Lỗi khi cắt clip.")
            return False

    # -------------------------------------------------------------
    # BƯỚC 5: TỰ ĐỘNG UPLOAD (YOUTUBE SOURCE/CLIPS & FACEBOOK ALBUM)
    # -------------------------------------------------------------
    if skip_upload:
        print_banner("BƯỚC 5: BỎ QUA UPLOAD (--skip-upload)")
    elif dry_run:
        print_banner(f"BƯỚC 5: CHẠY THỬ UPLOAD {platform.upper()} (--dry-run)")
        _sys_dir = os.path.dirname(os.path.abspath(__file__))
        if platform in ["youtube", "both"]:
            if yt_mode in ["source", "both"]:
                print("\n[*] [DRY-RUN] YouTube Source + Chapters:")
                subprocess.run([sys.executable, os.path.join(_sys_dir, "upload_source_youtube.py"), video_path, norms_path, "--dry-run"])
            if yt_mode in ["clips", "both"]:
                print("\n[*] [DRY-RUN] YouTube Clips:")
                yt_cmd = [sys.executable, os.path.join(_sys_dir, "upload_clips.py"), "--clips-dir", clips_dir, "--dry-run"]
                if upload_start > 0:
                    yt_cmd.extend(["--start", str(upload_start)])
                subprocess.run(yt_cmd)
        if platform in ["facebook", "both"]:
            print("\n[*] [DRY-RUN] Facebook Album:")
            subprocess.run([sys.executable, os.path.join(_sys_dir, "upload_facebook.py"), "--clips-dir", clips_dir, "--dry-run"])
    else:
        _sys_dir = os.path.dirname(os.path.abspath(__file__))
        if platform in ["youtube", "both"]:
            if yt_mode in ["source", "both"]:
                print_banner("BƯỚC 5A1: TỰ ĐỘNG ĐĂNG VIDEO SOURCE (DÀI) LÊN YOUTUBE KÈM CHAPTERS")
                res_yt = subprocess.run([sys.executable, os.path.join(_sys_dir, "upload_source_youtube.py"), video_path, norms_path])
                if res_yt.returncode != 0:
                    print("[!] Upload YouTube Source gặp sự cố, kiểm tra upload_source_log.txt.")

            if yt_mode in ["clips", "both"]:
                print_banner("BƯỚC 5A2: TỰ ĐỘNG ĐĂNG TỪNG CLIP LÊN YOUTUBE")
                yt_cmd = [sys.executable, os.path.join(_sys_dir, "upload_clips.py"), "--clips-dir", clips_dir]
                if upload_start > 0:
                    yt_cmd.extend(["--start", str(upload_start)])
                res_yt_clips = subprocess.run(yt_cmd)
                if res_yt_clips.returncode != 0:
                    print("[!] Upload YouTube Clips gặp sự cố, kiểm tra upload_log.txt.")

        if platform in ["facebook", "both"]:
            print_banner("BƯỚC 5B: TỰ ĐỘNG ĐĂNG TOÀN BỘ CLIPS THÀNH 1 ALBUM LÊN FACEBOOK")
            res_fb = subprocess.run([sys.executable, os.path.join(_sys_dir, "upload_facebook.py"), "--clips-dir", clips_dir])
            if res_fb.returncode != 0:
                print("[!] Upload Facebook Album gặp sự cố, kiểm tra upload_fb_log.txt.")

    elapsed = time.time() - start_total_time
    print_banner(f"HOÀN TẤT TOÀN BỘ PIPELINE TRONG {elapsed/60:.1f} PHÚT!")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Master Pipeline: Tự động hóa 100% xử lý video thể thao từ URL/Video đến YouTube & Facebook",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ sử dụng:
  python auto_pipeline.py "https://www.facebook.com/dalisportss/videos/27910556711971209"
  python auto_pipeline.py "video.mp4" --platform facebook
  python auto_pipeline.py "video.mp4" --platform youtube --yt-mode both
  python auto_pipeline.py "video.mp4" --platform both
  python auto_pipeline.py "video.mp4" --dry-run
  python auto_pipeline.py "video.mp4" --skip-upload
        """
    )
    parser.add_argument("input", nargs="?", default=None, help="Link video Facebook hoặc đường dẫn file .mp4")
    parser.add_argument("--platform", choices=["youtube", "facebook", "both"], default="youtube", help="Nền tảng upload: youtube, facebook, hoặc both (mặc định: youtube)")
    parser.add_argument("--yt-mode", choices=["source", "clips", "both"], default="source", help="Chế độ đăng YouTube: source (video dài kèm chapters), clips (từng clip), hoặc both (mặc định: source)")
    parser.add_argument("--api-key", default=None, help="Gemini API Key (mặc định đọc từ .env)")
    parser.add_argument("--model", default="gemini-2.5-flash-lite", help="Model Gemini (mặc định: gemini-2.5-flash-lite)")
    parser.add_argument("--skip-download", action="store_true", help="Bỏ qua bước tải video")
    parser.add_argument("--skip-timeline", action="store_true", help="Bỏ qua bước scan timeline nếu đã có file *_timeline.txt")
    parser.add_argument("--skip-cut", action="store_true", help="Bỏ qua bước cắt clip (nếu chỉ muốn upload video gốc)")
    parser.add_argument("--skip-upload", action="store_true", help="Bỏ qua bước upload")
    parser.add_argument("--dry-run", action="store_true", help="Chạy thử nghiệm không upload thật")
    parser.add_argument("--review-timeline", action="store_true", help="Đếm ngược 10s cho phép kiểm tra timeline trước khi cắt")
    parser.add_argument("--start", type=int, default=0, help="Bắt đầu upload từ clip thứ N")
    parser.add_argument("--court", default=None, help="Tên sân thi đấu (ví dụ: Sân 1, Sân 2)")
    parser.add_argument("--tournament", default=None, help="Tên giải đấu (ghi đè)")
    parser.add_argument("--category", default=None, help="Nội dung thi đấu (ví dụ: Đôi Nam, Đơn Nữ)")
    parser.add_argument("--sponsor", default=None, help="Nhà tài trợ / đơn vị đồng hành")
    parser.add_argument("--yt-url", default=None, help="URL video YouTube nguồn")

    args, unknown = parser.parse_known_args()
    if unknown:
        print(f"[*] Cảnh báo: Các tham số chưa hỗ trợ được bỏ qua an toàn: {unknown}")

    target = args.input
    if not target:
        # Nếu không truyền tham số, tìm video mp4 mới nhất trong thư mục hoặc yêu cầu nhập
        cands = glob.glob(os.path.join(FOLDER, "*.mp4"))
        cands = [c for c in cands if "timeline" not in os.path.basename(c).lower()]
        if cands:
            latest = max(cands, key=os.path.getmtime)
            print(f"[*] Không truyền tham số, tự động chọn video mới nhất: {os.path.basename(latest)}")
            target = latest
        else:
            target = input("Nhập link video Facebook hoặc đường dẫn file .mp4: ").strip()

    if not target:
        print("[!] Không có dữ liệu đầu vào. Thoát.")
        sys.exit(1)

    run_pipeline(
        input_target=target,
        platform=args.platform,
        yt_mode=args.yt_mode,
        api_key=args.api_key,
        model=args.model,
        skip_download=args.skip_download,
        skip_timeline=args.skip_timeline,
        skip_cut=args.skip_cut,
        skip_upload=args.skip_upload,
        dry_run=args.dry_run,
        review_timeline=args.review_timeline,
        upload_start=args.start,
        court=args.court,
        tournament=args.tournament,
        category=args.category,
        sponsor=args.sponsor,
        yt_url=args.yt_url
    )


if __name__ == "__main__":
    main()
