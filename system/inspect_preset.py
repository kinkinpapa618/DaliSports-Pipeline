import sys
import xml.etree.ElementTree as ET
sys.stdout.reconfigure(encoding="utf-8")

tree = ET.parse(r'E:\www\DaliSports-Pipeline\2026-09-12_giai-pickleball-tranh-cup-doppelherz\livestream\preset.vmix')
root = tree.getroot()
print('Root tag:', root.tag)
print('Version:', root.findtext('Version'))

for idx, inp in enumerate(root.findall('Input')):
    t = inp.attrib.get('Type')
    title = inp.attrib.get('Title') or inp.attrib.get('OriginalTitle')
    val = (inp.text or '').strip()
    if len(val) > 60:
        val = val[:57] + '...'
    print(f"Input #{idx+1}: [Type {t}] {title} => {val}")
