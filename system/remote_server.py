#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
remote_server.py - DaliSports Studio Remote Web Access & Cloudflare Tunnel Server
Cung cấp Web REST API, WebSocket streaming log, và Cloudflare Tunnel tự động
để truy cập và điều khiển DaliSports Studio từ xa trên điện thoại, máy tính bảng hoặc bất kỳ máy tính nào.
"""

import os
import sys
import re
import json
import glob
import time
import shutil
import asyncio
import subprocess
import threading
from pathlib import Path
from typing import Optional, List, Dict, Any

# Enforce UTF-8 on Windows Console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

# Determine Workspace Root
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DESKTOP_DIST = os.path.join(WORKSPACE_ROOT, "desktop", "dist")

app = FastAPI(title="DaliSports Studio Remote API", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_custom_header(request, call_next):
    response = await call_next(request)
    response.headers["X-Dali-Server"] = "local-remote-server-v1"
    return response

# Global State
class ServerState:
    def __init__(self):
        self.pipeline_proc: Optional[asyncio.subprocess.Process] = None
        self.pipeline_running = False
        self.ws_clients: List[WebSocket] = []
        self.tunnel_proc: Optional[subprocess.Popen] = None
        self.tunnel_url: Optional[str] = None
        self.tunnel_error: Optional[str] = None
        self.tunnel_thread: Optional[threading.Thread] = None

state = ServerState()

# ============================================================
# Cloudflare Tunnel Management
# ============================================================

def find_cloudflared() -> Optional[str]:
    # 1. System PATH
    w = shutil.which("cloudflared")
    if w and os.path.exists(w):
        return w
    
    # 2. LocalAppData on Windows
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if local_app_data:
        c1 = os.path.join(local_app_data, "Cloudflare", "cloudflared", "cloudflared.exe")
        if os.path.exists(c1):
            return c1
        c2 = os.path.join(local_app_data, "Programs", "cloudflared", "cloudflared.exe")
        if os.path.exists(c2):
            return c2
            
    # 3. User profile path
    user_profile = os.environ.get("USERPROFILE", "")
    if user_profile:
        c3 = os.path.join(user_profile, "AppData", "Local", "Cloudflare", "cloudflared", "cloudflared.exe")
        if os.path.exists(c3):
            return c3

    return None

def _run_tunnel_process(port: int):
    bin_path = find_cloudflared()
    if not bin_path:
        state.tunnel_error = "Không tìm thấy cloudflared.exe trên hệ thống."
        return

    # Bắt buộc dùng --config NUL (Windows) để bỏ qua file ~/.cloudflared/config.yml có sẵn trên máy
    null_device = "NUL" if sys.platform == "win32" else "/dev/null"
    cmd = [bin_path, "tunnel", "--config", null_device, "--url", f"http://127.0.0.1:{port}"]

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="ignore",
            bufsize=1,
        )
        state.tunnel_proc = proc

        while proc.poll() is None:
            line = proc.stdout.readline()
            if not line:
                continue
            m = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
            if m and not state.tunnel_url:
                state.tunnel_url = m.group(0)
                state.tunnel_error = None
                print(f"\n[CLOUDFLARE TUNNEL SAN SANG] Public URL moi: {state.tunnel_url}")
                print_qr(state.tunnel_url)
    except Exception as e:
        state.tunnel_error = str(e)
        print(f"[Tunnel Error] {e}")

def start_tunnel_service(port: int = 8765) -> bool:
    # Luon dung tien trinh cu truoc de moi lan bat se tao ra mot link tunnel moi
    stop_tunnel_service()
    time.sleep(0.5)

    state.tunnel_url = None
    state.tunnel_error = None
    t = threading.Thread(target=_run_tunnel_process, args=(port,), daemon=True)
    t.start()
    state.tunnel_thread = t

    # Cho toi da 15 giay de lay link trycloudflare moi
    t0 = time.time()
    while time.time() - t0 < 15:
        if state.tunnel_url or state.tunnel_error:
            break
        time.sleep(0.3)

    return state.tunnel_url is not None

def stop_tunnel_service():
    if state.tunnel_proc:
        try:
            pid = state.tunnel_proc.pid
            if sys.platform == "win32" and pid:
                subprocess.run(f"taskkill /F /T /PID {pid}", shell=True, capture_output=True)
            else:
                state.tunnel_proc.terminate()
                state.tunnel_proc.kill()
        except Exception:
            pass
        state.tunnel_proc = None
    state.tunnel_url = None
    state.tunnel_error = None

def print_qr(url: str):
    try:
        import qrcode
        qr = qrcode.QRCode()
        qr.add_data(url)
        print("\n" + "=" * 50)
        print(" QUET MA QR NAY TREN DIEN THOAI DE TRUY CAP TU XA:")
        print("=" * 50)
        qr.print_ascii(invert=True)
        print("=" * 50 + "\n")
    except Exception:
        pass

# ============================================================
# API Endpoints
# ============================================================

@app.get("/api/tunnel/status")
async def get_tunnel_status():
    active = (
        state.tunnel_proc is not None 
        and state.tunnel_proc.poll() is None 
        and state.tunnel_url is not None
    )
    return {
        "active": active,
        "url": state.tunnel_url if active else None,
        "error": state.tunnel_error,
    }

@app.post("/api/tunnel/start")
async def api_start_tunnel(port: int = 8765):
    ok = start_tunnel_service(port)
    return {
        "success": ok,
        "url": state.tunnel_url,
        "error": state.tunnel_error,
    }

@app.post("/api/tunnel/stop")
async def api_stop_tunnel():
    stop_tunnel_service()
    return {"success": True}

@app.get("/api/version")
async def get_version():
    pkg_path = os.path.join(WORKSPACE_ROOT, "desktop", "package.json")
    version = "1.1.0"
    if os.path.exists(pkg_path):
        try:
            with open(pkg_path, "r", encoding="utf-8") as f:
                pkg = json.load(f)
                version = pkg.get("version", version)
        except Exception:
            pass
    return {"version": version}

@app.get("/api/update/check")
async def check_update(url: Optional[str] = None):
    # Read manifest
    manifest_path = os.path.join(WORKSPACE_ROOT, "version.json")
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {
                    "hasUpdate": False,
                    "currentVersion": data.get("version", "1.1.0"),
                    "latestVersion": data.get("version", "1.1.0"),
                    "checkedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "releaseNotes": data.get("releaseNotes", []),
                }
        except Exception:
            pass
    return {
        "hasUpdate": False,
        "currentVersion": "1.1.0",
        "latestVersion": "1.1.0",
        "checkedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

@app.get("/api/tournaments")
async def list_tournaments():
    results = []
    if not os.path.exists(WORKSPACE_ROOT):
        return results

    tournament_dir_regex = re.compile(r"^\d{4}-\d{2}-\d{2}_.+$")
    entries = sorted(os.listdir(WORKSPACE_ROOT), reverse=True)

    img_exts = re.compile(r"\.(png|jpg|jpeg|webp|bmp)$", re.I)
    vid_exts = re.compile(r"\.(mp4|mov|avi|mkv|ts)$", re.I)

    for entry in entries:
        folder_path = os.path.join(WORKSPACE_ROOT, entry)
        if not os.path.isdir(folder_path):
            continue
        if not tournament_dir_regex.match(entry):
            continue

        date_match = re.match(r"^(\d{4}-\d{2}-\d{2})", entry)
        date = date_match.group(1) if date_match else ""

        name = entry[11:].replace("-", " ").replace("_", " ").strip()
        name = name.capitalize()

        sport_type = "badminton"
        lower_folder = entry.lower()
        if "pickleball" in lower_folder:
            sport_type = "pickleball"
        elif "tennis" in lower_folder:
            sport_type = "tennis"

        info_file = os.path.join(folder_path, "dieu_hanh", "tournament_info.json")
        if not os.path.exists(info_file):
            info_file = os.path.join(folder_path, "tournament_info.json")

        source_url = None
        court = None
        category = None
        sponsor = None
        description = None
        if os.path.exists(info_file):
            try:
                with open(info_file, "r", encoding="utf-8") as f:
                    info = json.load(f)
                    name = info.get("name", name)
                    sport_type = info.get("sportType", sport_type)
                    source_url = info.get("source_url")
                    court = info.get("court")
                    category = info.get("category")
                    sponsor = info.get("sponsor")
                    description = info.get("description")
            except Exception:
                pass

        # Check video
        video_dir = os.path.join(folder_path, "video")
        has_video = False
        video_file = None
        video_size_mb = 0
        if os.path.exists(video_dir):
            files = os.listdir(video_dir)
            video_files = [f for f in files if vid_exts.search(f)]
            if video_files:
                has_video = True
                video_file = os.path.join("video", video_files[0])
                try:
                    video_size_mb = round(os.path.getsize(os.path.join(video_dir, video_files[0])) / (1024 * 1024))
                except Exception:
                    pass

        # Check timeline
        tl_path = os.path.join(folder_path, "timeline.json")
        has_timeline = os.path.exists(tl_path)
        match_count = 0
        if has_timeline:
            try:
                with open(tl_path, "r", encoding="utf-8") as f:
                    tl_data = json.load(f)
                    if isinstance(tl_data, list):
                        match_count = len(tl_data)
                    elif isinstance(tl_data, dict):
                        match_count = len(tl_data.get("matches", []))
            except Exception:
                pass

        # Check clips
        clips_dir = os.path.join(folder_path, "clips")
        has_clips = False
        clip_count = 0
        if os.path.exists(clips_dir):
            clip_files = [f for f in os.listdir(clips_dir) if f.endswith(".mp4")]
            clip_count = len(clip_files)
            has_clips = clip_count > 0

        # Upload status
        uploaded_yt = False
        uploaded_fb = False
        root_upload_log = os.path.join(WORKSPACE_ROOT, "upload_source_log.txt")
        t_upload_log = os.path.join(folder_path, "upload_source_log.txt")
        for log_path in [root_upload_log, t_upload_log]:
            if os.path.exists(log_path):
                try:
                    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                        txt = f.read()
                        if entry in txt or "http" in txt:
                            uploaded_yt = True
                except Exception:
                    pass

        fb_log = os.path.join(folder_path, "upload_fb_log.txt")
        if os.path.exists(fb_log):
            uploaded_fb = True

        # Check Livestream assets
        livestream_dir = os.path.join(folder_path, "livestream")
        has_preset_vmix = os.path.exists(os.path.join(livestream_dir, "preset.vmix"))

        has_backdrop = False
        backdrop_path = None
        backdrop_dir = os.path.join(livestream_dir, "backdrop")
        if os.path.exists(backdrop_dir):
            b_files = [f for f in os.listdir(backdrop_dir) if img_exts.search(f)]
            if b_files:
                has_backdrop = True
                backdrop_path = os.path.join("livestream", "backdrop", b_files[0])
        if not has_backdrop and os.path.exists(livestream_dir):
            l_files = [f for f in os.listdir(livestream_dir) if img_exts.search(f)]
            if l_files:
                has_backdrop = True
                backdrop_path = os.path.join("livestream", l_files[0])

        logos_count = 0
        logos_dir = os.path.join(livestream_dir, "logos")
        if os.path.exists(logos_dir):
            logos_count = len([f for f in os.listdir(logos_dir) if img_exts.search(f)])

        tvc_count = 0
        tvc_dir = os.path.join(livestream_dir, "tvc")
        if os.path.exists(tvc_dir):
            tvc_count = len([f for f in os.listdir(tvc_dir) if vid_exts.search(f)])

        dieu_hanh_dir = os.path.join(folder_path, "dieu_hanh")
        has_athletes_list = False
        has_dieule = False
        if os.path.exists(dieu_hanh_dir):
            dh_files = os.listdir(dieu_hanh_dir)
            has_athletes_list = any(re.search(r"vdv|danh_sach|athletes", f, re.I) and re.search(r"\.(xlsx|xls|csv|txt)$", f, re.I) for f in dh_files)
            has_dieule = any(re.search(r"dieu_le|quy_dinh|rules", f, re.I) and re.search(r"\.(txt|docx|doc|pdf)$", f, re.I) for f in dh_files)

        has_start_bat = os.path.exists(os.path.join(folder_path, "START.bat"))

        results.append({
            "id": entry,
            "name": name,
            "folderName": entry,
            "path": folder_path,
            "date": date,
            "sportType": sport_type,
            "sourceUrl": source_url,
            "court": court,
            "category": category,
            "sponsor": sponsor,
            "description": description,
            "hasVideo": has_video,
            "videoFile": video_file,
            "videoSizeMb": video_size_mb,
            "hasTimeline": has_timeline,
            "timelineFile": "timeline.json" if has_timeline else None,
            "matchCount": match_count,
            "hasClips": has_clips,
            "clipCount": clip_count,
            "uploadedYoutube": uploaded_yt,
            "uploadedFacebook": uploaded_fb,
            "hasPresetVmix": has_preset_vmix,
            "hasBackdrop": has_backdrop,
            "backdropPath": backdrop_path,
            "hasLogos": logos_count > 0,
            "logosCount": logos_count,
            "hasTvc": tvc_count > 0,
            "tvcCount": tvc_count,
            "hasAthletesList": has_athletes_list,
            "hasDieule": has_dieule,
            "hasStartBat": has_start_bat,
        })

    return results

@app.post("/api/tournaments")
async def create_tournament(payload: Dict[str, Any] = Body(...)):
    date = payload.get("date", "").strip()
    slug = payload.get("slug", "").strip()
    if not date or not slug:
        raise HTTPException(status_code=400, detail="Date and slug are required")

    folder_name = f"{date}_{slug}"
    t_path = os.path.join(WORKSPACE_ROOT, folder_name)
    os.makedirs(os.path.join(t_path, "video"), exist_ok=True)
    os.makedirs(os.path.join(t_path, "clips"), exist_ok=True)

    info_path = os.path.join(t_path, "tournament_info.json")
    with open(info_path, "w", encoding="utf-8") as f:
        json.dump({
            "name": slug.replace("-", " ").title(),
            "date": date,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }, f, ensure_ascii=False, indent=2)

    return {"success": True, "folderName": folder_name, "path": t_path}

@app.post("/api/tournaments/create-full")
async def create_tournament_full(payload: Dict[str, Any] = Body(...)):
    name = payload.get("name", "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Tên giải đấu là bắt buộc")

    date_str = payload.get("date") or time.strftime("%Y-%m-%d")
    sport_type = payload.get("sportType") or "badminton"
    court = payload.get("court") or "Sân 1"
    sponsor = payload.get("sponsor") or ""
    description = payload.get("description") or f"Trực tiếp và phát sóng giải {name}."

    # Sinh slug
    clean_slug = re.sub(r"^\d{4}-\d{2}-\d{2}[_-]", "", name.strip())
    # Bỏ dấu tiếng Việt cơ bản
    clean_slug = re.sub(r"[àáạảãâầấậẩẫăằắặẳẵ]", "a", clean_slug, flags=re.I)
    clean_slug = re.sub(r"[èéẹẻẽêềếệểễ]", "e", clean_slug, flags=re.I)
    clean_slug = re.sub(r"[ìíịỉĩ]", "i", clean_slug, flags=re.I)
    clean_slug = re.sub(r"[òóọỏõôồốộổỗơờớợởỡ]", "o", clean_slug, flags=re.I)
    clean_slug = re.sub(r"[ùúụủũưừứựửữ]", "u", clean_slug, flags=re.I)
    clean_slug = re.sub(r"[ỳýỵỷỹ]", "y", clean_slug, flags=re.I)
    clean_slug = re.sub(r"[đ]", "d", clean_slug, flags=re.I)
    clean_slug = re.sub(r"[^a-zA-Z0-9]+", "-", clean_slug).strip("-").lower()
    if not clean_slug:
        clean_slug = "giai-dau"

    folder_name = f"{date_str}_{clean_slug}"
    t_path = os.path.join(WORKSPACE_ROOT, folder_name)

    # Tạo các thư mục chuẩn
    os.makedirs(os.path.join(t_path, "dieu_hanh"), exist_ok=True)
    os.makedirs(os.path.join(t_path, "livestream", "backdrop"), exist_ok=True)
    os.makedirs(os.path.join(t_path, "livestream", "logos"), exist_ok=True)
    os.makedirs(os.path.join(t_path, "livestream", "tvc"), exist_ok=True)
    os.makedirs(os.path.join(t_path, "video"), exist_ok=True)
    os.makedirs(os.path.join(t_path, "clips"), exist_ok=True)

    info_path = os.path.join(t_path, "dieu_hanh", "tournament_info.json")
    with open(info_path, "w", encoding="utf-8") as f:
        json.dump({
            "name": name,
            "slug": clean_slug,
            "date": date_str,
            "sportType": sport_type,
            "description": description,
            "court": court,
            "sponsor": sponsor,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }, f, ensure_ascii=False, indent=2)

    # Copy files mẫu nếu có
    samples_dir = os.path.join(WORKSPACE_ROOT, "templates", "samples")
    if os.path.exists(samples_dir):
        dl = os.path.join(samples_dir, "dieu_le.txt")
        if os.path.exists(dl):
            shutil.copy2(dl, os.path.join(t_path, "dieu_hanh", "dieu_le.txt"))
        vdv = os.path.join(samples_dir, "danh_sach_vdv.csv")
        if os.path.exists(vdv):
            shutil.copy2(vdv, os.path.join(t_path, "dieu_hanh", "danh_sach_vdv.csv"))
        bat = os.path.join(samples_dir, "START.bat")
        if os.path.exists(bat):
            shutil.copy2(bat, os.path.join(t_path, "START.bat"))

    # Gọi sinh preset.vmix
    script = os.path.join(WORKSPACE_ROOT, "system", "vmix_preset_builder.py")
    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable, "-u", script, "--tournament", t_path, "--json",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=WORKSPACE_ROOT
        )
        await proc.communicate()
    except Exception:
        pass

    return {"success": True, "folderName": folder_name, "path": t_path}

@app.post("/api/tournaments/update")
async def update_tournament(payload: Dict[str, Any] = Body(...)):
    t_path = payload.get("tournamentPath", "")
    updates = payload.get("updates", {})
    if not t_path or not os.path.exists(t_path):
        raise HTTPException(status_code=404, detail="Tournament folder not found")

    info_file = os.path.join(t_path, "dieu_hanh", "tournament_info.json")
    if not os.path.exists(info_file):
        info_file = os.path.join(t_path, "tournament_info.json")

    curr = {}
    if os.path.exists(info_file):
        try:
            with open(info_file, "r", encoding="utf-8") as f:
                curr = json.load(f)
        except Exception:
            pass

    curr.update(updates)
    with open(info_file, "w", encoding="utf-8") as f:
        json.dump(curr, f, ensure_ascii=False, indent=2)

    return {"success": True}

@app.post("/api/video/extract-info")
async def api_extract_video_info(payload: Dict[str, str] = Body(...)):
    url = payload.get("url", "").strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL required")

    script = os.path.join(WORKSPACE_ROOT, "system", "extract_video_info.py")
    proc = await asyncio.create_subprocess_exec(
        sys.executable, script, url,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=WORKSPACE_ROOT,
    )
    stdout, stderr = await proc.communicate()
    out_text = stdout.decode("utf-8", errors="ignore")

    try:
        data = json.loads(out_text.strip())
        return data
    except Exception:
        return {"title": out_text.strip() or "Video", "url": url}

@app.post("/api/tournaments/create-from-video")
async def create_from_video(payload: Dict[str, Any] = Body(...)):
    url = payload.get("url", "")
    title = payload.get("title", "")
    date = payload.get("date", time.strftime("%Y-%m-%d"))
    slug = payload.get("slug", "giai-dau")
    folder_name = f"{date}_{slug}"
    t_path = os.path.join(WORKSPACE_ROOT, folder_name)

    os.makedirs(os.path.join(t_path, "video"), exist_ok=True)
    os.makedirs(os.path.join(t_path, "clips"), exist_ok=True)

    info_path = os.path.join(t_path, "tournament_info.json")
    with open(info_path, "w", encoding="utf-8") as f:
        json.dump({
            "name": title or slug.replace("-", " ").title(),
            "source_url": url,
            "date": date,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }, f, ensure_ascii=False, indent=2)

    return {"success": True, "folderName": folder_name, "path": t_path}

@app.get("/api/timeline")
async def get_timeline(path: str = Query(...)):
    tl_file = os.path.join(path, "timeline.json")
    if not os.path.exists(tl_file):
        return {"matches": [], "rawJson": None}

    try:
        with open(tl_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            matches = data if isinstance(data, list) else data.get("matches", [])
            return {"matches": matches, "rawJson": data, "detectedFile": "timeline.json"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading timeline: {e}")

@app.post("/api/timeline")
async def save_timeline(payload: Dict[str, Any] = Body(...)):
    t_path = payload.get("tournamentPath", "")
    matches = payload.get("matches", [])
    if not t_path or not os.path.exists(t_path):
        raise HTTPException(status_code=404, detail="Tournament path not found")

    tl_file = os.path.join(t_path, "timeline.json")
    with open(tl_file, "w", encoding="utf-8") as f:
        json.dump({"matches": matches}, f, ensure_ascii=False, indent=2)

    return {"success": True}

# ============================================================
# Pipeline Runner & WebSocket Logs
# ============================================================

async def broadcast_ws(msg: dict):
    for ws in list(state.ws_clients):
        try:
            await ws.send_text(json.dumps(msg))
        except Exception:
            state.ws_clients.remove(ws)

@app.websocket("/ws/pipeline")
async def ws_pipeline(websocket: WebSocket):
    await websocket.accept()
    state.ws_clients.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in state.ws_clients:
            state.ws_clients.remove(websocket)

@app.get("/api/pipeline/status")
async def pipeline_status():
    running = state.pipeline_proc is not None and state.pipeline_proc.returncode is None
    return {"isRunning": running}

@app.post("/api/pipeline/start")
async def start_pipeline(options: Dict[str, Any] = Body(...)):
    if state.pipeline_proc and state.pipeline_proc.returncode is None:
        return {"success": False, "error": "Pipeline đang chạy!"}

    t_path = options.get("tournamentPath", "")
    script_path = os.path.join(WORKSPACE_ROOT, "system", "auto_pipeline.py")
    args = [sys.executable, "-u", script_path, t_path]

    if options.get("ytUrl"):
        args.extend(["--yt-url", options["ytUrl"].strip()])
    if options.get("courtName"):
        args.extend(["--court", options["courtName"].strip()])
    if options.get("tournamentName"):
        args.extend(["--tournament", options["tournamentName"].strip()])
    if options.get("sponsor"):
        args.extend(["--sponsor", options["sponsor"].strip()])
    if options.get("category"):
        args.extend(["--category", options["category"].strip()])
    # 4 bước có thể chạy độc lập: cho phép skip từng bước
    if options.get("skipDownload"):
        args.append("--skip-download")
    if options.get("skipTimeline"):
        args.append("--skip-timeline")
    if options.get("skipCut"):
        args.append("--skip-cut")
    if options.get("skipUpload"):
        args.append("--skip-upload")
    if options.get("dryRun"):
        args.append("--dry-run")
    if options.get("platform"):
        args.extend(["--platform", options["platform"]])
    if options.get("ytMode"):
        args.extend(["--yt-mode", options["ytMode"]])

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUNBUFFERED"] = "1"

    proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=WORKSPACE_ROOT,
        env=env,
    )
    state.pipeline_proc = proc
    state.pipeline_running = True

    async def stream_output():
        async def read_stream(stream, level):
            while True:
                line = await stream.readline()
                if not line:
                    break
                text = line.decode("utf-8", errors="ignore").rstrip("\r\n")
                log_msg = {
                    "type": "log",
                    "payload": {
                        "id": f"log-{time.time()}",
                        "timestamp": time.strftime("%H:%M:%S"),
                        "level": level,
                        "message": text,
                    },
                }
                await broadcast_ws(log_msg)

        await asyncio.gather(
            read_stream(proc.stdout, "info"),
            read_stream(proc.stderr, "warn"),
        )
        code = await proc.wait()
        state.pipeline_running = False
        state.pipeline_proc = None
        await broadcast_ws({"type": "exit", "payload": code})

    asyncio.create_task(stream_output())
    return {"success": True}

@app.post("/api/pipeline/kill")
async def kill_pipeline():
    if state.pipeline_proc and state.pipeline_proc.returncode is None:
        try:
            state.pipeline_proc.terminate()
        except Exception:
            pass
        return {"success": True}
    return {"success": False}

# ============================================================
# Video Import trực tiếp (file upload) + Timeline độc lập + Chapters
# ============================================================

from fastapi import UploadFile, File

@app.post("/api/video/import")
async def import_video_file(tournamentPath: str = Query(...), file: UploadFile = File(...)):
    """Upload file mp4 trực tiếp vào thư mục video của giải (độc lập, không cần link)"""
    if not tournamentPath or not os.path.exists(tournamentPath):
        raise HTTPException(status_code=404, detail="Tournament path not found")
    video_dir = os.path.join(tournamentPath, "video")
    os.makedirs(video_dir, exist_ok=True)
    dest = os.path.join(video_dir, file.filename or "source.mp4")
    try:
        content = await file.read()
        with open(dest, "wb") as f:
            f.write(content)
        return {"success": True, "path": dest, "filename": os.path.basename(dest), "size": len(content)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# Livestream Assets Import & vMix Presets
# ============================================================

from typing import List

@app.post("/api/livestream/import-backdrop")
async def import_backdrop_api(tournamentPath: str = Query(...), file: UploadFile = File(...)):
    """Upload ảnh Backdrop cho giải đấu"""
    if not tournamentPath or not os.path.exists(tournamentPath):
        raise HTTPException(status_code=404, detail="Tournament path not found")
    backdrop_dir = os.path.join(tournamentPath, "livestream", "backdrop")
    os.makedirs(backdrop_dir, exist_ok=True)

    # Xóa ảnh backdrop cũ nếu có
    for f in os.listdir(backdrop_dir):
        try:
            os.unlink(os.path.join(backdrop_dir, f))
        except Exception:
            pass

    filename = file.filename or "backdrop.png"
    dest = os.path.join(backdrop_dir, filename)
    try:
        content = await file.read()
        with open(dest, "wb") as f:
            f.write(content)

        # Tự động cập nhật preset vMix
        script = os.path.join(WORKSPACE_ROOT, "system", "vmix_preset_builder.py")
        proc = await asyncio.create_subprocess_exec(
            sys.executable, "-u", script, "--tournament", tournamentPath, "--json",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=WORKSPACE_ROOT
        )
        await proc.communicate()

        return {"success": True, "dest": dest, "filename": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/livestream/import-logos")
async def import_logos_api(tournamentPath: str = Query(...), files: List[UploadFile] = File(...)):
    """Upload nhiều file ảnh Logo nhà tài trợ"""
    if not tournamentPath or not os.path.exists(tournamentPath):
        raise HTTPException(status_code=404, detail="Tournament path not found")
    logos_dir = os.path.join(tournamentPath, "livestream", "logos")
    os.makedirs(logos_dir, exist_ok=True)

    count = 0
    try:
        for f in files:
            dest = os.path.join(logos_dir, f.filename or f"logo_{count}.png")
            content = await f.read()
            with open(dest, "wb") as out:
                out.write(content)
            count += 1

        # Cập nhật preset vMix
        script = os.path.join(WORKSPACE_ROOT, "system", "vmix_preset_builder.py")
        proc = await asyncio.create_subprocess_exec(
            sys.executable, "-u", script, "--tournament", tournamentPath, "--json",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=WORKSPACE_ROOT
        )
        await proc.communicate()

        return {"success": True, "count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/livestream/import-tvc")
async def import_tvc_api(tournamentPath: str = Query(...), files: List[UploadFile] = File(...)):
    """Upload nhiều file video TVC quảng cáo"""
    if not tournamentPath or not os.path.exists(tournamentPath):
        raise HTTPException(status_code=404, detail="Tournament path not found")
    tvc_dir = os.path.join(tournamentPath, "livestream", "tvc")
    os.makedirs(tvc_dir, exist_ok=True)

    count = 0
    try:
        for f in files:
            dest = os.path.join(tvc_dir, f.filename or f"tvc_{count}.mp4")
            content = await f.read()
            with open(dest, "wb") as out:
                out.write(content)
            count += 1

        # Cập nhật preset vMix
        script = os.path.join(WORKSPACE_ROOT, "system", "vmix_preset_builder.py")
        proc = await asyncio.create_subprocess_exec(
            sys.executable, "-u", script, "--tournament", tournamentPath, "--json",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=WORKSPACE_ROOT
        )
        await proc.communicate()

        return {"success": True, "count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/livestream/import-athletes")
async def import_athletes_api(tournamentPath: str = Query(...), file: UploadFile = File(...)):
    """Upload file danh sách VĐV (CSV, Excel)"""
    if not tournamentPath or not os.path.exists(tournamentPath):
        raise HTTPException(status_code=404, detail="Tournament path not found")
    dieu_hanh_dir = os.path.join(tournamentPath, "dieu_hanh")
    os.makedirs(dieu_hanh_dir, exist_ok=True)

    filename = file.filename or "danh_sach_vdv.csv"
    dest = os.path.join(dieu_hanh_dir, filename)
    try:
        content = await file.read()
        with open(dest, "wb") as f:
            f.write(content)
        return {"success": True, "dest": dest, "filename": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/livestream/build-preset")
async def build_preset_api(payload: Dict[str, Any] = Body(...)):
    """Xuất preset vMix theo giải đấu"""
    t_path = payload.get("tournamentPath", "")
    if not t_path or not os.path.exists(t_path):
        raise HTTPException(status_code=404, detail="Tournament not found")
    script = os.path.join(WORKSPACE_ROOT, "system", "vmix_preset_builder.py")
    proc = await asyncio.create_subprocess_exec(
        sys.executable, "-u", script, "--tournament", t_path, "--json",
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=WORKSPACE_ROOT
    )
    stdout, stderr = await proc.communicate()
    try:
        out_str = stdout.decode(errors="ignore").strip()
        parsed = json.loads(out_str)
        return parsed
    except Exception:
        return {"success": proc.returncode == 0, "presetPath": os.path.join(t_path, "livestream", "preset.vmix")}

@app.post("/api/livestream/start-live")
async def start_live_api(payload: Dict[str, Any] = Body(...)):
    """Khởi động 1-Click Live"""
    t_path = payload.get("tournamentPath", "")
    if not t_path or not os.path.exists(t_path):
        raise HTTPException(status_code=404, detail="Tournament not found")
    bat_path = os.path.join(t_path, "START.bat")
    if os.path.exists(bat_path):
        import subprocess
        subprocess.Popen(["cmd.exe", "/c", "start", "cmd.exe", "/k", bat_path], cwd=t_path)
        return {"success": True}
    script = os.path.join(WORKSPACE_ROOT, "system", "start_live_orchestrator.py")
    import subprocess
    subprocess.Popen(["cmd.exe", "/c", "start", "cmd.exe", "/k", sys.executable, script, "--tournament", t_path], cwd=WORKSPACE_ROOT)
    return {"success": True}

@app.post("/api/tournaments/sync-dalisports")
async def sync_dalisports_api():
    """Đồng bộ các giải đấu Sắp diễn ra từ app.dalisports.vn"""
    script = os.path.join(WORKSPACE_ROOT, "system", "sync_dalisports.py")
    proc = await asyncio.create_subprocess_exec(
        sys.executable, "-u", script,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=WORKSPACE_ROOT
    )
    stdout, stderr = await proc.communicate()
    out_str = stdout.decode(errors="ignore").strip()
    marker = "[JSON RESULT]"
    if marker in out_str:
        json_part = out_str.split(marker)[-1].strip()
        try:
            return json.loads(json_part)
        except Exception:
            pass
    try:
        return json.loads(out_str)
    except Exception:
        return {"success": proc.returncode == 0, "raw": out_str, "error": stderr.decode(errors="ignore")}

@app.post("/api/timeline/generate")
async def generate_timeline_api(payload: Dict[str, Any] = Body(...)):
    """Bước 2 độc lập: chạy Gemini Timeline quét banner scoreboard"""
    t_path = payload.get("tournamentPath", "")
    if not t_path or not os.path.exists(t_path):
        raise HTTPException(status_code=404, detail="Tournament not found")
    video_dir = os.path.join(t_path, "video")
    video_path = None
    if os.path.exists(video_dir):
        vids = [f for f in os.listdir(video_dir) if re.search(r"\.(mp4|mkv|mov)$", f, re.I)]
        if vids:
            video_path = os.path.join(video_dir, vids[0])
    if not video_path:
        return {"success": False, "error": "Chưa có video trong thư mục giải"}
    script = os.path.join(WORKSPACE_ROOT, "system", "gemini_timeline.py")
    proc = await asyncio.create_subprocess_exec(sys.executable, "-u", script, video_path, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=WORKSPACE_ROOT)
    stdout, stderr = await proc.communicate()
    return {"success": proc.returncode == 0, "output": (stdout.decode(errors="ignore") + stderr.decode(errors="ignore"))[-4000:]}

@app.post("/api/timeline/normalize")
async def normalize_timeline_api(payload: Dict[str, Any] = Body(...)):
    """Bước 2b độc lập: chuẩn hóa dữ liệu timeline"""
    t_path = payload.get("tournamentPath", "")
    if not t_path or not os.path.exists(t_path):
        raise HTTPException(status_code=404, detail="Tournament not found")
    # Tìm timeline txt
    tl = None
    for f in os.listdir(t_path):
        if "timeline" in f and f.endswith(".txt") and "norms" not in f:
            tl = os.path.join(t_path, f)
            break
    if not tl:
        # fallback: tìm trong video subfolder
        for root, _, files in os.walk(t_path):
            for f in files:
                if "timeline" in f and f.endswith(".txt") and "norms" not in f:
                    tl = os.path.join(root, f)
                    break
    if not tl:
        return {"success": False, "error": "Không tìm thấy timeline txt"}
    script = os.path.join(WORKSPACE_ROOT, "system", "normalize.py")
    proc = await asyncio.create_subprocess_exec(sys.executable, "-u", script, tl, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=WORKSPACE_ROOT)
    stdout, stderr = await proc.communicate()
    return {"success": proc.returncode == 0, "output": (stdout.decode(errors="ignore") + stderr.decode(errors="ignore"))[-4000:]}

@app.get("/api/chapters/preview")
async def chapters_preview(path: str = Query(...)):
    """Sinh chapters để chèn vào description YouTube (độc lập)"""
    # Tìm norms hoặc timeline json
    video_path = ""
    norms_path = None
    # tìm video
    vdir = os.path.join(path, "video")
    if os.path.exists(vdir):
        vids = [f for f in os.listdir(vdir) if f.endswith(".mp4")]
        if vids: video_path = os.path.join(vdir, vids[0])
    # tìm norms
    for cand in [os.path.join(path, f) for f in os.listdir(path) if "norms" in f] if os.path.exists(path) else []:
        norms_path = cand
        break
    try:
        # reuse logic from upload_source_youtube
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location("upload_src", os.path.join(WORKSPACE_ROOT, "system", "upload_source_youtube.py"))
        mod = _ilu.module_from_spec(spec)
        spec.loader.exec_module(mod)
        title, description = mod.build_youtube_chapters_and_title(video_path or path, norms_path)
        # Parse chapters block
        chapters = []
        for line in description.splitlines():
            if re.match(r"^\d{2}:\d{2}:\d{2}\s", line) or "Trận" in line and re.match(r"^\d", line):
                chapters.append(line)
        # Also extract via regex 00:00:00
        if not chapters:
            chapters = re.findall(r"\d{2}:\d{2}:\d{2}[^\n]*", description)
        return {"title": title, "description": description, "chapters": chapters or description.splitlines()[:20]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# SEO Preview & Config
# ============================================================

@app.post("/api/seo/preview")
async def seo_preview(payload: Dict[str, Any] = Body(...)):
    try:
        from seo_helper import load_seo_config, generate_clip_title, generate_clip_description, get_tags
        t_name = payload.get("tournamentName", "")
        p_a = payload.get("playerA", "")
        p_b = payload.get("playerB", "")
        category = payload.get("category", "")
        round_name = payload.get("round", "")
        court = payload.get("court", "")

        cfg = load_seo_config(tournament_name=t_name)
        title = generate_clip_title(cfg, t_name, p_a, p_b, category, round_name, court)
        desc = generate_clip_description(cfg, t_name, p_a, p_b, category, round_name)
        tags = get_tags(cfg)
        return {"title": title, "description": desc, "tags": tags}
    except Exception as e:
        return {
            "title": f"[{payload.get('round', 'Trận Đấu')}] {payload.get('playerA', '')} vs {payload.get('playerB', '')}",
            "description": f"Giải {payload.get('tournamentName', '')}",
            "tags": ["dalisports", "thethao"],
        }

@app.get("/api/config")
async def get_config():
    env_file = os.path.join(WORKSPACE_ROOT, ".env")
    conf = {
        "GEMINI_API_KEY": "",
        "GEMINI_MODEL": "gemini-2.5-flash-lite",
        "FB_PAGE_ID": "",
        "FB_PAGE_ACCESS_TOKEN": "",
        "UPDATE_CHECK_URL": "",
        "hasCookiesTxt": os.path.exists(os.path.join(WORKSPACE_ROOT, "cookies.txt")),
        "hasClientSecrets": os.path.exists(os.path.join(WORKSPACE_ROOT, "client_secrets.json")),
        "hasYoutubeToken": os.path.exists(os.path.join(WORKSPACE_ROOT, "yt_profile", "upload_youtube_oauth.json")),
    }
    if os.path.exists(env_file):
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip()
                    if k in conf:
                        conf[k] = v
        except Exception:
            pass
    return conf

@app.post("/api/config")
async def save_config(updates: Dict[str, Any] = Body(...)):
    env_file = os.path.join(WORKSPACE_ROOT, ".env")
    lines = []
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

    applied_keys = set()
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            k = stripped.split("=", 1)[0].strip()
            if k in updates:
                new_lines.append(f"{k}={updates[k]}\n")
                applied_keys.add(k)
                continue
        new_lines.append(line)

    for k, v in updates.items():
        if k not in applied_keys:
            new_lines.append(f"{k}={v}\n")

    with open(env_file, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    return {"success": True}

# ============================================================
# Static Files & SPA Fallback
# ============================================================

if os.path.exists(DESKTOP_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(DESKTOP_DIST, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        target_path = os.path.join(DESKTOP_DIST, full_path)
        if full_path and os.path.exists(target_path) and os.path.isfile(target_path):
            return FileResponse(target_path)
        index_file = os.path.join(DESKTOP_DIST, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return JSONResponse({"error": "Desktop web bundle not found. Please run 'npm run build' in desktop/."}, status_code=404)

# ============================================================
# Main Entry Point
# ============================================================

def main():
    import argparse
    import socket

    parser = argparse.ArgumentParser(description="DaliSports Studio Remote Server")
    parser.add_argument("--port", type=int, default=8765, help="Port to listen on (default: 8765)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host interface (default: 0.0.0.0)")
    parser.add_argument("--tunnel", action="store_true", help="Automatically start Cloudflare Tunnel")
    args = parser.parse_args()

    # Get local LAN IP
    local_ip = "127.0.0.1"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        pass

    print("\n" + "=" * 65)
    print("        DALISPORTS STUDIO - MAY CHU TRUY CAP TU XA")
    print("=" * 65)
    print(f" [Local Web]     http://localhost:{args.port}")
    print(f" [Mang Noi Bo]   http://{local_ip}:{args.port}")
    print("=" * 65)

    if args.tunnel:
        print("\n[*] Dang khoi tao Cloudflare Tunnel cong khai...")
        start_tunnel_service(args.port)

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")

if __name__ == "__main__":
    main()
