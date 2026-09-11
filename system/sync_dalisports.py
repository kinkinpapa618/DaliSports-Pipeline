#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_dalisports.py
Đồng bộ hóa dữ liệu giải đấu từ nền tảng app.dalisports.vn (tab SẮP DIỄN RA) về DaliSports Studio.
1. Quét danh sách giải từ API https://api.dalisports.vn/api/tournaments/groups?per_page=99
2. Lọc các giải trong tab "SẮP DIỄN RA" (end_date >= ngày hiện tại)
3. Tự động khởi tạo / cập nhật thư mục chuẩn cho từng giải:
   - dieu_hanh/tournament_info.json
   - dieu_hanh/danh_sach_vdv.csv (tải toàn bộ VĐV các nội dung)
   - dieu_hanh/dieu_le.txt
   - livestream/backdrop/ (tải banner backdrop chính thức từ R2)
   - livestream/preset.vmix (tự động xuất file preset vMix theo bộ môn)
   - START.bat (launcher 1-click livestream)
4. Trả về kết quả JSON chi tiết cho Electron App / Web Remote
"""

import os
import sys
import re
import csv
import json
import time
import shutil
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "system"))

from vmix_preset_builder import build_vmix_preset

API_BASE = "https://api.dalisports.vn/api"
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

def fetch_json(url: str, timeout: int = 20) -> dict:
    req = urllib.request.Request(url, headers=DEFAULT_HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))

def download_file(url: str, dest_path: Path, timeout: int = 30) -> bool:
    try:
        req = urllib.request.Request(url, headers=DEFAULT_HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content = resp.read()
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            with open(dest_path, "wb") as f:
                f.write(content)
        return True
    except Exception as e:
        print(f"[!] Lỗi tải file {url}: {e}")
        return False

def slugify(text: str) -> str:
    import unicodedata
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    text = text.replace('Đ', 'D').replace('đ', 'd').lower()
    text = re.sub(r"[^a-z0-9\s-]", " ", text)
    text = re.sub(r"\s+", "-", text.strip())
    text = re.sub(r"-+", "-", text)
    return text.strip("-")

def detect_sport_type(name: str) -> str:
    name_l = name.lower()
    if "pickleball" in name_l:
        return "pickleball"
    elif "cầu lông" in name_l or "badminton" in name_l:
        return "badminton"
    elif "tennis" in name_l or "quần vợt" in name_l:
        return "tennis"
    return "pickleball"

def sync_upcoming_tournaments(workspace_root: Path = PROJECT_ROOT) -> dict:
    print("=" * 65)
    print("  🔄 ĐỒNG BỘ DỮ LIỆU GIẢI ĐẤU TỪ APP.DALISPORTS.VN VỀ STUDIO  ")
    print("=" * 65)

    now_utc = datetime.now(timezone.utc)
    today_str = now_utc.strftime("%Y-%m-%d")

    groups_url = f"{API_BASE}/tournaments/groups?per_page=99"
    try:
        data = fetch_json(groups_url)
        all_groups = data.get("items", [])
    except Exception as e:
        err_msg = f"Không thể kết nối đến {groups_url}: {str(e)}"
        print(f"[!] {err_msg}")
        return {"success": False, "error": err_msg}

    # Lọc các giải đấu ở tab "SẮP DIỄN RA" (end_date >= ngày hiện tại)
    upcoming_groups = []
    for g in all_groups:
        end_date_str = g.get("end_date") or g.get("start_date") or ""
        if not end_date_str:
            continue
        try:
            # Parse ISO date (e.g. 2026-09-12T13:00:00Z)
            clean_date = end_date_str.replace("Z", "+00:00")
            end_dt = datetime.fromisoformat(clean_date)
            # Nếu ngày kết thúc >= hôm nay (so sánh theo UTC date)
            if end_dt.date() >= now_utc.date():
                upcoming_groups.append(g)
        except Exception:
            # Fallback so sánh chuỗi YYYY-MM-DD
            if end_date_str[:10] >= today_str:
                upcoming_groups.append(g)

    print(f"[*] Tìm thấy {len(upcoming_groups)} giải đấu SẮP DIỄN RA trên app.dalisports.vn.")

    synced_items = []

    for g in upcoming_groups:
        g_name = g.get("group_name", "Giải Đấu").strip()
        g_id = g.get("group_id", "")
        slug = g.get("slug") or slugify(g_name)
        start_date = g.get("start_date", today_str)[:10]
        banner_url = g.get("banner_url")
        venue = g.get("venue", "Sân thi đấu chính")
        venue_address = g.get("venue_address", "")
        sport = detect_sport_type(g_name)
        sub_tournaments = g.get("tournaments", [])

        folder_name = f"{start_date}_{slug}"
        tournament_dir = workspace_root / folder_name
        is_new = not tournament_dir.exists()
        action = "created" if is_new else "updated"

        print(f"\n--- Đang xử lý: {g_name} ({action.upper()}) ---")
        print(f"    Thư mục: {tournament_dir.name}")
        print(f"    Ngày: {start_date} | Sân: {venue} | Bộ môn: {sport}")

        # 1. Tạo cây thư mục chuẩn
        for d in [
            "dieu_hanh",
            "livestream/backdrop",
            "livestream/logos",
            "livestream/tvc",
            "video",
            "clips",
            "thumbnails"
        ]:
            (tournament_dir / d).mkdir(parents=True, exist_ok=True)

        # 2. Tải Backdrop / Banner chính thức từ hệ thống
        has_backdrop = False
        backdrop_file = None
        # Kiểm tra xem trong thư mục backdrop đã có file chưa
        existing_backdrops = list((tournament_dir / "livestream" / "backdrop").glob("*.*"))
        if existing_backdrops:
            has_backdrop = True
            backdrop_file = existing_backdrops[0]
        elif banner_url and banner_url.startswith("http"):
            ext = os.path.splitext(banner_url.split("?")[0])[1] or ".jpg"
            save_path = tournament_dir / "livestream" / "backdrop" / f"backdrop_{g_id[:8]}{ext}"
            print(f"    [*] Đang tải Backdrop từ: {banner_url[:60]}...")
            if download_file(banner_url, save_path):
                has_backdrop = True
                backdrop_file = save_path
                print(f"    [✓] Đã tải Backdrop thành công: {save_path.name}")

        # 3. Lấy danh sách vận động viên các nội dung thi đấu
        all_participants = []
        sub_tournament_names = []

        for sub in sub_tournaments:
            sub_id = sub.get("id")
            sub_name = sub.get("name", "Nội dung")
            sub_tournament_names.append(sub_name)

            if sub_id:
                part_url = f"{API_BASE}/tournaments/{sub_id}/participants?per_page=99"
                try:
                    p_data = fetch_json(part_url)
                    p_items = p_data.get("items", [])
                    for p in p_items:
                        p["_sub_tournament"] = sub_name
                        all_participants.append(p)
                except Exception as e:
                    print(f"    [!] Lỗi lấy danh sách VĐV nội dung '{sub_name}': {e}")

        # Ghi danh sách VĐV ra file CSV (UTF-8-SIG để Excel tiếng Việt không bị lỗi font)
        csv_file = tournament_dir / "dieu_hanh" / "danh_sach_vdv.csv"
        try:
            with open(csv_file, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "STT",
                    "Họ và tên VĐV 1",
                    "CLB / Đơn vị 1",
                    "Giới tính 1",
                    "Họ và tên VĐV 2",
                    "CLB / Đơn vị 2",
                    "Giới tính 2",
                    "Nội dung thi đấu",
                    "Điểm trình cặp",
                    "Số bốc thăm / Vị trí",
                    "Trạng thái điểm danh"
                ])
                for idx, p in enumerate(all_participants, 1):
                    p1_name = p.get("player1_name") or ""
                    p1_club = p.get("player1_club_name") or ""
                    p1_gender = "Nam" if p.get("player1_gender") == "male" else ("Nữ" if p.get("player1_gender") == "female" else "")
                    p2_name = p.get("player2_name") or ""
                    p2_club = p.get("player2_club_name") or ""
                    p2_gender = "Nam" if p.get("player2_gender") == "male" else ("Nữ" if p.get("player2_gender") == "female" else "")
                    sub_t = p.get("_sub_tournament", "")
                    rating = p.get("combined_rating", "")
                    roll_num = p.get("rolling_number", "")
                    checked = "Đã điểm danh" if p.get("checked_in") else "Chưa"
                    writer.writerow([
                        idx, p1_name, p1_club, p1_gender, p2_name, p2_club, p2_gender, sub_t, rating, roll_num, checked
                    ])
            print(f"    [✓] Đã xuất danh sách {len(all_participants)} VĐV vào {csv_file.name}")
        except Exception as e:
            print(f"    [!] Không thể ghi file CSV VĐV: {e}")

        # 4. Ghi file thông tin giải đấu tournament_info.json
        info_file = tournament_dir / "dieu_hanh" / "tournament_info.json"
        existing_info = {}
        if info_file.exists():
            try:
                with open(info_file, "r", encoding="utf-8") as f:
                    existing_info = json.load(f)
            except Exception:
                pass

        t_info = {
            "name": g_name,
            "folderName": folder_name,
            "date": start_date,
            "sport": sport,
            "sportType": sport,
            "court": venue,
            "venue": venue,
            "venue_address": venue_address,
            "sponsor": existing_info.get("sponsor", ""),
            "description": existing_info.get("description") or f"Giải đấu được đồng bộ từ app.dalisports.vn (Mã: {g_id[:8]})",
            "sub_tournaments": sub_tournament_names,
            "dalisports_group_id": g_id,
            "sync_source": "app.dalisports.vn",
            "last_synced_at": datetime.now().isoformat()
        }
        with open(info_file, "w", encoding="utf-8") as f:
            json.dump(t_info, f, ensure_ascii=False, indent=2)

        # 5. Mẫu điều lệ giải nếu chưa có
        dieu_le_file = tournament_dir / "dieu_hanh" / "dieu_le.txt"
        if not dieu_le_file.exists():
            with open(dieu_le_file, "w", encoding="utf-8") as f:
                f.write(f"ĐIỀU LỆ THI ĐẤU - {g_name}\n")
                f.write(f"Thời gian: {start_date}\n")
                f.write(f"Địa điểm: {venue}\n")
                if venue_address:
                    f.write(f"Địa chỉ: {venue_address}\n")
                f.write(f"Bộ môn: {sport.upper()}\n\n")
                f.write("CÁC NỘI DUNG THI ĐẤU:\n")
                for s in sub_tournament_names:
                    f.write(f"- {s}\n")

        # 6. File launcher 1-Click START.bat
        bat_file = tournament_dir / "START.bat"
        if not bat_file.exists():
            sample_bat = PROJECT_ROOT / "templates" / "samples" / "START.bat"
            if sample_bat.exists():
                shutil.copy2(sample_bat, bat_file)
            else:
                with open(bat_file, "w", encoding="utf-8") as f:
                    f.write("@echo off\n")
                    f.write("chcp 65001 >nul\n")
                    f.write("title DaliSports - 1-Click Livestream\n")
                    f.write('python "%~dp0..\\system\\start_live_orchestrator.py" --tournament "%~dp0"\n')
                    f.write("pause\n")

        # 7. Khởi tạo timeline.json nếu chưa có
        timeline_file = tournament_dir / "timeline.json"
        if not timeline_file.exists():
            with open(timeline_file, "w", encoding="utf-8") as f:
                json.dump([], f)

        # 8. Tự động chuẩn hóa & xuất file Preset vMix
        preset_built = False
        preset_file = tournament_dir / "livestream" / "preset.vmix"
        try:
            b_res = build_vmix_preset(str(tournament_dir))
            if b_res.get("success"):
                preset_built = True
                print(f"    [✓] Đã tự động sinh Preset vMix: {preset_file.name} (Bộ môn: {sport})")
        except Exception as e:
            print(f"    [!] Chưa thể build preset.vmix: {e}")

        synced_items.append({
            "name": g_name,
            "folder": folder_name,
            "path": str(tournament_dir),
            "action": action,
            "sport": sport,
            "start_date": start_date,
            "venue": venue,
            "has_backdrop": has_backdrop,
            "athletes_count": len(all_participants),
            "sub_tournaments_count": len(sub_tournament_names),
            "preset_built": preset_built
        })

    print("\n" + "=" * 65)
    print(f"  ✅ ĐỒNG BỘ HOÀN TẤT: {len(synced_items)} giải đấu đã sẵn sàng trong Studio!  ")
    print("=" * 65)

    return {
        "success": True,
        "upcoming_count": len(upcoming_groups),
        "synced_count": len(synced_items),
        "items": synced_items
    }

if __name__ == "__main__":
    result = sync_upcoming_tournaments()
    print("\n[JSON RESULT]")
    print(json.dumps(result, ensure_ascii=False, indent=2))
