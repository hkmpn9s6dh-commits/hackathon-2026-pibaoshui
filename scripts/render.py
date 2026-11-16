# -*- coding: utf-8 -*-
"""逐帧渲染《皮包水》→ rawvideo 喂 ffmpeg。

镜头运动只用缩放与竖向微移（源图 2:3，9:16 取样窗横向几乎没有余量）。
字幕：白字 + 墨描边；拟声字与片名用楷体，压在画面里。
"""
import os, sys, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import story as S

ROOT = S.ROOT
W, H, FPS = S.W, S.H, S.FPS
PLATES = os.path.join(ROOT, "assets", "plates")
FONT_DIR = os.path.join(ROOT, "assets", "fonts")
BUILD = os.path.join(ROOT, "build")
os.makedirs(BUILD, exist_ok=True)

INK = (27, 26, 23)
PAPER = (243, 237, 225)
CINNABAR = (179, 58, 43)

# 淡入淡出的镜头（两侧都淡）：幕间用
FADES = {"S01", "S06", "S13", "S21", "S26", "S29", "S30"}


FONTS = {"serif": "NotoSerifSC-600.subset.ttf", "brush": "MaShanZheng.subset.ttf"}


def font(size, name="serif"):
    return ImageFont.truetype(os.path.join(FONT_DIR, FONTS[name]), size)


_F = {}


def F(size, name="serif"):
    k = (size, name)
    if k not in _F:
        _F[k] = font(size, name)
    return _F[k]


def ease_io(x):
    x = min(max(x, 0.0), 1.0)
    return 0.5 - 0.5 * math.cos(math.pi * x)


# ---------------------------------------------------------------- 纸
def paper_canvas(seed=7):
    rng = np.random.default_rng(seed)
    h, w = H, W
    base = np.zeros((h, w, 3), np.float32)
    for i, c in enumerate(PAPER):
        base[..., i] = c
    # 大块色差（宣纸的不匀）
    low = rng.normal(0, 1, (h // 24 + 2, w // 24 + 2)).astype(np.float32)
    low = np.array(Image.fromarray(((low * 40) + 128).clip(0, 255).astype(np.uint8))
                   .resize((w, h), Image.BICUBIC), np.float32) - 128
    base += (low * 0.16)[..., None]
    # 纤维
    fib = rng.normal(0, 1, (h, w)).astype(np.float32)
    fib = np.array(Image.fromarray(((fib * 30) + 128).clip(0, 255).astype(np.uint8))
                   .filter(ImageFilter.GaussianBlur(0.6)), np.float32) - 128
    base += (fib * 0.10)[..., None]
    return Image.fromarray(base.clip(0, 255).astype(np.uint8))


_PAPER = None


def paper():
    global _PAPER
    if _PAPER is None:
        _PAPER = paper_canvas()
    return _PAPER


# ---------------------------------------------------------------- 颗粒与暗角
_rng = np.random.default_rng(11)
GRAIN = _rng.normal(0, 1, (H + 64, W + 64)).astype(np.float32)
_yy, _xx = np.mgrid[0:H, 0:W]
_r = np.sqrt(((_xx - W / 2) / (W * 0.62)) ** 2 + ((_yy - H / 2) / (H * 0.62)) ** 2)
VIG = (1.0 - 0.16 * np.clip(_r, 0, 1) ** 2.2).astype(np.float32)[..., None]


def post(im, frame_i, grain=0.055):
    a = np.asarray(im.convert("RGB"), np.float32)
    g = GRAIN[frame_i % 64:frame_i % 64 + H, frame_i * 7 % 64:frame_i * 7 % 64 + W]
    a += (g * grain * 255.0)[..., None]
    a *= VIG
    return a.clip(0, 255).astype(np.uint8)


# ---------------------------------------------------------------- 取样窗
def window(shot, p):
    """p: 0→1 镜头内进度。返回图版像素坐标 (x0,y0,x1,y1, 缩放到画幅)。"""
    src = plate(shot["plate"])
    pw, ph = src.size
    sx0, sy0, sx1, sy1 = S.SAFE
    z = shot.get("z", 1.0)
    cam = shot.get("cam", "still")
    t = ease_io(p)
    if cam == "push_in":
        zz = 1.0 + (z - 1.0) * t
    elif cam == "push_out":
        zz = z - (z - 1.0) * t
    elif cam in ("drift_up", "drift_down"):
        zz = z
    else:
        zz = 1.0 + (z - 1.0) * 0.25 * t

    # 安全区内的最大 9:16 窗
    max_h = (sy1 - sy0) * ph
    win_h = max_h / zz
    win_w = win_h * S.AR
    max_w = (sx1 - sx0) * pw
    if win_w > max_w:
        win_w = max_w
        win_h = win_w / S.AR

    cx = 0.5 * (sx0 + sx1) * pw
    cy = shot.get("cy", 0.5) * ph
    if cam == "drift_up":
        cy -= (t - 0.5) * 0.05 * ph
    elif cam == "drift_down":
        cy += (t - 0.5) * 0.05 * ph

    x0 = min(max(cx - win_w / 2, sx0 * pw), sx1 * pw - win_w)
    y0 = min(max(cy - win_h / 2, sy0 * ph), sy1 * ph - win_h)
    return x0, y0, win_w, win_h


_plates = {}


def plate(key):
    if key not in _plates:
        _plates[key] = Image.open(os.path.join(PLATES, key + ".png")).convert("RGB")
    return _plates[key]


def sample(shot, p):
    if shot["plate"] is None:
        return paper().copy()
    src = plate(shot["plate"])
    x0, y0, ww, wh = window(shot, p)
    # AFFINE: 输出 1080×1920 取自 (x0,y0) 起、宽 ww、高 wh 的区域
    sx = ww / W
    sy = wh / H
    return src.transform((W, H), Image.AFFINE, (sx, 0, x0, 0, sy, y0),
                         resample=Image.BICUBIC)


# ---------------------------------------------------------------- 文字层
def text_layer(text, size, fname="serif", fill=(255, 255, 255), stroke=0,
               stroke_fill=INK, tracking=0.0):
    f = F(size, fname)
    asc, desc = f.getmetrics()
    tw = int(f.getlength(text) + tracking * max(len(text) - 1, 0))
    pad = stroke + 8
    im = Image.new("RGBA", (tw + pad * 2, asc + desc + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f2 = F(size, fname)
    d.text((pad, pad), text, font=f2, fill=fill + (255,),
           stroke_width=stroke, stroke_fill=stroke_fill + (255,))
    return im


_subs = {}


def subtitle(text):
    if text in _subs:
        return _subs[text]
    size = 46 if len(text) <= 18 else 42
    im = text_layer(text, size, "serif", (255, 255, 255), stroke=5, stroke_fill=(20, 19, 17))
    # 阴影
    sh = Image.new("RGBA", (im.width + 8, im.height + 8), (0, 0, 0, 0))
    sh.paste(im, (4, 4), im)
    sh = sh.filter(ImageFilter.GaussianBlur(3))
    a = np.asarray(sh, np.float32)
    a[..., 3] *= 0.55
    sh = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    _subs[text] = (sh, im)
    return _subs[text]


def draw_sub(frame, text, alpha=1.0):
    sh, im = subtitle(text)
    x = (W - im.width) // 2 + 4
    y = H - 268
    if alpha < 1.0:
        im = im.copy()
        a = np.asarray(im, np.float32)
        a[..., 3] *= alpha
        im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    frame.alpha_composite(sh, (x, y))
    frame.alpha_composite(im, (x, y))


def draw_mark(frame, m):
    size = int(m["size"] * H)
    txt = m["text"]
    fname = "brush" if m["kind"] in ("sfx", "title") else "serif"
    if m["kind"] == "title":
        im = text_layer(txt, size, "brush", INK, stroke=0, tracking=0.10)
    elif m["kind"] in ("sfx",):
        im = text_layer(txt, size, "brush", INK, stroke=0)
    elif m["kind"] == "note":
        im = text_layer(txt, size, "serif", (120, 112, 100))
    elif m["kind"] == "note2":
        im = text_layer(txt, size, "serif", (120, 112, 100))
    else:
        im = text_layer(txt, size, fname, CINNABAR, stroke=0, tracking=0.34)
    if m.get("rot"):
        im = im.rotate(m["rot"], resample=Image.BICUBIC, expand=True)
    x = int(m["x"] * W - im.width / 2)
    y = int(m["y"] * H - im.height / 2)
    frame.alpha_composite(im, (x, y))


# ---------------------------------------------------------------- 镜头内的画
def shot_frame(shot, local_t, frame_i):
    p = local_t / shot["dur"]
    base = sample(shot, p).convert("RGB")

    if shot["plate"] is None:                       # 片尾卡：宣纸 + 朱印
        d = ImageDraw.Draw(base)
        # 一条极淡的横线，压在片名下方
        d.line([(W * 0.22, H * 0.585), (W * 0.78, H * 0.585)], fill=(190, 180, 165), width=2)
        # 朱印（右下，一方小红块 + 白文）
        s = 84
        x0, y0 = int(W * 0.615), int(H * 0.578)
        d.rectangle([x0, y0, x0 + s, y0 + s], fill=CINNABAR)
        seal = text_layer("海陵", int(s * 0.34), "serif", (255, 250, 244))
        base.paste(seal, (x0 + (s - seal.width) // 2, y0 + (s - seal.height) // 2), seal)

    frame = base.convert("RGBA")
    return frame


# ---------------------------------------------------------------- 主循环
def render(out_path):
    cmd = ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
           "-pix_fmt", "yuv420p", "-movflags", "+faststart", out_path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    i = 0
    total = int(round(S.TOTAL * FPS))
    for shot in S.SHOTS:
        n = int(round(shot["dur"] * FPS))
        marks = [m for m in S.MARKS if m["shot"] == shot["id"]]
        for k in range(n):
            lt = k / FPS
            frame = shot_frame(shot, lt, i)

            # 镜头内的拟声字/题字
            for m in marks:
                mt = m["t"]
                a = min(1.0, max(0.0, (lt - mt) / 0.25)) if lt >= mt else 0.0
                if m["kind"] == "sfx":
                    # 拟声字只停 1.6 秒
                    a *= max(0.0, 1.0 - max(0.0, lt - mt - 1.2) / 0.5)
                if a > 0.01:
                    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                    draw_mark(layer, m)
                    if a < 1.0:
                        arr = np.asarray(layer, np.float32)
                        arr[..., 3] *= a
                        layer = Image.fromarray(arr.clip(0, 255).astype(np.uint8))
                    frame.alpha_composite(layer)

            # 字幕
            for ln in S.LINES:
                if ln["t0"] - 0.001 <= lt + S.START[shot["id"]] <= ln["t1"] + 0.001:
                    a = 1.0
                    edge = min(lt + S.START[shot["id"]] - ln["t0"], ln["t1"] - (lt + S.START[shot["id"]]))
                    if edge < 0.18:
                        a = max(0.0, edge / 0.18)
                    draw_sub(frame, ln["text"], a)

            arr = post(frame, i)

            # 幕间淡入淡出
            abs_t = S.START[shot["id"]] + lt
            fade = 1.0
            if shot["id"] in FADES:
                if lt < 0.30:
                    fade = lt / 0.30
                elif lt > shot["dur"] - 0.30:
                    fade = max(0.0, (shot["dur"] - lt) / 0.30)
            if fade < 1.0:
                arr = (arr * fade).astype(np.uint8)

            proc.stdin.write(arr.tobytes())
            i += 1
            if i % 240 == 0:
                print(f"  {i}/{total} frames  ({i/total*100:.0f}%)", flush=True)
    proc.stdin.close()
    proc.wait()
    return i


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BUILD, "video.mp4")
    n = render(out)
    print(f"frames={n} total={S.TOTAL:.1f}s -> {out}")
