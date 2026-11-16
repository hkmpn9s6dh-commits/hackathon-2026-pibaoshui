# -*- coding: utf-8 -*-
"""声音：edge-tts 配音 + numpy 合成环境音/音效/箫 + 混音。

输出 build/audio.wav（48k / 16bit / 立体声），响度对到 -16 LUFS。
"""
import os, sys, math, json, asyncio, subprocess, wave
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import story as S

ROOT = S.ROOT
BUILD = os.path.join(ROOT, "build")
VO = os.path.join(BUILD, "vo")
os.makedirs(VO, exist_ok=True)
SR = 48000
N = int(S.TOTAL * SR) + SR * 2


def idx(t):
    return max(0, int(round(t * SR)))


def add(buf, x, t, gain=1.0):
    i = idx(t)
    n = min(len(x), buf.shape[0] - i)
    if n <= 0:
        return
    buf[i:i + n] += x[:n] * gain


def env_ad(n, a=0.01, d=0.3):
    a_n = max(1, int(a * SR))
    d_n = max(1, int(d * SR))
    e = np.ones(n, np.float32)
    a_n = min(a_n, n)
    e[:a_n] = np.linspace(0, 1, a_n)
    d_n = min(d_n, n - a_n)
    if d_n > 0:
        e[n - d_n:] *= np.linspace(1, 0, d_n) ** 2
    return e


def noise(n, rng):
    return rng.normal(0, 1, n).astype(np.float32)


def lp(x, a):
    """一阶低通。a 越小越闷。"""
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc += a * (x[i] - acc)
        y[i] = acc
    return y


def lp_fast(x, k=64):
    """用卷积近似低通（快）。"""
    ker = np.ones(k, np.float32) / k
    return np.convolve(x, ker, mode="same").astype(np.float32)


def bp(x, lo=1, hi=8):
    """粗略带通：先降采样再升采样。"""
    y = lp_fast(x, hi)
    y2 = lp_fast(y, lo * 4)
    return (y - y2).astype(np.float32)


# ---------------------------------------------------------------- 配音
async def _tts(text, voice, rate, pitch, out):
    import edge_tts
    com = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    await com.save(out)


def tts(text, who, out):
    v = S.VOICE[who]
    asyncio.run(_tts(text, v["voice"], v["rate"], v["pitch"], out))


def read_wav(p):
    with wave.open(p, "rb") as w:
        n = w.getnframes()
        data = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32) / 32768.0
        if w.getnchannels() == 2:
            data = data.reshape(-1, 2).mean(axis=1)
    return data


def resample(x, sr_in, sr_out=SR):
    if sr_in == sr_out:
        return x
    n = int(len(x) * sr_out / sr_in)
    return np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x).astype(np.float32)


def build_vo(buf, report):
    for k, ln in enumerate(S.LINES):
        if ln["kind"] not in ("d", "n"):
            continue
        raw = os.path.join(VO, f"{k:02d}_{ln['who']}.mp3")
        if not os.path.exists(raw):
            tts(ln["text"], ln["who"], raw)
        wav = os.path.join(VO, f"{k:02d}.wav")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw,
                        "-ar", str(SR), "-ac", "1", wav], check=True)
        x = read_wav(wav)
        slot = ln["t1"] - ln["t0"]
        dur = len(x) / SR
        report.append(dict(text=ln["text"], who=ln["who"], t0=ln["t0"],
                           slot=round(slot, 2), vo=round(dur, 2)))
        add(buf, x, ln["t0"], 1.0)
    return buf


# ---------------------------------------------------------------- 环境音
def synth_sfx(kind, dur, rng):
    n = int(dur * SR)
    if n <= 0:
        return np.zeros(1, np.float32)
    if kind == "room":
        x = lp_fast(noise(n, rng), 400) * 0.5
        return x * env_ad(n, 0.5, 0.5)
    if kind == "boil":
        base = bp(noise(n, rng), 2, 24)
        am = 0.55 + 0.45 * np.sin(2 * np.pi * 3.1 * np.arange(n) / SR)
        bub = (rng.random(n) > 0.9993).astype(np.float32)
        bub = np.convolve(bub, np.hanning(240), mode="same") * 3.0
        return ((base * am) * 0.5 + bub) * env_ad(n, 1.0, 1.2)
    if kind == "match":
        x = noise(n, rng) * np.exp(-np.arange(n) / (0.05 * SR))
        click = np.zeros(n, np.float32)
        for c in range(4):
            i0 = int(c * 0.12 * SR)
            click[i0:i0 + 300] += noise(300, rng) * np.exp(-np.arange(300) / 60)
        return (x * 0.4 + click) * env_ad(n, 0.005, 0.3)
    if kind == "door":
        t = np.arange(n) / SR
        creak = np.sin(2 * np.pi * (180 + 90 * t / dur) * t) * 0.3
        creak *= (rng.random(n) > 0.5).astype(np.float32) * 0.6 + 0.4
        thud = np.zeros(n, np.float32)
        thud[int(0.55 * SR):int(0.55 * SR) + 2400] = \
            noise(2400, rng) * np.exp(-np.arange(2400) / 500)
        return (creak * 0.5 + thud * 0.7) * env_ad(n, 0.02, 0.5)
    if kind == "pour":
        x = bp(noise(n, rng), 8, 64)
        t = np.arange(n) / SR
        x *= 0.6 + 0.4 * np.sin(2 * np.pi * 6 * t) ** 2
        return x * env_ad(n, 0.15, 0.5)
    if kind == "chop":
        out = np.zeros(n, np.float32)
        step = int(0.42 * SR)
        for i0 in range(0, n - 800, step):
            seg = noise(800, rng) * np.exp(-np.arange(800) / 90)
            out[i0:i0 + 800] += seg * (0.7 + 0.3 * rng.random())
        return out * env_ad(n, 0.05, 0.4)
    if kind == "shop":
        x = bp(noise(n, rng), 3, 12) * 0.5
        t = np.arange(n) / SR
        x *= 0.6 + 0.4 * np.sin(2 * np.pi * 0.7 * t)
        clink = np.zeros(n, np.float32)
        for c in range(int(dur / 7)):
            i0 = int((c * 7 + rng.random() * 4) * SR)
            if i0 + 3000 < n:
                clink[i0:i0 + 3000] += (noise(3000, rng) *
                                        np.exp(-np.arange(3000) / 700) * 0.5)
        return (x + clink) * env_ad(n, 1.5, 1.5)
    if kind == "fry":
        x = bp(noise(n, rng), 6, 40)
        t = np.arange(n) / SR
        x *= 0.7 + 0.3 * np.sin(2 * np.pi * 11 * t) ** 2
        return x * env_ad(n, 0.3, 0.6)
    if kind == "street":
        x = lp_fast(noise(n, rng), 120) * 0.7
        t = np.arange(n) / SR
        x *= 0.7 + 0.3 * np.sin(2 * np.pi * 0.23 * t)
        bell = np.zeros(n, np.float32)
        i0 = int(dur * 0.55 * SR)
        m = min(9000, n - i0)
        if m > 0:
            tt = np.arange(m) / SR
            bell[i0:i0 + m] = (np.sin(2 * np.pi * 2350 * tt) +
                               np.sin(2 * np.pi * 3170 * tt)) * np.exp(-tt / 0.25) * 0.25
        return (x + bell) * env_ad(n, 1.2, 1.2)
    if kind == "city":
        x = lp_fast(noise(n, rng), 90) * 0.8
        t = np.arange(n) / SR
        x *= 0.75 + 0.25 * np.sin(2 * np.pi * 0.11 * t)
        return x * env_ad(n, 2.0, 2.0)
    return np.zeros(n, np.float32)


# ---------------------------------------------------------------- 箫
def flute(freq, dur, rng):
    n = int(dur * SR)
    t = np.arange(n) / SR
    vib = 1 + 0.004 * np.sin(2 * np.pi * 4.6 * t) * np.minimum(1, t / 0.5)
    ph = 2 * np.pi * freq * t * vib
    tone = (np.sin(ph) + 0.28 * np.sin(2 * ph) + 0.12 * np.sin(3 * ph)
            + 0.05 * np.sin(5 * ph))
    breath = bp(noise(n, rng), 40, 120) * 0.05
    e = np.ones(n, np.float32)
    a = int(0.14 * SR)
    e[:a] = np.linspace(0, 1, a) ** 0.7
    r = int(0.30 * SR)
    e[-r:] *= np.linspace(1, 0, r) ** 1.4
    return (tone * 0.5 + breath) * e


def reverb(x, rng, wet=0.35, decay=1.9):
    n_ir = int(decay * SR)
    ir = rng.normal(0, 1, n_ir).astype(np.float32)
    ir *= np.exp(-np.arange(n_ir) / (n_ir / 4.5))
    ir = lp_fast(ir, 12)
    ir /= np.sqrt((ir ** 2).sum())
    L = len(x) + n_ir - 1
    nfft = 1 << (L - 1).bit_length()
    y = np.fft.irfft(np.fft.rfft(x, nfft) * np.fft.rfft(ir, nfft), nfft)[:len(x)]
    return (x * (1 - wet) + y * wet * 2.2).astype(np.float32)


# D 小调五声：D F G A C
FREQ = {"D3": 146.83, "F3": 174.61, "G3": 196.00, "A3": 220.00,
        "C4": 261.63, "D4": 293.66, "F4": 349.23, "G4": 392.00, "A4": 440.00}

# (起点秒, 音, 时长)  —— 稀疏，只压在情绪转折上
MELODY = [
    (4.0, "A3", 3.2), (12.5, "D4", 3.0),
    (33.0, "F3", 2.6), (46.0, "G3", 2.4),
    (72.0, "C4", 2.8), (86.0, "A3", 3.4),
    (101.0, "F3", 2.6), (113.0, "D3", 4.0),
    (126.0, "G3", 2.4), (140.0, "A3", 3.6),
    (158.0, "C4", 2.6), (170.0, "D4", 3.4),
    (182.0, "F3", 3.0), (194.0, "D3", 4.2),
    (207.0, "A3", 3.2), (218.0, "D3", 4.5),
]


def build_music(rng):
    buf = np.zeros(N, np.float32)
    for t0, name, dur in MELODY:
        x = flute(FREQ[name], dur, rng)
        add(buf, x, t0, 1.0)
    wet = reverb(buf, rng, wet=0.42, decay=2.6)
    return wet


# ---------------------------------------------------------------- 主流程
def main():
    rng = np.random.default_rng(2026)
    rep = []
    vo = np.zeros(N, np.float32)
    build_vo(vo, rep)

    sfx = np.zeros(N, np.float32)
    for c in S.SFX:
        x = synth_sfx(c["kind"], c["dur"], rng)
        add(sfx, x, c["t"], c["gain"])

    mus = build_music(rng) * S.MUSIC["gain"]

    # 配音响度归一：把每条 VO 的峰值控住，再整体混
    vo_pk = np.abs(vo).max() or 1.0
    vo = vo / vo_pk * 0.72

    # 侧链：配音处压低音乐与音效（简单包络）
    env = np.ones(N, np.float32)
    win = int(0.35 * SR)
    for ln in S.LINES:
        if ln["kind"] not in ("d", "n"):
            continue
        i0, i1 = idx(ln["t0"] - 0.15), idx(ln["t1"] + 0.35)
        seg = np.linspace(0, 1, min(win, max(1, (i1 - i0) // 3)))
        env[i0:i1] *= 0.55
        env[i0:i0 + len(seg)] *= np.linspace(1, 0.55, len(seg))
        tail = env[i1:i1 + len(seg)]
        if len(tail):
            tail *= np.linspace(0.55, 1, len(tail))
    mus *= env
    sfx *= (0.85 + 0.15 * env)

    mix = vo + mus + sfx
    # 温柔限幅
    mix = np.tanh(mix * 1.05) * 0.92

    st = np.stack([mix, mix], axis=1)
    pcm = (st.clip(-1, 1) * 32767).astype(np.int16)

    raw = os.path.join(BUILD, "audio_raw.wav")
    with wave.open(raw, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())

    out = os.path.join(BUILD, "audio.wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw,
                    "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", str(SR),
                    "-c:a", "pcm_s16le", out], check=True)
    print(f"audio -> {out}")
    json.dump(rep, open(os.path.join(BUILD, "vo_report.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    over = [r for r in rep if r["vo"] > r["slot"] + 0.12]
    for r in over:
        print("  ! 配音超槽:", r["text"], r["vo"], ">", r["slot"])
    print(f"  配音 {len(rep)} 条，超槽 {len(over)} 条")


if __name__ == "__main__":
    main()
