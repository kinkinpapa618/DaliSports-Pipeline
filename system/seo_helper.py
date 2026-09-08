#!/usr/bin/env python3
# seo_helper.py - Helper chung cho SEO YouTube: load config theo giải, sinh title/mô tả/hashtag/tags
import os
import sys
import re
import json
import glob

sys.stdout.reconfigure(encoding="utf-8")

FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONFIG_DIR = os.path.join(FOLDER, "seo_config")

def slugify(text: str) -> str:
    import unicodedata
    # Chuyển tiếng Việt có dấu -> không dấu
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    # Đ xử lý riêng (NFD không tách Đ)
    text = text.replace('Đ', 'D').replace('đ', 'd')
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s-]", " ", text)
    text = re.sub(r"\s+", "-", text.strip())
    text = re.sub(r"-+", "-", text)
    return text.strip("-")

def detect_sport(tournament_name: str, video_path: str = "") -> str:
    s = (tournament_name + " " + video_path).lower()
    if "pickleball" in s or "pickle" in s:
        return "pickleball"
    return "badminton"

def load_seo_config(tournament_name: str = "", video_path: str = "", sport: str = None) -> dict:
    """Tìm config phù hợp: ưu tiên file khớp slug tournament, fallback _default_{sport}.json"""
    sport = sport or detect_sport(tournament_name, video_path)
    candidates = glob.glob(os.path.join(CONFIG_DIR, "*.json"))
    if tournament_name:
        slug = slugify(tournament_name)
        slug_words = set(slug.split("-"))
        # 1. Khớp chính xác slug trước
        exact = os.path.join(CONFIG_DIR, f"{slug}.json")
        if os.path.exists(exact):
            try:
                with open(exact, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    if sport and cfg.get("sport") and cfg.get("sport") != sport:
                        pass
                    else:
                        return cfg
            except Exception:
                pass
        # 2. Tìm file gần giống - chấm điểm theo số từ chung, chọn điểm cao nhất
        best_cfg = None
        best_score = -1
        best_base = ""
        for cand in candidates:
            base = os.path.splitext(os.path.basename(cand))[0]
            if base.startswith("_default"):
                continue
            try:
                with open(cand, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
            except Exception:
                continue
            if sport and cfg.get("sport") and cfg.get("sport") != sport:
                continue
            base_words = set(base.split("-"))
            # Điểm: số từ chung, ưu tiên base là substring của slug hoặc ngược lại
            if slug in base or base in slug:
                score = 100 + len(slug_words & base_words)
            else:
                common = slug_words & base_words
                # Loại từ chung chung quá ngắn
                common_filtered = {w for w in common if len(w) > 3}
                # Cần ít nhất 2 từ dài chung và phải có từ đặc trưng (hong loan / ttbc)
                if len(common_filtered) < 2:
                    continue
                score = len(common_filtered)
                # Bonus nếu có từ đặc trưng trùng
                if any(w in base for w in slug.split("-") if len(w) > 4 and w not in ["giai","cau","long","nam"]):
                    score += 5
            if score > best_score:
                best_score = score
                best_cfg = cfg
                best_base = base
        if best_cfg and best_score >= 2:
            return best_cfg
    # Fallback default theo sport
    default_path = os.path.join(CONFIG_DIR, f"_default_{sport}.json")
    if os.path.exists(default_path):
        try:
            with open(default_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    # Fallback badminton nếu không có gì
    fallback = os.path.join(CONFIG_DIR, "_default_badminton.json")
    if os.path.exists(fallback):
        with open(fallback, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def build_dynamic_description(config: dict, chapters: list, match_count: int) -> str:
    intro = config.get("description_intro", "")
    try:
        intro_filled = intro.format(
            match_count=match_count,
            tournament_full=config.get("tournament_full", ""),
            location=config.get("location", ""),
            date=config.get("date", ""),
            organizer=config.get("organizer", ""),
            court=config.get("court", ""),
            short_keyword=config.get("short_keyword", "")
        )
    except Exception:
        intro_filled = intro
    outro = config.get("description_outro", "")
    hashtags = " ".join(config.get("hashtags", []))
    # Chapters đã có prefix timeline, thêm vào sau intro
    chapters_block = "\n".join(chapters) if chapters else ""
    parts = [intro_filled, "", chapters_block, "", outro]
    if hashtags:
        parts.append("")
        parts.append(hashtags)
    return "\n".join([p for p in parts if p is not None]).strip()

def build_source_title(config: dict, match_count: int, tournament_name: str = "") -> str:
    template = config.get("title_source_template", "")
    tn = tournament_name or config.get("tournament_full", "GIẢI CẦU LÔNG - 2026")
    court = config.get("court", "SÂN 2")
    if template:
        try:
            title = template.format(
                tournament_full=tn,
                court=court,
                match_count=match_count,
                short_keyword=config.get("short_keyword", ""),
                location=config.get("location", "")
            )
        except Exception:
            title = f"{tn} | {court} | Trọn Bộ {match_count} Trận | Full HD"
    else:
        title = f"{tn} | {court} | Trọn Bộ {match_count} Trận | Full HD"
    if len(title) > 100:
        title = title[:100].rsplit(" ", 1)[0]
    return title.strip()

def build_clip_title(config: dict, category: str, players: str, tournament_name: str = "") -> str:
    template = config.get("title_clip_template", "")
    tn = tournament_name or config.get("tournament_full", "")
    court = config.get("court", "")
    if template:
        try:
            title = template.format(
                tournament_full=tn,
                category=category,
                players=players,
                court=court
            )
        except Exception:
            title = f"{tn} | {category} | {players}"
    else:
        title = f"{tn} | {category} | {players}"
    # Thêm court nếu chưa có và còn chỗ
    if court and court not in title and len(title) + len(f" | {court}") <= 100:
        title = f"{title} | {court}"
    if len(title) > 100:
        title = title[:100].rsplit(" ", 1)[0].strip().rstrip(" -|")
    return title.strip()

def get_hashtags(config: dict) -> str:
    return " ".join(config.get("hashtags", []))

def get_tags(config: dict) -> list:
    return config.get("tags", [])
