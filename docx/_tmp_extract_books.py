# -*- coding: utf-8 -*-
import pathlib
import re

out = pathlib.Path(r"D:\aicoding\mylib\docx\_tmp_extract")
out.mkdir(parents=True, exist_ok=True)

# ---- Book 1 ----
p1 = pathlib.Path(
    r"D:\aicoding\mylib\tools\book-extracts\run1\per_book\01_SOURCE_9787121529535_论文不是写出来的_AI科研思维训练与智能协同写作实战_DZ.docx.txt"
)
t1 = p1.read_text(encoding="utf-8")

# Prefer body occurrences: after "第 1 篇AI 写作范式" marker that starts body
body_anchor = t1.find("第 1 篇AI 写作范式")
if body_anchor < 0:
    body_anchor = t1.find("学术写作的核心不在于")
body = t1[body_anchor:] if body_anchor >= 0 else t1

starts = []
for m in re.finditer(r"^第\s*([1-9])\s*章\s*\n([^\n]+)", body, re.M):
    starts.append((int(m.group(1)), body_anchor + m.start(), m.group(2).strip()))

by = {}
for n, s, title in starts:
    # keep first body hit per chapter
    if n not in by:
        by[n] = (s, title)

print("book1 chapters:", sorted((k, v[1]) for k, v in by.items()))
keys = sorted(by)
for i, n in enumerate(keys):
    s, title = by[n]
    e = by[keys[i + 1]][0] if i + 1 < len(keys) else len(t1)
    chunk = t1[s:e]
    (out / f"b1_ch{n:02d}_head.txt").write_text(chunk[:9000], encoding="utf-8")
    (out / f"b1_ch{n:02d}_mid.txt").write_text(chunk[len(chunk) // 3 : len(chunk) // 3 + 6000], encoding="utf-8")
    print(n, "len", len(chunk), title)

for kw in [
    "资料投喂法",
    "要素组合法",
    "分步指令法",
    "多轮优化法",
    "倒金字塔",
    "黑箱",
    "概念拆离法",
    "层次分解法",
    "拆分组合法",
    "维度转换法",
    "负面启发法",
    "应用拓展法",
    "逻辑调优法",
    "标准 1",
    "标准 2",
    "标准 3",
    "文献综述的四条逻辑",
    "拆分任务管理",
]:
    i = t1.find(kw)
    print("b1 kw", kw, i)
    if i >= 0:
        safe = re.sub(r"[^\w\u4e00-\u9fff]+", "_", kw)[:40]
        (out / f"b1_kw_{safe}.txt").write_text(t1[max(0, i - 300) : i + 4500], encoding="utf-8")

# ---- Book 2 ----
p2 = pathlib.Path(
    r"D:\aicoding\mylib\tools\book-extracts\run1\per_book\05_SOURCE_如何用AI写论文_实操与规范_9787300343532.docx.txt"
)
t2 = p2.read_text(encoding="utf-8")

# body chapters often duplicated; take occurrences after page "2\n第一章" content
# Find longer chapter headings in body
markers = [
    ("01", "第一章\n用 AI 写论文"),
    ("02", "第二章\n正确使用 AI"),
    ("03", "第三章\nAIGC 工具全景"),
    ("04", "第四章\n文科生必学"),
    ("05", "第五章\nAI 学术伦理"),
    ("06", "第六章\nAI 写作全流程"),
]
# fallback searches
fallbacks = [
    ("01", "用 AI 写论文 ：六个关键问题"),
    ("02", "正确使用 AI 进行学术写作的前提要求"),
    ("03", "AIGC 工具全景化介绍"),
    ("04", "文科生必学的 AI 操作"),
    ("05", "AI 学术伦理"),
    ("06", "AI 写作全流程实战攻略"),
]

positions = []
for code, needle in fallbacks:
    # take last occurrence which tends to be body for this extract
    idxs = [m.start() for m in re.finditer(re.escape(needle), t2)]
    if not idxs:
        print("missing", needle)
        continue
    # prefer mid/late occurrences (skip TOC)
    pos = idxs[-1] if len(idxs) == 1 else idxs[1] if len(idxs) > 1 else idxs[0]
    # if first is TOC early, pick first after char 5000
    late = [i for i in idxs if i > 4500]
    pos = late[0] if late else idxs[-1]
    positions.append((code, pos, needle))
    print("b2", code, pos, needle, "all", idxs)

positions.sort(key=lambda x: x[1])
for i, (code, pos, needle) in enumerate(positions):
    e = positions[i + 1][1] if i + 1 < len(positions) else len(t2)
    chunk = t2[pos:e]
    (out / f"b2_ch{code}_head.txt").write_text(chunk[:10000], encoding="utf-8")
    (out / f"b2_ch{code}_mid.txt").write_text(chunk[len(chunk) // 3 : len(chunk) // 3 + 7000], encoding="utf-8")
    (out / f"b2_ch{code}_tail.txt").write_text(chunk[-7000:], encoding="utf-8")
    print("b2 wrote", code, "len", len(chunk))

for kw in [
    "自证合规",
    "混合式创新",
    "文责自负",
    "九大应用场景",
    "什么场合可以使用",
    "提示词工程",
    "文献综述",
    "开题报告",
    "去 AI",
    "AI 味",
    "润色",
    "披露",
    "引用",
]:
    i = t2.find(kw)
    print("b2 kw", kw, i)
    if i >= 0:
        safe = re.sub(r"[^\w\u4e00-\u9fff]+", "_", kw)[:40]
        (out / f"b2_kw_{safe}.txt").write_text(t2[max(0, i - 200) : i + 4000], encoding="utf-8")

print("DONE", out)
