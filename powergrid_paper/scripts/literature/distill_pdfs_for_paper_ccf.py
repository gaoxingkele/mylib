"""Distill local dataset-benchmark PDFs into journal-skill evidence notes."""
from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(r"D:/aicoding/powergrid_benchmark")
PDF_ROOT = ROOT / "papers/literature/dataset_benchmark_papers/pdfs"
OUT = Path(r"C:/Users/10175/.claude/skills/Paper_CCF/resources/powergrid-open-data-corpus-distill.md")
META = ROOT / "papers/literature/dataset_benchmark_papers/metadata"

TOPIC_RULES = [
    ("load_forecasting", r"load forecast|electricity demand|time.?series forecast|informer|autoformer|timesnet|patchtst|dlinear"),
    ("opf_learning", r"optimal power flow|opf|unit commitment|pglib|pglearn|matpower"),
    ("rl_grid", r"grid2op|l2rpn|reinforcement learning|topology control"),
    ("battery", r"battery|soh|soc|rul|lithium|degradation|bess"),
    ("ev_charging", r"electric vehicle|ev charging|acn-|vehicle.to.grid|v2g"),
    ("wind_solar", r"wind power|solar irradiance|nsrdb|sdwpf|photovoltaic|renewable"),
    ("theft_anomaly", r"electricity theft|anomaly detection|non.?technical loss"),
    ("pmu_event", r"pmu|phasor|event detection|cascading"),
    ("dga", r"dissolved gas|transformer.*fault|dga"),
    ("resilience", r"resilience|contingency|n-1|cascading failure"),
]


def text_of(pdf: Path, max_pages: int = 4) -> str:
    try:
        r = PdfReader(str(pdf))
        parts = []
        for i, page in enumerate(r.pages[:max_pages]):
            parts.append(page.extract_text() or "")
        return "\n".join(parts)
    except Exception as exc:
        return f"[extract_error] {exc}"


def classify(text: str) -> list[str]:
    low = text.lower()
    hits = []
    for name, pat in TOPIC_RULES:
        if re.search(pat, low, re.I):
            hits.append(name)
    return hits or ["other"]


def flags(text: str) -> dict:
    low = text.lower()
    return {
        "public_dataset_mention": bool(re.search(r"open.?source|public(ly)? available|github\.com|zenodo|ieee dataport|uci |kaggle", low)),
        "baseline_compare": bool(re.search(r"baseline|compare(d|s|ison)? (with|to|against)|benchmark", low)),
        "ablation": bool(re.search(r"ablation|component analysis|sensitivity analysis", low)),
        "metrics_named": bool(re.search(r"\b(mae|rmse|mape|mse|f1|auc|accuracy)\b", low)),
        "real_grid_case": bool(re.search(r"ieee \d+|matpower|simbench|rts-gmlc|pglib|activsg|real.?world", low)),
        "code_release": bool(re.search(r"code (is |will be )?available|open.?source code|github\.com/.+/", low)),
        "limitation_section": bool(re.search(r"limitation|future work|threats to validity", low)),
        "numbered_contrib": bool(re.search(r"contribution(s)?\s*(:|are|of this)|we (make|claim) the following", low)),
    }


def main() -> None:
    # unique digests
    seen = set()
    uniq: list[Path] = []
    for p in sorted(PDF_ROOT.rglob("*.pdf")):
        dig = p.stem.split("__")[-1]
        if dig in seen:
            continue
        seen.add(dig)
        uniq.append(p)

    rows = []
    topic_counter = Counter()
    flag_counter = Counter()
    for p in uniq:
        txt = text_of(p)
        topics = classify(txt)
        fl = flags(txt)
        for t in topics:
            topic_counter[t] += 1
        for k, v in fl.items():
            if v:
                flag_counter[k] += 1
        title = p.stem.split("__")[1] if "__" in p.stem else p.stem
        rows.append(
            {
                "file": str(p.relative_to(ROOT)).replace("\\", "/"),
                "title_guess": title.replace("_", " ")[:120],
                "topics": topics,
                "flags": fl,
                "chars": len(txt),
                "snippet": re.sub(r"\s+", " ", txt)[:350],
            }
        )

    # journal routing hints from curated exemplars
    oa_targets = Counter()
    curated = META / "dataset_direction_sci_exemplars_curated.csv"
    if curated.exists():
        for r in csv.DictReader(curated.open(encoding="utf-8-sig")):
            for t in (r.get("oa_sci_targets") or "").split(";"):
                t = t.strip()
                if t:
                    oa_targets[t] += 1

    lines = []
    lines.append("# Power-grid open-data corpus distill (local PDF cache)")
    lines.append("")
    lines.append("Source: `powergrid_benchmark/papers/literature/dataset_benchmark_papers/pdfs/`")
    lines.append(f"As-of: 2026-07-27 · Unique PDFs analyzed: **{len(uniq)}** (of 245 files; deduped by content digest).")
    lines.append("Extraction: first ≤4 pages via pypdf (front-matter bias). Use as **routing/evidence heuristics**, not as WoS-verified journal acceptance rates.")
    lines.append("")
    lines.append("## Topic mix")
    lines.append("")
    for t, c in topic_counter.most_common():
        lines.append(f"- `{t}`: {c}")
    lines.append("")
    lines.append("## Front-matter signal rates (unique PDFs)")
    lines.append("")
    n = len(uniq) or 1
    for k, c in flag_counter.most_common():
        lines.append(f"- **{k}**: {c}/{n} ({100*c/n:.0f}%)")
    lines.append("")
    lines.append("## OA SCI targets named in curated dataset→journal map")
    lines.append("")
    for t, c in oa_targets.most_common(20):
        lines.append(f"- {t}: {c} dataset rows")
    lines.append("")
    lines.append("## Distilled acceptance patterns for Paper_CCF OA journals")
    lines.append("")
    lines.append("### Shared patterns across this corpus (power × ML / open data)")
    lines.append("")
    lines.append("1. **Public benchmark naming is a first-class contribution signal.** High-fit papers explicitly name ETT/Informer, ACN-Data, NASA PCoE, SDWPF, PGLib-OPF, Grid2Op/L2RPN, MATPOWER/SimBench — and state train/test protocol. Anonymous “a utility dataset” without a release path is weaker for IEEE Access / Energies / Scientific Reports.")
    lines.append("2. **Baselines are genre-dependent.** Forecasting/theft papers almost always list named baselines + MAE/RMSE/MAPE or F1/AUC. OPF/RL/planning papers often pass on case-study self-comparison (IEEE-bus / scenario schemes) without a long DL baseline table.")
    lines.append("3. **Ablation/sensitivity is uneven.** Present in ~strong forecasting & hybrid-method papers; often absent in survey/framework and pure case studies — Energies historically still accepts those if energy application + validation exist.")
    lines.append("4. **Code/data availability statements are common in arXiv/open-data lines; rare as runnable artifacts.** For OA journals, a Data Availability Statement + DOI/GitHub link is enough; artifact badges are optional.")
    lines.append("5. **Numbered contribution lists (3–5 bullets)** appear frequently in IEEE-Access-style and applied-energy framing even when novelty is incremental.")
    lines.append("6. **Topic→OA journal routing observed in curated map:** load/price/wind/solar forecast → Energies / Energy Reports / IEEE Access; OPF/learning-OPF/GNN → IEEE Access / Energies; battery SOH → IEEE Access / Energies / Electronics; EV/ACN → Energies / IEEE Access (+ WEVJ outside this skill set); theft → Scientific Reports / IEEE Access; PMU/event → IEEE Access / Electronics / Sensors; resilience/planning with SDG narrative → Sustainability / Energies.")
    lines.append("")
    lines.append("### Per-journal skill updates implied by this corpus")
    lines.append("")
    lines.append("| Journal skill | What this corpus adds |")
    lines.append("|---|---|")
    lines.append("| `ieee-access` | Open power benchmarks (ETT, NASA, ACN, PGLib) + numbered contributions + baseline tables without significance tests remain the norm for DL; private utility data still OK if protocol disclosed. |")
    lines.append("| `mdpi-energies` | Strongest catch-all for energy-applied forecasting, DER, BESS markets, SimBench/Ausgrid-style studies; sensitivity preferred; public dataset citation strengthens reproducibility claims. |")
    lines.append("| `mdpi-electronics` | Fits PMU/event, DGA/transformer diagnosis, embedded/edge metering ML when EE hardware/signal angle is explicit. |")
    lines.append("| `mdpi-applied-sciences` | Application-first case studies (utility planning, field metering) can substitute heavy algorithmic novelty. |")
    lines.append("| `mdpi-sustainability` | Only when renewable integration / DR / planning papers quantify sustainability/SDG impact — not pure MAE tables. |")
    lines.append("| `mdpi-sensors` | PMU / IoT sensing / condition monitoring must be the core, not a side dataset. |")
    lines.append("| `elsevier-energy-reports` | AI-for-energy forecasting/optimization with energy contribution in front; natural Q1 OA companion to Energy/Applied Energy. |")
    lines.append("| `frontiers-energy-research` | Route via Smart Grids / Energy Systems sections for BESS balancing, DR, grid optimization. |")
    lines.append("| `nature-scientific-reports` | Soundness megajournal path for theft/anomaly and cross-domain ML-on-grid; Nature OA PDF examples exist in corpus (theft, SDWPF→Scientific Data sibling). |")
    lines.append("| `ieee-oajpe` / `csee-jpes` / `pcmp` | Prefer when contribution is power-system-first (planning/ops/protection) rather than generic DL-on-ETT. |")
    lines.append("")
    lines.append("## Sample inventory (unique digests)")
    lines.append("")
    lines.append("| Topics | Title (from filename) | Public-data | Baselines | Metrics |")
    lines.append("|---|---|:---:|:---:|:---:|")
    for r in rows:
        fl = r["flags"]
        lines.append(
            f"| {', '.join(r['topics'][:3])} | {r['title_guess'][:70]} | "
            f"{'Y' if fl['public_dataset_mention'] else ''} | "
            f"{'Y' if fl['baseline_compare'] else ''} | "
            f"{'Y' if fl['metrics_named'] else ''} |"
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    # also dump json for debugging
    (META / "powergrid_open_data_corpus_distill.json").write_text(
        json.dumps({"n": len(uniq), "topics": topic_counter, "flags": flag_counter, "rows": rows}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"wrote {OUT}")
    print("topics", dict(topic_counter.most_common()))
    print("flags", dict(flag_counter))


if __name__ == "__main__":
    main()
