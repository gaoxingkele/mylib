"""Build ARA skeletons for the external dataset-benchmark paper collection."""

from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE_CSV = ROOT / "papers" / "literature" / "dataset_benchmark_papers" / "metadata" / "dataset_paper_candidates_filtered.csv"
COLLECTION_ROOT = ROOT / "ara_collections" / "dataset_benchmark_papers"
PAPERS_ROOT = COLLECTION_ROOT / "papers"


def slugify(text: str, limit: int = 80) -> str:
    text = text.lower().strip()
    text = re.sub(r"https?://", "", text)
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    text = re.sub(r"_+", "_", text)
    return (text[:limit].strip("_") or "paper")


def normalize_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()


def dedupe_key(row: dict[str, str]) -> str:
    # DOI/OpenAlex metadata can be incomplete or duplicated; title is the most stable
    # key for this harvested reading list.
    return normalize_title(row["title"])


def csv_escape_list(values: list[str]) -> str:
    return "; ".join(sorted(v for v in set(values) if v))


def read_rows() -> list[dict[str, str]]:
    with SOURCE_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def merge_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[dedupe_key(row)].append(row)

    merged: list[dict[str, str]] = []
    for _, group in grouped.items():
        # Prefer rows with DOI, then PDF, then higher relevance score.
        group = sorted(
            group,
            key=lambda r: (
                bool(r.get("doi")),
                bool(r.get("pdf_path")),
                float(r.get("relevance_score") or 0),
            ),
            reverse=True,
        )
        base = dict(group[0])
        base["dataset_id"] = csv_escape_list([r["dataset_id"] for r in group])
        base["dataset_category"] = csv_escape_list([r["dataset_category"] for r in group])
        base["dataset_tasks"] = csv_escape_list([r["dataset_tasks"] for r in group])
        base["matched_aliases"] = csv_escape_list([r["matched_aliases"] for r in group])
        base["all_openalex_ids"] = csv_escape_list([r["openalex_id"] for r in group])
        base["all_pdf_paths"] = csv_escape_list([r["pdf_path"] for r in group])
        merged.append(base)
    return sorted(merged, key=lambda r: (r["dataset_id"], r["title"]))


def paper_id(index: int, row: dict[str, str]) -> str:
    year = str(row.get("year") or "unknown")
    dataset = slugify(row["dataset_id"].split(";")[0], 32)
    title = slugify(row["title"], 64)
    return f"lit_{year}_{dataset}_{index:03d}_{title}"


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_paper_ara(pid: str, row: dict[str, str]) -> None:
    paper_dir = PAPERS_ROOT / pid
    yaml_title = row["title"].replace('"', '\\"')
    for subdir in [
        "logic/solution",
        "src/code",
        "src/configs",
        "trace",
        "evidence/source",
        "evidence/runs",
        "evidence/tables",
        "evidence/figures",
    ]:
        (paper_dir / subdir).mkdir(parents=True, exist_ok=True)

    metadata = {
        **row,
        "paper_id": pid,
        "collection": "dataset_benchmark_papers",
        "collection_status": "external_literature_collection",
        "ownership_status": "external_paper_not_project_original",
        "created_date": date.today().isoformat(),
    }
    write_text(paper_dir / "metadata.json", json.dumps(metadata, ensure_ascii=False, indent=2) + "\n")

    write_text(
        paper_dir / "PAPER.md",
        f"""---
title: "{yaml_title}"
year: {row.get('year') or 'null'}
collection: "dataset_benchmark_papers"
collection_status: "external_literature_collection"
ownership_status: "external_paper_not_project_original"
dataset_ids: "{row['dataset_id']}"
---

# {row['title']}

## Collection Mark

- Paper ID: `{pid}`
- Collection: `dataset_benchmark_papers`
- Collection Status: `external_literature_collection` / 外部论文集
- Ownership Status: `external_paper_not_project_original`
- Note: This artifact is not one of the two project-owned original papers marked `original_pending_publication`.

## Bibliographic Metadata

- Year: {row.get('year') or 'Not specified in provided sources'}
- Publication date: {row.get('publication_date') or 'Not specified in provided sources'}
- Venue/source: {row.get('source') or 'Not specified in provided sources'}
- Venue bucket: `{row.get('venue_bucket') or 'not_classified'}`
- DOI: {row.get('doi') or 'Not specified in provided sources'}
- OpenAlex: {row.get('openalex_id') or row.get('all_openalex_ids') or 'Not specified in provided sources'}
- OA status: {row.get('oa_status') or 'Not specified in provided sources'}

## Dataset Link

- Matched dataset(s): `{row['dataset_id']}`
- Dataset category: {row.get('dataset_category') or 'Not specified in provided sources'}
- Matched aliases: {row.get('matched_aliases') or 'Not specified in provided sources'}
- Dataset tasks: {row.get('dataset_tasks') or 'Not specified in provided sources'}

## Artifact Links

- Local PDF: `{row.get('pdf_path') or 'Not downloaded or not openly available'}`
- Source URL: {row.get('landing_page') or row.get('oa_url') or row.get('doi') or 'Not specified in provided sources'}
- Local code: see `src/code/README.md`.

## Reproduction Status

Scaffolded from metadata and available PDF/code links. Full method extraction, environment repair, and reproduction remain pending.
""",
    )

    write_text(
        paper_dir / "logic" / "problem.md",
        f"""# Problem Layer

This external paper is included because it was found in the dataset-centered literature harvest for power-grid benchmark datasets.

## Benchmark Relevance

- Dataset(s): `{row['dataset_id']}`
- Mention evidence: {row.get('mention_evidence') or 'Not specified in provided sources'}
- Comparison signal: {row.get('comparison_signal') or 'Not specified in provided sources'}

## Current Gaps

- Exact experiment tables and figures have not yet been extracted into this ARA.
- Full reproduction dependencies are not yet validated.
- SCI/CCF status is a candidate label until manually checked against WoS/JCR or the CCF list.
""",
    )

    write_text(
        paper_dir / "logic" / "claims.md",
        f"""# Claims

| Claim ID | Claim | Status | Proof |
|---|---|---|---|
| C1 | This external paper is a candidate power-grid dataset benchmark paper linked to `{row['dataset_id']}`. | Metadata-supported | E1 |
| C2 | The artifact is part of the external literature collection and is not a project-owned original paper. | User-policy-supported | E2 |

Scientific claims from the paper are not yet extracted. Add exact claims only after reading the full paper and grounding them in evidence files.
""",
    )

    write_text(
        paper_dir / "logic" / "concepts.md",
        f"""# Concepts

| Concept | Definition | Source |
|---|---|---|
| Dataset-linked benchmark paper | A paper that mentions or uses at least one dataset from the local public dataset pool. | Literature harvest metadata |
| External literature collection | A reproducibility-oriented ARA set for papers authored outside this benchmark project. | User instruction |
| Matched dataset | `{row['dataset_id']}` | `dataset_paper_candidates_filtered.csv` |
""",
    )

    write_text(
        paper_dir / "logic" / "experiments.md",
        """# Experiments

| Experiment ID | Purpose | Config | Evidence | Status |
|---|---|---|---|---|
| E1 | Verify that the paper uses or compares against the matched dataset. | Read full paper; extract dataset mentions, tables, figures, and benchmark setup. | `evidence/source/source_overview.md` | Planned |
| E2 | Locate and validate official or author-provided code. | Inspect `src/code/README.md`; clone status in collection manifest. | `src/code/README.md` | Planned |
| E3 | Reproduce core reported experiment. | To be derived from paper/code after environment audit. | `evidence/runs/` | Planned |
""",
    )

    write_text(
        paper_dir / "logic" / "related_work.md",
        f"""# Related Work

This ARA belongs to the dataset benchmark literature layer.

- Dataset relation: `{row['dataset_id']}`
- Venue/source: {row.get('source') or 'Not specified in provided sources'}
- DOI: {row.get('doi') or 'Not specified in provided sources'}

Typed relationships to project-owned original papers are not yet established.
""",
    )

    write_text(
        paper_dir / "logic" / "solution" / "constraints.md",
        """# Constraints

- Do not treat paywalled PDFs as locally available unless an open version exists.
- Do not infer code availability from paper title alone.
- Do not mark this paper as `original_pending_publication`; it is external literature.
- Exact numerical results must be copied into `evidence/`, not guessed from metadata.
""",
    )

    write_text(
        paper_dir / "logic" / "solution" / "method.md",
        """# Method

Not extracted yet. Fill after reading the paper and any available code repository.
""",
    )

    write_text(
        paper_dir / "src" / "environment.md",
        """# Environment

Not specified in provided sources.

## Code Status

See `src/code/README.md` and the collection-level `code_harvest_manifest.csv`.
""",
    )

    write_text(
        paper_dir / "src" / "code" / "README.md",
        """# Code

No confirmed local code repository has been attached yet.

If a public GitHub repository is found, clone it under this directory or record it in
the collection-level code manifest with a confidence note.
""",
    )

    write_text(
        paper_dir / "evidence" / "README.md",
        f"""# Evidence

## Source Evidence

- Candidate metadata: `papers/literature/dataset_benchmark_papers/metadata/dataset_paper_candidates_filtered.csv`
- Local PDF: `{row.get('pdf_path') or 'Not downloaded or not openly available'}`
- DOI: {row.get('doi') or 'Not specified in provided sources'}
- Landing page: {row.get('landing_page') or 'Not specified in provided sources'}
- OA URL: {row.get('oa_url') or 'Not specified in provided sources'}

## Pending Evidence Extraction

- Tables: not extracted.
- Figures: not extracted.
- Exact benchmark settings: not extracted.
- Exact result numbers: not extracted.
""",
    )

    write_text(
        paper_dir / "evidence" / "source" / "source_overview.md",
        f"""# Source Overview

## Paper

- Title: {row['title']}
- Source: {row.get('source') or 'Not specified in provided sources'}
- Local PDF: `{row.get('pdf_path') or 'Not downloaded or not openly available'}`

## Dataset Match

- Dataset(s): `{row['dataset_id']}`
- Matched aliases: {row.get('matched_aliases') or 'Not specified in provided sources'}

## Code

Not confirmed at scaffold time. See `src/code/README.md`.
""",
    )

    write_text(
        paper_dir / "trace" / "exploration_tree.yaml",
        f"""version: 1
paper_id: {pid}
collection: dataset_benchmark_papers
nodes:
  - id: root
    type: import
    status: done
    provenance: ai-executed
    support_level: explicit
    summary: "Create external literature ARA scaffold from dataset-centered paper harvest."
    children:
      - metadata_import
      - pdf_status
      - code_search_pending
  - id: metadata_import
    type: evidence
    status: done
    provenance: ai-executed
    support_level: explicit
    summary: "Imported bibliographic and dataset-link metadata from filtered candidate CSV."
    children: []
  - id: pdf_status
    type: evidence
    status: {"done" if row.get("pdf_path") else "blocked"}
    provenance: ai-executed
    support_level: explicit
    summary: "Local PDF status recorded as: {row.get('pdf_path') or 'not openly downloaded'}."
    children: []
  - id: code_search_pending
    type: decision
    status: open
    provenance: ai-suggested
    support_level: inferred
    summary: "Search for public GitHub code and attach only high-confidence matches."
    children: []
""",
    )


def write_collection_index(rows: list[dict[str, str]]) -> None:
    COLLECTION_ROOT.mkdir(parents=True, exist_ok=True)
    manifest_fields = [
        "paper_id",
        "title",
        "year",
        "dataset_id",
        "source",
        "venue_bucket",
        "doi",
        "openalex_id",
        "pdf_path",
        "ara_path",
        "collection_status",
        "ownership_status",
        "code_status",
        "code_path",
        "code_url",
    ]
    with (COLLECTION_ROOT / "collection_manifest.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=manifest_fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in manifest_fields})

    lines = [
        "# Dataset Benchmark Paper ARA Collection",
        "",
        "This directory contains external-literature ARA scaffolds for papers that mention or use the local public power-grid dataset pool.",
        "",
        "## Collection Policy",
        "",
        "- Collection status: `external_literature_collection` / 外部论文集.",
        "- Ownership status: `external_paper_not_project_original`.",
        "- These papers are not the two project-owned papers marked `original_pending_publication`.",
        "- Paywalled papers are represented by metadata and DOI only unless an open version exists.",
        "- GitHub code is attached only when a public repository can be found with sufficient confidence.",
        "",
        "## Counts",
        "",
        f"- ARA paper scaffolds: {len(rows)}",
        f"- With local PDF: {sum(1 for r in rows if r.get('pdf_path'))}",
        "",
        "## Files",
        "",
        "- `collection_manifest.csv`: one row per external paper ARA.",
        "- `code_harvest_manifest.csv`: generated by `scripts/literature/harvest_literature_code.py`.",
        "- `papers/<paper_id>/`: one ARA scaffold per paper.",
    ]
    write_text(COLLECTION_ROOT / "README.md", "\n".join(lines) + "\n")


def main() -> int:
    rows = merge_rows(read_rows())
    output_rows: list[dict[str, str]] = []
    for index, row in enumerate(rows, start=1):
        pid = paper_id(index, row)
        build_paper_ara(pid, row)
        out = dict(row)
        out["paper_id"] = pid
        out["ara_path"] = str((PAPERS_ROOT / pid).relative_to(ROOT)).replace("\\", "/")
        out["collection_status"] = "external_literature_collection"
        out["ownership_status"] = "external_paper_not_project_original"
        out["code_status"] = "not_searched"
        out["code_path"] = ""
        out["code_url"] = ""
        output_rows.append(out)
    write_collection_index(output_rows)
    print(f"ara_scaffolds: {len(output_rows)}")
    print(f"with_pdf: {sum(1 for r in output_rows if r.get('pdf_path'))}")
    print(f"output: {COLLECTION_ROOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
