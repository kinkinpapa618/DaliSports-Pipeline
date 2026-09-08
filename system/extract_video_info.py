#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_video_info.py - Trích xuất và tự động lọc dữ liệu thông minh từ link video (YouTube / Facebook)
Phục vụ tính năng: Nhập link video -> Agent tự động phân tích và tạo giải đấu trong bảng
"""

import sys
import os
import re
import json
import subprocess
from datetime import datetime

# Đảm bảo xuất UTF-8 trên Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


def remove_vietnamese_accents(text: str) -> str:
    """Chuyển chuỗi tiếng Việt có dấu thành không dấu để làm slug"""
    patterns = {
        '[àáạảãâầấậẩẫăằắặẳẵ]': 'a',
        '[èéẹẻẽêềếệểễ]': 'e',
        '[ìíịỉĩ]': 'i',
        '[òóọỏõôồốộổỗơờớợởỡ]': 'o',
        '[ùúụủũưừứựửữ]': 'u',
        '[ỳýỵỷỹ]': 'y',
        '[đ]': 'd',
        '[ÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴ]': 'A',
        '[ÈÉẸẺẼÊỀẾỆỂỄ]': 'E',
        '[ÌÍỊỈĨ]': 'I',
        '[ÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠ]': 'O',
        '[ÙÚỤỦŨƯỪỨỰỬỮ]': 'U',
        '[ỲÝỴỶỸ]': 'Y',
        '[Đ]': 'D'
    }
    output = text
    for regex, replacement in patterns.items():
        output = re.sub(regex, replacement, output)
    return output


def generate_slug(text: str) -> str:
    """Tạo slug chuẩn dạng: giai-cau-long-ba-vi-2026"""
    clean = remove_vietnamese_accents(text).lower()
    # Loại bỏ tiền tố ngày nếu có
    clean = re.sub(r'^\d{4}-\d{2}-\d{2}[-_]', '', clean)
    clean = re.sub(r'[^a-z0-9]+', '-', clean)
    clean = clean.strip('-')
    return clean or "giai-dau-the-thao"


def clean_live_noise(text: str) -> str:
    """Loại bỏ các cụm từ thừa thường gặp trong tiêu đề livestream"""
    noise_patterns = [
        r'^\s*\[.*?\]\s*',                     # [Trực tiếp]
        r'^\s*\(.*?\)\s*',                     # (Trực tiếp)
        r'\b(trực tiếp|truc tiep|livestream|live stream|live|phát trực tiếp)\b\s*[:|\-]?\s*',
        r'\b(full match|fullmatch|highlight|highlights|toàn trận)\b\s*[:|\-]?\s*',
        r'\b(hd|full hd|1080p|720p|4k|60fps)\b',
        r'#\w+',                               # Hashtags
    ]
    res = text
    for pat in noise_patterns:
        res = re.sub(pat, ' ', res, flags=re.IGNORECASE)
    # Rút gọn khoảng trắng
    res = re.sub(r'\s+', ' ', res).strip()
    return res


def extract_tournament_name(raw_title: str) -> str:
    """Trích xuất tên giải đấu sạch từ tiêu đề video"""
    cleaned = clean_live_noise(raw_title)

    # Thử tách theo các phân vùng phổ biến: | hoặc -
    segments = re.split(r'\s*[|]\s*', cleaned)
    if len(segments) == 1:
        segments = re.split(r'\s+-\s+', cleaned)

    # 1. Tìm segment chứa từ khóa 'giải' hoặc 'cup' hoặc 'championship'
    for seg in segments:
        s = seg.strip(" -|:[]()")
        if re.search(r'\b(giải|giai|cúp|cup|open|championship|tournament)\b', s, re.IGNORECASE):
            # Cắt bớt phần vòng đấu hoặc sân nếu dính vào segment
            s = re.sub(r'\s*-\s*(bán kết|chung kết|tứ kết|vòng bảng|sân \d+).*$', '', s, flags=re.IGNORECASE)
            s = s.strip(" -|:[]()")
            if s:
                return s

    # 2. Nếu không tìm thấy segment đặc thù, lấy segment đầu tiên có nghĩa (> 5 ký tự)
    for seg in segments:
        s = seg.strip(" -|:[]()")
        if len(s) >= 5 and not re.search(r'^(sân|court|bán kết|chung kết)\b', s, re.IGNORECASE):
            return s

    clean_final = cleaned.strip(" -|:[]()")
    return clean_final or "Giải Đấu Thể Thao"


def detect_sport(text: str) -> str:
    """Tự động nhận diện môn thể thao từ tiêu đề"""
    lower = text.lower()
    if "pickleball" in lower or "pickle" in lower:
        return "pickleball"
    if "tennis" in lower or "quần vợt" in lower or "quan vot" in lower:
        return "tennis"
    if "cầu lông" in lower or "cau long" in lower or "badminton" in lower:
        return "badminton"
    return "badminton"


def detect_category(text: str) -> str:
    """Nhận diện nội dung thi đấu"""
    lower = text.lower()
    if "đôi nam nữ" in lower or "doi nam nu" in lower or "nam nữ" in lower:
        return "Đôi Nam Nữ"
    if "đôi nam" in lower or "doi nam" in lower:
        return "Đôi Nam"
    if "đôi nữ" in lower or "doi nu" in lower:
        return "Đôi Nữ"
    if "đơn nam" in lower or "don nam" in lower:
        return "Đơn Nam"
    if "đơn nữ" in lower or "don nu" in lower:
        return "Đơn Nữ"
    return "Đôi Nam"


def detect_court(text: str) -> str:
    """Nhận diện số sân"""
    m = re.search(r'\b(sân|court)\s*(\d+|[a-zA-Z])\b', text, re.IGNORECASE)
    if m:
        return f"Sân {m.group(2).upper()}"
    return "Sân 1"


def detect_round(text: str) -> str:
    """Nhận diện vòng đấu"""
    lower = text.lower()
    if "chung kết" in lower or "chung ket" in lower or "final" in lower:
        return "Chung Kết"
    if "bán kết" in lower or "ban ket" in lower or "semi" in lower:
        return "Bán Kết"
    if "tứ kết" in lower or "tu ket" in lower or "quarter" in lower:
        return "Tứ Kết"
    if "vòng bảng" in lower or "vong bang" in lower or "group" in lower:
        return "Vòng Bảng"
    return "Vòng Bảng"


def detect_date(raw_title: str, upload_date_str: str = "") -> str:
    """Trích xuất ngày tháng theo định dạng YYYY-MM-DD"""
    if upload_date_str and len(upload_date_str) == 8 and upload_date_str.isdigit():
        return f"{upload_date_str[0:4]}-{upload_date_str[4:6]}-{upload_date_str[6:8]}"

    # Thử tìm DD/MM/YYYY hoặc DD-MM-YYYY trong tiêu đề
    m = re.search(r'(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})', raw_title)
    if m:
        d, mon, y = m.group(1).zfill(2), m.group(2).zfill(2), m.group(3)
        return f"{y}-{mon}-{d}"

    # Thử tìm YYYY-MM-DD
    m2 = re.search(r'(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})', raw_title)
    if m2:
        y, mon, d = m2.group(1), m2.group(2).zfill(2), m2.group(3).zfill(2)
        return f"{y}-{mon}-{d}"

    # Fallback: Ngày hôm nay
    return datetime.now().strftime("%Y-%m-%d")


def extract_from_url(url: str) -> dict:
    """Gọi yt-dlp để lấy metadata JSON từ URL"""
    raw_title = ""
    upload_date = ""
    duration = 0
    thumbnail = ""
    channel = ""
    description = ""

    try:
        # Chạy yt-dlp lấy thông tin json nhanh (--skip-download)
        cmd = [
            os.environ.get("YTDLP", "yt-dlp"),
            "--dump-json",
            "--no-playlist",
            "--skip-download",
            "--no-warnings",
            "--ignore-errors",
            url
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=20, encoding="utf-8", errors="replace")
        if res.returncode == 0 and res.stdout.strip():
            # yt-dlp có thể xuất 1 hoặc nhiều dòng JSON nếu có cảnh báo, lấy dòng JSON hợp lệ đầu tiên
            for line in res.stdout.strip().splitlines():
                line = line.strip()
                if line.startswith("{") and line.endswith("}"):
                    try:
                        data = json.loads(line)
                        raw_title = data.get("title") or ""
                        upload_date = data.get("upload_date") or ""
                        duration = data.get("duration") or 0
                        thumbnail = data.get("thumbnail") or ""
                        channel = data.get("channel") or data.get("uploader") or ""
                        description = data.get("description") or ""
                        break
                    except Exception:
                        continue
    except Exception as e:
        sys.stderr.write(f"Cảnh báo yt-dlp: {e}\n")

    # Nếu yt-dlp không lấy được title, đoán từ url
    if not raw_title:
        # Cố gắng lấy ID hoặc phần pathname của url làm tiêu đề tạm
        clean_url = url.split("?")[0].rstrip("/")
        slug_part = os.path.basename(clean_url)
        raw_title = f"Video Trực Tiếp - {slug_part}" if slug_part else "Video Thể Thao Mới"

    tournament_name = extract_tournament_name(raw_title)
    sport_type = detect_sport(raw_title + " " + description)
    category = detect_category(raw_title)
    court = detect_court(raw_title)
    round_name = detect_round(raw_title)
    date_str = detect_date(raw_title, upload_date)
    slug = generate_slug(tournament_name)
    folder_name = f"{date_str}_{slug}"

    return {
        "success": True,
        "url": url,
        "raw_title": raw_title,
        "tournament_name": tournament_name,
        "date": date_str,
        "sport_type": sport_type,
        "category": category,
        "court": court,
        "round": round_name,
        "slug": slug,
        "folder_name": folder_name,
        "duration_seconds": duration,
        "thumbnail": thumbnail,
        "channel": channel
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "Vui lòng truyền link video URL."}))
        sys.exit(1)

    url = sys.argv[1].strip()
    if not url:
        print(json.dumps({"success": False, "error": "URL trống."}))
        sys.exit(1)

    info = extract_from_url(url)
    print(json.dumps(info, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
