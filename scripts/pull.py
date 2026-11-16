# -*- coding: utf-8 -*-
"""把 ImageGen 落在 plates/ 里、还没改名的长文件名，按修改时间顺序改成 Pxx.png。

用法：py -3 scripts/pull.py P11 P12 P07 P10
只认名字不以 P 开头的 png，避免误改。
"""
import os, sys, glob

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "plates")
targets = sys.argv[1:]
if not targets:
    sys.exit("要给的图版名，例如 P11 P12")

files = [f for f in glob.glob(os.path.join(D, "*.png"))
         if not os.path.basename(f).startswith("P")]
files.sort(key=os.path.getmtime)
if len(files) < len(targets):
    sys.exit(f"待改名文件只有 {len(files)} 个，不够 {len(targets)} 个：{[os.path.basename(f) for f in files]}")
for t, f in zip(targets, files):
    dst = os.path.join(D, t + ".png")
    os.replace(f, dst)
    print(f"{os.path.basename(f)[:28]}…  ->  {t}.png")
