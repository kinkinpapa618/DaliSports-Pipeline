#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vmix_controller.py
Quản lý tiến trình vMix và điều khiển vMix thông qua Web API (HTTP port 8088):
- Khởi động vMix nạp preset
- Nạp Stream URL & Stream Key
- Lưu preset
"""

import os
import sys
import time
import subprocess
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

DEFAULT_VMIX_EXE = r"C:\Program Files (x86)\vMix\vMix64.exe"
DEFAULT_API_PORT = 8088

class VMixController:
    def __init__(self, vmix_exe: str = "", api_port: int = DEFAULT_API_PORT):
        self.vmix_exe = vmix_exe or os.environ.get("VMIX_EXE_PATH") or DEFAULT_VMIX_EXE
        self.api_port = api_port
        self.api_url = f"http://127.0.0.1:{self.api_port}/api"

    def is_api_alive(self, timeout: float = 1.5) -> bool:
        """Kiểm tra vMix Web API có đang phản hồi không."""
        try:
            req = urllib.request.Request(self.api_url)
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return response.status == 200
        except Exception:
            return False

    def is_process_running(self) -> bool:
        """Kiểm tra tiến trình vMix64.exe hoặc vMix.exe."""
        try:
            output = subprocess.check_output(
                'tasklist /FI "IMAGENAME eq vMix64.exe" /NH',
                shell=True,
                text=True,
                encoding="utf-8",
                errors="ignore"
            )
            if "vMix64.exe" in output:
                return True
            output = subprocess.check_output(
                'tasklist /FI "IMAGENAME eq vMix.exe" /NH',
                shell=True,
                text=True,
                encoding="utf-8",
                errors="ignore"
            )
            return "vMix.exe" in output
        except Exception:
            return self.is_api_alive()

    def launch_vmix(self, preset_path: str, wait_ready: bool = True, timeout: int = 40) -> bool:
        """Khởi động vMix với file preset chỉ định."""
        p_path = Path(preset_path).resolve()
        if not p_path.exists():
            print(f"[!] Lỗi: Không tìm thấy file preset: {p_path}")
            return False

        if not os.path.exists(self.vmix_exe):
            # Thử tìm các đường dẫn phổ biến khác
            alt_paths = [
                r"C:\Program Files\vMix\vMix64.exe",
                r"C:\vMix\vMix64.exe",
                r"C:\Program Files (x86)\vMix\vMix.exe"
            ]
            for alt in alt_paths:
                if os.path.exists(alt):
                    self.vmix_exe = alt
                    break

        if not os.path.exists(self.vmix_exe):
            print(f"[!] Cảnh báo: Không tìm thấy file thực thi vMix tại '{self.vmix_exe}'.")
            print("    Vui lòng kiểm tra lại đường dẫn cài đặt vMix.")
            return False

        # Nếu vMix đang chạy, gọi lệnh OpenPreset qua API hoặc lệnh dòng lệnh
        if self.is_api_alive():
            print(f"[*] vMix đang chạy. Đang nạp Preset: {p_path.name}...")
            self.send_command("OpenPreset", Value=str(p_path))
            time.sleep(2)
            self.focus_vmix_window()
            return True

        print(f"[*] Đang khởi động vMix với Preset: {p_path}...")
        try:
            # Dùng start của Windows shell để đảm bảo mở cửa sổ GUI tương tác trên Desktop
            subprocess.Popen(f'start "" "{self.vmix_exe}" "{p_path}"', shell=True)
        except Exception as e:
            print(f"[!] Lỗi khi khởi động vMix: {e}")
            return False

        if not wait_ready:
            return True

        print("[*] Đang chờ vMix khởi động và kích hoạt Web API...")
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.is_api_alive():
                print("[✓] vMix Web API đã sẵn sàng kết nối!")
                time.sleep(2)  # Cho vMix ổn định hoàn toàn inputs
                self.focus_vmix_window()
                return True
            time.sleep(1)

        print("[!] Hết thời gian chờ (timeout) kích hoạt vMix Web API.")
        return False

    def focus_vmix_window(self):
        """Đưa cửa sổ giao diện vMix lên màn hình chính."""
        try:
            import ctypes
            user32 = ctypes.windll.user32

            def enum_cb(hwnd, extra):
                if user32.IsWindowVisible(hwnd):
                    length = user32.GetWindowTextLengthW(hwnd)
                    if length > 0:
                        buff = ctypes.create_unicode_buffer(length + 1)
                        user32.GetWindowTextW(hwnd, buff, length + 1)
                        title = buff.value.lower()
                        if "vmix" in title and "code" not in title and "studio" not in title:
                            user32.ShowWindow(hwnd, 9)
                            user32.SetForegroundWindow(hwnd)
                            return False
                return True

            WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
            user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
        except Exception:
            pass

    def send_command(self, function: str, **params) -> bool:
        """Gửi Function tới vMix Web API."""
        query_params = {"Function": function}
        for k, v in params.items():
            if v is not None:
                query_params[k] = str(v)

        url = f"{self.api_url}/?{urllib.parse.urlencode(query_params)}"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status == 200
        except Exception as e:
            print(f"[!] Lỗi gọi vMix API ({function}): {e}")
            return False

    def set_streaming_settings(self, stream_url: str, stream_key: str, channel: int = 1) -> bool:
        """Nạp Stream URL và Stream Key vào vMix."""
        ch_idx = str(max(0, channel - 1))
        print(f"[*] Đang nạp thông số Streaming vào vMix (Channel {channel}, Index {ch_idx})...")
        success_url = True
        if stream_url:
            success_url = self.send_command("StreamingSetURL", Value=stream_url, SelectedName=ch_idx)
        
        success_key = self.send_command("StreamingSetKey", Value=stream_key, SelectedName=ch_idx)
        
        if success_key:
            print("[✓] Đã nạp thành công Stream Key vào vMix!")
            return True
        else:
            print("[!] Không thể nạp Stream Key vào vMix. Hãy kiểm tra kết nối Web API.")
            return False

    def start_streaming(self, channel: int = 1) -> bool:
        """Bật Stream trên vMix."""
        return self.send_command("StartStreaming", Value=str(channel))

    def stop_streaming(self, channel: int = 1) -> bool:
        """Tắt Stream trên vMix."""
        return self.send_command("StopStreaming", Value=str(channel))

if __name__ == "__main__":
    controller = VMixController()
    print(f"Kiểm tra vMix: process={controller.is_process_running()}, api_alive={controller.is_api_alive()}")
