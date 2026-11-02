# -*- coding: utf-8 -*-
import pathlib
import re

out = pathlib.Path(r"D:\aicoding\mylib\docx\_tmp_extract")
t1 = pathlib.Path(
    r"D:\aicoding\mylib\tools\book-extracts\run1\per_book\01_SOURCE_9787121529535_论文不是写出来的_AI科研思维训练与智能协同写作实战_DZ.docx.txt"
).read_text(encoding="utf-8")
t2 = pathlib.Path(
    r"D:\aicoding\mylib\tools\book-extracts\run1\per_book\05_SOURCE_如何用AI写论文_实操与规范_9787300343532.docx.txt"
).read_text(encoding="utf-8")

# Book1: extract keyword from BODY only (after part1 body)
body1 = t1.find("学术写作的核心不在于")
assert body1 > 0
B1 = t1[body1:]

def save_kw(prefix, text, kw, n=5000):
    i = text.find(kw)
    print(prefix, kw, i)
    if i < 0:
        return
    safe = re.sub(r"[^\w\u4e00-\u9fff]+", "_", kw)[:50]
    (out / f"{prefix}_{safe}.txt").write_text(text[max(0, i - 200) : i + n], encoding="utf-8")

for kw in [
    "资料投喂法",
    "要素组合法",
    "分步指令法",
    "多轮优化法",
    "标准 1：遵循规范性",
    "标准 2：适切学科性",
    "标准 3：符合学术性",
    "概念拆离法",
    "层次分解法",
    "拆分组合法",
    "维度转换法",
    "负面启发法",
    "应用拓展法",
    "逻辑调优法",
    "寻找三类矛盾",
    "文献综述的四条逻辑路线",
    "防止“黑箱”写作",
    "拆分任务管理",
    "从兴趣到题目",
    "事前引导",
    "事后校验",
    "学习知识",
    "问题导向",
    "批判创新",
]:
    save_kw("b1b", B1, kw, 5500)

# Book2 body chapters by late unique markers
b2_map = [
    ("01", 4920),  # approximate; refine below
]
# find body starts
for label, needle in [
    ("01", "什么是 AIGC?"),
    ("02", "学术论文核心要求在 AI 时代的延续"),
    ("03", "DeepSeek 介绍"),
    ("04", "什么是提示词以及提示词工程"),
    ("05", "什么场合可以使用 AI 、什么场合不可以"),
    ("06", "撰写文献综述"),
]:
    idxs = [m.start() for m in re.finditer(re.escape(needle), t2)]
    late = [i for i in idxs if i > 8000] or idxs
    print("b2", label, late[:3], "alln", len(idxs))
    start = late[0]
    # expand back a bit
    start2 = t2.rfind("\n", max(0, start - 400), start)
    chunk_start = start2 if start2 > 0 else start
    # end = next late marker
    b2_map.append((label, chunk_start))

# rebuild clean
pairs = []
for label, needle in [
    ("01", "什么是 AIGC?"),
    ("02", "学术论文核心要求在 AI 时代的延续"),
    ("03", "DeepSeek 介绍"),
    ("04", "什么是提示词以及提示词工程"),
    ("05", "什么场合可以使用 AI 、什么场合不可以"),
    ("06", "撰写文献综述"),
]:
    idxs = [m.start() for m in re.finditer(re.escape(needle), t2)]
    late = [i for i in idxs if i > 8000] or idxs
    pairs.append((label, late[0], needle))
pairs.sort(key=lambda x: x[1])
for i, (label, start, needle) in enumerate(pairs):
    e = pairs[i + 1][1] if i + 1 < len(pairs) else len(t2)
    # rewind to chapter title if possible
    head = t2.rfind("第", max(0, start - 1200), start)
    s = head if head >= 0 else max(0, start - 200)
    chunk = t2[s:e]
    (out / f"b2b_ch{label}.txt").write_text(chunk, encoding="utf-8")
    print("wrote b2b", label, "from", s, "len", len(chunk), "head", chunk[:60].replace("\n", " "))

for kw in [
    "自证合规",
    "混合式创新",
    "文责自负",
    "九大应用场景",
    "技术敬畏",
    "规则敬畏",
    "AI 味",
    "恰当说明",
    "保留材料",
    "交叉验证",
    "提示词工程",
    "开题报告",
    "文献综述",
    "润色",
    "抄袭",
]:
    # prefer late hits
    idxs = [m.start() for m in re.finditer(re.escape(kw), t2)]
    late = [i for i in idxs if i > 8000] or idxs
    if not late:
        print("miss", kw)
        continue
    i = late[0]
    safe = re.sub(r"[^\w\u4e00-\u9fff]+", "_", kw)[:40]
    (out / f"b2b_{safe}.txt").write_text(t2[max(0, i - 300) : i + 5000], encoding="utf-8")
    print("b2b kw", kw, i)

print("OK")
