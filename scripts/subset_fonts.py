# -*- coding: utf-8 -*-
"""把字体裁成只含本片用到字的子集，产物进 assets/fonts/，随仓库一起走。

- 思源宋体 VF 先定到 wght=600 再裁（可变字体整体太大）。
- 毛笔字（马善政楷书，OFL）直接裁。
- 只裁一次，产物提交；verify 里只核对覆盖，不重新生成。
"""
import os, sys, glob
from fontTools import subset, ttLib
from fontTools.varLib import instancer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import story as S

FD = os.path.join(ROOT, "assets", "fonts")

# 本片会出现的所有字：字幕、题字、片尾说明、片名、副标
TEXTS = [l["text"] for l in S.LINES] + [m["text"] for m in S.MARKS]
TEXTS += [S.TITLE, S.SUBTITLE]
EXTRA = "，。、：；！？·—…（）《》0123456789ABCDFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz%"
CHARS = sorted(set("".join(TEXTS) + EXTRA))
print(f"用到 {len(CHARS)} 个字符")


def build(src, out, chars, instance=None):
    font = ttLib.TTFont(src)
    if instance:
        font = instancer.instantiateVariableFont(font, instance, inplace=True, updateFontNames=True)
    opts = subset.Options()
    opts.layout_features = ["*"]
    opts.drop_tables += ["DSIG"]
    opts.notdef_outline = True
    opts.recalc_bounds = True
    sub = subset.Subsetter(options=opts)
    sub.populate(text="".join(chars))
    sub.subset(font)
    font.save(out)
    print(f"  {os.path.basename(out)}  {os.path.getsize(out)/1024:.0f} KB")


if __name__ == "__main__":
    build(os.path.join(FD, "NotoSerifSC-VF.ttf"),
          os.path.join(FD, "NotoSerifSC-600.subset.ttf"), CHARS, {"wght": 600})
    build(os.path.join(FD, "MaShanZheng.ttf"),
          os.path.join(FD, "MaShanZheng.subset.ttf"), CHARS)
