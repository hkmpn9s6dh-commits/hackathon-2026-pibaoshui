# -*- coding: utf-8 -*-
"""只重渲一个镜头，参数与 render.py 完全一致，便于和母版 -c copy 拼接。

  py -3 scripts/render_one.py S30 build/s30.mp4
"""
import os, sys, subprocess
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
import story as S
import render as R

sid = sys.argv[1]
out = sys.argv[2]
shot = [s for s in S.SHOTS if s["id"] == sid][0]
cmd = ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{R.W}x{R.H}",
       "-r", str(R.FPS), "-i", "-", "-an", "-c:v", "libx264", "-preset", "medium",
       "-crf", "23", "-pix_fmt", "yuv420p", out]
proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL)
n = int(round(shot["dur"] * R.FPS))
marks = [m for m in S.MARKS if m["shot"] == sid]
for k in range(n):
    lt = k / R.FPS
    frame = R.shot_frame(shot, lt, k)
    for m in marks:
        base = S.START[sid]
        a = min(1.0, max(0.0, (lt - m["t"]) / 0.25)) if lt >= m["t"] else 0.0
        if m["kind"] == "sfx":
            a *= max(0.0, 1.0 - max(0.0, lt - m["t"] - 1.2) / 0.5)
        if a > 0.01:
            layer = R.Image.new("RGBA", (R.W, R.H), (0, 0, 0, 0))
            R.draw_mark(layer, m)
            if a < 1.0:
                arr = np.asarray(layer, np.float32); arr[..., 3] *= a
                layer = R.Image.fromarray(arr.clip(0, 255).astype(np.uint8))
            frame.alpha_composite(layer)
    arr = R.post(frame, k)
    if sid in R.FADES:
        fade = 1.0
        if lt < 0.30:
            fade = lt / 0.30
        elif lt > shot["dur"] - 0.30:
            fade = max(0.0, (shot["dur"] - lt) / 0.30)
        if fade < 1.0:
            arr = (arr * fade).astype(np.uint8)
    proc.stdin.write(arr.tobytes())
proc.stdin.close()
print("rc", proc.wait(), out, n, "frames")
