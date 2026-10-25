#!/usr/bin/env python3
"""智慧芽（PatSnap）AI 查新客户端——方案二：会把技术方案全文发给智慧芽。

与 patsnap.py（方案一，只检索、不外发方案）分开。每个子命令都必须带 --authorized，
表示用户已针对这份具体内容明确授权外发；不带则拒绝调用。

子命令（输入一律从 --input-file 读 UTF-8 文本，不在命令行里写方案；证据 JSON 存 --out）：
  ai30   --input-file F [--effect-file F2] [--limit 20]   AI30 相似专利检索与特征比对（同步）
  ai29   --input-file F [--effect-file F2] [--limit 20]   AI29 技术构思验证：建任务→轮询→取比对结果
  m002   --input-file F [--lang cn]                       M002 查新智能体：建任务→轮询结果
  ai35   --input-file F [--lang cn] [--title T]           AI35 查新 12 步：自动确认方案摘要、特征、检索要素，
                                                          取对比文献与特征比对，生成并下载报告链接
  poll   --api m002|ai29|ai35 --task-id ID                已有任务继续轮询

红线：结果属模型意见（R_self 同级）。其给出的文献号须用 patsnap.py fetch 取原文核验后才可写入
01_现有技术检索报告.md；"新颖性/创造性"结论不等于授权概率。
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from patsnap import call, save  # noqa: E402

POLL_SEC = 20


def _data(rec: dict) -> dict:
    d = rec["response"].get("data")
    return d if isinstance(d, dict) else {"_data": d}


def _step(path: str, body: dict, out: Path | None, stem: str) -> dict:
    rec = call("POST", path, body)
    save(rec, out, stem)
    if not rec["ok"]:
        r = rec["response"]
        raise SystemExit(f"[{path}] 失败 http={rec['http']} code={r.get('error_code')} msg={r.get('error_msg')}")
    return rec


def _poll(path: str, body: dict, out: Path | None, stem: str, done, max_min: float) -> dict:
    t_end = time.time() + max_min * 60
    while True:
        rec = call("POST", path, body)
        if not rec["ok"]:
            save(rec, out, stem)
            r = rec["response"]
            raise SystemExit(f"[{path}] 失败 code={r.get('error_code')} msg={r.get('error_msg')}")
        if done(_data(rec)):
            save(rec, out, stem)
            return rec
        if time.time() > t_end:
            save(rec, out, stem + "_timeout")
            raise SystemExit(f"[{path}] 轮询超时（{max_min} 分钟），task 仍在运行，可用 poll 子命令继续")
        print(f"[poll] {path} 未完成，{POLL_SEC}s 后重试", file=sys.stderr)
        time.sleep(POLL_SEC)


def _finished(d: dict) -> bool:
    st = str(d.get("status") or d.get("task_status") or d.get("state") or "").lower()
    if st in ("success", "succeed", "completed", "complete", "finished", "done", "2"):
        return True
    if st in ("failed", "fail", "error"):
        raise SystemExit(f"任务失败：{json.dumps(d, ensure_ascii=False)[:500]}")
    return False


def run_ai30(a):
    body = {"tech_means": a.text, "limit": a.limit}
    if a.effect:
        body["tech_effect"] = a.effect
    return _step("/search/patent/similar-patent-comparison", body, a.out, "AI30")


def run_ai29(a):
    body = {"tech_means": a.text, "limit": a.limit}
    if a.effect:
        body["tech_effect"] = a.effect
    rec = _step("/search/patent/idea-validation/task/create", body, a.out, "AI29-1")
    job = _data(rec).get("job_id")
    return poll_ai29(a, job)


def poll_ai29(a, job):
    print(f"[AI29] job_id={job}", file=sys.stderr)
    return _poll("/search/patent/idea-validation/similar-patent-comparison", {"job_id": job}, a.out, "AI29-2",
                 lambda d: bool(d.get("patents") or d.get("data") or d.get("result") or _finished(d)), a.max_min)


def run_m002(a):
    rec = _step("/ai/novelty-check-agent-creation", {"text": a.text, "lang": a.lang}, a.out, "M002-1")
    return poll_m002(a, _data(rec).get("task_id"))


def poll_m002(a, tid):
    print(f"[M002] task_id={tid}", file=sys.stderr)
    return _poll("/ai/novelty-check-agent-query", {"task_id": tid}, a.out, "M002-2", _finished, a.max_min)


def run_ai35(a):
    body = {"input": a.text, "lang": a.lang}
    rec = _step("/ai/novelty-search/submit", body, a.out, "AI35-01_submit")
    tid = _data(rec).get("task_id")
    print(f"[AI35] task_id={tid}", file=sys.stderr)
    return poll_ai35(a, tid)


def poll_ai35(a, tid):
    b = {"task_id": tid}
    # 2 方案摘要：等生成后原样确认（不改写，避免把本机判断注入外部结果）
    r = _poll("/ai/novelty-search/tech-solution/get", b, a.out, "AI35-02_solution",
              lambda d: bool(d.get("tech_solution")), a.max_min)
    _step("/ai/novelty-search/tech-solution/update", {**b, "tech_solution": _data(r)["tech_solution"]},
          a.out, "AI35-03_solution_confirm")
    r = _poll("/ai/novelty-search/feature/extract", b, a.out, "AI35-04_features",
              lambda d: bool(d.get("tech_features")), a.max_min)
    _step("/ai/novelty-search/feature/confirm", {**b, "tech_features": _data(r)["tech_features"]},
          a.out, "AI35-05_features_confirm")
    r = _poll("/ai/novelty-search/retrieval/elements", b, a.out, "AI35-06_elements",
              lambda d: bool(d.get("elements")), a.max_min)
    _step("/ai/novelty-search/agent-search", {**b, "elements": _data(r)["elements"]}, a.out, "AI35-07_search")
    r = _poll("/ai/novelty-search/agent-result", b, a.out, "AI35-08_result", _finished, a.max_min)
    final = _data(r).get("final_result") or _data(r).get("feature_comparison")
    if final:
        _step("/ai/novelty-search/feature/comparison/confirm", {**b, "final_result": final},
              a.out, "AI35-09_comparison_confirm")
    _step("/ai/novelty-search/export", {**b, "title": a.title}, a.out, "AI35-10_export")
    return _poll("/ai/novelty-search/report/get", b, a.out, "AI35-11_report",
                 lambda d: bool(d.get("url") or d.get("report_url") or d.get("download_url")), a.max_min)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("ai30", "ai29", "m002", "ai35", "poll"):
        p = sub.add_parser(name)
        p.add_argument("--authorized", action="store_true", help="用户已明确授权外发这份技术方案全文")
        p.add_argument("--out", type=Path, required=True, help="证据 JSON 目录")
        p.add_argument("--max-min", type=float, default=30, help="单步轮询上限（分钟）")
        if name == "poll":
            p.add_argument("--api", choices=("m002", "ai29", "ai35"), required=True)
            p.add_argument("--task-id", required=True)
        else:
            p.add_argument("--input-file", type=Path, required=True)
        if name in ("ai30", "ai29"):
            p.add_argument("--effect-file", type=Path)
            p.add_argument("--limit", type=int, default=20)
        if name in ("m002", "ai35", "poll"):
            p.add_argument("--lang", default="cn")
        if name in ("ai35", "poll"):
            p.add_argument("--title", default="查新报告")
    a = ap.parse_args()
    if not a.authorized:
        raise SystemExit("拒绝：AI 查新会把技术方案全文发给智慧芽，须用户明确授权后加 --authorized")
    if a.cmd == "poll":
        rec = {"m002": poll_m002, "ai29": poll_ai29, "ai35": poll_ai35}[a.api](a, a.task_id)
    else:
        a.text = a.input_file.read_text(encoding="utf-8").strip()
        a.effect = a.effect_file.read_text(encoding="utf-8").strip() if getattr(a, "effect_file", None) else None
        rec = {"ai30": run_ai30, "ai29": run_ai29, "m002": run_m002, "ai35": run_ai35}[a.cmd](a)
    print(json.dumps(rec["response"], ensure_ascii=False)[:4000])


if __name__ == "__main__":
    main()
