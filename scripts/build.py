# -*- coding: utf-8 -*-
"""一条命令出片：渲染 → 混音 → 合流 → 出成片与网页小样。

  py -3 scripts/build.py            # 全流程
  py -3 scripts/build.py --skip-render
"""
import os, sys, subprocess, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import story as S

B = os.path.join(ROOT, "build")
OUT = os.path.join(ROOT, "out")
os.makedirs(OUT, exist_ok=True)


def run(cmd, **kw):
    print("$", " ".join(cmd))
    return subprocess.run(cmd, check=True, **kw)


def main():
    skip = "--skip-render" in sys.argv
    video = os.path.join(B, "video.mp4")
    audio = os.path.join(B, "audio.wav")
    if not skip:
        run([sys.executable, os.path.join(ROOT, "scripts", "render.py"), video])
    if not os.path.exists(audio) or not skip:
        run([sys.executable, os.path.join(ROOT, "scripts", "audio.py")])

    master = os.path.join(OUT, "pi-baoshui.mp4")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-i", audio,
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
         "-shortest", "-movflags", "+faststart", master])
    print("master:", master, f"{os.path.getsize(master)/1024/1024:.1f} MB")

    # 网页小样：720×1280，给放映页用（不参与交件）
    os.makedirs(os.path.join(ROOT, "site"), exist_ok=True)
    web = os.path.join(ROOT, "site", "clip.mp4")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", master,
         "-vf", "scale=720:1280", "-c:v", "libx264", "-crf", "27",
         "-preset", "slow", "-c:a", "aac", "-b:a", "96k",
         "-movflags", "+faststart", web])
    print("web:", web, f"{os.path.getsize(web)/1024/1024:.1f} MB")

    # 封面：取 0:30（她推门，两位盲读评委都选它当封面）与 3:46（片名卡）
    for t, name in [(30.0, "cover.jpg"), (226.0, "endcard.jpg")]:
        run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", master,
             "-frames:v", "1", "-q:v", "2", os.path.join(ROOT, "site", name)])


if __name__ == "__main__":
    main()
