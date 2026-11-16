# -*- coding: utf-8 -*-
"""抽帧检查：py -3 scripts/stills.py 5 55 150 225"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import story as S
import render as R

OUT = os.path.join(R.BUILD, "stills")
os.makedirs(OUT, exist_ok=True)

for arg in sys.argv[1:]:
    t = float(arg)
    shot = None
    for s in S.SHOTS:
        if S.START[s["id"]] <= t < S.START[s["id"]] + s["dur"]:
            shot = s
            break
    if shot is None:
        shot = S.SHOTS[-1]
    lt = t - S.START[shot["id"]]
    frame = R.shot_frame(shot, lt, int(round(t * S.FPS)))
    for m in [m for m in S.MARKS if m["shot"] == shot["id"]]:
        if lt >= m["t"]:
            layer = R.Image.new("RGBA", (R.W, R.H), (0, 0, 0, 0))
            R.draw_mark(layer, m)
            frame.alpha_composite(layer)
    for ln in S.LINES:
        if ln["t0"] <= t <= ln["t1"]:
            R.draw_sub(frame, ln["text"])
    arr = R.post(frame, int(round(t * S.FPS)))
    R.Image.fromarray(arr).save(os.path.join(OUT, f"t{t:07.2f}_{shot['id']}.png"))
    print(shot["id"], f"{lt:.2f}s ->", os.path.join(OUT, f"t{t:07.2f}_{shot['id']}.png"))
