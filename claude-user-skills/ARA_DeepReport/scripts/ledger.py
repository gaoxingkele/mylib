"""autodeepreport — 证据账本 (claims ledger)

把研究报告的"已核验事实"持久化为结构化账本（ARA 的 evidence+logic 层 + provenance），
是"版本升级式报告"实现持续学习（不灾难性遗忘）的记忆核心。

每条 claim 字段：
  id          稳定标识（kebab-case），跨版本不变 —— 升级时据此 replay/比对
  dimension   所属维度/章节（如 公共外交 / USAID / 工作效果）
  text        断言主题（"VOA 播出语种数"）
  value       取值/结论（"约48种"）
  confidence  high|medium|low      —— EWC 式重要度：high+多源 = 受保护、升级时不重研
  status      confirmed|revised|disputed|refuted   —— 死胡同(refuted)也保留(ARA trace)
  volatility  static|time-sensitive —— time-sensitive 触发 staleness 复检 (Domain-IL)
  sources     [url, ...]           —— 证据相关性：每条断言须挂可核查出处
  provenance  ai-verified|user|ai-suggested|user-revised
  last_verified  YYYY-MM-DD
  note        修正说明 / 与底稿差异

用法：
  python ledger.py init     <ledger.json>
  python ledger.py add      <ledger.json> --id ID --dim D --text T --value V \
                            [--confidence high] [--status confirmed] [--volatility static] \
                            [--sources url1,url2] [--provenance ai-verified] \
                            [--last-verified 2026-06-10] [--note "..."]
  python ledger.py bulk     <ledger.json> <claims.json>     # 批量 upsert（list[claim]）
  python ledger.py stats    <ledger.json>
  python ledger.py stale    <ledger.json> [--as-of 2026-06-10] [--max-age-days 120]
  python ledger.py protected <ledger.json> [--min-sources 2]   # 受保护(免重研)的高置信断言
  python ledger.py diff     <old.json> <new.json>          # 升级变更：新增/修订/翻案/保留
"""
import argparse
import json
import sys
import io
from datetime import date, datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

FIELDS = ["id", "dimension", "text", "value", "confidence", "status",
          "volatility", "sources", "provenance", "last_verified", "note"]
CONF = {"high", "medium", "low"}
STATUS = {"confirmed", "revised", "disputed", "refuted"}
VOL = {"static", "time-sensitive"}


def load(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return {"version": "0.0.0", "updated": "", "claims": []}
    data.setdefault("claims", [])
    return data


def save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _index(data):
    return {c["id"]: c for c in data["claims"]}


def cmd_init(a):
    save(a.ledger, {"version": "0.0.0", "updated": str(date.today()), "claims": []})
    print(f"已创建空账本: {a.ledger}")


def _upsert(data, claim):
    idx = _index(data)
    cid = claim["id"]
    if cid in idx:
        idx[cid].update({k: v for k, v in claim.items() if v is not None})
    else:
        data["claims"].append(claim)


def cmd_add(a):
    data = load(a.ledger)
    claim = {
        "id": a.id, "dimension": a.dim, "text": a.text, "value": a.value,
        "confidence": a.confidence, "status": a.status, "volatility": a.volatility,
        "sources": [s.strip() for s in a.sources.split(",") if s.strip()] if a.sources else [],
        "provenance": a.provenance,
        "last_verified": a.last_verified or str(date.today()),
        "note": a.note or "",
    }
    _validate(claim)
    _upsert(data, claim)
    data["updated"] = str(date.today())
    save(a.ledger, data)
    print(f"已写入断言 [{a.id}] ({a.status}/{a.confidence})")


def cmd_bulk(a):
    data = load(a.ledger)
    with open(a.claims, "r", encoding="utf-8") as f:
        items = json.load(f)
    n = 0
    for c in items:
        c.setdefault("sources", [])
        c.setdefault("last_verified", str(date.today()))
        c.setdefault("note", "")
        _coerce(c)
        _validate(c)
        _upsert(data, c)
        n += 1
    data["updated"] = str(date.today())
    save(a.ledger, data)
    print(f"批量 upsert {n} 条断言，账本现有 {len(data['claims'])} 条")


def _coerce(c):
    """容错归一化 agent 产出的常见枚举偏差(数值置信度/中文状态/stable 等)。"""
    cf = c.get("confidence")
    if cf is not None:
        try:
            v = float(cf); c["confidence"] = "high" if v >= 0.9 else "medium" if v >= 0.78 else "low"
        except (ValueError, TypeError):
            if cf not in CONF:
                c["confidence"] = "medium"
    sm = {"确证": "confirmed", "指称": "disputed", "修正": "revised", "否证": "refuted"}
    if c.get("status") in sm:
        c["status"] = sm[c["status"]]
    elif c.get("status") and c["status"] not in STATUS:
        c["status"] = "confirmed"
    vm = {"stable": "static", "静态": "static", "时效": "time-sensitive", "时效性": "time-sensitive",
          "dynamic": "time-sensitive", "evolving": "time-sensitive"}
    if c.get("volatility") in vm:
        c["volatility"] = vm[c["volatility"]]
    elif c.get("volatility") and c["volatility"] not in VOL:
        c["volatility"] = "static"


def _validate(c):
    for req in ("id", "dimension", "text"):
        if not c.get(req):
            raise SystemExit(f"断言缺少必填字段: {req} -> {c}")
    if c.get("confidence") and c["confidence"] not in CONF:
        raise SystemExit(f"confidence 非法: {c['confidence']}")
    if c.get("status") and c["status"] not in STATUS:
        raise SystemExit(f"status 非法: {c['status']}")
    if c.get("volatility") and c["volatility"] not in VOL:
        raise SystemExit(f"volatility 非法: {c['volatility']}")


def cmd_stats(a):
    data = load(a.ledger)
    claims = data["claims"]
    print(f"账本: {a.ledger}  版本 {data.get('version')}  共 {len(claims)} 条断言")
    for key in ("status", "confidence", "volatility", "dimension"):
        agg = {}
        for c in claims:
            agg[c.get(key, "—")] = agg.get(c.get(key, "—"), 0) + 1
        print(f"  按 {key}: " + ", ".join(f"{k}={v}" for k, v in sorted(agg.items())))
    no_src = [c["id"] for c in claims if not c.get("sources")]
    if no_src:
        print(f"  ⚠ 无出处断言 {len(no_src)} 条: {', '.join(no_src[:10])}")


def _age_days(d, as_of):
    try:
        d0 = datetime.strptime(d, "%Y-%m-%d").date()
        return (as_of - d0).days
    except Exception:
        return 99999


def cmd_stale(a):
    data = load(a.ledger)
    as_of = datetime.strptime(a.as_of, "%Y-%m-%d").date() if a.as_of else date.today()
    out = []
    for c in data["claims"]:
        if c.get("volatility") == "time-sensitive":
            age = _age_days(c.get("last_verified", ""), as_of)
            if age >= a.max_age_days:
                out.append((age, c))
    out.sort(reverse=True)
    print(f"需复检的时效性断言 (as-of {as_of}, 阈值 {a.max_age_days} 天): {len(out)} 条")
    for age, c in out:
        print(f"  [{c['id']}] {c['dimension']} | {c['text']} = {c.get('value','')} "
              f"(上次核验 {c.get('last_verified','?')}, {age} 天前)")


def cmd_protected(a):
    """EWC 式：高置信 + 静态 + 多源 → 升级时受保护、无需重研。"""
    data = load(a.ledger)
    prot = [c for c in data["claims"]
            if c.get("confidence") == "high"
            and c.get("status") == "confirmed"
            and c.get("volatility", "static") == "static"
            and len(c.get("sources", [])) >= a.min_sources]
    print(f"受保护(免重研)断言: {len(prot)}/{len(data['claims'])} 条")
    for c in prot:
        print(f"  [{c['id']}] {c['dimension']} | {c['text']}")


def cmd_diff(a):
    old = _index(load(a.old))
    new = _index(load(a.new))
    added = [cid for cid in new if cid not in old]
    removed = [cid for cid in old if cid not in new]
    revised, preserved, flipped = [], [], []
    for cid in new:
        if cid in old:
            o, n = old[cid], new[cid]
            if o.get("status") != n.get("status"):
                flipped.append((cid, o.get("status"), n.get("status")))
            elif o.get("value") != n.get("value"):
                revised.append((cid, o.get("value"), n.get("value")))
            else:
                preserved.append(cid)
    print("=== 版本升级变更摘要 ===")
    print(f"新增 {len(added)} | 修订(值变) {len(revised)} | 翻案(状态变) {len(flipped)} | "
          f"保留(replay) {len(preserved)} | 移除 {len(removed)}")
    for cid in added:
        print(f"  + 新增 [{cid}] {new[cid]['text']} = {new[cid].get('value','')}")
    for cid, ov, nv in revised:
        print(f"  ~ 修订 [{cid}]: {ov}  →  {nv}")
    for cid, os_, ns in flipped:
        print(f"  ! 翻案 [{cid}]: {os_} → {ns}")
    for cid in removed:
        print(f"  - 移除 [{cid}]")
    # 机器可读输出
    if a.json_out:
        save(a.json_out, {"added": added, "revised": [r[0] for r in revised],
                          "flipped": [f[0] for f in flipped],
                          "preserved": preserved, "removed": removed})
        print(f"变更已写入 {a.json_out}")


def main():
    p = argparse.ArgumentParser(description="autodeepreport 证据账本")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init"); s.add_argument("ledger"); s.set_defaults(fn=cmd_init)

    s = sub.add_parser("add"); s.add_argument("ledger")
    s.add_argument("--id", required=True); s.add_argument("--dim", required=True)
    s.add_argument("--text", required=True); s.add_argument("--value", default=None)
    s.add_argument("--confidence", default=None); s.add_argument("--status", default="confirmed")
    s.add_argument("--volatility", default="static"); s.add_argument("--sources", default=None)
    s.add_argument("--provenance", default="ai-verified"); s.add_argument("--last-verified", dest="last_verified", default=None)
    s.add_argument("--note", default=None); s.set_defaults(fn=cmd_add)

    s = sub.add_parser("bulk"); s.add_argument("ledger"); s.add_argument("claims")
    s.set_defaults(fn=cmd_bulk)

    s = sub.add_parser("stats"); s.add_argument("ledger"); s.set_defaults(fn=cmd_stats)

    s = sub.add_parser("stale"); s.add_argument("ledger")
    s.add_argument("--as-of", dest="as_of", default=None)
    s.add_argument("--max-age-days", dest="max_age_days", type=int, default=120)
    s.set_defaults(fn=cmd_stale)

    s = sub.add_parser("protected"); s.add_argument("ledger")
    s.add_argument("--min-sources", dest="min_sources", type=int, default=2)
    s.set_defaults(fn=cmd_protected)

    s = sub.add_parser("diff"); s.add_argument("old"); s.add_argument("new")
    s.add_argument("--json-out", dest="json_out", default=None); s.set_defaults(fn=cmd_diff)

    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
