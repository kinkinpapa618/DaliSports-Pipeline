#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
start_live_orchestrator.py
Bộ điều phối 1-Click Livestream:
1. Kiểm tra & chuẩn hóa Preset vMix (gọi vmix_preset_builder.py nếu chưa có)
2. Bật vMix nạp Preset tương ứng của giải
3. Mở Facebook Live Producer, điền Tiêu đề/Mô tả chuẩn SEO và lấy Stream Key
4. Tự động nạp Stream Key vào vMix qua Web API
5. Giữ tab Facebook Live trên màn hình và thông báo sẵn sàng cho kỹ thuật viên
"""

import os
import sys
import time
import json
import argparse
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "system"))

from vmix_preset_builder import build_vmix_preset
from vmix_controller import VMixController
from live_facebook_streamkey import get_facebook_stream_info

def load_settings() -> dict:
    defaults = {
        "vmixExePath": r"C:\Program Files (x86)\vMix\vMix64.exe",
        "facebookPageUrl": "https://www.facebook.com/dalisportss",
        "vmixApiPort": 8088
    }

    # Đọc từ .env nếu có
    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k, v = k.strip(), v.strip().strip('"').strip("'")
                        if k == "VMIX_EXE_PATH" and v:
                            defaults["vmixExePath"] = v
                        elif k == "FACEBOOK_PAGE_URL" and v:
                            defaults["facebookPageUrl"] = v
                        elif k == "VMIX_API_PORT" and v:
                            defaults["vmixApiPort"] = int(v)
        except Exception:
            pass

    settings_file = PROJECT_ROOT / "desktop" / "settings.json"
    if not settings_file.exists():
        settings_file = PROJECT_ROOT / "settings.json"
    
    if settings_file.exists():
        try:
            with open(settings_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                defaults.update(data)
        except Exception:
            pass

    # Ưu tiên biến môi trường hệ thống
    if os.environ.get("VMIX_EXE_PATH"):
        defaults["vmixExePath"] = os.environ["VMIX_EXE_PATH"]
    if os.environ.get("FACEBOOK_PAGE_URL"):
        defaults["facebookPageUrl"] = os.environ["FACEBOOK_PAGE_URL"]
    if os.environ.get("VMIX_API_PORT"):
        try:
            defaults["vmixApiPort"] = int(os.environ["VMIX_API_PORT"])
        except ValueError:
            pass

    return defaults

def start_one_click_live(tournament_path: str, page_url: str = "") -> bool:
    clean_path = str(tournament_path).strip().strip('"\'').rstrip('\\/').strip('"\'')
    t_path = Path(clean_path).resolve()
    print("=" * 65)
    print("  🚀 DALISPORTS PIPELINE - BẮT ĐẦU QUY TRÌNH 1-CLICK LIVESTREAM  ")
    print("=" * 65)
    print(f"[*] Thư mục giải đấu: {t_path}")

    settings = load_settings()
    vmix_exe = settings.get("vmixExePath", r"C:\Program Files (x86)\vMix\vMix64.exe")
    fb_page = page_url or settings.get("facebookPageUrl", "https://www.facebook.com/dalisportss")
    api_port = int(settings.get("vmixApiPort", 8088))

    # --- BƯỚC 1: KIỂM TRA & CHUẨN BỊ PRESET VMIX ---
    preset_file = t_path / "livestream" / "preset.vmix"
    if not preset_file.exists():
        print("\n[*] Chưa tìm thấy preset.vmix của giải. Đang tiến hành tạo mới từ nguyên liệu...")
        preset_res = build_vmix_preset(str(t_path))
        if not preset_res.get("success"):
            print(f"[!] Không thể tạo preset vMix: {preset_res.get('error')}")
            return False
        print(f"[✓] Đã tạo preset.vmix thành công ({preset_res.get('sport')})!")
    else:
        print(f"[✓] Đã có file preset: {preset_file}")

    # --- BƯỚC 2: KHỞI ĐỘNG VMIX & NẠP PRESET ---
    print("\n" + "-" * 50)
    print("[*] BƯỚC 2: Khởi động vMix và kết nối Web API...")
    controller = VMixController(vmix_exe=vmix_exe, api_port=api_port)
    vmix_ready = controller.launch_vmix(str(preset_file), wait_ready=True, timeout=35)
    if not vmix_ready:
        print("[!] Không thể kết nối tới vMix Web API. Bạn hãy chắc chắn vMix đang chạy.")
        print("    Tiếp tục tiến trình lấy Stream Key Facebook...")

    # --- BƯỚC 3: MỞ TRÌNH DUYỆT FACEBOOK LIVE & LẤY STREAM KEY ---
    print("\n" + "-" * 50)
    print("[*] BƯỚC 3: Mở trình duyệt, tạo sự kiện Facebook Live với SEO & lấy Stream Key...")
    fb_out = get_facebook_stream_info(str(t_path), fb_page)
    res_data = fb_out.get("result", {})
    stream_key = res_data.get("streamKey", "")
    server_url = res_data.get("serverUrl", "rtmps://live-api-s.facebook.com:443/rtmp/")

    # Nếu chưa lấy được tự động, cho phép dán tay nhanh
    if not stream_key:
        print("\n[?] Hãy dán Stream Key từ Facebook vào đây nếu chưa nhận diện tự động:")
        try:
            manual_key = input("👉 Stream Key (hoặc nhấn Enter để bỏ qua): ").strip()
            if manual_key:
                stream_key = manual_key
        except Exception:
            pass

    # --- BƯỚC 4: NẠP STREAM KEY VÀO VMIX ---
    if stream_key:
        print("\n" + "-" * 50)
        print("[*] BƯỚC 4: Đang truyền Stream Key vào vMix...")
        if controller.is_api_alive():
            success = controller.set_streaming_settings(server_url, stream_key)
            if success:
                print("🎉 THÀNH CÔNG: vMix đã nhận Stream Key và lưu cấu hình!")
            else:
                print("[!] Không thể truyền key vào vMix qua API. Bạn có thể paste trực tiếp vào vMix Settings.")
        else:
            print("[!] vMix API không phản hồi. Bạn hãy paste Stream Key thủ công vào mục Stream của vMix:")
            print(f"    Stream Key: {stream_key}")
    else:
        print("\n[!] Không có Stream Key để nạp vào vMix.")

    # --- BƯỚC 5: SẴN SÀNG PHÁT SÓNG ---
    print("\n" + "=" * 65)
    print("  ✅ TẤT CẢ ĐÃ SẴN SÀNG PHÁT SÓNG (READY TO GO LIVE)!  ")
    print("=" * 65)
    print("1. Kiểm tra góc máy, âm thanh và bảng điểm trong vMix.")
    print("2. Bấm nút [STREAM] ở góc dưới vMix để bắt đầu gửi tín hiệu hình ảnh.")
    print("3. Kiểm tra khung hình preview trên cửa sổ Facebook Live đang mở.")
    print("4. Bấm nút [Phát trực tiếp / Go Live] trên Facebook để chính thức lên sóng!")
    print("\n👉 Nhấn Enter để gửi lệnh 'StartStreaming' từ vMix ngay lập tức, hoặc đóng cửa sổ này khi xong...")
    
    try:
        user_input = input()
        if controller.is_api_alive():
            print("[*] Đang gửi lệnh StartStreaming tới vMix...")
            controller.start_streaming()
            print("[✓] Đã kích hoạt Stream trên vMix thành công!")
    except Exception:
        pass

    # Giữ browser context
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print("\n[*] Đã kết thúc tiến trình hỗ trợ Livestream.")

    return True

def main():
    parser = argparse.ArgumentParser(description="DaliSports 1-Click Livestream Orchestrator")
    parser.add_argument("--tournament", "-t", type=str, default="", help="Đường dẫn thư mục giải đấu")
    parser.add_argument("--page", "-p", type=str, default="", help="URL Fanpage Facebook")
    args = parser.parse_args()

    raw_dir = args.tournament or os.getcwd()
    tournament_dir = str(raw_dir).strip().strip('"\'').rstrip('\\/').strip('"\'')
    start_one_click_live(tournament_dir, args.page)

if __name__ == "__main__":
    main()
