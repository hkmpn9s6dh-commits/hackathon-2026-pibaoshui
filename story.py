# -*- coding: utf-8 -*-
"""《皮包水》唯一真源：图版、镜头、字幕、声音。

改片子只改这个文件；render.py / audio.py / verify.py 全部从这里读。
坐标一律用「图版内的比例」(0-1)，与图版实际像素无关。
"""
import os

ROOT = os.path.dirname(os.path.abspath(__file__))

W, H, FPS = 1080, 1920, 24          # 竖屏 9:16，1080×1920，24fps
AR = W / H

# 图版安全区：右下角是工具水印（约 x>0.89、y>0.945），永远不进画
SAFE = (0.015, 0.015, 0.888, 0.940)
# 9:16 取样窗宽（占图版宽度的比例）：由安全区高度决定
WIN_W = round((SAFE[3] - SAFE[1]) * (1024 / 1536) * (1536 / 1024) * AR, 4)
WIN_W = 0.776

TITLE = "皮包水"
SUBTITLE = "泰州 · 海陵 · 一早"

# ---------------------------------------------------------------- 图版
# key: 文件名（assets/plates/<key>.png）
# ref: 用哪张人物设定图做图生图（爷爷 / 孙女 / 双人）
STYLE = ("写意水墨淡彩，宣纸底，墨线细而干净，大面积留白，"
         "色板只用墨黑、宣纸米白、茶褐、朱砂红四色。写实比例，"
         "不要日式动漫大眼，不要塑料光泽，不要三维渲染感。"
         "画面里不要任何文字、招牌字、商标、水印、二维码。"
         "主体集中在画面中间 80%，四周留白边距。")

PLATES = {
    "P01": dict(ref=None, prompt=(
        "黎明前的江南小城老街全景：青砖墙、湿的青石板路、一条窄河与石桥，"
        "远处一座楼阁的剪影，两边低矮的店铺屋檐，两家店透出暖黄的灯泡光，"
        "蒸笼的白汽从门缝里冒出来。天是宣纸的灰白，没有太阳。空无一人的街道。")),
    "P02": dict(ref=None, prompt=(
        "一家老早茶店的木门脸，天没亮：两扇旧木门半开，门里透出暖黄灯光和白汽，"
        "门口摆着两张矮方桌和几条长凳，屋檐下挂着一只光秃秃的灯泡，"
        "门边的墙上有一块空白的木牌（不要写字）。地上是湿的青砖。")),
    "P03": dict(ref=None, prompt=(
        "早茶店后厨：一口大灶，灶上坐着一只大铁锅，白汽腾腾；旁边是长条木案板、"
        "几只白瓷碗、一摞竹蒸笼、一把菜刀、一块白豆腐干；头顶一盏裸灯泡，"
        "光只照亮案板那一小块，四周是墨一样的暗。")),
    "P04": dict(ref="ye", prompt=(
        "同一个人物设定：七十岁的老人半身像，站在后厨的暗处，低着头划火柴点灶，"
        "火柴的光从下方照着他的脸，额头上是汗，肩上的灰毛巾垂下来。"
        "背景全黑，只有灶口的微光和火柴的一点朱红。")),
    "P05": dict(ref="sun", prompt=(
        "同一个人物设定：二十八岁的女子半身像，站在店门口，背后是门外灰白的冷光和"
        "雾，脖子上一条鲜红围巾；她一手推着半开的木门，肩上挎着包，神情倔，"
        "脸上有夜路的寒气。门框内是暖黄的灯光，她身上是冷的。")),
    "P06": dict(ref=None, prompt=(
        "案板特写俯拍：一只牛皮纸信封平放在木案板边上，信封上空白无字，"
        "旁边是一块白豆腐干、一把菜刀、一只白瓷碗；灯光从左上角斜下来，"
        "信封的一角被压在一只粗瓷杯下面。画面里不要任何文字。")),
    "P07": dict(ref="ye", prompt=(
        "同一个人物设定：老人的一双手在案板上切干丝，特写只拍手、刀和豆腐干；"
        "手背青筋凸起、指节粗大、有一道旧疤；刀切下的干丝细如发丝，"
        "整整齐齐排在案板上。背景是深色的木案板和暗。")),
    "P08": dict(ref=None, prompt=(
        "特写：一只铜壶把滚水冲进白瓷碗里，碗里是细白的干丝；水柱是白的，"
        "蒸汽大片涌起来，把上半张画面糊成留白；桌面是旧木。逆光，只见水与汽。")),
    "P09": dict(ref=None, prompt=(
        "俯拍特写：一只白瓷浅碟，碟里是烫好的干丝堆成小丘，上面铺姜丝、"
        "几只小虾米，淋着深色酱油和一点麻油，光在酱油上发亮；碟子旁边"
        "是一只青花小碗。整张画只有碟心一点朱红（一粒虾米）。")),
    "P10": dict(ref="sun", prompt=(
        "同一个人物设定：二十八岁女子的一双手，用筷子夹起一绺干丝，干丝散开、"
        "掉回碗里；特写只拍手、筷子和碗，红围巾的一角在画面边缘；"
        "手的皮肤偏冷色，指甲剪得很短。")),
    "P11": dict(ref="ye", prompt=(
        "同一个人物设定：七十岁老人半身像，正面略侧，站在蒸汽后面看着镜头外"
        "（看着孙女），手里端着一只白瓷碗，眉头皱着，嘴角向下；"
        "蒸汽在他脸前飘过，只遮住半边脸。")),
    "P12": dict(ref="sun", prompt=(
        "同一个人物设定：二十八岁女子半身像，低着头站在案板前，红围巾垂在胸前，"
        "刘海遮住眼睛，一只手撑在案板边缘，另一只手垂着；背景是暗的后厨，"
        "只有侧后方一点灯光勾出她的轮廓。")),
    "P13": dict(ref=None, prompt=(
        "老早茶店的门口，从店内往门外看：一个六十多岁的老人掀开棉布门帘走进来，"
        "逆光只剩剪影，手里卷着一份报纸；门外的青石板路泛着天光，"
        "门内是暖黄的灯。人物只作剪影，看不清脸。")),
    "P14": dict(ref=None, prompt=(
        "俯拍一张旧方桌：桌上摆着两副碗筷，一副前面坐过人（碗里有剩汤、筷子架在碗上），"
        "另一副整整齐齐摆着、没有人坐、碗是干净的、筷子平放在碗边；"
        "桌面是磨得发亮的旧木，有一圈圈茶渍。光从左边窗子进来。")),
    "P15": dict(ref="ye", prompt=(
        "同一个人物设定：老人的一双手端着一只木托盘，托盘上是一壶茶、一只白瓷杯、"
        "一碟干丝；特写只拍手、托盘和托盘上的东西，背景是虚的店堂与雾气。")),
    "P16": dict(ref=None, prompt=(
        "厨房特写：一条鲫鱼放进热油锅里，油花四溅，鱼身微焦，锅边有一把铁铲；"
        "灶火从锅底舔上来，把鱼和油照成暖橙；背景是暗。")),
    "P17": dict(ref=None, prompt=(
        "厨房特写：铁铲在锅里把煎过的鱼捣碎，鱼肉碎开、骨头断开、油和碎肉混在一起，"
        "看起来狼藉；一只铜壶正要往里冲开水，蒸汽腾起。画面粗粝、不美化。")),
    "P18": dict(ref=None, prompt=(
        "厨房特写：锅里的汤在大火中翻滚，汤已经变成牛奶一样的乳白色，"
        "白汽大量涌起，几乎糊满画面上半部；锅边一只长柄勺。"
        "整张画只有白、墨和一点暖褐。")),
    "P19": dict(ref="sun", prompt=(
        "同一个人物设定：二十八岁女子半身像，站在灶前低头看锅，"
        "锅里的白光从下方照上来，把她的脸照得很亮，眼睛睁着，"
        "红围巾被光染得发亮；背景全暗，只有灶口的光。")),
    "P20": dict(ref=None, prompt=(
        "天亮时的老街：青石板路被晨光照亮，一个骑车人从远处骑过只留剪影，"
        "屋檐下挂着一排竹篮，河面反着灰白的光，空气里有雾；"
        "整张画是淡墨加一点暖色，留白很多。")),
    "P21": dict(ref="sun", prompt=(
        "同一个人物设定：二十八岁女子半身像，穿着白色围裙，双手端着一只木托盘，"
        "托盘上一碗面，汤汁微晃；她站在店堂里往门口走，表情紧张，"
        "红围巾塞在围裙领口里；背景是虚化的桌椅和晨光。")),
    "P22": dict(ref="both", prompt=(
        "同两个人物设定：后厨里，七十岁的老人把身上的深蓝围裙解下来，"
        "正往二十八岁女子的身上系；老人低着头，女子站着不动、双手垂在身侧。"
        "两人半身，面对面，靠得很近；背景是暗的灶台和一盏灯。")),
    "P23": dict(ref="ye", prompt=(
        "同一个人物设定：七十岁老人的背影，从小店的门口走进外面的晨光里，"
        "肩上还搭着那条灰毛巾，身形瘦，一只手扶着门框；"
        "门内是暗的，门外是白的，他的背影被光吃掉一半。")),
    "P24": dict(ref=None, prompt=(
        "空的早茶店堂：一张旧方桌上摆着两副碗筷，都没有人；"
        "晨光从门口斜进来，落在桌面上，尘埃在光里浮；"
        "四周的桌椅空着，墙上什么都没有（不要写字）。安静、干净、留白。")),
    "P25": dict(ref=None, prompt=(
        "城市出租屋的清晨：一扇小窗，窗外是密密麻麻的高楼和灰白的天；"
        "窗下一张很小的折叠桌，桌上一只电热壶、一只白瓷碗、一块豆腐干、一把菜刀；"
        "墙是白的，什么都没有。冷色，留白。")),
    "P26": dict(ref="sun", prompt=(
        "同一个人物设定：二十八岁女子的一双手，在出租屋的小桌上把滚水冲进白瓷碗，"
        "碗里是干丝；手腕上空空的，红围巾的一角垂在画面右上；"
        "蒸汽在冷色的窗光里上升。特写只拍手、碗和蒸汽。")),
    "P27": dict(ref=None, prompt=(
        "出租屋小桌的俯拍：一只白瓷碗里是烫好的干丝，旁边平放着两双筷子，"
        "桌面上没有别人；窗光斜进来，碗边有一点水痕。极简，留白，"
        "只有白、墨和一点茶褐。")),
}

# 人物设定图（图生图的参考）
CHAR = {
    "ye": "assets/char/ye.png",
    "sun": "assets/char/sun.png",
}


# ---------------------------------------------------------------- 镜头
# dur: 秒；cam: push_in / push_out / drift_up / drift_down / still
# z: 终止缩放（push_in 从 1.0 推到 z；push_out 从 z 拉回 1.0）
# cx/cy: 取样窗中心（图版比例）。9:16 窗宽 0.78，横移空间很小，靠缩放与竖向微移做运动。
SHOTS = [
    dict(id="S01", plate="P01", dur=7.0, cam="push_in", z=1.10, cy=0.46),
    dict(id="S02", plate="P02", dur=6.0, cam="drift_up", z=1.04, cy=0.42),
    dict(id="S03", plate="P03", dur=6.0, cam="push_in", z=1.08, cy=0.45),
    dict(id="S04", plate="P04", dur=7.0, cam="push_in", z=1.07, cy=0.32),
    dict(id="S05", plate="P05", dur=7.0, cam="push_in", z=1.08, cy=0.34),
    dict(id="S06", plate="P06", dur=8.0, cam="push_out", z=1.08, cy=0.50),
    dict(id="S07", plate="P07", dur=6.0, cam="drift_down", z=1.05, cy=0.44),
    dict(id="S08", plate="P08", dur=7.0, cam="push_in", z=1.09, cy=0.50),
    dict(id="S09", plate="P09", dur=10.0, cam="push_in", z=1.07, cy=0.50),
    dict(id="S10", plate="P10", dur=7.0, cam="push_in", z=1.09, cy=0.48),
    dict(id="S11", plate="P11", dur=7.0, cam="still", z=1.03, cy=0.32),
    dict(id="S12", plate="P12", dur=8.0, cam="push_in", z=1.07, cy=0.34),
    dict(id="S13", plate="P11", dur=8.0, cam="push_in", z=1.16, cy=0.28),
    dict(id="S14", plate="P13", dur=7.0, cam="drift_up", z=1.04, cy=0.48),
    dict(id="S15", plate="P14", dur=7.0, cam="push_in", z=1.10, cy=0.48),
    dict(id="S16", plate="P15", dur=8.0, cam="still", z=1.04, cy=0.50),
    dict(id="S17", plate="P14", dur=8.0, cam="push_in", z=1.18, cy=0.56),
    dict(id="S18", plate="P16", dur=7.0, cam="push_in", z=1.09, cy=0.50),
    dict(id="S19", plate="P17", dur=8.0, cam="still", z=1.05, cy=0.50),
    dict(id="S20", plate="P18", dur=9.0, cam="push_in", z=1.11, cy=0.52),
    dict(id="S21", plate="P19", dur=7.0, cam="push_in", z=1.09, cy=0.28),
    dict(id="S22", plate="P20", dur=7.0, cam="drift_up", z=1.05, cy=0.50),
    dict(id="S23", plate="P21", dur=8.0, cam="still", z=1.04, cy=0.38),
    dict(id="S24", plate="P22", dur=8.0, cam="push_in", z=1.10, cy=0.40),
    dict(id="S25", plate="P23", dur=8.0, cam="still", z=1.04, cy=0.44),
    dict(id="S26", plate="P24", dur=8.0, cam="push_in", z=1.07, cy=0.50),
    dict(id="S27", plate="P25", dur=9.0, cam="push_in", z=1.08, cy=0.46),
    dict(id="S28", plate="P26", dur=9.0, cam="push_in", z=1.08, cy=0.48),
    dict(id="S29", plate="P27", dur=8.0, cam="still", z=1.04, cy=0.50),
    dict(id="S30", plate=None, dur=12.0, cam="still", z=1.0, cy=0.5),
]

# 镜头起点（自动累加）
START = {}
_t = 0.0
for _s in SHOTS:
    START[_s["id"]] = _t
    _t += _s["dur"]
TOTAL = _t


def at(shot, offset=0.0):
    """镜头内偏移 → 绝对时间。"""
    return round(START[shot] + offset, 3)


# ---------------------------------------------------------------- 字幕与配音
# kind: d=对白（烧字幕 + 配音）  n=旁白（烧字幕 + 配音）  t=字卡
# t0/t1 是绝对秒。who: ye / sun / ke / nar
LINES = [
    dict(t0=at("S02", 0.8), t1=at("S02", 4.6), kind="n", who="nar",
         text="泰州，早上四点。"),
    dict(t0=at("S06", 3.2), t1=at("S06", 5.4), kind="d", who="ye", text="放桌上。"),
    dict(t0=at("S07", 1.2), t1=at("S07", 3.4), kind="d", who="ye", text="手洗了没有。"),
    dict(t0=at("S07", 3.6), t1=at("S07", 5.4), kind="d", who="sun", text="洗了。"),
    dict(t0=at("S08", 1.4), t1=at("S08", 3.6), kind="d", who="ye", text="再洗一遍。"),
    dict(t0=at("S09", 1.0), t1=at("S09", 4.6), kind="d", who="ye",
         text="一烫去豆腥，二烫定形，"),
    dict(t0=at("S09", 4.8), t1=at("S09", 9.7), kind="d", who="ye",
         text="三烫回热。少一烫，就是凉菜。"),
    dict(t0=at("S10", 2.0), t1=at("S10", 4.2), kind="d", who="sun", text="散了。"),
    dict(t0=at("S11", 1.4), t1=at("S11", 3.6), kind="d", who="ye", text="散了重来。"),
    dict(t0=at("S11", 4.0), t1=at("S11", 6.4), kind="d", who="ye", text="干丝不等人。"),
    dict(t0=at("S12", 1.6), t1=at("S12", 5.4), kind="d", who="sun",
         text="这店一年挣不了几个钱。"),
    dict(t0=at("S13", 1.6), t1=at("S13", 5.8), kind="d", who="ye",
         text="你算的是钱，我算的是人。"),
    dict(t0=at("S14", 3.0), t1=at("S14", 5.0), kind="d", who="ke", text="老样子。"),
    dict(t0=at("S15", 2.4), t1=at("S15", 4.6), kind="d", who="sun", text="这桌有人？"),
    dict(t0=at("S16", 1.2), t1=at("S16", 3.6), kind="d", who="ye", text="老周的。"),
    dict(t0=at("S16", 4.2), t1=at("S16", 6.6), kind="d", who="ye", text="三年没来了。"),
    dict(t0=at("S17", 1.4), t1=at("S17", 4.0), kind="d", who="sun",
         text="那你摆它做什么。"),
    dict(t0=at("S17", 4.4), t1=at("S17", 8.0), kind="d", who="ye",
         text="位子空着，人就没走远。"),
    dict(t0=at("S19", 2.6), t1=at("S19", 6.2), kind="d", who="ye",
         text="鱼要捣碎，汤才白。"),
    dict(t0=at("S20", 4.4), t1=at("S20", 6.2), kind="d", who="sun", text="人呢。"),
    dict(t0=at("S22", 1.2), t1=at("S22", 3.4), kind="n", who="nar", text="天亮了。"),
    dict(t0=at("S23", 1.6), t1=at("S23", 3.6), kind="d", who="ke", text="新来的？"),
    dict(t0=at("S23", 3.8), t1=at("S23", 5.8), kind="d", who="sun", text="我是他孙女。"),
    dict(t0=at("S23", 6.0), t1=at("S23", 9.2), kind="d", who="ke", text="怪不得。手一样。"),
    dict(t0=at("S24", 1.4), t1=at("S24", 4.0), kind="d", who="ye", text="店你卖。"),
    dict(t0=at("S24", 4.4), t1=at("S24", 6.8), kind="d", who="ye", text="手艺你带走。"),
    dict(t0=at("S25", 2.0), t1=at("S25", 6.4), kind="d", who="ye",
         text="一个人，也要吃好一顿早饭。"),
    dict(t0=at("S27", 1.6), t1=at("S27", 4.9), kind="n", who="nar", text="上海。第二年春天。"),
    dict(t0=at("S28", 1.4), t1=at("S28", 4.5), kind="n", who="nar",
         text="一烫去豆腥，二烫定形，"),
    dict(t0=at("S28", 4.8), t1=at("S28", 7.4), kind="n", who="nar", text="三烫回热。"),
]

# 拟声/题字（烧在画面里，不配音）
MARKS = [
    dict(shot="S03", t=1.2, kind="sfx", text="嗤", x=0.30, y=0.24, size=0.13, rot=-6),
    dict(shot="S08", t=0.8, kind="sfx", text="哗", x=0.70, y=0.28, size=0.15, rot=4),
    dict(shot="S30", t=0.6, kind="title", text="皮包水", x=0.50, y=0.42, size=0.17, rot=0),
    dict(shot="S30", t=2.4, kind="sub", text="泰 州 · 海 陵 · 一 早", x=0.50, y=0.545, size=0.032, rot=0),
    dict(shot="S30", t=5.0, kind="note", text="本片画面、配音、音乐均由生成式 AI 与程序合成", x=0.50, y=0.80, size=0.0205, rot=0),
    dict(shot="S30", t=5.0, kind="note2", text="全片无实拍素材", x=0.50, y=0.832, size=0.0205, rot=0),
]

# ---------------------------------------------------------------- 声音
VOICE = {
    "ye": dict(voice="zh-CN-YunxiNeural", rate="-12%", pitch="-8Hz"),
    "sun": dict(voice="zh-CN-XiaoyiNeural", rate="-8%", pitch="-2Hz"),
    "ke": dict(voice="zh-CN-YunjianNeural", rate="-10%", pitch="-4Hz"),
    "nar": dict(voice="zh-CN-YunyangNeural", rate="-14%", pitch="-6Hz"),
}

# 环境音/音效：[kind, 绝对起点, 时长, 参数]
SFX = [
    dict(kind="room", t=0.0, dur=TOTAL, gain=0.10),          # 底噪
    dict(kind="boil", t=0.0, dur=at("S04", 0.0) + 1.0, gain=0.16),   # 水沸（开场）
    dict(kind="match", t=at("S03", 1.4), dur=1.2, gain=0.20),
    dict(kind="door", t=at("S05", 0.3), dur=1.6, gain=0.20),
    dict(kind="pour", t=at("S08", 0.4), dur=2.4, gain=0.18),
    dict(kind="chop", t=at("S07", 0.2), dur=5.0, gain=0.10),
    dict(kind="shop", t=at("S14", 0.0), dur=at("S21", 8.0) - at("S14", 0.0), gain=0.09),
    dict(kind="fry", t=at("S18", 0.0), dur=at("S20", 9.0) - at("S18", 0.0), gain=0.16),
    dict(kind="pour", t=at("S20", 1.0), dur=2.0, gain=0.12),
    dict(kind="street", t=at("S22", 0.0), dur=at("S26", 8.0) - at("S22", 0.0), gain=0.10),
    dict(kind="city", t=at("S27", 0.0), dur=at("S29", 8.0) - at("S27", 0.0), gain=0.09),
    dict(kind="pour", t=at("S28", 1.0), dur=2.2, gain=0.14),
]

# 音乐：箫/口琴式单旋律，全片一条，稀疏
MUSIC = dict(gain=0.11)
