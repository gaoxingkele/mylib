# -*- coding: utf-8 -*-
import pathlib
import re

out = pathlib.Path(r"D:\aicoding\mylib\docx\_tmp_extract")
t2 = pathlib.Path(
    r"D:\aicoding\mylib\tools\book-extracts\run1\per_book\05_SOURCE_如何用AI写论文_实操与规范_9787300343532.docx.txt"
).read_text(encoding="utf-8")

# Body chapter 1: look for "什么是 AIGC" after TOC
i = t2.find("什么是 AIGC")
print("AIGC at", i)
# rewind to nearest 第一章
prev = t2.rfind("第一章", 0, i)
print("第一章 before", prev)
print(repr(t2[prev : prev + 200]))

# Better body map by section titles unique in body
needles = [
    ("01", "一 、什么是 AIGC"),
    ("02", "一 、创新、严谨、 负责与合规"),
    ("03", "一 、DeepSeek 介绍"),
    ("04", "一 、AIGC 基础：什么是提示词"),
    ("05", "一 、什么场合可以使用 AI"),
    ("06", "一 、撰写文献综述"),
]
pos = []
for code, n in needles:
    idxs = [m.start() for m in re.finditer(re.escape(n), t2)]
    late = [x for x in idxs if x > 4000] or idxs
    p = late[0]
    pos.append((code, p, n))
    print(code, p, idxs)

pos.sort(key=lambda x: x[1])
# extend start of ch01 back to chapter title
starts = []
for i, (code, p, n) in enumerate(pos):
    # find chapter heading within 800 chars before
    head = t2.rfind("第", max(0, p - 800), p)
    start = head if head >= 0 else p
    starts.append((code, start, n))
    print("start", code, start)

for i, (code, start, n) in enumerate(starts):
    e = starts[i + 1][1] if i + 1 < len(starts) else len(t2)
    chunk = t2[start:e]
    (out / f"b2_ch{code}_fullhead.txt").write_text(chunk[:12000], encoding="utf-8")
    (out / f"b2_ch{code}_fullmid.txt").write_text(
        chunk[len(chunk) // 3 : len(chunk) // 3 + 8000], encoding="utf-8"
    )
    (out / f"b2_ch{code}_fulltail.txt").write_text(chunk[-8000:], encoding="utf-8")
    print("wrote", code, len(chunk))

# AI味 / 去痕迹 related
for kw in ["AI 味", "AI味", "机器味", "套话", "同质化", "人工校验", "交叉验证", "提示词"]:
    idxs = [m.start() for m in re.finditer(re.escape(kw), t2)]
    print(kw, idxs[:8], "count", len(idxs))
    if idxs:
        i = idxs[min(2, len(idxs) - 1)]
        safe = re.sub(r"[^\w\u4e00-\u9fff]+", "_", kw)
        (out / f"b2_extra_{safe}.txt").write_text(t2[max(0, i - 400) : i + 3500], encoding="utf-8")
