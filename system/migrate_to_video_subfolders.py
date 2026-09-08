#!/usr/bin/env python3
# migrate_to_video_subfolders.py - Tách mỗi video trong tournament folder thành subfolder riêng
# Cấu trúc mới: Sân 2/YYYY-MM-DD_slug_tournament/video-slug/ (mỗi link 1 thư mục)
import os, glob, shutil, re, sys
sys.stdout.reconfigure(encoding="utf-8")
FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
try:
    import seo_helper
except: seo_helper=None

def get_video_slug(video_path, tournament_name=""):
    base = os.path.splitext(os.path.basename(video_path))[0]
    if tournament_name and tournament_name.lower() in base.lower():
        idx = base.lower().find(tournament_name.lower()) + len(tournament_name)
        suffix = base[idx:].strip(" -|📍")
        if suffix: base = suffix
    if "📅" in base:
        base = base.split("📅")[-1].strip()
    elif "📍" in base:
        base = base.split("📍")[-1].strip()
    base = re.sub(r"^[🔴\s\[\]LIVE\s]+", "", base, flags=re.IGNORECASE).strip(" -")
    if not base or len(base)<3:
        base = os.path.splitext(os.path.basename(video_path))[0][:30]
    if seo_helper:
        slug = seo_helper.slugify(base)
    else:
        import unicodedata
        slug = unicodedata.normalize('NFD', base)
        slug = ''.join(c for c in slug if unicodedata.category(c)!='Mn').replace('Đ','D').replace('đ','d').lower()
        slug = re.sub(r"[^a-z0-9\s-]", " ", slug)
        slug = re.sub(r"\s+", "-", slug.strip())
    return slug[:40].strip("-") or "video"

for tournament_dir in glob.glob(os.path.join(FOLDER, "20*_*")):
    if not os.path.isdir(tournament_dir): continue
    # Chỉ xử lý tournament folder có mp4 trực tiếp (cấu trúc cũ)
    mp4s = [f for f in glob.glob(os.path.join(tournament_dir, "*.mp4")) if os.path.isfile(f)]
    if not mp4s:
        print(f"[SKIP] {os.path.basename(tournament_dir)}: không có mp4 trực tiếp (đã là cấu trúc mới hoặc rỗng)")
        continue
    # Đọc tournament name từ norms đầu tiên
    tname=""
    for nf in glob.glob(os.path.join(tournament_dir, "*_norms.txt")):
        try:
            with open(nf, "r", encoding="utf-8") as f:
                for line in f:
                    parts=[p.strip() for p in line.split(" | ")]
                    if len(parts)>=2:
                        tname=parts[1]; break
            if tname: break
        except: pass
    print(f"\n[{os.path.basename(tournament_dir)}] Tách {len(mp4s)} video -> subfolders (tournament={tname[:30]})")
    for mp4 in sorted(mp4s):
        base = os.path.splitext(os.path.basename(mp4))[0]
        slug = get_video_slug(mp4, tname)
        subdir = os.path.join(tournament_dir, slug)
        # Tránh trùng: nếu slug đã tồn tại và chứa file khác, thêm suffix
        orig_slug=slug
        counter=1
        while os.path.exists(subdir) and not os.path.isfile(os.path.join(subdir, os.path.basename(mp4))):
            # Nếu folder tồn tại nhưng không chứa file này, đổi tên
            if len(os.listdir(subdir))==0:
                break
            slug=f"{orig_slug}-{counter}"
            subdir=os.path.join(tournament_dir, slug)
            counter+=1
            if counter>10: break
        os.makedirs(subdir, exist_ok=True)
        print(f"  -> {slug}/ : {os.path.basename(mp4)[:50]}")
        # Move mp4 + timelines
        for src in [mp4, base + "_timeline.txt", base + "_timeline_norms.txt", base + "_timeline.txt".replace("_timeline.txt","_timeline_norms.txt")]:
            # src đã là mp4, còn lại cần tìm đúng path
            if not os.path.exists(src):
                # Thử tìm với base đầy đủ
                cand = os.path.join(tournament_dir, os.path.basename(src))
                if os.path.exists(cand):
                    src=cand
                else:
                    continue
            dest = os.path.join(subdir, os.path.basename(src))
            if os.path.abspath(src)==os.path.abspath(dest):
                continue
            if os.path.exists(dest):
                print(f"    [SKIP] {os.path.basename(src)} đã tồn tại")
            else:
                print(f"    [MOVE] {os.path.basename(src)}")
                shutil.move(src, dest)
        # Di chuyển clips liên quan? Giữ clips ở tournament root cho legacy, không move hết
        # Nếu clips trong tournament root có thể phân bổ sau

print("\n=== HOÀN TẤT ===")
for td in glob.glob(os.path.join(FOLDER, "20*_*")):
    if os.path.isdir(td):
        print(f"\n{os.path.basename(td)}/")
        for entry in os.listdir(td):
            p=os.path.join(td, entry)
            if os.path.isdir(p):
                cnt=len(os.listdir(p)) if os.path.isdir(p) else 0
                print(f"  {entry}/ ({cnt} files)")
                if entry=="clips":
                    for f in os.listdir(p)[:3]:
                        print(f"    {f[:60]}")
            else:
                print(f"  {entry}")
