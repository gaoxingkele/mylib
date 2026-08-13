#!/usr/bin/env python3
"""powergrid_skills 任务路由 CLI。

用法:
    python router.py "给 references.bib 做引用核查"
    python router.py --list
    python router.py --json "全文一致性和 LaTeX 检查"

纯 stdlib。路由表见同目录 router.yaml（受控子集，由本文件内置迷你解析器读取）。
打分规则：任务描述中每命中一个关键词计 1 分，命中越多排名越前；无命中时打印全部类别。
"""
import argparse
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROUTER_YAML = os.path.join(BASE, "router.yaml")


def _strip_quotes(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def parse_router_yaml(path):
    """解析 router.yaml 的受控子集：

    顶层标量 ``key: value``、``categories:`` 列表（``- id: x`` 开头），
    类别内标量 ``name:`` / ``note:`` 与列表 ``match:`` / ``components:``。
    仅支持整行注释（# 开头），不支持行内注释。
    """
    doc = {"default_note": "", "categories": []}
    current = None       # 当前类别 dict
    current_list = None  # 当前正在填充的列表键名
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n")
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            indent = len(line) - len(line.lstrip())
            if indent == 0:
                # 顶层：default_note: "..." 或 categories:
                key, _, value = stripped.partition(":")
                key = key.strip()
                if key == "categories":
                    current = None
                    current_list = None
                elif value.strip():
                    doc[key] = _strip_quotes(value)
            elif indent == 2 and stripped.startswith("- "):
                # 新类别：- id: xxx
                current = {}
                doc["categories"].append(current)
                current_list = None
                key, _, value = stripped[2:].partition(":")
                current[key.strip()] = _strip_quotes(value)
            elif current is not None and indent == 4:
                key, _, value = stripped.partition(":")
                key = key.strip()
                if value.strip():
                    current[key] = _strip_quotes(value)
                    current_list = None
                else:
                    current[key] = []
                    current_list = key
            elif current is not None and indent >= 6 and stripped.startswith("- "):
                if current_list:
                    current[current_list].append(_strip_quotes(stripped[2:]))
    return doc


def score_category(category, text):
    """返回 (score, [命中的关键词])。大小写不敏感子串匹配。"""
    text_lower = text.lower()
    hits = [kw for kw in category.get("match", []) if kw.lower() in text_lower]
    return len(hits), hits


def resolve_components(category):
    """把相对路径转成绝对路径，并标注文件是否存在。"""
    out = []
    for rel in category.get("components", []):
        abspath = os.path.normpath(os.path.join(BASE, rel))
        out.append({"path": abspath, "exists": os.path.exists(abspath)})
    return out


def route(doc, text):
    scored = []
    for order, cat in enumerate(doc["categories"]):
        score, hits = score_category(cat, text)
        if score > 0:
            scored.append((score, -order, cat, hits))
    scored.sort(reverse=True)  # 分数降序；同分保持 yaml 原顺序
    return [(cat, score, hits) for score, _, cat, hits in scored]


def print_category(cat, score, hits, matched):
    header = "[{}] {}".format(cat.get("id", "?"), cat.get("name", ""))
    if matched:
        header += "  (score={}, 命中: {})".format(score, "、".join(hits))
    print(header)
    for comp in resolve_components(cat):
        mark = "" if comp["exists"] else "  [缺失!]"
        print("    {}{}".format(comp["path"], mark))
    note = cat.get("note", "")
    if note:
        print("    note: " + note)
    print()


def main():
    # 统一 UTF-8 输出：Windows 管道默认 GBK 会导致中文乱码（agent/IDE 消费场景）
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(
        description="powergrid_skills 任务路由：按任务描述输出应加载的组件清单")
    ap.add_argument("task", nargs="?", help="任务描述（中英文均可）")
    ap.add_argument("--list", action="store_true", help="列出全部任务类别")
    ap.add_argument("--json", action="store_true", help="机器可读 JSON 输出")
    args = ap.parse_args()

    doc = parse_router_yaml(ROUTER_YAML)

    if args.list:
        if args.json:
            print(json.dumps(
                [{"id": c.get("id"), "name": c.get("name"), "match": c.get("match", [])}
                 for c in doc["categories"]],
                ensure_ascii=False, indent=2))
        else:
            print("全部任务类别（共 {} 个）：\n".format(len(doc["categories"])))
            for c in doc["categories"]:
                print("  {:<24s} {}".format(c.get("id", "?"), c.get("name", "")))
            print("\n默认提示: " + doc["default_note"])
        return 0

    if not args.task:
        ap.error("需要提供任务描述，或使用 --list")

    results = route(doc, args.task)

    if args.json:
        payload = {
            "task": args.task,
            "matched": bool(results),
            "default_note": doc["default_note"],
            "categories": [
                {
                    "id": cat.get("id"),
                    "name": cat.get("name"),
                    "score": score,
                    "hits": hits,
                    "components": resolve_components(cat),
                    "note": cat.get("note", ""),
                }
                for cat, score, hits in results
            ] if results else [
                {
                    "id": cat.get("id"),
                    "name": cat.get("name"),
                    "score": 0,
                    "hits": [],
                    "components": resolve_components(cat),
                    "note": cat.get("note", ""),
                }
                for cat in doc["categories"]
            ],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if results:
        print("任务: {}\n匹配到 {} 个类别（按命中数排序）：\n".format(args.task, len(results)))
        for cat, score, hits in results:
            print_category(cat, score, hits, matched=True)
    else:
        print("任务: {}\n未命中任何关键词，列出全部类别：\n".format(args.task))
        for cat in doc["categories"]:
            print_category(cat, 0, [], matched=False)

    print("默认提示: " + doc["default_note"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
