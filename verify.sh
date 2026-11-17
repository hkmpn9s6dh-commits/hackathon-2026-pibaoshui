#!/usr/bin/env bash
# 一条命令把这部片子从头验一遍。全新 clone 只需要 python + ffmpeg + pip -r requirements.txt
set -euo pipefail
cd "$(dirname "$0")"

PY=${PY:-py -3}
command -v py >/dev/null 2>&1 || PY=python3

echo "== 0. 依赖 =="
$PY - <<'EOF'
import importlib.util, sys
need = ["numpy", "PIL", "fontTools", "edge_tts", "brotli"]
miss = [m for m in need if importlib.util.find_spec(m) is None]
if miss:
    sys.exit("缺依赖：" + ", ".join(miss) + "\n  pip install -r requirements.txt")
print("依赖齐")
EOF

echo "== 1. 图版与字体 =="
$PY - <<'EOF'
import os, sys
sys.path.insert(0, ".")
import story as S
miss = [p for p in [k for k in S.PLATES] if not os.path.exists(f"assets/plates/{p}.png")]
if miss:
    sys.exit("缺图版：" + ", ".join(miss))
for f in ["NotoSerifSC-600.subset.ttf", "MaShanZheng.subset.ttf"]:
    if not os.path.exists(f"assets/fonts/{f}"):
        sys.exit("缺字体 " + f + "（跑 scripts/subset_fonts.py 生成，需要 assets/fonts 下的原始字体）")
print(f"图版 {len(S.PLATES)} 张、字体 2 套")
EOF

echo "== 2. 成片 =="
if [ ! -f out/pi-baoshui.mp4 ]; then
  echo "   out/pi-baoshui.mp4 不存在，现在从头构建（约 6 分钟）"
  $PY scripts/build.py
fi

echo "== 3. 闸 C 逐条 =="
$PY scripts/verify.py

echo "== 4. 分镜表与代码是否一致 =="
$PY scripts/gen_shots.py --check

echo
echo "全部通过。"
