# -*- coding: utf-8 -*-
"""从 story.py 生成 docs/03-SHOTS.md（分镜表），并可反向核对文档没被手改歪。

  py -3 scripts/gen_shots.py          # 写文件
  py -3 scripts/gen_shots.py --check  # 只核对（verify.sh 用这个）
"""
import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import story as S

OUT = os.path.join(ROOT, "docs", "03-SHOTS.md")
CAM = {"push_in": "推", "push_out": "拉", "still": "定", "drift_up": "上移", "drift_down": "下移"}


def build():
    L = []
    L.append("# 03 · 分镜表（由 `story.py` 生成，不要手改）\n")
    L.append(f"共 {len(S.SHOTS)} 个镜头，总时长 **{S.TOTAL:.1f} 秒**"
             f"（{int(S.TOTAL//60)}:{S.TOTAL%60:05.2f}），1080×1920 / {S.FPS}fps。\n")
    L.append("| # | 时间 | 时长 | 图版 | 运镜 | 图版内容 | 声音 |")
    L.append("| --- | --- | --- | --- | --- | --- | --- |")
    for s in S.SHOTS:
        t0 = S.START[s["id"]]
        mm, ss = int(t0 // 60), t0 % 60
        plate = s["plate"] or "—（片尾卡）"
        desc = "—"
        if s["plate"]:
            p = S.PLATES[s["plate"]]["prompt"]
            desc = p.split("\n")[-1][:34].replace("|", "／")
        lines = [l["text"] for l in S.LINES
                 if l["t0"] >= t0 - 0.01 and l["t1"] <= t0 + s["dur"] + 0.01]
        audio = " ／ ".join(lines) if lines else "环境音"
        cam = CAM.get(s["cam"], s["cam"]) + (f" 至 {s['z']:.2f}×" if s["cam"] in ("push_in", "push_out") else "")
        L.append(f"| {s['id']} | {mm}:{ss:05.2f} | {s['dur']:.1f}s | {plate} | {cam} | {desc}… | {audio} |")
    L.append("\n## 图版清单\n")
    L.append("| 图版 | 谁出现 | 用途 |")
    L.append("| --- | --- | --- |")
    used = {}
    for s in S.SHOTS:
        if s["plate"]:
            used.setdefault(s["plate"], []).append(s["id"])
    for k in sorted(S.PLATES):
        v = S.PLATES[k]
        who = {"ye": "爷爷", "sun": "孙女", "both": "两人"}.get(v["ref"], "无人")
        L.append(f"| {k} | {who} | {', '.join(used.get(k, ['（未用）']))} |")
    return "\n".join(L) + "\n"


def main():
    txt = build()
    if "--check" in sys.argv:
        if not os.path.exists(OUT):
            sys.exit("docs/03-SHOTS.md 不存在，先跑 py -3 scripts/gen_shots.py")
        old = open(OUT, encoding="utf-8").read()
        if old.strip() != txt.strip():
            sys.exit("docs/03-SHOTS.md 与 story.py 不一致 —— 重跑 py -3 scripts/gen_shots.py")
        print("分镜表与 story.py 一致")
        return
    open(OUT, "w", encoding="utf-8").write(txt)
    print("written:", OUT)


if __name__ == "__main__":
    main()
