#!/usr/bin/env python3
# verify_probes.py — ch09-12 自查探针
import re, sys, pathlib

BASE = pathlib.Path(__file__).parent / "chapters"
BANNED = ["某种", "微微", "不由自主", "仿佛", "一丝", "不易察觉"]
FILES = [f"ch{i:02d}.md" for i in range(1, 27)]

# 每章字数参考带（ch21 4400-4700；ch22/23 缓冲至 6000；ch24 允许 7000-8000；ch25 4400-5000；ch26 3000-4000）
BAND = {"ch21.md": (4300, 4800), "ch22.md": (4300, 6100), "ch23.md": (4300, 6100), "ch24.md": (6800, 8200), "ch25.md": (4400, 5000), "ch26.md": (3000, 4000)}
DEFAULT_BAND = (4300, 4800)

REQUIRED = {
    "ch17.md": ["## 第十七章 嘲意", "〔顾问工作记录 · 16〕", "市场为叙事付的钱，总是多于为事实付的", "标记点", "连环杀手为何停手"],
    "ch18.md": ["## 第十八章 精化", "〔顾问工作记录 · 17〕", "剔除佐藤：残差超限", "剔除", "八月六日", "列席", "八月七日", "候补", "同余", "佐藤実"],
    "ch19.md": ["## 第十九章 双重", "〔顾问工作记录 · 18〕", "覆盖率达预期", "候补", "佐藤", "签到表"],
    "ch20.md": ["## 第二十章 样本外", "〔顾问工作记录 · 19〕", "样本外事件", "佐藤実", "钱包", "不到两天", "八月八日"],
    "ch21.md": ["## 第二十一章 帮凶", "〔顾问工作记录 · 20〕", "钱包", "安全", "佐藤"],
    "ch22.md": ["## 第二十二章 策展", "〔顾问工作记录 · 21〕", "他开始重算了", "548", "549", "策展", "下个月开始，我不做了。对不起，也谢谢你。", "镜像"],
    "ch23.md": ["## 第二十三章 重演", "〔顾问工作记录 · 22〕", "我等这一步，比等任何一笔成交都久", "聘任记录", "排除", "548"],
    "ch24.md": ["## 第二十四章 自白·上", "〔顾问工作记录 · 23〕", "星座不是天空的事实，是观察者的事实", "持仓", "镜像", "列席", "本案例异常洁净", "他的拟合速率高于预期", "已更正"],
    "ch25.md": ["## 第二十五章 自白·下", "〔顾问工作记录 · 24〕", "世界不惩罚错误，只惩罚运气差", "我只是把这句话做成了实验", "胶带", "雨衣", "钱包", "举手之劳", "三浦太一", "佐藤実", "门罗", "酒会"],
    "ch26.md": ["## 第二十六章 不拟合", "〔顾问工作记录 · 25〕", "截图", "数据区为空", "无批注文字", "四月九日", "这个案子太干净了"],
}

# 批注内禁用内部编号
AN_FORBIDDEN = ["E1", "E2", "E3", "E4", "E5"]

# AN-20 剂量纪律：ch21 不得出现「已更正/548/549」
CH21_FORBIDDEN = ["已更正", "548", "549"]
# 「已更正」全书白名单：ch03×2 + ch24×1，恰 3 处
YIGENG_WHITELIST = {"ch03.md": 2, "ch24.md": 1}

fail = 0
for fn in FILES:
    text = (BASE / fn).read_text(encoding="utf-8")
    errs = []
    for w in BANNED:
        if w in text:
            errs.append(f"禁用词: {w} ×{text.count(w)}")
    dashes = text.count("——")
    if dashes > 3:
        errs.append(f"破折号 {dashes} > 3")
    for r in REQUIRED.get(fn, []):
        if r not in text:
            errs.append(f"缺必需串: {r}")
    if fn == "ch21.md":
        for w in CH21_FORBIDDEN:
            if w in text:
                errs.append(f"ch21 违规命中(AN-20 剂量纪律): {w} ×{text.count(w)}")
    c = text.count("已更正")
    if fn in YIGENG_WHITELIST:
        if c != YIGENG_WHITELIST[fn]:
            errs.append(f"「已更正」{fn} 应为 {YIGENG_WHITELIST[fn]} 处，实际 {c}")
    elif c:
        errs.append(f"「已更正」白名单外出现: {fn} ×{c}")
    # 引号配对（中文弯引号与直引号分开统计）
    for q in ['"', '"', "「"]:
        pairs = {'"': ('"', '"'), '"': ('"', '"'), "「": ("「", "」")}
        o, c = pairs[q]
        if text.count(o) != text.count(c):
            errs.append(f"引号不配对 {o}{c}: {text.count(o)}/{text.count(c)}")
    # 批注区块内部编号检查
    m = re.search(r"〔顾问工作记录[\s\S]*$", text)
    if m:
        for f in AN_FORBIDDEN:
            if re.search(rf"\b{f}\b", m.group(0)):
                errs.append(f"批注内出现内部编号 {f}")
    n = len(re.sub(r"\s", "", text))
    print(f"{fn}: {n} 字, 破折号 {dashes}")
    if fn in BAND:
        lo, hi = BAND[fn]
        if not (lo <= n <= hi):
            errs.append(f"字数 {n} 超出 {lo}-{hi} 参考带")
    if errs:
        fail = 1
        for e in errs:
            print("  [FAIL]", e)
    else:
        print("  [PASS]")
sys.exit(fail)
