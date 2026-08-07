"""Filter dataset paper candidates to power-grid relevant reading lists."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from search_dataset_benchmark_papers import OUT_ROOT, reconstruct_abstract


META = OUT_ROOT / "metadata"
RAW = META / "openalex_raw"
INPUT = META / "dataset_paper_candidates.csv"
FILTERED = META / "dataset_paper_candidates_filtered.csv"
SUMMARY = META / "dataset_paper_summary.csv"
DOWNLOAD_LOG = META / "download_log_filtered.csv"


DOMAIN_TERMS = [
    "power",
    "electric",
    "electricity",
    "grid",
    "opf",
    "load flow",
    "optimal power flow",
    "unit commitment",
    "transmission",
    "distribution",
    "voltage",
    "reactive",
    "frequency",
    "renewable",
    "solar",
    "wind",
    "photovoltaic",
    "microgrid",
    "energy",
    "charging",
    "ev ",
    "electric vehicle",
    "pmu",
    "phasor",
    "transformer",
    "dga",
    "dissolved gas",
    "reliability",
    "outage",
    "lmp",
    "market",
    "irradiance",
    "weather",
    "forecast",
    "battery",
    "lithium",
    "soh",
    "soc",
    "rul",
    "bess",
    "energy storage",
    "fcr",
    "afrr",
    "capacity factor",
]


AMBIGUOUS_DATASETS = {"gridstage", "dgann_duval", "dgadb", "lbnl_pmu_event_library", "psml"}


EXCLUDE_TERMS = [
    "neuron",
    "neurons",
    "visual cortex",
    "reservoir area",
    "entrepreneurial",
    "online learning application",
    "climate change education",
    "beam deflection transmission electron",
]


def load_abstracts() -> dict[str, str]:
    abstracts: dict[str, str] = {}
    for path in RAW.glob("*.json"):
        try:
            works = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        for work in works:
            work_id = work.get("id") or ""
            if work_id and work_id not in abstracts:
                abstracts[work_id] = reconstruct_abstract(work.get("abstract_inverted_index"))
    return abstracts


def relevant(row: dict[str, str], abstract: str) -> tuple[bool, str]:
    title_abstract = " ".join([row.get("title", ""), abstract]).lower()
    text = " ".join([row.get("title", ""), row.get("source", ""), row.get("matched_aliases", ""), abstract]).lower()
    if any(term in text for term in EXCLUDE_TERMS):
        return False, "excluded_by_non_power_domain_terms"
    dataset_id = row["dataset_id"]
    if dataset_id in AMBIGUOUS_DATASETS:
        if dataset_id in {"dgann_duval", "dgadb"}:
            has_dga_context = any(term in title_abstract for term in ["dga", "dissolved gas", "duval", "transformer"])
            has_fault_context = any(term in title_abstract for term in ["fault", "diagnosis", "insulation", "transformer"])
            if not (has_dga_context and has_fault_context):
                return False, "missing_transformer_dga_context"
        elif dataset_id == "gridstage":
            has_dataset_context = "gridstage" in title_abstract or "synthetic pmu" in title_abstract
            has_grid_context = any(term in title_abstract for term in ["pmu", "phasor", "power grid", "grid disturbance"])
            if not (has_dataset_context and has_grid_context):
                return False, "missing_gridstage_pmu_context"
        elif dataset_id == "lbnl_pmu_event_library":
            has_pmu = any(term in title_abstract for term in ["pmu", "phasor"])
            has_event = any(term in title_abstract for term in ["event", "disturbance", "fault", "power grid"])
            if not (has_pmu and has_event):
                return False, "missing_lbnl_pmu_event_context"
        elif dataset_id == "psml":
            has_power_ts = any(term in title_abstract for term in ["power", "grid", "load", "renewable", "energy"])
            has_ml_or_forecast = any(term in title_abstract for term in ["forecast", "time series", "machine learning", "reasoning"])
            if not (has_power_ts and has_ml_or_forecast):
                return False, "missing_psml_power_timeseries_context"
    if any(term in text for term in DOMAIN_TERMS):
        return True, "power_domain_term_match"
    return False, "missing_power_domain_term"


def write_summary(rows: list[dict[str, str]]) -> None:
    by_dataset: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        by_dataset.setdefault(row["dataset_id"], []).append(row)
    summary_rows = []
    for dataset_id, group in sorted(by_dataset.items()):
        summary_rows.append(
            {
                "dataset_id": dataset_id,
                "candidate_count": len(group),
                "sci_journal_candidates": sum(1 for r in group if r["venue_bucket"] == "sci_journal_candidate"),
                "ccf_conference_candidates": sum(1 for r in group if r["venue_bucket"] == "ccf_conference_candidate"),
                "downloaded_pdfs": sum(1 for r in group if r.get("pdf_path")),
            }
        )
    with SUMMARY.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["dataset_id", "candidate_count", "sci_journal_candidates", "ccf_conference_candidates", "downloaded_pdfs"],
        )
        writer.writeheader()
        writer.writerows(summary_rows)

    lines = [
        "# Dataset Benchmark Paper Search",
        "",
        "- Search window: `2023-07-09` to `2026-07-09`.",
        "- Source: OpenAlex works API full-text metadata search.",
        "- Scope: existing local public power-grid datasets.",
        "- Download policy: only open-access/public PDFs were downloaded; paywalled PDFs were not fetched.",
        "- SCI/CCF status is a candidate label and must be verified against WoS/JCR and the current CCF list.",
        "- `metadata/dataset_paper_candidates.csv` is the raw candidate set.",
        "- `metadata/dataset_paper_candidates_filtered.csv` is the power-grid reading list.",
        "",
        "## Filtered Summary",
        "",
        "| Dataset | Candidates | SCI journal candidates | CCF conference candidates | Downloaded PDFs |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in summary_rows:
        lines.append(
            f"| `{row['dataset_id']}` | {row['candidate_count']} | {row['sci_journal_candidates']} | {row['ccf_conference_candidates']} | {row['downloaded_pdfs']} |"
        )
    (OUT_ROOT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    abstracts = load_abstracts()
    with INPUT.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    fields = list(rows[0].keys()) + ["domain_relevance", "domain_relevance_reason"] if rows else []
    filtered: list[dict[str, str]] = []
    for row in rows:
        abstract = abstracts.get(row.get("openalex_id", ""), "")
        is_relevant, reason = relevant(row, abstract)
        row["domain_relevance"] = "yes" if is_relevant else "no"
        row["domain_relevance_reason"] = reason
        if is_relevant:
            filtered.append(row)

    with FILTERED.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(filtered)

    with DOWNLOAD_LOG.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["dataset_id", "title", "pdf_path", "pdf_source_url"])
        writer.writeheader()
        for row in filtered:
            if row.get("pdf_path"):
                writer.writerow(
                    {
                        "dataset_id": row["dataset_id"],
                        "title": row["title"],
                        "pdf_path": row["pdf_path"],
                        "pdf_source_url": row["pdf_source_url"],
                    }
                )

    write_summary(filtered)
    print(f"raw_rows: {len(rows)}")
    print(f"filtered_rows: {len(filtered)}")
    print(f"filtered_pdfs: {sum(1 for r in filtered if r.get('pdf_path'))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
