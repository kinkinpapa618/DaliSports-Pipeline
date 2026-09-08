#!/usr/bin/env python3
# normalize.py - Chuẩn hóa tiêu đề video từ file timeline
# Hỗ trợ 2 định dạng:
#   1) Dòng RAW_TITLE:/NORM_TITLE: (tiêu đề đơn)
#   2) Dòng timeline:  START - END - RAW_TITLE   (nhiều trận)
# Quy tắc:
#   - Tên giải: VIẾT HOA TOÀN BỘ
#   - Năm: giữ nguyên
#   - Nội dung thi đấu / vòng: viết hoa chữ cái đầu mỗi từ
#   - Tên người: viết hoa chữ cái đầu mỗi từ
#   - Tên >= 3 từ: chỉ giữ 2 từ cuối
#   - 2 người 1 đội: "A - B"; 2 đội: "Đội1 vs Đội2"; 4 người: "A - B vs C - D"
#   - Toàn bộ tiêu đề <= 100 ký tự (thử 2 từ tên -> 1 từ tên -> cắt tại dấu cách)
import re
import sys
import glob
import os

sys.stdout.reconfigure(encoding="utf-8")

YEAR_RE = re.compile(r"^\d{4}$")
TL_RE = re.compile(r"^\s*(\d{1,2}:\d{2}(?::\d{2})?)\s*-\s*(\d{1,2}:\d{2}(?::\d{2})?)\s*-\s*(.+?)\s*$")


def title_case(s: str) -> str:
    return s.strip().title()


def shorten_name(name: str, keep: int = 2) -> str:
    words = name.split()
    if len(words) > keep:
        words = words[-keep:]
    return " ".join(words)


def normalize_names(seg: str, keep: int = 2) -> str:
    teams = re.split(r"\s+vs\s+", seg.strip(), flags=re.IGNORECASE)
    out_teams = []
    for team in teams:
        # Tách từng VĐV trong đội: phân tách bởi "/" HOẶC " - " (dấu cách - dấu cách)
        # để tránh lỗi cắt nhầm tên có dấu "-" (vd "HÙNG - HÙNG" -> "Hùng - Hùng")
        players = [shorten_name(title_case(p), keep) for p in re.split(r"\s*/\s*|\s+-\s+", team.strip())]
        out_teams.append(" - ".join([p for p in players if p]))
    return " vs ".join(out_teams)


def _build(raw: str, keep: int) -> str:
    sections = [s.strip() for s in raw.split("|")]
    first_parts = [p.strip() for p in sections[0].split("-")]
    tournament = first_parts[0].upper()
    rest = []
    for p in first_parts[1:]:
        rest.append(p if YEAR_RE.match(p) else title_case(p))
    new_first = tournament + (" - " + " - ".join(rest) if rest else "")
    out = [new_first]
    for seg in sections[1:]:
        if re.search(r"vs", seg, re.IGNORECASE) or "/" in seg:
            out.append(normalize_names(seg, keep))
        else:
            out.append(title_case(seg))
    return " | ".join(out)


def _shorten_tournament(tournament: str, max_len: int) -> str:
    """Rút gọn tên giải nhưng cố gắng giữ lại năm (4 số cuối) nếu có."""
    if len(tournament) <= max_len:
        return tournament
    # Tách năm ở cuối (ví dụ: ' 2026') - chỉ khi kết thúc bằng năm
    m = re.search(r'\s+\d{4}\s*$', tournament)
    year = m.group(0) if m else ""
    base = tournament[:m.start()] if m else tournament
    allowed_base = max_len - len(year)
    if allowed_base < 20:
        return tournament[:max_len].rsplit(" ", 1)[0].strip().rstrip(" -|")
    cut = base[:allowed_base]
    # Nếu cắt giữa chừng từ, lùi về dấu cách gần nhất
    if len(base) > allowed_base and " " in cut:
        # Kiểm tra xem có cắt giữa từ không
        if allowed_base < len(base) and not base[allowed_base].isspace():
            cut = cut.rsplit(" ", 1)[0]
        # Nếu cut kết thúc bằng dấu '(' dở dang, xóa luôn cụm '('
        cut = re.sub(r'\s*\([^)]*$', '', cut)
    cut = cut.strip().rstrip(" -|")
    # Xóa ngoặc đơn dở dang còn sót
    cut = re.sub(r'\s*\([^)]*$', '', cut).strip().rstrip(" -|")
    return (cut + year).strip()


def normalize(raw: str) -> str:
    raw = raw.strip().replace("<", "").replace(">", "")
    raw = re.sub(r"\s+", " ", raw)
    if not raw:
        return ""
    result = _build(raw, 2)
    if len(result) > 100:
        result = _build(raw, 1)
    if len(result) > 100:
        # Ưu tiên cắt bớt phần tên giải thay vì cắt mất tên VĐV đối thủ
        parts = result.split(" | ")
        if len(parts) >= 2:
            tournament = parts[0]
            players = parts[-1]
            middles = parts[1:-1]
            sep_len = 3 * (len(parts) - 1)  # " | "
            fixed_len = len(players) + sum(len(m) for m in middles) + sep_len
            max_tournament = 100 - fixed_len
            if max_tournament >= 20 and len(tournament) > max_tournament:
                tournament = _shorten_tournament(tournament, max_tournament)
                result = " | ".join([tournament] + middles + [players])
        if len(result) > 100:
            candidate = result[:100].rsplit(" ", 1)[0]
            candidate = re.sub(r'\s+vs\s*$', '', candidate, flags=re.IGNORECASE)
            candidate = re.sub(r'\s*-\s*$', '', candidate)
            candidate = re.sub(r'\s*\|\s*$', '', candidate)
            candidate = candidate.strip()
            if len(candidate) > 100:
                candidate = candidate[:100].rsplit(" ", 1)[0].strip()
            result = candidate
    return result


def detect_sport_from_text(text: str) -> str:
    t = text.lower()
    if "pickleball" in t or "pickle" in t:
        return "pickleball"
    return "badminton"


def process_line(line: str) -> str:
    """Chuẩn hóa 1 dòng timeline định dạng: START - END - RAW_TITLE"""
    m = TL_RE.match(line)
    if not m:
        return line.strip()
    start, end, title = m.group(1), m.group(2), m.group(3)
    return f"{start} - {end} | {normalize(title)}"


def process_file(path: str, sport: str = None):
    with open(path, encoding="utf-8-sig") as f:
        lines = f.readlines()
    # Auto detect sport nếu không truyền
    if not sport:
        sport = detect_sport_from_text(" ".join(lines[:5]) + " " + os.path.basename(path))

    # --- Chế độ 1: RAW_TITLE / NORM_TITLE (tiêu đề đơn) ---
    raw = ""
    norm_line_idx = None
    raw_line_idx = None
    for i, line in enumerate(lines):
        if line.startswith("RAW_TITLE:"):
            raw = line.split(":", 1)[1].strip()
            raw_line_idx = i
        elif line.startswith("NORM_TITLE:"):
            norm_line_idx = i
    if raw:
        norm = normalize(raw)
        norm_text = f"NORM_TITLE: {norm}\n"
        if norm_line_idx is not None:
            lines[norm_line_idx] = norm_text
        elif raw_line_idx is not None:
            lines.insert(raw_line_idx + 1, norm_text)
        else:
            lines.append("\n" + norm_text)
        with open(path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        print(f"[+] {os.path.basename(path)} (single)\n    NORM: {norm}")
        return

    # --- Chế độ 2: timeline nhiều trận ---
    out = []
    for line in lines:
        m = TL_RE.match(line)
        if not m:
            continue
        start, end, title = m.group(1), m.group(2), m.group(3)
        out.append(f"{start} - {end} | {normalize(title)}")
    if not out:
        print(f"[!] Bỏ qua {path}: không tìm thấy dòng RAW_TITLE hay timeline")
        return
    base = os.path.splitext(path)[0]
    out_path = base + "_norms.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print(f"[+] {os.path.basename(path)} -> {os.path.basename(out_path)} ({len(out)} trận)")
    for o in out:
        print("    " + o)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Chuẩn hóa timeline - hỗ trợ 2 môn")
    parser.add_argument("paths", nargs="*", help="Đường dẫn file *_timeline.txt")
    parser.add_argument("--sport", choices=["badminton", "pickleball"], default=None, help="Ép môn thể thao (mặc định auto detect)")
    args = parser.parse_args()
    paths = args.paths or glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "*_timeline.txt"))
    # Lọc bỏ file _norms.txt khỏi danh sách tự động
    paths = [p for p in paths if "_norms.txt" not in p]
    for p in paths:
        process_file(p, sport=args.sport)
