# -*- coding: utf-8 -*-
"""PAA validator: runs Seal Level 1 + four patent-specific gates.

Usage:
    python validate.py <paa-dir>
    python validate.py <paa-dir> --json      # JSON output
    python validate.py <paa-dir> --quiet     # only FAIL/WARN lines

Checks (per references/validation-checklist.md and references/gates-checklist.md):
  - mandatory-core files exist and non-empty
  - cognitive layer structure
  - application layer structure
  - exploration tree parses + has correct support_level
  - evidence integrity (pn format, no fabrication)
  - cross-layer binding
  - the four gates
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

# ----- Constants -----
MANDATORY_FILES = [
    "MANIFEST.md",
    "logic/invention.md",
    "logic/subject_matter.md",
    "logic/claims_analysis.md",
    "logic/inventive_concepts.md",
    "logic/prior_art.md",
    "logic/related_work.md",
    "logic/solution/constraints.md",
    "application/claims.md",
    "application/specification.md",
    "application/drawings.md",
    "application/abstract.md",
    "trace/exploration_tree.yaml",
    "evidence/README.md",
]

# Loose CN patent number check (CN + 8 or 9 digits + optional kind letter)
PN_RE = re.compile(r"^CN\d{8,9}[A-Z]?$")

# Banned phrases in 权利要求/说明书 (case-sensitive, word-boundary to avoid false positives such as 查询请求)
BANNED_IN_CLAIMS = ["约", "大概", "左右", "优选", "最好", "如权利要求"]
BANNED_IN_CLAIMS_RE = re.compile(r"(?:约|大概|左右|优选|最好|如权利要求)(?![一-鿿])")
BANNED_IN_EFFECTS = ["100%", "大幅", "领先", "遥遥", "完美", "绝对化"]


# ----- Helpers -----
def ok(check): return {"check": check, "status": "PASS", "msg": ""}
def warn(check, msg): return {"check": check, "status": "WARN", "msg": msg}
def fail(check, msg): return {"check": check, "status": "FAIL", "msg": msg}


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


# ----- Checks -----
def check_mandatory_core(paa: Path, results: list):
    for rel in MANDATORY_FILES:
        p = paa / rel
        if not p.exists():
            results.append(fail(f"core:{rel}", "MISSING"))
        elif not read(p).strip():
            results.append(fail(f"core:{rel}", "EMPTY"))
        else:
            results.append(ok(f"core:{rel}"))


def check_cognitive_layer(paa: Path, results: list):
    inv = read(paa / "logic/invention.md")
    sm = read(paa / "logic/subject_matter.md")
    ca = read(paa / "logic/claims_analysis.md")
    ic = read(paa / "logic/inventive_concepts.md")
    pa_text = read(paa / "logic/prior_art.md")

    # 1. invention.md should have 技术问题/技术手段/技术效果 chain markers
    for marker in ["技术问题", "技术手段", "技术效果"]:
        if marker not in inv:
            results.append(warn(f"cognitive:invention.md:{marker}", "技术问题/手段/效果 闭环缺一段"))
        else:
            results.append(ok(f"cognitive:invention.md:{marker}"))

    # 2. subject_matter.md should reference Article 25 or 2.2
    if not re.search(r"25\s*条|2\.2\s*条|客体|智力活动|商业方法", sm):
        results.append(warn("cognitive:subject_matter.md", "未引用 Article 25 / 2.2 条; 门禁1可能FAIL"))

    # 3. claims_analysis.md should mention preamble / 特征部分
    for marker in ["前序", "特征部分", "preamble", "characterizing"]:
        if marker.lower() not in ca.lower():
            results.append(warn(f"cognitive:claims_analysis.md:{marker}", "独权拆解缺要素"))
            break
    else:
        results.append(ok("cognitive:claims_analysis.md:split"))

    # 4. inventive_concepts.md should have ≥1 C## block with Statement + Proof
    if re.search(r"^###\s+C\d+", ic, re.M):
        results.append(ok("cognitive:inventive_concepts.md:concept-block"))
    else:
        results.append(fail("cognitive:inventive_concepts.md:concept-block",
                            "无 C## concept block"))

    # 5. prior_art.md should have pn entries; relationship field; evidence_file ref
    pns_in_pa = re.findall(r"\bCN\d{8,9}[A-Z]?\b", pa_text)
    if not pns_in_pa:
        results.append(fail("cognitive:prior_art.md:no-pn", "无真实pn"))
    else:
        results.append(ok(f"cognitive:prior_art.md:pns({len(set(pns_in_pa))})"))
        # Check each pn has evidence files
        for pn in set(pns_in_pa):
            search_p = paa / "evidence/prior_art_search" / f"{pn}.json"
            claim_p = paa / "evidence/prior_art_claims" / f"{pn}.md"
            if not search_p.exists():
                results.append(fail(f"evidence:prior_art_search:{pn}", "MISSING"))
            if not claim_p.exists():
                results.append(fail(f"evidence:prior_art_claims:{pn}", "MISSING"))


def check_application_layer(paa: Path, results: list):
    claims = read(paa / "application/claims.md")
    spec = read(paa / "application/specification.md")
    drawings = read(paa / "application/drawings.md")
    abstract = read(paa / "application/abstract.md")

    # 1. claims should have ≥1 独立权利要求 with preamble + 特征部分 structure
    if not re.search(r"(?:其特征在于|characterizing)", claims):
        results.append(fail("application:claims.md:structure", "无独立权利要求前序/特征部分结构"))
    else:
        results.append(ok("application:claims.md:structure"))

    # 2. claims should have NO banned phrases (word-boundary match; 约→查询请求 → not banned)
    for m in BANNED_IN_CLAIMS_RE.finditer(claims):
        results.append(fail(f"application:claims.md:banned:{m.group()}",
                            f"权利要求出现禁用词 {m.group()} (位置 {m.start()})"))

    # 3. spec should have all five elements
    five = ["技术领域", "背景技术", "发明内容", "附图说明", "具体实施方式"]
    for el in five:
        if el not in spec:
            results.append(warn(f"application:specification.md:{el}", "缺一个五要素"))

    # 4. abstract ≤ 300 字
    abstract_chars = len(re.sub(r"\s", "", abstract))
    if abstract_chars == 0:
        results.append(fail("application:abstract.md:empty", "EMPTY"))
    elif abstract_chars > 300:
        results.append(fail("application:abstract.md:length",
                            f"{abstract_chars} 字 > 300"))
    else:
        results.append(ok(f"application:abstract.md:length({abstract_chars})"))

    # 5. abstract should specify 摘要附图
    if not re.search(r"摘要附图", abstract):
        results.append(warn("application:abstract.md:no-summary-fig", "未指定摘要附图"))

    # 6. drawings should have ≥1 figure
    if not re.search(r"图\d+|图\s*\d+|Fig\.\s*\d+", drawings):
        results.append(warn("application:drawings.md:no-fig", "无附图条目"))


def check_exploration_tree(paa: Path, results: list):
    import yaml
    tree_path = paa / "trace/exploration_tree.yaml"
    if not tree_path.exists():
        return  # already covered by mandatory check
    text = read(tree_path)
    try:
        tree = yaml.safe_load(text)
    except Exception as e:
        results.append(fail("trace:exploration_tree.yaml:yaml", f"YAML parse error: {e}"))
        return
    if not isinstance(tree, dict):
        results.append(fail("trace:exploration_tree.yaml:shape", "not a dict at root"))
        return
    nodes = tree.get("nodes") or []
    if not nodes:
        results.append(warn("trace:exploration_tree.yaml:no-nodes", "无节点"))
    # support_level + source_ref checks
    for n in nodes:
        if not isinstance(n, dict) or "id" not in n:
            results.append(fail("trace:exploration_tree.yaml:node-shape", "node missing id"))
            continue
        nid = n.get("id")
        sl = n.get("support_level")
        if sl not in ("explicit", "inferred"):
            results.append(fail(f"trace:exploration_tree.yaml:{nid}:support_level",
                                f"node has support_level={sl}, must be explicit|inferred"))
        if sl == "explicit" and not n.get("source_ref"):
            results.append(fail(f"trace:exploration_tree.yaml:{nid}:source_ref",
                                "explicit node missing source_ref"))
    # prior-art nodes must have real pn
    for n in nodes:
        if n.get("type") == "prior-art":
            pn = n.get("pn")
            if not pn or not PN_RE.match(pn):
                results.append(fail(f"trace:exploration_tree.yaml:{n.get('id')}:pn",
                                    f"prior-art pn invalid: {pn}"))


def check_evidence_integrity(paa: Path, results: list):
    # Walk all md/json files in evidence/ and look for pn patterns
    pns_referenced = set()
    for sub in ("logic", "application", "trace"):
        d = paa / sub
        if not d.exists(): continue
        for f in d.rglob("*"):
            if f.is_file() and f.suffix in (".md", ".yaml", ".txt"):
                pns_referenced.update(re.findall(r"\bCN\d{8,9}[A-Z]?\b", read(f)))

    pns_with_evidence = set()
    search_dir = paa / "evidence/prior_art_search"
    if search_dir.exists():
        for f in search_dir.glob("CN*.json"):
            m = PN_RE.match(f.stem)
            if m: pns_with_evidence.add(m.group())

    missing = pns_referenced - pns_with_evidence
    if missing:
        results.append(fail("evidence:missing-pn-search", f"{len(missing)} pn无search记录: {sorted(missing)[:5]}"))
    else:
        results.append(ok(f"evidence:pn-search({len(pns_with_evidence)})"))


def check_cross_layer_binding(paa: Path, results: list):
    ca = read(paa / "logic/claims_analysis.md")
    pa_text = read(paa / "logic/prior_art.md")
    spec = read(paa / "application/specification.md")
    score_path = paa / "evidence/scoring/scoring.json"

    diff_features = re.findall(r"D\d+", ca)
    diff_features_unique = sorted(set(diff_features))
    if not diff_features_unique:
        results.append(warn("binding:no-diff-features", "未识别到区别特征 D##"))
        return

    for d in diff_features_unique:
        # Check embodiment reference
        if not re.search(rf"{d}[^\\n]*实施例", spec) and not re.search(rf"实施例[\\s\\S]{{0,80}}{d}", spec):
            results.append(fail(f"binding:{d}:embodiment", f"{d} 无对应实施例引用"))
        # Check prior-art reference
        if d not in pa_text:
            results.append(warn(f"binding:{d}:prior_art", f"{d} 在 prior_art.md 无显式引用"))

    # Score file existence (if PAA has scoring, validate structure)
    if score_path.exists():
        try:
            data = json.loads(read(score_path))
            if "scores" not in data:
                results.append(warn("binding:scoring:no-scores", "scoring.json 缺 scores 字段"))
            else:
                results.append(ok(f"binding:scoring({len(data['scores'])} experts)"))
        except Exception as e:
            results.append(fail("binding:scoring:json", f"JSON parse error: {e}"))


# ----- Gates -----
def gate_1_subject_matter(paa: Path) -> dict:
    sm = read(paa / "logic/subject_matter.md")
    claims = read(paa / "application/claims.md")
    if not re.search(r"25\s*条|2\.2\s*条|客体|智力活动|商业方法", sm):
        return {"status": "FAIL", "reason": "subject_matter.md 未做 Article 25/2.2 检查",
                "fix": "在 logic/subject_matter.md 完成客体适格分析，明确标记风险等级"}
    if not claims.strip():
        return {"status": "FAIL", "reason": "无权利要求",
                "fix": "先撰写 application/claims.md"}
    # heuristic: presence of technical-feature phrasing in 独立权利要求
    if not re.search(r"其特征在于", claims):
        return {"status": "FAIL", "reason": "无'其特征在于'特征部分标识",
                "fix": "在 application/claims.md 中明确以'其特征在于'切分前序与特征部分"}
    return {"status": "PASS", "reason": ""}


def gate_2_novelty_inventive(paa: Path) -> dict:
    ca = read(paa / "logic/claims_analysis.md")
    pa_text = read(paa / "logic/prior_art.md")
    if not ca.strip():
        return {"status": "FAIL", "reason": "无独权拆解",
                "fix": "先写 logic/claims_analysis.md"}
    diffs = sorted(set(re.findall(r"D\d+", ca)))
    pns = sorted(set(re.findall(r"\bCN\d{8,9}[A-Z]?\b", pa_text)))
    if not pns:
        return {"status": "FAIL", "reason": "logic/prior_art.md 无真实pn",
                "fix": "用 incopat-search skill 跑查新，把真实pn+检索式写入 evidence/prior_art_search/"}
    if not diffs:
        return {"status": "FAIL", "reason": "无区别特征",
                "fix": "在 logic/claims_analysis.md 列 D01..DXX 每条区别特征"}
    return {"status": "PASS", "reason": f"区别特征 {len(diffs)} 条 / 对比文件 {len(pns)} 个"}


def gate_3_sufficient_disclosure(paa: Path) -> dict:
    spec = read(paa / "application/specification.md")
    claims = read(paa / "application/claims.md")
    if not spec.strip():
        return {"status": "FAIL", "reason": "无说明书",
                "fix": "撰写 application/specification.md 含五要素"}
    # heuristic — count 实施例 paragraphs
    n_emb = len(re.findall(r"实施例\s*[一二三四五六七八九十0-9]+", spec))
    n_claim_feats = len(re.findall(r"其特征在于", claims)) or 1
    if n_emb < n_claim_feats:
        return {"status": "WARN", "reason": f"实施例{n_emb} < 权利要求特征{n_claim_feats}",
                "fix": "为每条权利要求特征补 ≥1 实施例段落，含数值实例"}
    return {"status": "PASS", "reason": f"实施例{n_emb}"}


def gate_4_no_fabrication(paa: Path) -> dict:
    """Walk all md/json files; collect all cited pns; verify each has search receipt."""
    pns_cited = set()
    for sub in ("logic", "application", "trace"):
        d = paa / sub
        if not d.exists(): continue
        for f in d.rglob("*"):
            if f.is_file() and f.suffix in (".md", ".yaml", ".txt"):
                pns_cited.update(re.findall(r"\bCN\d{8,9}[A-Z]?\b", read(f)))

    if not pns_cited:
        return {"status": "FAIL", "reason": "无任何 cited pn — 可能未做查新",
                "fix": "运行 incopat-search skill 至少做一次语义检索+1组定向检索式"}

    pns_with_evidence = set()
    search_dir = paa / "evidence/prior_art_search"
    if search_dir.exists():
        for f in search_dir.glob("CN*.json"):
            m = PN_RE.match(f.stem)
            if m: pns_with_evidence.add(m.group())

    missing = pns_cited - pns_with_evidence
    if missing:
        return {"status": "FAIL",
                "reason": f"{len(missing)} cited pn 无 search 记录: {sorted(missing)[:5]}",
                "fix": "对每个被引用的 pn 跑一次 incopat-search，把原始响应存为 evidence/prior_art_search/<pn>.json"}
    return {"status": "PASS", "reason": f"{len(pns_with_evidence)} cited pn 全部溯源"}


# ----- Main = =----
def main():
    ap = argparse.ArgumentParser(description="Validate a PAA")
    ap.add_argument("dir", help="target PAA directory")
    ap.add_argument("--json", action="store_true", help="JSON output")
    ap.add_argument("--quiet", action="store_true", help="only FAIL/WARN")
    args = ap.parse_args()

    paa = Path(args.dir)
    if not paa.exists():
        print(f"ERROR: {paa} not found", file=sys.stderr)
        sys.exit(2)

    results = []
    check_mandatory_core(paa, results)
    check_cognitive_layer(paa, results)
    check_application_layer(paa, results)
    check_exploration_tree(paa, results)
    check_evidence_integrity(paa, results)
    check_cross_layer_binding(paa, results)

    gates = {
        "gate_1_subject_matter": gate_1_subject_matter(paa),
        "gate_2_novelty_inventive": gate_2_novelty_inventive(paa),
        "gate_3_sufficient_disclosure": gate_3_sufficient_disclosure(paa),
        "gate_4_no_fabrication": gate_4_no_fabrication(paa),
    }
    gates_overall = "PASS" if all(g["status"] in ("PASS", "WARN") for g in gates.values()) else "FAIL"

    summary = {
        "artifact": str(paa),
        "gates_overall": gates_overall,
        "checks": results,
        "gates": gates,
    }

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=1))
    else:
        # human-readable
        n_pass = sum(1 for r in results if r["status"] == "PASS")
        n_warn = sum(1 for r in results if r["status"] == "WARN")
        n_fail = sum(1 for r in results if r["status"] == "FAIL")
        print(f"\n=== PAA Validation: {paa}")
        print(f"Checks: {n_pass} PASS  {n_warn} WARN  {n_fail} FAIL")
        print(f"\nGates: {gates_overall}")
        for k, v in gates.items():
            print(f"  {k}: {v['status']}  {v.get('reason','')}")
        if not args.quiet:
            for r in results:
                if r["status"] in ("WARN", "FAIL"):
                    print(f"  [{r['status']}] {r['check']}: {r['msg']}")
        print()

    # exit code: 0 PASS, 1 FAIL
    sys.exit(0 if n_fail == 0 and gates_overall == "PASS" else 1)


if __name__ == "__main__":
    main()