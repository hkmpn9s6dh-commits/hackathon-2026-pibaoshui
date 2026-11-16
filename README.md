# 《皮包水》— 泰州首届 AI 漫剧创作大赛（社会组）参赛作品

一部 3 分 52 秒的水墨漫剧。孙女要卖掉爷爷开了四十年的早茶店，爷爷不拦，只让她在最后一个早晨，陪他把一碟干丝烫三遍。

- **正片**：`out/pi-baoshui.mp4`（1080×1920 / 24fps / H.264 / 见 `out/`）
- **放映页**：`site/index.html`（含 720p 小样 `site/clip.mp4`）
- **赛事**：「泰州有戏·剧创未来」泰州首届 AI 漫剧创作大赛 · 社会组 · 截止 2026-12-03
- **官方平台**：<https://tobyai.js118114.com/event/taizhou/#/>

## 一句话看懂工程

这部片子**没有一帧是手画的，也没有一句台词是现场念的**：图是文生图/图生图出的，声音是 TTS 与 numpy 合成的，纸纹、暗角、颗粒、字幕、朱砂印、镜头运动全是 `scripts/render.py` 逐帧算出来的。

全片的唯一真源是 **`story.py`**——图版提示词、30 个镜头、30 条台词、音效表、配音音色全在里面。改片子只改这一个文件，然后重跑。

## 跑起来

```bash
pip install -r requirements.txt        # numpy pillow fonttools edge-tts brotli
py -3 scripts/subset_fonts.py          # ① 裁字体子集（需要 assets/fonts 下的原始字体，见下）
py -3 scripts/build.py                 # ② 渲染 + 混音 + 合流 + 出网页小样（约 6 分钟）
bash verify.sh                         # ③ 闸 C 逐条验，退出码即结论
py -3 scripts/gen_shots.py             # ④ 由 story.py 重生成分镜表
```

只验不改：`bash verify.sh`。只跑某一项：`py -3 scripts/verify.py --faces` / `--fonts`。

**原始字体**（裁子集用，仓库里只放子集）：`assets/fonts/NotoSerifSC-VF.ttf`（思源宋体，OFL）与 `assets/fonts/MaShanZheng.ttf`（马善政毛笔楷书，OFL）。两者都可从 fontsource / Google Fonts 取；本机从 Windows 字体目录与 jsDelivr 拿的。

**图版**：`assets/plates/P01…P27.png` 已随仓库提交（27 张，共约 60 MB）。重新生成需要 `ImageGen` 工具，不在脚本里——提示词都在 `story.PLATES`，一条一条贴即可。

## 目录

```
story.py                唯一真源：图版提示词 / 镜头 / 台词 / 声音
SPEC.md                 闸 A：官方规则原文、范围、12 条验收条件
docs/01-STORY.md        剧本、全片台词表、史实与风物出处
docs/02-STYLE.md        风格、人物设定、人物一致性怎么验
docs/03-SHOTS.md        分镜表（脚本生成，勿手改）
docs/04-PROOF.md        闸 C 举证（命令与输出）
docs/05-SUBMISSION.md   交件单：报名、上传、材料清单
docs/06-AI-USAGE.md     官方要求的 AI 工具使用说明
scripts/render.py       逐帧渲染，直接喂 ffmpeg
scripts/audio.py        edge-tts 配音 + numpy 合成环境音与箫 + 混音
scripts/verify.py       闸 C 的判据
scripts/gen_shots.py    分镜表生成 / 反向核对
scripts/subset_fonts.py 字体子集
scripts/pull.py         把 ImageGen 的长文件名按序改成 Pxx.png
proof/                  举证产物（verify.log、faces/strip.png、faces/report.json）
```

## 三条设计决定

1. **9:16 竖屏 + 2:3 图版**。图版按 2:3 生成，取样窗按 9:16 在安全区内裁；镜头运动只做推拉与竖向微移——源图横向几乎没有余量，硬做横移就会拍到工具水印。
2. **四色板**。墨黑 / 宣纸米白 / 茶褐 / 朱砂红。朱红只给两处：孙女的围巾、灶口的火。这样评委在缩略图里也能一眼认人。
3. **人物一致靠三层**：图生图（设定图当 image1）+ 服装记号每次点名（灰毛巾 / 红围巾）+ 后期统一色链。判据见 `docs/02-STYLE.md` §三。

## 已知弱项

- 水墨笔触下的人脸在低分辨率下细节少，机械比对对角度敏感；`P19`（下逆光正脸）与 `P22`（双人同框）的「区分度」一项是靠证据条人工复核的，数值记在 `proof/faces/report.json`。
- 片子偏静，靠推移与声音推进；不是快切爽剧。
- 单条 400 MB 左右的母版是 CRF 18 + 颗粒的结果；平台限 2 GB，够用。

## 许可

代码 MIT。图版为本片专用（AI 生成 + 后期），随片提交。字体子集来自 OFL 字体，许可证随 `assets/fonts/LICENSE.md`。
