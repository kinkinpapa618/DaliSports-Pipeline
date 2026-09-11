#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vmix_preset_builder.py
Tự động quét nguyên liệu trong thư mục giải đấu (backdrop, logos, tvc, điều hành)
và sinh file preset.vmix tương thích 100% với vMix nguyên bản (native XML).
"""

import os
import sys
import json
import re
import argparse
import xml.etree.ElementTree as ET
from pathlib import Path

# Đảm bảo in UTF-8 không lỗi trên Windows
sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "templates" / "vmix"
MASTER_TEMPLATE = TEMPLATES_DIR / "master_template.vmix"
TITLE_GTZIP_PATH = Path(r"C:\Users\dalis\Desktop\Khach Moi - TriColor v2.gtzip")
if not TITLE_GTZIP_PATH.exists():
    TITLE_GTZIP_PATH = Path(r"E:\Vmix\Khach Moi - TriColor v2.gtzip")

def find_first_file(directory: Path, extensions: tuple) -> Path | None:
    if not directory.exists() or not directory.is_dir():
        return None
    lower_exts = tuple(e.lower() for e in extensions)
    for f in directory.iterdir():
        if f.is_file() and f.suffix.lower() in lower_exts:
            return f
    return None

def find_all_files(directory: Path, extensions: tuple) -> list[Path]:
    if not directory.exists() or not directory.is_dir():
        return []
    lower_exts = tuple(e.lower() for e in extensions)
    result = [f for f in directory.iterdir() if f.is_file() and f.suffix.lower() in lower_exts]
    return sorted(result, key=lambda p: p.name.lower())

def build_vmix_preset(tournament_path: str) -> dict:
    clean_path = str(tournament_path).strip().strip('"\'').rstrip('\\/').strip('"\'')
    t_path = Path(clean_path).resolve()
    if not t_path.exists():
        return {"success": False, "error": f"Không tìm thấy thư mục: {t_path}"}

    # 1. Đọc tournament_info.json
    info_file = t_path / "dieu_hanh" / "tournament_info.json"
    if not info_file.exists():
        info_file = t_path / "tournament_info.json"

    tournament_info = {}
    if info_file.exists():
        try:
            with open(info_file, "r", encoding="utf-8") as f:
                tournament_info = json.load(f)
        except Exception as e:
            print(f"[!] Cảnh báo: Không thể đọc {info_file}: {e}")

    t_name = tournament_info.get("name") or t_path.name
    t_sport = (tournament_info.get("sportType") or tournament_info.get("sport") or "pickleball").lower()

    # 2. Quét nguyên liệu trong livestream/
    livestream_dir = t_path / "livestream"
    livestream_dir.mkdir(parents=True, exist_ok=True)

    img_exts = (".png", ".jpg", ".jpeg", ".webp", ".bmp")
    vid_exts = (".mp4", ".mov", ".avi", ".mkv", ".ts")

    # Backdrop giải đấu
    backdrop_dir = livestream_dir / "backdrop"
    backdrop_file = find_first_file(backdrop_dir, img_exts) or find_first_file(livestream_dir, img_exts)

    # Sponsor Logos
    logos_dir = livestream_dir / "logos"
    logo_files = find_all_files(logos_dir, img_exts)

    # TVC Videos
    tvc_dir = livestream_dir / "tvc"
    tvc_files = find_all_files(tvc_dir, vid_exts)

    # 3. Nạp Master Template chuẩn Native vMix
    if not MASTER_TEMPLATE.exists():
        return {"success": False, "error": f"Không tìm thấy master template tại {MASTER_TEMPLATE}"}

    try:
        tree = ET.parse(str(MASTER_TEMPLATE))
        root = tree.getroot()
    except Exception as e:
        return {"success": False, "error": f"Lỗi parse Master Template XML: {e}"}

    # 4. Thay thế Backdrop vào Input màn hình chờ (Input Type=1 hoặc Title chứa man-hinh-cho / Backdrop)
    if backdrop_file:
        for inp in root.findall("Input"):
            orig = inp.attrib.get("OriginalTitle", "")
            title = inp.attrib.get("Title", "")
            if "man-hinh-cho" in orig.lower() or "backdrop" in orig.lower() or "man-hinh-cho" in title.lower():
                inp.text = str(backdrop_file.resolve())
                inp.attrib["Title"] = f"Backdrop - {t_name}"
                inp.attrib["OriginalTitle"] = f"Backdrop - {t_name}"
                break

    # 5. Thêm Title Khách Mời (Khach Moi - TriColor v2.gtzip) nếu chưa có
    title_path_str = str(TITLE_GTZIP_PATH.resolve()) if TITLE_GTZIP_PATH.exists() else ""
    if title_path_str:
        has_gtzip = any("gtzip" in (inp.attrib.get("OriginalTitle") or "").lower() for inp in root.findall("Input"))
        if not has_gtzip:
            # Tạo node Input GT Title chuẩn vMix
            gt_elem = ET.Element("Input", {
                "Type": "9000",
                "Position": "0",
                "RangeStart": "0",
                "RangeStop": "0",
                "State": "1",
                "OriginalTitle": TITLE_GTZIP_PATH.name,
                "Title": TITLE_GTZIP_PATH.name,
                "Loop": "False",
                "VolumeF": "1",
                "Muted": "True",
                "BalanceF": "0",
                "AspectRatio": "100",
                "Category": "0",
                "MouseClickAction": "0",
                "GOClickAction": "20",
                "Solo": "False",
                "BusMaster": "True",
                "XML": '<items><item name="GuestSub.Text" version="2"><value>Khách mời Talkshow</value></item><item name="GuestTitle.Text" version="2"><value>Giám đốc Marketing</value></item><item name="GuestName.Text" version="2"><value>NGUYỄN VĂN A</value></item></items>'
            })
            gt_elem.text = title_path_str
            # Chèn vào danh sách inputs
            root.append(gt_elem)

    # 6. Cập nhật Stream URL & Key nếu có trong tournament_info
    stream_url = tournament_info.get("streamUrl")
    stream_key = tournament_info.get("streamKey")
    if stream_key:
        dest0 = root.find(".//Destination0")
        if dest0 is not None and dest0.text:
            dest0_text = dest0.text
            dest0_text = re.sub(r"<Stream>.*?</Stream>", f"<Stream>{stream_key}</Stream>", dest0_text)
            dest0_text = re.sub(r"<Facebook_Stream_Key\.username>.*?</Facebook_Stream_Key\.username>", f"<Facebook_Stream_Key.username>{stream_key}</Facebook_Stream_Key.username>", dest0_text)
            if stream_url:
                dest0_text = re.sub(r"<URL>.*?</URL>", f"<URL>{stream_url}</URL>", dest0_text)
            dest0.text = dest0_text

    # 7. Xuất preset.vmix
    output_preset = livestream_dir / "preset.vmix"
    tree.write(str(output_preset), encoding="utf-8", xml_declaration=False)

    result = {
        "success": True,
        "presetPath": str(output_preset),
        "tournamentName": t_name,
        "sport": t_sport,
        "hasBackdrop": bool(backdrop_file),
        "backdropPath": str(backdrop_file) if backdrop_file else None,
        "hasTitleGtzip": bool(title_path_str),
        "logosCount": len(logo_files),
        "tvcCount": len(tvc_files),
        "templateUsed": "master_template.vmix (Native vMix XML)"
    }
    return result

def main():
    parser = argparse.ArgumentParser(description="Tự động sinh vMix Native Preset từ nguyên liệu giải đấu")
    parser.add_argument("--tournament", "-t", type=str, default="", help="Đường dẫn thư mục giải đấu")
    parser.add_argument("--json", action="store_true", help="Xuất kết quả định dạng JSON")
    args = parser.parse_args()

    raw_dir = args.tournament or os.getcwd()
    tournament_dir = str(raw_dir).strip().strip('"\'').rstrip('\\/').strip('"\'')
    res = build_vmix_preset(tournament_dir)

    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        if res.get("success"):
            print(f"[✓] Đã tạo thành công Native Preset vMix:")
            print(f"    - File: {res['presetPath']}")
            print(f"    - Giải: {res['tournamentName']} ({res['sport']})")
            print(f"    - Backdrop: {'Có' if res['hasBackdrop'] else 'Chưa có'}")
            print(f"    - Title GTZip: {'Có' if res['hasTitleGtzip'] else 'Không'}")
            print(f"    - Số Logo tài trợ: {res['logosCount']}")
            print(f"    - Số TVC quảng cáo: {res['tvcCount']}")
        else:
            print(f"[X] Lỗi tạo Preset: {res.get('error')}")
            sys.exit(1)

if __name__ == "__main__":
    main()
