# -*- coding: utf-8 -*-
"""Deep structural/stylistic distill of journal full-text PDFs → Paper_CCF skills."""
from __future__ import annotations

import json
import math
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PDF_ROOT = ROOT / "papers/literature/target_journal_related/fulltext_by_journal"
META = ROOT / "papers/literature/target_journal_related/metadata"
OUT_JSON = META / "journal_deep_distill.json"
OUT_MD = META / "journal_deep_distill_notes.md"
SKILL_ROOT = Path.home() / ".claude/skills/Paper_CCF/journals"
BATCH_MD = Path.home() / ".claude/skills/Paper_CCF/resources/target-journals-2026-batch-distill.md"

try:
    from pypdf import PdfReader
except ImportError:
    from PyPDF2 import PdfReader  # type: ignore

SECTION_HEADER = "### Distilled deep structure & style (local corpus, 2026-08)"

# numbered or named section headers
SEC_RE = re.compile(
    r"(?m)^(?:\s*)((?:\d{1,2}(?:\.\d{1,2}){0,2})|[IVX]{1,4})[\.\s)\-]+([A-Z][A-Za-z0-9 ,/&\-]{2,80})\s*$"
)
NAMED_SEC_RE = re.compile(
    r"(?mi)^\s*(Abstract|Keywords?|Introduction|Related\s+Works?|Literature\s+Review|"
    r"Materials?\s+and\s+Methods?|Methodology|Proposed\s+Method|Method(?:ology|s)?|"
    r"System\s+Model|Problem\s+Formulation|Experimental?\s+(?:Setup|Results?|Evaluation)|"
    r"Results?(?:\s+and\s+Discussion)?|Discussion|Ablation|Case\s+Study|"
    r"Conclusion(?:s)?(?:\s+and\s+Future\s+Work)?|Acknowledg(?:e)?ments?|References|"
    r"Data\s+Availability|Conflicts?\s+of\s+Interest|Author\s+Contributions)\s*$"
)

FIG_RE = re.compile(r"\b(?:Figure|Fig\.|FIG\.)\s*(\d+[A-Za-z]?)\b")
TABLE_RE = re.compile(r"\b(?:Table|TABLE)\s*(\d+)\b")
EQ_RE = re.compile(r"(?:\(\s*\d+\s*\)|Eq(?:uation)?\.?\s*\d+|=\s*[^\n]{0,40})")
FORMULA_LINE_RE = re.compile(r"(?m)^[^\n]{0,120}[=≤≥∈∑∫∂√αβγδθλμσω]\s*[^\n]{0,120}$")
DATASET_RE = re.compile(
    r"\b(?:dataset|data\s*set|benchmark|IEEE\s*\d+|UCI|Kaggle|ETT[hm]?\d*|Matpower|"
    r"PGLib|Grid2Op|RTS|NREL|ENTSO|Mendeley|open[\s-]?data)\b",
    re.I,
)
ALGO_NAME_RE = re.compile(
    r"\b(?:LSTM|BiLSTM|GRU|BiGRU|CNN|ResNet|Transformer|BERT|XGBoost|LightGBM|SVM|"
    r"Random\s+Forest|PSO|GA|NSGA|GNN|GAT|DQN|PPO|Informer|Autoformer|Attention|"
    r"Kalman|ARIMA|YOLO|VGG|Adam|SGD)\b",
    re.I,
)
BLOCK_DIAG_RE = re.compile(
    r"\b(?:block\s+diagram|flowchart|flow\s+chart|schematic|architecture\s+(?:diagram|figure)|"
    r"framework\s+(?:diagram|overview)|system\s+overview|pipeline)\b",
    re.I,
)
BASELINE_RE = re.compile(r"\b(?:baseline|compared\s+with|comparison\s+with|state[- ]of[- ]the[- ]art|SOTA)\b", re.I)
ABLATION_RE = re.compile(r"\b(?:ablation|sensitivity\s+analy)\b", re.I)
INNOV_ALGO_RE = re.compile(
    r"\b(?:novel\s+algorithm|proposed\s+algorithm|new\s+method|we\s+propose\s+a\s+new|"
    r"theoretical\s+contribution|convergence\s+proof|complexity\s+analysis)\b",
    re.I,
)
INNOV_INTEG_RE = re.compile(
    r"\b(?:hybrid|framework|integrated|combination|pipeline|end[- ]to[- ]end|"
    r"application\s+to|case\s+study|real[- ]world|deploy)\b",
    re.I,
)

STOP = set(
    """
    the a an and or of to in for on with by from as is are was were be been being
    this that these those it its their our we you your they them he she his her
    at into over under between among not no nor so if then than which who whom
    what when where how why can may might must shall should will would also
    using used use based paper proposed method methods results result figure
    table section et al via per such into about more most other into
    """.split()
)

TERM_CAND_RE = re.compile(r"\b([A-Z][A-Za-z0-9\-]{2,}(?:\s+[A-Z][A-Za-z0-9\-]{2,}){0,3})\b")
SENT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"'])")


def words(text: str) -> list[str]:
    return re.findall(r"[A-Za-z][A-Za-z0-9\-]{1,}", text)


def word_count(text: str) -> int:
    return len(words(text))


def paragraphs(text: str) -> list[str]:
    """Estimate paragraphs from PDF text (often lacks blank lines)."""
    parts = re.split(r"\n\s*\n+", text)
    out = []
    for p in parts:
        p2 = re.sub(r"\s+", " ", p).strip()
        if len(p2) >= 80 and word_count(p2) >= 25:
            out.append(p2)
    if len(out) >= 5:
        return out
    # PDF line-wrap fallback: rebuild sentences, pack ~120-180 words per paragraph
    flat = re.sub(r"\s+", " ", text)
    sents = [s.strip() for s in SENT_RE.split(flat) if len(s.strip()) > 30]
    if not sents:
        # crude chunk by words
        toks = words(flat)
        chunk = 140
        return [" ".join(toks[i : i + chunk]) for i in range(0, len(toks), chunk) if len(toks[i : i + chunk]) >= 40]
    packed, buf, wc = [], [], 0
    for s in sents:
        sw = word_count(s)
        if wc + sw > 160 and buf:
            packed.append(" ".join(buf))
            buf, wc = [s], sw
        else:
            buf.append(s)
            wc += sw
    if buf:
        packed.append(" ".join(buf))
    return [p for p in packed if word_count(p) >= 30]


NOISE_START = re.compile(
    r"^(?:This work is licensed|Creative Commons|doi\.org|http|www\.|Email |Received:|Accepted:|"
    r"Published:|Citation:|Copyright|MDPI|Elsevier|Springer|Wiley|PeerJ|Figure \d|Table \d|"
    r"Since January|The COVID-19|These permissions|Journal of |Downloaded from|"
    r"Available online|echT |Tech Science|ComputMaterContin)",
    re.I,
)


def sentence_starters(text: str, n: int = 12) -> list[str]:
    flat = re.sub(r"\s+", " ", text)
    sents = [s.strip() for s in SENT_RE.split(flat) if len(s.strip()) > 50]
    starters = []
    for s in sents[:120]:
        if NOISE_START.search(s):
            continue
        if re.search(r"creativecommons|rights reserved|all rights", s, re.I):
            continue
        toks = words(s)[:8]
        if len(toks) >= 4:
            starters.append(" ".join(toks[:6]))
    return [x for x, _ in Counter(starters).most_common(n)]


def split_sections(full: str) -> list[dict]:
    """Return list of {title, text}."""
    matches = []
    for m in NAMED_SEC_RE.finditer(full):
        matches.append((m.start(), m.group(1).strip()))
    for m in SEC_RE.finditer(full):
        title = m.group(2).strip()
        if len(title) < 3:
            continue
        matches.append((m.start(), f"{m.group(1)} {title}"))
    matches = sorted(set(matches), key=lambda x: x[0])
    cleaned = []
    for pos, title in matches:
        if cleaned and pos - cleaned[-1][0] < 40:
            continue
        cleaned.append((pos, title))
    secs = []
    for i, (pos, title) in enumerate(cleaned):
        end = cleaned[i + 1][0] if i + 1 < len(cleaned) else len(full)
        body = full[pos:end]
        body = re.sub(r"^[^\n]*\n", "", body, count=1)
        secs.append({"title": title, "text": body})
    if not secs:
        secs = [{"title": "Body", "text": full}]
    return secs


def classify_section(title: str) -> str:
    t = title.lower()
    if "abstract" in t:
        return "abstract"
    if "introduction" in t:
        return "introduction"
    if "related" in t or "literature" in t:
        return "related_work"
    if any(x in t for x in ("method", "proposed", "model", "formulation", "approach", "algorithm")):
        return "method"
    if any(x in t for x in ("experiment", "result", "evaluation", "case study", "ablation", "discussion")):
        return "experiment"
    if "conclusion" in t:
        return "conclusion"
    if "reference" in t or "acknowledg" in t:
        return "back"
    return "other"


def extract_abstract(text: str) -> str:
    m = re.search(
        r"Abstract\s*[:：]?\s*(.{80,2500}?)(?:\n\s*Keywords|\n\s*1[\.\s]|Introduction|1\s+Introduction)",
        text,
        re.I | re.S,
    )
    if m:
        return re.sub(r"\s+", " ", m.group(1)).strip()
    return ""


def extract_conclusion(secs: list[dict], full: str) -> str:
    for s in secs:
        if classify_section(s["title"]) == "conclusion":
            return re.sub(r"\s+", " ", s["text"])[:2000]
    m = re.search(
        r"(?is)(?:\d+[\.\s]+)?Conclusions?\b(.{120,2000}?)(?:Acknowledg|References|Conflicts|Data Availability|\Z)",
        full,
    )
    if m:
        return re.sub(r"\s+", " ", m.group(1)).strip()
    return ""


def abstract_style(abs_text: str) -> dict:
    if not abs_text:
        return {"words": 0, "sentences": 0, "pattern": "missing"}
    sents = [s.strip() for s in SENT_RE.split(abs_text) if s.strip()]
    wc = word_count(abs_text)
    has_bg = bool(re.search(r"\b(?:however|although|challenge|problem|critical|important)\b", abs_text, re.I))
    has_method = bool(re.search(r"\b(?:propose|proposed|present|develop|introduce)\b", abs_text, re.I))
    has_result = bool(re.search(r"\b(?:result|achieve|improv|outperform|accuracy|rmse|mae|f1)\b", abs_text, re.I))
    has_contrib = bool(re.search(r"\b(?:contribution|main\s+findings?|key\s+findings?)\b", abs_text, re.I))
    pattern = []
    if has_bg:
        pattern.append("gap/background")
    if has_method:
        pattern.append("method claim")
    if has_result:
        pattern.append("quantitative result")
    if has_contrib:
        pattern.append("explicit contributions")
    return {
        "words": wc,
        "sentences": len(sents) or abs_text.count(".") + 1,
        "pattern": " → ".join(pattern) or "descriptive",
        "has_numbers": bool(re.search(r"\d+(\.\d+)?%?", abs_text)),
    }


def conclusion_style(conc: str) -> dict:
    if not conc:
        return {"words": 0, "pattern": "missing"}
    has_summary = bool(re.search(r"\b(?:in this paper|this paper|we proposed|we presented)\b", conc, re.I))
    has_findings = bool(re.search(r"\b(?:results?\s+show|demonstrat|indicat|confirm)\b", conc, re.I))
    has_limit = bool(re.search(r"\b(?:limitations?|however|although|future\s+work)\b", conc, re.I))
    has_future = bool(re.search(r"\b(?:future\s+work|further\s+research|will\s+be\s+extended)\b", conc, re.I))
    pattern = []
    if has_summary:
        pattern.append("restate contribution")
    if has_findings:
        pattern.append("restate findings")
    if has_limit:
        pattern.append("limitations")
    if has_future:
        pattern.append("future work")
    return {"words": word_count(conc), "pattern": " → ".join(pattern) or "short wrap-up", "has_numbers": bool(re.search(r"\d+", conc))}


def analyze_pdf(pdf: Path) -> dict:
    try:
        reader = PdfReader(str(pdf))
        n_pages = len(reader.pages)
        page_texts = []
        for i in range(n_pages):
            try:
                page_texts.append(reader.pages[i].extract_text() or "")
            except Exception:
                page_texts.append("")
        full = "\n".join(page_texts)
    except Exception as e:
        return {"file": pdf.name, "error": str(e)}

    full_norm = full.replace("\r", "")
    wc = word_count(full_norm)
    secs = split_sections(full_norm)
    # drop references-heavy noise for content metrics
    content_secs = [s for s in secs if classify_section(s["title"]) != "back"]
    paras = paragraphs(full_norm)
    para_wcs = [word_count(p) for p in paras] or [0]

    fig_ids = set(FIG_RE.findall(full_norm))
    tab_ids = set(TABLE_RE.findall(full_norm))
    # formula proxies: numbered equations + dense math lines
    eq_nums = len(set(re.findall(r"\(\s*(\d+)\s*\)", full_norm)))
    math_lines = len(FORMULA_LINE_RE.findall(full_norm))
    n_formulas = max(eq_nums, math_lines // 3)

    dataset_mentions = sorted(set(m.group(0) for m in DATASET_RE.finditer(full_norm)))
    algo_mentions = sorted(set(m.group(0) for m in ALGO_NAME_RE.finditer(full_norm)))

    # block diagrams: figure captions / nearby text
    block_hits = []
    for m in BLOCK_DIAG_RE.finditer(full_norm):
        ctx = full_norm[max(0, m.start() - 120) : m.end() + 120]
        fig = FIG_RE.search(ctx)
        # find which section
        sec_name = "unknown"
        pos = m.start()
        acc = 0
        for s in secs:
            acc += len(s["title"]) + len(s["text"]) + 1
            if pos <= acc:
                sec_name = s["title"]
                break
        block_hits.append({"section": sec_name, "fig": fig.group(0) if fig else "", "snippet": re.sub(r"\s+", " ", ctx)[:160]})

    # charts/experiment figures: count unique figure numbers; block diagrams subset
    n_charts = len(fig_ids)
    n_block = len({(b["fig"] or b["snippet"][:40]) for b in block_hits}) or (1 if block_hits else 0)

    abs_text = extract_abstract(full_norm)
    conc_text = extract_conclusion(secs, full_norm)

    # per-section stats
    sec_stats = []
    for s in content_secs:
        ps = paragraphs(s["text"])
        pwc = [word_count(p) for p in ps] or [0]
        sec_stats.append(
            {
                "title": s["title"][:80],
                "kind": classify_section(s["title"]),
                "words": word_count(s["text"]),
                "paragraphs": len(ps),
                "avg_para_words": round(sum(pwc) / max(len(pwc), 1), 1),
                "figures_mentioned": len(set(FIG_RE.findall(s["text"]))),
                "tables_mentioned": len(set(TABLE_RE.findall(s["text"]))),
                "has_block_diagram_lang": bool(BLOCK_DIAG_RE.search(s["text"])),
            }
        )

    # terms
    terms = Counter()
    for m in TERM_CAND_RE.finditer(full_norm[:50000]):
        t = m.group(1).strip()
        tl = t.lower()
        if tl in STOP or len(t) < 4:
            continue
        if tl in {
            "figure", "table", "section", "journal", "volume", "article", "license",
            "creative", "commons", "elsevier", "springer", "wiley", "mdpi", "https", "http",
        }:
            continue
        if re.search(r"creativecommons|rightsreserved|doi\.org", tl):
            continue
        terms[t] += 1

    innov_algo = len(INNOV_ALGO_RE.findall(full_norm))
    innov_integ = len(INNOV_INTEG_RE.findall(full_norm))
    if innov_algo > innov_integ * 1.2:
        innov_type = "algorithm_innovation"
    elif innov_integ > innov_algo * 1.2:
        innov_type = "integration_application"
    else:
        innov_type = "mixed"

    exp_strength = 0
    if BASELINE_RE.search(full_norm):
        exp_strength += 1
    if ABLATION_RE.search(full_norm):
        exp_strength += 1
    if len(dataset_mentions) >= 2:
        exp_strength += 1
    if len(algo_mentions) >= 3:
        exp_strength += 1
    if n_charts >= 4:
        exp_strength += 1
    exp_label = ["thin", "moderate", "solid", "strong", "very_strong"][min(exp_strength, 4)]

    return {
        "file": pdf.name,
        "error": "",
        "pages": n_pages,
        "words": wc,
        "n_sections": len(content_secs),
        "n_paragraphs": len(paras),
        "avg_para_words": round(sum(para_wcs) / max(len(para_wcs), 1), 1),
        "median_para_words": round(statistics.median(para_wcs), 1) if para_wcs else 0,
        "n_formulas": n_formulas,
        "n_datasets_mentioned": len(dataset_mentions),
        "datasets": dataset_mentions[:12],
        "n_algos_mentioned": len(algo_mentions),
        "algos": algo_mentions[:15],
        "n_figures": n_charts,
        "n_tables": len(tab_ids),
        "n_block_diagrams": n_block,
        "block_diagram_sections": sorted({b["section"][:60] for b in block_hits})[:8],
        "abstract": abstract_style(abs_text),
        "conclusion": conclusion_style(conc_text),
        "sentence_starters": sentence_starters(full_norm[:30000], 8),
        "top_terms": [t for t, _ in terms.most_common(15)],
        "sections": sec_stats[:12],
        "innovation_type": innov_type,
        "innovation_scores": {"algo": innov_algo, "integration": innov_integ},
        "experiment_strength": exp_label,
        "has_baseline": bool(BASELINE_RE.search(full_norm)),
        "has_ablation": bool(ABLATION_RE.search(full_norm)),
    }


def avg(xs):
    xs = [x for x in xs if x is not None]
    return round(sum(xs) / len(xs), 1) if xs else 0


def med(xs):
    xs = [x for x in xs if x is not None]
    return round(statistics.median(xs), 1) if xs else 0


def summarize_journal(slug: str, records: list[dict]) -> dict:
    ok = [r for r in records if not r.get("error")]
    if not ok:
        return {"slug": slug, "n": 0, "markdown": "_No readable PDFs._\n", "records": records}

    # aggregate
    pages = [r["pages"] for r in ok]
    words_ = [r["words"] for r in ok]
    secs = [r["n_sections"] for r in ok]
    paras = [r["n_paragraphs"] for r in ok]
    para_w = [r["avg_para_words"] for r in ok]
    formulas = [r["n_formulas"] for r in ok]
    datasets = [r["n_datasets_mentioned"] for r in ok]
    algos = [r["n_algos_mentioned"] for r in ok]
    figs = [r["n_figures"] for r in ok]
    tabs = [r["n_tables"] for r in ok]
    blocks = [r["n_block_diagrams"] for r in ok]
    abs_w = [r["abstract"]["words"] for r in ok]
    abs_s = [r["abstract"]["sentences"] for r in ok]
    conc_w = [r["conclusion"]["words"] for r in ok]

    innov = Counter(r["innovation_type"] for r in ok)
    exp = Counter(r["experiment_strength"] for r in ok)
    block_secs = Counter()
    for r in ok:
        for s in r.get("block_diagram_sections") or []:
            block_secs[classify_section(s) if s else "unknown"] += 1
            block_secs[s[:40]] += 1

    terms = Counter()
    starters = Counter()
    alg_c = Counter()
    data_c = Counter()
    abs_pat = Counter()
    conc_pat = Counter()
    kind_words = defaultdict(list)
    kind_paras = defaultdict(list)

    for r in ok:
        for t in r.get("top_terms") or []:
            terms[t] += 1
        for s in r.get("sentence_starters") or []:
            starters[s] += 1
        for a in r.get("algos") or []:
            alg_c[a] += 1
        for d in r.get("datasets") or []:
            data_c[d] += 1
        abs_pat[r["abstract"].get("pattern", "")] += 1
        conc_pat[r["conclusion"].get("pattern", "")] += 1
        for sec in r.get("sections") or []:
            kind_words[sec["kind"]].append(sec["words"])
            kind_paras[sec["kind"]].append(sec["paragraphs"])

    dominant_innov = innov.most_common(1)[0][0] if innov else "mixed"
    innov_zh = {
        "algorithm_innovation": "算法创新（新模型/证明/复杂度）",
        "integration_application": "集成/应用创新（混合框架、场景落地、端到端流水线）",
        "mixed": "算法创新与集成应用并重",
    }[dominant_innov]

    # section writing notes
    sec_notes = []
    kind_tips = {
        "introduction": "动机→缺口→贡献列表；少公式，偶发总览框图",
        "related_work": "分主题综述 + 与本文差异句；少图表",
        "method": "符号/问题定义→算法或框架→复杂度或流程框图；公式与架构图密集",
        "experiment": "数据集+基线+指标表+对比/消融图；强调可复现设置",
        "conclusion": "重述贡献与定量结果→局限→未来工作",
    }
    for kind in ("introduction", "related_work", "method", "experiment", "conclusion"):
        if kind not in kind_words:
            continue
        tip = kind_tips.get(kind, "")
        sec_notes.append(
            f"  - **{kind}**: avg ~{avg(kind_words[kind]):.0f} words / ~{avg(kind_paras[kind]):.1f} paragraphs"
            + (f"；核心写法：{tip}" if tip else "")
        )

    block_pref = ", ".join(f"{k}×{v}" for k, v in block_secs.most_common(6) if not k.startswith("unknown")) or "rarely lexicalized"

    md = []
    md.append(f"- Deep sample: **n={len(ok)}** PDFs under `fulltext_by_journal/{slug}/`.")
    md.append(
        f"- **Length:** pages mean/median **{avg(pages)}/{med(pages)}** "
        f"(range {min(pages)}–{max(pages)}); words mean/median **{avg(words_):.0f}/{med(words_):.0f}**."
    )
    md.append(
        f"- **Structure:** sections mean **{avg(secs)}**; paragraphs mean **{avg(paras)}**; "
        f"words/paragraph mean/median **{avg(para_w)}/{med(para_w)}**."
    )
    md.append(
        f"- **Artifacts:** formulas≈**{avg(formulas)}**; figures≈**{avg(figs)}**; tables≈**{avg(tabs)}**; "
        f"block-diagrams≈**{avg(blocks)}** (mentions). Block-diagram sections: {block_pref}."
    )
    md.append(
        f"- **Experiment load:** datasets mentioned≈**{avg(datasets)}**/paper; named algorithms≈**{avg(algos)}**/paper; "
        f"baseline signal **{sum(1 for r in ok if r['has_baseline'])}/{len(ok)}**; "
        f"ablation/sensitivity **{sum(1 for r in ok if r['has_ablation'])}/{len(ok)}**; "
        f"strength histogram: {dict(exp)}."
    )
    md.append(f"- **Innovation preference:** **{innov_zh}** (votes {dict(innov)}).")
    md.append(
        f"- **Abstract craft:** mean **{avg(abs_w):.0f}** words / **{avg(abs_s):.1f}** sentences; "
        f"dominant pattern: `{abs_pat.most_common(1)[0][0] if abs_pat else 'n/a'}` "
        f"(top patterns {abs_pat.most_common(3)})."
    )
    md.append(
        f"- **Conclusion craft:** mean **{avg(conc_w):.0f}** words; "
        f"dominant pattern: `{conc_pat.most_common(1)[0][0] if conc_pat else 'n/a'}` "
        f"(top {conc_pat.most_common(3)})."
    )
    md.append("- **Chapter size/role (corpus means):**")
    md.extend(sec_notes or ["  - (section headers weakly detected; rely on length/artifact stats)"])
    md.append("- **Frequent terms:** " + ", ".join(t for t, _ in terms.most_common(12)) + ".")
    md.append("- **Frequent named algorithms:** " + (", ".join(f"{a}({c})" for a, c in alg_c.most_common(8)) or "n/a") + ".")
    md.append("- **Frequent dataset/benchmark cues:** " + (", ".join(f"{d}({c})" for d, c in data_c.most_common(8)) or "n/a") + ".")
    clean_starters = [
        s
        for s, _ in starters.most_common(20)
        if not re.search(
            r"doi org|Email |Downloaded|COVID-19 resource|permissions are granted|"
            r"Available online|echT |https doi|ComputMaterContin",
            s,
            re.I,
        )
    ][:6]
    md.append("- **Common sentence openings:** " + ("; ".join(f"`{s}`" for s in clean_starters) or "n/a") + ".")
    md.append(
        "- **Writing logic to emulate:** match the dominant innovation mode; "
        "keep section budget near the means above; put architecture/block diagrams in method "
        "(and sometimes experiment overview); pair claims with the observed figure/table/formula density; "
        "abstract should follow the dominant pattern and usually include a quantitative punchline when the corpus does."
    )

    return {
        "slug": slug,
        "n": len(ok),
        "stats": {
            "pages_mean": avg(pages),
            "pages_median": med(pages),
            "words_mean": avg(words_),
            "sections_mean": avg(secs),
            "paragraphs_mean": avg(paras),
            "para_words_mean": avg(para_w),
            "formulas_mean": avg(formulas),
            "figures_mean": avg(figs),
            "tables_mean": avg(tabs),
            "block_diagrams_mean": avg(blocks),
            "datasets_mean": avg(datasets),
            "algos_mean": avg(algos),
            "innovation": dominant_innov,
            "experiment_strength": dict(exp),
        },
        "markdown": "\n".join(md) + "\n",
        "records": ok,
    }


def patch_skill(slug: str, block: str) -> bool:
    path = SKILL_ROOT / slug / "SKILL.md"
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    new_sec = (
        f"{SECTION_HEADER}\n\n{block}\n"
        f"Corpus path: `papers/literature/target_journal_related/fulltext_by_journal/{slug}/`.\n"
    )
    if SECTION_HEADER in text:
        text = re.sub(
            rf"{re.escape(SECTION_HEADER)}.*?(?=\n## |\n### [^D]|\Z)",
            new_sec + "\n",
            text,
            count=1,
            flags=re.S,
        )
    elif "### Distilled full-text patterns" in text:
        # insert deep section after the shallow full-text patterns block
        m = re.search(r"### Distilled full-text patterns.*?(?=\n## |\n### |\Z)", text, flags=re.S)
        if m:
            text = text[: m.end()] + "\n" + new_sec + text[m.end() :]
        else:
            text = text.rstrip() + "\n\n" + new_sec
    else:
        m = re.search(r"\n## (APC|Review|Official|Common desk|Method)", text)
        if m:
            text = text[: m.start()] + "\n" + new_sec + text[m.start() :]
        else:
            text = text.rstrip() + "\n\n" + new_sec
    path.write_text(text, encoding="utf-8")
    return True


def main():
    META.mkdir(parents=True, exist_ok=True)
    all_summ = []
    md_parts = ["# Journal deep distill notes (2026-08)\n", f"Root: `{PDF_ROOT}`\n"]
    raw = {}

    for d in sorted(PDF_ROOT.glob("*")):
        if not d.is_dir() or d.name.startswith("_"):
            continue
        recs = []
        pdfs = sorted(d.glob("*.pdf"))[:12]
        print(f"=== {d.name} n={len(pdfs)} ===", flush=True)
        for pdf in pdfs:
            print("  ", pdf.name[:70], flush=True)
            recs.append(analyze_pdf(pdf))
        summ = summarize_journal(d.name, recs)
        all_summ.append(summ)
        raw[d.name] = {"summary": {k: v for k, v in summ.items() if k != "records"}, "papers": recs}
        md_parts.append(f"## {d.name}\n\n{summ['markdown']}")
        patched = patch_skill(d.name, summ["markdown"])
        print(f"  patched={patched} innov={summ.get('stats', {}).get('innovation')}", flush=True)

    OUT_MD.write_text("\n".join(md_parts), encoding="utf-8")
    OUT_JSON.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")

    # refresh batch overview
    lines = [
        "# Target-journal batch distill notes (2026-08)\n",
        "Full-text PDFs under `powergrid_benchmark/papers/literature/target_journal_related/fulltext_by_journal/<slug>/`.\n",
        "Deep notes: `metadata/journal_deep_distill_notes.md` + `metadata/journal_deep_distill.json`.\n",
        "Each `journals/<slug>/SKILL.md` has **Distilled deep structure & style** (pages/words/sections/paragraphs/formulas/figures/block-diagrams/abstract·conclusion craft/innovation mode).\n",
        "\n## Counts & deep means\n",
        "| slug | n | pages | words | secs | figs | formulas | innov |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for s in all_summ:
        st = s.get("stats") or {}
        lines.append(
            f"| `{s['slug']}` | {s['n']} | {st.get('pages_mean', 0)} | {st.get('words_mean', 0)} | "
            f"{st.get('sections_mean', 0)} | {st.get('figures_mean', 0)} | {st.get('formulas_mean', 0)} | "
            f"{st.get('innovation', '')} |"
        )
    lines.append(
        "\n**Gaps:** KeAi / MDPI Machines may be <10 if publisher stampPDF 403 persists; "
        "prefer EuropePMC/arXiv/aria2 mirrors.\n"
    )
    BATCH_MD.write_text("\n".join(lines), encoding="utf-8")
    print("wrote", OUT_MD, flush=True)
    print("wrote", OUT_JSON, flush=True)
    print("wrote", BATCH_MD, flush=True)


if __name__ == "__main__":
    main()
