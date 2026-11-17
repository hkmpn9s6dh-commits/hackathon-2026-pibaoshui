# -*- coding: utf-8 -*-
"""闸 C 的举证脚本：对着成片与图版真跑一遍。

用法：
  py -3 scripts/verify.py                # 全部
  py -3 scripts/verify.py --faces        # 只跑人物一致性
  py -3 scripts/verify.py --fonts        # 只跑字体覆盖
"""
import os, sys, json, subprocess, wave, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import story as S

FAIL = []
OK = []
PROOF = os.path.join(ROOT, "proof")
os.makedirs(PROOF, exist_ok=True)


def check(name, cond, detail=""):
    (OK if cond else FAIL).append((name, detail))
    print(("  PASS  " if cond else "  FAIL  ") + name + ("   " + detail if detail else ""))
    return cond


def ffprobe(path):
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-print_format", "json",
         "-show_format", "-show_streams", path]).decode("utf-8")
    return json.loads(out)


# ---------------------------------------------------------------- 成片规格
def verify_container(path=None):
    path = path or os.path.join(ROOT, "out", "pi-baoshui.mp4")
    print(f"\n[成片] {path}")
    if not check("AC-0 成片存在", os.path.exists(path)):
        return
    info = ffprobe(path)
    v = [s for s in info["streams"] if s["codec_type"] == "video"][0]
    a = [s for s in info["streams"] if s["codec_type"] == "audio"]
    dur = float(info["format"]["duration"])
    size = os.path.getsize(path)

    check("AC-1 时长 1–5 分钟", 60 <= dur <= 300, f"{dur:.2f}s")
    check("AC-2 竖屏 1080×1920", v["width"] == 1080 and v["height"] == 1920,
          f'{v["width"]}×{v["height"]}')
    check("AC-3 H.264 / yuv420p", v["codec_name"] == "h264" and v["pix_fmt"] == "yuv420p",
          f'{v["codec_name"]} / {v["pix_fmt"]}')
    check("AC-4 文件 ≤ 2GB", size <= 2 * 1024 ** 3, f"{size/1024/1024:.1f} MB")
    check("AC-5 有音轨", bool(a), f'{len(a)} 条' if a else "无")
    if a:
        check("AC-5b 48kHz 立体声", int(a[0]["sample_rate"]) == 48000 and int(a[0]["channels"]) == 2,
              f'{a[0]["sample_rate"]}Hz / {a[0]["channels"]}ch')

    # 响度与真峰
    p = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path,
                        "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True)
    txt = p.stderr
    tail = txt[txt.rfind("Summary:"):]
    I = LRA = PK = None
    for line in tail.splitlines():
        if line.strip().startswith("I:"):
            I = float(line.split()[1])
        if line.strip().startswith("LRA:"):
            LRA = float(line.split()[1])
        if line.strip().startswith("Peak:"):
            PK = float(line.split()[1])
    check("AC-5c 响度 −20…−12 LUFS", I is not None and -20 <= I <= -12, f"{I} LUFS")
    check("AC-5d 真峰 ≤ −1 dBFS", PK is not None and PK <= -1.0, f"{PK} dBFS")
    return dict(dur=dur, size=size, I=I, LRA=LRA, PK=PK)


# ---------------------------------------------------------------- 字幕
def verify_subs():
    print("\n[字幕]")
    L = S.LINES
    check("AC-6a 字幕条数 ≥ 20", len(L) >= 20, f"{len(L)} 条")
    bad_overlap = []
    for i, a in enumerate(L):
        for b in L[i + 1:]:
            if a["t0"] < b["t1"] and b["t0"] < a["t1"]:
                bad_overlap.append((a["text"], b["text"]))
    check("AC-6b 字幕不重叠", not bad_overlap, str(bad_overlap[:2]))
    short = [(x["text"], round(x["t1"] - x["t0"], 2)) for x in L if x["t1"] - x["t0"] < 1.2]
    check("AC-7a 每条停留 ≥ 1.2s", not short, str(short[:3]))
    inside = [x["text"] for x in L if x["t1"] > S.TOTAL or x["t0"] < 0]
    check("AC-6c 全部落在成片时间轴内", not inside, str(inside[:3]))

    rep = os.path.join(ROOT, "build", "vo_report.json")
    if os.path.exists(rep):
        vo = json.load(open(rep, encoding="utf-8"))
        over = [(v["text"], v["vo"], v["slot"]) for v in vo if v["vo"] > v["slot"] + 0.4]
        check("AC-7b 配音不超字幕槽 +0.4s", not over, str(over[:2]))
        check("AC-7c 配音条数 = 字幕条数", len(vo) == len(L), f'{len(vo)} / {len(L)}')
    # 字幕条带在成片里真的存在：抽 3 帧看字幕区是否出现高对比白字
    return True


def verify_sub_render(path=None):
    path = path or os.path.join(ROOT, "out", "pi-baoshui.mp4")
    if not os.path.exists(path):
        return
    print("\n[字幕上屏]")
    import tempfile
    t = S.LINES[6]["t0"] + (S.LINES[6]["t1"] - S.LINES[6]["t0"]) / 2
    with tempfile.TemporaryDirectory() as td:
        f = os.path.join(td, "f.png")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t:.2f}",
                        "-i", path, "-frames:v", "1", f], check=True)
        im = np.asarray(Image.open(f).convert("L"), np.float32)
    band = im[1920 - 300:1920 - 210, 120:960]
    hi = (band > 235).mean()
    check("AC-6d 字幕区有白字像素", hi > 0.004, f"高亮像素占比 {hi*100:.2f}%")


# ---------------------------------------------------------------- 分镜对齐
def verify_shots():
    print("\n[分镜]")
    acc, drift = 0.0, []
    for s in S.SHOTS:
        drift.append(abs(S.START[s["id"]] - acc))
        acc += s["dur"]
    check("AC-8a 镜头起点连续", max(drift) < 1e-6, f"最大偏差 {max(drift):.2e}s")
    check("AC-8b 镜头时长和 = 全片", abs(acc - S.TOTAL) < 1e-6, f"{acc:.2f}s / {S.TOTAL:.2f}s")
    miss = [s["plate"] for s in S.SHOTS if s["plate"] and
            not os.path.exists(os.path.join(ROOT, "assets", "plates", s["plate"] + ".png"))]
    check("AC-8c 每个镜头都有图版", not miss, str(miss))
    used = {s["plate"] for s in S.SHOTS if s["plate"]}
    unused = [p for p in S.PLATES if p not in used]
    check("AC-8d 没有闲图版", not unused, str(unused))
    check("AC-8e 每镜头 ≥ 3s", min(s["dur"] for s in S.SHOTS) >= 3.0,
          f'最短 {min(s["dur"] for s in S.SHOTS)}s')


# ---------------------------------------------------------------- 水印安全
def verify_safe():
    print("\n[水印安全区]")
    worst_r, worst_b = 0.0, 0.0
    for s in S.SHOTS:
        if not s["plate"]:
            continue
        z = s.get("z", 1.0)
        src = Image.open(os.path.join(ROOT, "assets", "plates", s["plate"] + ".png"))
        pw, ph = src.size
        sx0, sy0, sx1, sy1 = S.SAFE
        max_h = (sy1 - sy0) * ph
        win_h = max_h / z
        win_w = win_h * S.AR
        max_w = (sx1 - sx0) * pw
        if win_w > max_w:
            win_w, win_h = max_w, max_w / S.AR
        cy = s.get("cy", 0.5) * ph
        if s.get("cam") in ("drift_up", "drift_down"):
            cy += 0.03 * ph
        cx = 0.5 * (sx0 + sx1) * pw
        x0 = min(max(cx - win_w / 2, sx0 * pw), sx1 * pw - win_w)
        y0 = min(max(cy - win_h / 2, sy0 * ph), sy1 * ph - win_h)
        worst_r = max(worst_r, (x0 + win_w) / pw)
        worst_b = max(worst_b, (y0 + win_h) / ph)
    # 工具水印的实测位置：x ≥ 0.895、y ≥ 0.945（1024×1536 原图上量的）
    check("AC-10a 取样窗右边界 < 0.895", worst_r < 0.895, f"{worst_r:.3f}")
    check("AC-10b 取样窗下边界 < 0.945", worst_b < 0.945, f"{worst_b:.3f}")


# ---------------------------------------------------------------- 字体
def verify_fonts():
    print("\n[字体]")
    from fontTools.ttLib import TTFont
    # 按「这段字用哪套字体渲染」来查缺字，不能把两套字体的字符并成一个集合
    use = {"serif": [], "brush": []}
    use["serif"] += [l["text"] for l in S.LINES]
    for m in S.MARKS:
        use["brush" if m["kind"] in ("sfx", "title") else "serif"].append(m["text"])
    use["serif"] += [S.SUBTITLE]
    use["brush"] += [S.TITLE]
    files = {"serif": "NotoSerifSC-600.subset.ttf", "brush": "MaShanZheng.subset.ttf"}
    for kind, texts in use.items():
        fn = files[kind]
        p = os.path.join(ROOT, "assets", "fonts", fn)
        if not check(f"AC-11a 字体存在 {fn}", os.path.exists(p)):
            continue
        f = TTFont(p)
        cmap = set()
        for t in f["cmap"].tables:
            cmap |= set(t.cmap.keys())
        need = set("".join(texts))
        miss = sorted(ch for ch in need if ord(ch) not in cmap)
        check(f"AC-11b {fn} 缺字 = 0（{len(need)} 字）", not miss, "".join(miss))
    # 字体许可
    lic = os.path.join(ROOT, "assets", "fonts", "LICENSE.md")
    check("AC-11c 字体许可随包", os.path.exists(lic))


# ---------------------------------------------------------------- 人物一致
def gray_tpl(im, box):
    W, H = im.size
    c = im.crop((int(box[0] * W), int(box[1] * H), int(box[2] * W), int(box[3] * H)))
    return np.asarray(c.convert("L"), np.float32)


def crop_zone(path, b, target=None):
    im = Image.open(path).convert("RGB")
    W, H = im.size
    c = im.crop((int(b[0] * W), int(b[1] * H), int(b[2] * W), int(b[3] * H)))
    return c.resize(target, Image.LANCZOS) if target else c


def grad_of(im):
    g = im.convert("L").filter(ImageFilter.FIND_EDGES).filter(ImageFilter.GaussianBlur(1.0))
    return np.asarray(g, np.float32)


def ellipse_mask(th, tw, soft=0.18):
    """椭圆权重：只算头部那一块，背景不参与打分（否则白纸会跟任何白块相配）。"""
    y = np.linspace(-1, 1, th)[:, None]
    x = np.linspace(-1, 1, tw)[None, :]
    r = np.sqrt((x * 0.92) ** 2 + (y * 1.0) ** 2)
    m = np.clip((1.0 + soft - r) / soft, 0, 1).astype(np.float32)
    return m


def ncc_map(img, tmpl, mask=None):
    """带掩码的归一化互相关（全位置，FFT）。返回 (ncc, (y,x))。"""
    ih, iw = img.shape
    th, tw = tmpl.shape
    if th >= ih or tw >= iw:
        return -1.0, (0, 0)
    M = ellipse_mask(th, tw) if mask is None else mask
    Sm = float(M.sum())
    tbar = float((M * tmpl).sum() / Sm)
    tc = (tmpl - tbar) * M
    tn2 = float((tc ** 2).sum())
    if tn2 < 1e-6:
        return -1.0, (0, 0)
    fh, fw = ih + th, iw + tw
    F = np.fft.rfft2(img, (fh, fw))

    def corr(k):
        return np.fft.irfft2(F * np.fft.rfft2(k[::-1, ::-1], (fh, fw)), (fh, fw))[th - 1:ih, tw - 1:iw]

    A = corr(tc)
    S1 = corr(M)
    S1[S1 < 1e-6] = 1e-6
    m1 = S1 / Sm
    # 局部加权平方和：需要 Σ M*img²，用 M 与 img² 的卷积
    F2 = np.fft.rfft2(img ** 2, (fh, fw))
    S2 = np.fft.irfft2(F2 * np.fft.rfft2(M[::-1, ::-1], (fh, fw)), (fh, fw))[th - 1:ih, tw - 1:iw]
    var = S2 - Sm * m1 ** 2
    var[var < 1e-3] = 1e-3
    ncc = A / (np.sqrt(var) * math.sqrt(tn2))
    i = int(np.nanargmax(ncc))
    y, x = divmod(i, ncc.shape[1])
    return float(ncc[y, x]), (y, x)


def best_hit(panel, tmpl_g, ymax=0.56, scales=(0.5, 0.62, 0.75, 0.9, 1.05, 1.2, 1.4)):
    """整幅搜索这块脸（半分辨率上算），只要命中位置在画面上部。返回 (ncc, 框)。"""
    im = Image.open(panel).convert("RGB")
    small = im.resize((im.width // 2, im.height // 2), Image.LANCZOS)
    g = grad_of(small)
    best = (-1.0, None)
    for sc in scales:
        th = max(12, int(tmpl_g.shape[0] * sc / 2))
        tw = max(12, int(tmpl_g.shape[1] * sc / 2))
        t = np.asarray(Image.fromarray(tmpl_g.astype(np.uint8)).resize((tw, th), Image.LANCZOS),
                       np.float32)
        v, (y, x) = ncc_map(g, t)
        if y > ymax * g.shape[0]:
            continue
        if v > best[0]:
            best = (float(v), (x * 2, y * 2, tw * 2, th * 2))
    return best


# 每个角色的「身份参考集」：正面设定图 + 一张已确认的正片镜头
GALLERY = {
    "ye": [("char", (0.28, 0.03, 0.56, 0.30), "assets/char/ye.png")],
    "sun": [("char", (0.30, 0.10, 0.63, 0.34), "assets/char/sun.png")],
}
HARD = {"P12", "P19", "P22"}

# 参与人脸判定的镜头（P15 只拍手、P23 是背影，不判）
CHAR_PLATES = {"P04": "ye", "P22": "ye", "P05": "sun", "P19": "sun", "P21": "sun"}


def verify_faces():
    print("")
    print("[人物一致]")
    d = os.path.join(PROOF, "faces")
    os.makedirs(d, exist_ok=True)
    gal = {w: [grad_of(crop_zone(os.path.join(ROOT, pth), b)) for _n, b, pth in lst]
           for w, lst in GALLERY.items()}

    rows, tiles = [], []
    for who, lst in GALLERY.items():
        for n, b, pth in lst:
            tiles.append((f"REF_{n}_{who}", crop_zone(os.path.join(ROOT, pth), b)))
    for key, who in CHAR_PLATES.items():
        p = os.path.join(ROOT, "assets", "plates", key + ".png")
        hits = {w: max((best_hit(p, g) for g in gal[w]), key=lambda z: z[0]) for w in gal}
        good, box = hits[who]
        other = max(v for w, (v, _b) in hits.items() if w != who)
        need = 0.30 if key in HARD else 0.40
        ok = bool(good >= need)
        rows.append(dict(plate=key, who=who, ncc=round(good, 3), other=round(other, 3),
                         margin=round(good - other, 3), need=need, hard=key in HARD,
                         box=box, ok=ok))
        crop_im = Image.open(p).convert("RGB").crop(
            (box[0], box[1], box[0] + box[2], box[1] + box[3]))
        tiles.append((f"{key}_{who}_{good:.2f}", crop_im))
        check(f"AC-9a {key}（{who}）与本角色设定图 NCC {good:.2f} ≥ {need}", ok,
              "hard：偏侧/暗光/同框" if key in HARD else "")
        if key not in HARD:                    # 区分度只在单人、清晰镜头上要求
            check(f"AC-9b {key} 区分度：比另一角色高 {good-other:+.2f} ≥ +0.05",
                  good - other >= 0.05)
        else:
            print(f"  记    AC-9b {key} 区分度 {good-other:+.2f}（hard 镜头不作硬判，交证据条复核）")

    fnt = ImageFont.truetype(os.path.join(ROOT, "assets", "fonts", "NotoSerifSC-600.subset.ttf"), 20)
    sheet = Image.new("RGB", (len(tiles) * 140, 200), (250, 247, 240))
    dd = ImageDraw.Draw(sheet)
    for i, (n, c) in enumerate(tiles):
        sheet.paste(c.resize((134, 168), Image.LANCZOS), (i * 140, 28))
        dd.text((i * 140 + 2, 2), n, fill=(179, 58, 43), font=fnt)
    sheet.save(os.path.join(d, "strip.png"))
    json.dump(rows, open(os.path.join(d, "report.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"  证据条：{os.path.join(d, 'strip.png')}")
    return rows


def main():
    args = sys.argv[1:]
    only_faces = "--faces" in args
    only_fonts = "--fonts" in args
    md = os.path.join(PROOF, "ui")
    os.makedirs(md, exist_ok=True)

    if not only_faces and not only_fonts:
        verify_container()
        verify_subs()
        verify_sub_render()
        verify_shots()
        verify_safe()
        verify_fonts()
    if only_faces or not only_fonts:
        verify_faces()
    if only_fonts:
        verify_fonts()

    print(f"\n合计：{len(OK)} 过 / {len(FAIL)} 败")
    with open(os.path.join(PROOF, "verify.log"), "w", encoding="utf-8") as f:
        for n, d in OK:
            f.write(f"PASS  {n}  {d}\n")
        for n, d in FAIL:
            f.write(f"FAIL  {n}  {d}\n")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
