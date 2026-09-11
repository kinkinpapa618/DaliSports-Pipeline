import os
import sys
import re
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding='utf-8')
tree = ET.parse(r'E:\www\DaliSports-Pipeline\2026-09-12_giai-pickleball-tranh-cup-doppelherz\livestream\preset.vmix')
root = tree.getroot()
raw = ET.tostring(root, encoding='utf-8').decode('utf-8')

matches = set(re.findall(r'[A-Za-z]:\\[^<"\'\r\n\t]+', raw))
print(f"Total file paths found: {len(matches)}")
for p in sorted(matches):
    # strip trailing spaces or entities
    clean_p = p.split('&')[0].strip()
    exists = os.path.exists(clean_p)
    print(f"[{'OK' if exists else 'MISSING'}] {clean_p}")
