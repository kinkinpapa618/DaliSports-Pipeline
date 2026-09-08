#!/usr/bin/env python3
import sys, subprocess, os
sys.stdout.reconfigure(encoding="utf-8")
# Launcher giữ tương thích sau khi move vào system/
res = subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "system", "auto_pipeline.py")] + sys.argv[1:])
sys.exit(res.returncode)
