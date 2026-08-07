"""Harvest recent target-journal papers related to the six planned manuscripts.

Targets:
- Energies
- Applied Sciences
- Electronics
- IEEE Access

The script searches OpenAlex for recent papers, downloads openly exposed PDFs
when available, builds per-paper ARA scaffolds, and writes a comparison report.
"""

from __future__ import annotations

import csv
import argparse
import hashlib
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT_ROOT = ROOT / "papers" / "literature" / "target_journal_related"
META_DIR = OUT_ROOT / "metadata"
PDF_DIR = OUT_ROOT / "pdfs"
ARA_ROOT = ROOT / "ara_collections" / "target_journal_related"
ARA_PAPERS = ARA_ROOT / "papers"
OPENALEX = "https://api.openalex.org/works"
CROSSREF = "https://api.crossref.org/works"
USER_AGENT = "powergrid-benchmark-target-journal-harvester/0.1"


JOURNALS = {
    "energies": {
        "display_name": "Energies",
        "source_id": "S198098182",
        "issn": "1996-1073",
        "publisher": "MDPI",
    },
    "applied_sciences": {
        "display_name": "Applied Sciences",
        "source_id": "S4210205812",
        "issn": "2076-3417",
        "publisher": "MDPI",
    },
    "electronics": {
        "display_name": "Electronics",
        "source_id": "S4210202905",
        "issn": "2079-9292",
        "publisher": "MDPI",
    },
    "ieee_access": {
        "display_name": "IEEE Access",
        "source_id": "S2485537415",
        "issn": "2169-3536",
        "publisher": "IEEE",
    },
}


TOPICS = {
    "p1_twin_gru_dispatch": {
        "planned_title": "Digital Twin-Driven Siamese GRU for Load-Aware Multi-Objective Power Grid Dispatch Optimization",
        "queries": [
            "power grid dispatch GRU",
            "power system dispatch digital twin",
            "load-aware dispatch optimization",
            "unit commitment neural network dispatch",
            "multi-objective power grid dispatch",
        ],
        "method_terms": ["gru", "lstm", "recurrent", "digital twin", "dispatch", "unit commitment", "optimization"],
        "task_terms": ["dispatch", "unit commitment", "economic dispatch", "optimal power flow", "load"],
    },
    "p2_hyperbolic_gcn_smart_dispatch": {
        "planned_title": "Graph Convolutional Network Based on Hyperbolic Space for Power Load Forecasting in Smart Dispatch Systems",
        "queries": [
            "power load forecasting graph convolutional network",
            "power load forecasting hyperbolic graph",
            "smart grid load forecasting GCN",
            "spatio-temporal graph neural network load forecasting",
            "power load forecasting transformer graph",
        ],
        "method_terms": ["graph convolution", "gcn", "graph neural", "hyperbolic", "transformer", "lstm", "forecast"],
        "task_terms": ["load forecasting", "smart grid", "dispatch", "power load", "forecasting"],
    },
    "p3_self_adaptive_mode_distribution_planning": {
        "planned_title": "Power Distribution Network Planning Strategy Optimization Based on a Self-Adaptive Multi-Objective Differential Evolution Algorithm",
        "queries": [
            "distribution network planning multi-objective differential evolution",
            "distribution network planning multi-objective optimization",
            "distributed generation planning differential evolution",
            "power distribution network planning evolutionary algorithm",
            "distribution network expansion planning optimization",
        ],
        "method_terms": ["differential evolution", "multi-objective", "evolutionary", "nsga", "planning", "optimization"],
        "task_terms": ["distribution network planning", "expansion planning", "distributed generation", "hosting capacity", "planning"],
    },
    "p4_resilience_distribution_planning": {
        "planned_title": "Resilience-Oriented Distribution Network Planning with Hybrid Multi-Objective Evolution and Scenario-Based DER Uncertainty",
        "queries": [
            "resilience distribution network planning multi-objective",
            "resilient distribution network planning DER uncertainty",
            "distribution network planning renewable uncertainty",
            "resilience-oriented distribution network optimization",
            "distribution network resilience evolutionary algorithm",
        ],
        "method_terms": ["resilience", "multi-objective", "evolutionary", "scenario", "uncertainty", "optimization"],
        "task_terms": ["distribution network", "planning", "resilience", "DER", "renewable", "uncertainty"],
    },
    "p5_hybrid_moea_feasibility_review": {
        "planned_title": "Investment Effectiveness Optimization Strategy Based on Hybrid Multi-Objective Evolution for Power Grid Feasibility Review",
        "queries": [
            "power grid investment effectiveness optimization",
            "power grid project investment multi-objective optimization",
            "power grid feasibility review investment decision",
            "electric power investment planning multi-criteria",
            "grid investment portfolio optimization reliability",
        ],
        "method_terms": ["investment", "portfolio", "multi-objective", "multi-criteria", "feasibility", "optimization"],
        "task_terms": ["investment", "feasibility", "project", "planning", "portfolio", "reliability"],
    },
    "p6_nsga_bls_feasibility_review": {
        "planned_title": "A Non-Dominated Sorting and Bidirectional Local Search Multi-Objective Evolution Algorithm for Investment Effectiveness Review of Power Grid Projects",
        "queries": [
            "non-dominated sorting power grid investment",
            "NSGA power grid planning investment",
            "multi-objective evolutionary algorithm power grid project planning",
            "local search multi-objective power system planning",
            "power grid project portfolio optimization NSGA",
        ],
        "method_terms": ["non-dominated sorting", "nsga", "local search", "multi-objective", "evolutionary", "portfolio"],
        "task_terms": ["investment", "project", "planning", "portfolio", "power grid", "review"],
    },
}


DOMAIN_TERMS = [
    "power grid",
    "power system",
    "grid",
    "energy",
    "electric",
    "electricity",
    "load",
    "dispatch",
    "distribution",
    "transmission",
    "renewable",
    "microgrid",
    "voltage",
    "unit commitment",
    "optimal power flow",
    "grid-side",
    "vehicle-to-grid",
    "v2g",
]

NEGATIVE_TERMS = [
    "stock market",
    "spanish market",
    "uav trajectory",
    "enrollment",
    "curriculum",
    "medical",
    "image segmentation",
]


@dataclass
class HarvestRecord:
    topic_id: str
    topic_title: str
    journal_key: str
    journal: str
    paper_id: str
    title: str
    publication_date: str
    year: str
    doi: str
    openalex_id: str
    landing_page: str
    oa_url: str
    is_oa: str
    source_pdf_url: str
    pdf_path: str
    relevance_score: str
    cited_by_count: str
    method_hits: str
    task_hits: str
    query_hit: str


def http_json(url: str, retries: int = 3) -> dict[str, Any]:
    last: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            last = exc
            if exc.code in {429, 503}:
                time.sleep(45 * (attempt + 1))
                continue
            time.sleep(2 * (attempt + 1))
        except Exception as exc:
            last = exc
            time.sleep(2 * (attempt + 1))
    raise last or RuntimeError("unknown JSON fetch failure")


def crossref_json(url: str, retries: int = 3) -> dict[str, Any]:
    last: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": USER_AGENT + " (mailto:research@example.com)",
                },
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            last = exc
            if exc.code in {429, 503}:
                time.sleep(20 * (attempt + 1))
                continue
            time.sleep(2 * (attempt + 1))
        except Exception as exc:
            last = exc
            time.sleep(2 * (attempt + 1))
    raise last or RuntimeError("unknown Crossref fetch failure")


def http_bytes(url: str, retries: int = 2) -> tuple[bytes, str]:
    last: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=90) as resp:
                return resp.read(), resp.headers.get("Content-Type", "")
        except Exception as exc:
            last = exc
            time.sleep(2 * (attempt + 1))
    raise last or RuntimeError("unknown byte fetch failure")


def safe_slug(text: str, limit: int = 80) -> str:
    text = re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_")
    return (text[:limit].strip("_") or "paper").lower()


def normalize_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()


def reconstruct_abstract(inv: dict[str, list[int]] | None) -> str:
    if not inv:
        return ""
    max_pos = max(pos for positions in inv.values() for pos in positions)
    words = [""] * (max_pos + 1)
    for token, positions in inv.items():
        for pos in positions:
            words[pos] = token
    return " ".join(words)


def date_parts_to_str(parts: dict[str, Any] | None) -> tuple[str, str]:
    date_parts = (parts or {}).get("date-parts") or []
    if not date_parts or not date_parts[0]:
        return "", ""
    values = date_parts[0]
    year = str(values[0]) if len(values) >= 1 else ""
    month = f"{values[1]:02d}" if len(values) >= 2 else "01"
    day = f"{values[2]:02d}" if len(values) >= 3 else "01"
    return f"{year}-{month}-{day}", year


def search_openalex(
    topic_id: str,
    query: str,
    journal_key: str,
    from_date: str,
    to_date: str,
    per_query: int,
    cache_only: bool = False,
) -> list[dict[str, Any]]:
    journal = JOURNALS[journal_key]
    raw_path = META_DIR / "openalex_raw" / f"{topic_id}__{journal_key}__{safe_slug(query, 48)}.json"
    if raw_path.exists():
        return json.loads(raw_path.read_text(encoding="utf-8"))
    if cache_only:
        return []
    filters = ",".join(
        [
            f"from_publication_date:{from_date}",
            f"to_publication_date:{to_date}",
            f"primary_location.source.id:{journal['source_id']}",
            f'fulltext.search:"{query}"',
        ]
    )
    params = {
        "filter": filters,
        "per-page": str(per_query),
        "sort": "relevance_score:desc",
    }
    url = OPENALEX + "?" + urllib.parse.urlencode(params)
    data = http_json(url)
    works = data.get("results") or []
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(json.dumps(works, ensure_ascii=False, indent=2), encoding="utf-8")
    return works


def crossref_to_work(item: dict[str, Any], journal_key: str) -> dict[str, Any]:
    title = " ".join(item.get("title") or []) if isinstance(item.get("title"), list) else (item.get("title") or "")
    abstract = item.get("abstract") or ""
    pub_date, pub_year = date_parts_to_str(
        item.get("published-online") or item.get("published-print") or item.get("published")
    )
    doi = item.get("DOI") or ""
    url = item.get("URL") or (f"https://doi.org/{doi}" if doi else "")
    links = item.get("link") or []
    pdf_url = next((link.get("URL") for link in links if ".pdf" in (link.get("URL") or "").lower()), "")
    return {
        "id": f"https://doi.org/{doi}" if doi else url or normalize_title(title),
        "title": title,
        "crossref_abstract": abstract,
        "publication_date": pub_date,
        "publication_year": pub_year,
        "doi": f"https://doi.org/{doi}" if doi and not doi.startswith("http") else doi,
        "ids": {"doi": f"https://doi.org/{doi}" if doi and not doi.startswith("http") else doi},
        "cited_by_count": item.get("is-referenced-by-count") or 0,
        "relevance_score": 0,
        "primary_location": {
            "landing_page_url": url,
            "pdf_url": pdf_url,
            "source": {"display_name": JOURNALS[journal_key]["display_name"]},
        },
        "best_oa_location": {"pdf_url": pdf_url, "landing_page_url": url},
        "open_access": {"is_oa": bool(pdf_url), "oa_url": pdf_url or url},
    }


def search_crossref(
    topic_id: str,
    query: str,
    journal_key: str,
    from_date: str,
    to_date: str,
    per_query: int,
    cache_only: bool = False,
) -> list[dict[str, Any]]:
    journal = JOURNALS[journal_key]
    raw_path = META_DIR / "crossref_raw" / f"{topic_id}__{journal_key}__{safe_slug(query, 48)}.json"
    if raw_path.exists():
        return [crossref_to_work(item, journal_key) for item in json.loads(raw_path.read_text(encoding="utf-8"))]
    if cache_only:
        return []
    filters = ",".join(
        [
            f"issn:{journal['issn']}",
            f"from-pub-date:{from_date}",
            f"until-pub-date:{to_date}",
            "type:journal-article",
        ]
    )
    params = {
        "filter": filters,
        "query": query,
        "rows": str(per_query),
        "select": "DOI,title,published-print,published-online,published,container-title,URL,is-referenced-by-count,abstract,link",
    }
    url = CROSSREF + "?" + urllib.parse.urlencode(params)
    data = crossref_json(url)
    items = data.get("message", {}).get("items") or []
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    return [crossref_to_work(item, journal_key) for item in items]


def pdf_candidates(work: dict[str, Any]) -> list[str]:
    urls: list[str] = []
    for loc_key in ["best_oa_location", "primary_location"]:
        loc = work.get(loc_key) or {}
        for key in ["pdf_url", "landing_page_url"]:
            val = loc.get(key)
            if val and val not in urls:
                urls.append(val)
    oa_url = (work.get("open_access") or {}).get("oa_url")
    if oa_url and oa_url not in urls:
        urls.append(oa_url)
    doi = ((work.get("ids") or {}).get("doi") or work.get("doi") or "")
    mdpi_pdf = mdpi_res_pdf_url(doi)
    if mdpi_pdf and mdpi_pdf not in urls:
        urls.insert(0, mdpi_pdf)
    if "arxiv.org/abs/" in doi:
        urls.append(doi.replace("/abs/", "/pdf/"))
    return urls


def mdpi_res_pdf_url(doi: str) -> str:
    doi = doi.lower().replace("https://doi.org/", "").strip()
    if not doi.startswith("10.3390/"):
        return ""
    suffix = doi.split("/", 1)[1]
    match = re.fullmatch(r"([a-z]+)(\d{2})(\d{2})(\d+)", suffix)
    if not match:
        return ""
    doi_prefix, volume, _issue, article = match.groups()
    slug_map = {
        "app": "applsci",
        "applsci": "applsci",
        "en": "energies",
        "energies": "energies",
        "electronics": "electronics",
    }
    slug = slug_map.get(doi_prefix)
    if not slug:
        return ""
    article_id = str(int(article)).zfill(5)
    stem = f"{slug}-{int(volume)}-{article_id}"
    return f"https://mdpi-res.com/d_attachment/{slug}/{stem}/article_deploy/{stem}.pdf"


def resolve_pdf_url(url: str) -> str | None:
    if url.lower().endswith(".pdf") or "/pdf" in url.lower():
        return url
    if "arxiv.org/abs/" in url:
        return url.replace("/abs/", "/pdf/")
    try:
        data, content_type = http_bytes(url, retries=1)
    except Exception:
        return None
    if data[:4] == b"%PDF" or "pdf" in content_type.lower():
        return url
    text = data.decode("utf-8", errors="ignore")
    matches = re.findall(r'href=["\']([^"\']+\.pdf(?:\?[^"\']*)?)["\']', text, flags=re.I)
    if matches:
        return urllib.parse.urljoin(url, matches[0])
    return None


def download_pdf(work: dict[str, Any], topic_id: str, paper_slug: str) -> tuple[str, str]:
    for candidate in pdf_candidates(work):
        pdf_url = resolve_pdf_url(candidate)
        if not pdf_url:
            continue
        digest = hashlib.sha1(pdf_url.encode("utf-8")).hexdigest()[:10]
        out_dir = PDF_DIR / topic_id
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"{paper_slug[:96].strip('_')}__{digest}.pdf"
        if path.exists() and path.stat().st_size > 0:
            return str(path.relative_to(ROOT)).replace("\\", "/"), pdf_url
        try:
            data, content_type = http_bytes(pdf_url)
        except Exception:
            continue
        if data[:4] != b"%PDF" and "pdf" not in content_type.lower():
            continue
        path.write_bytes(data)
        return str(path.relative_to(ROOT)).replace("\\", "/"), pdf_url
    return "", ""


def is_domain_relevant(title: str, abstract: str) -> bool:
    text = f"{title} {abstract}".lower()
    if any(term in text for term in NEGATIVE_TERMS):
        return False
    return any(term in text for term in DOMAIN_TERMS)


def hits(terms: list[str], text: str) -> list[str]:
    text_l = text.lower()
    return [term for term in terms if term.lower() in text_l]


def within_date_window(publication_date: str, from_date: str, to_date: str) -> bool:
    try:
        value = date.fromisoformat(publication_date)
        lower = date.fromisoformat(from_date)
        upper = date.fromisoformat(to_date)
    except ValueError:
        return False
    return lower <= value <= upper


def topic_score(topic: dict[str, Any], title: str, abstract: str, query: str) -> int:
    text = f"{title} {abstract}".lower()
    method_score = 4 * len(hits(topic["method_terms"], text))
    task_score = 5 * len(hits(topic["task_terms"], text))
    query_terms = [term for term in re.split(r"[^a-z0-9]+", query.lower()) if len(term) >= 4]
    query_score = sum(1 for term in set(query_terms) if term in text)
    domain_score = sum(1 for term in DOMAIN_TERMS if term in text)
    title_bonus = 2 * sum(1 for term in topic["task_terms"] if term.lower() in title.lower())
    return method_score + task_score + query_score + domain_score + title_bonus


def collect(
    from_date: str,
    to_date: str,
    per_query: int,
    max_per_topic: int,
    cache_only: bool = False,
    no_download: bool = False,
    provider: str = "crossref",
) -> list[HarvestRecord]:
    records: dict[tuple[str, str], HarvestRecord] = {}
    for topic_id, topic in TOPICS.items():
        candidates: dict[str, tuple[dict[str, Any], str]] = {}
        for journal_key in JOURNALS:
            for query in topic["queries"]:
                print(f"search {topic_id} | {journal_key} | {query}")
                works: list[dict[str, Any]] = []
                if provider in {"openalex", "both"}:
                    try:
                        works.extend(search_openalex(topic_id, query, journal_key, from_date, to_date, per_query, cache_only=cache_only))
                    except Exception as exc:
                        print(f"  OpenAlex search failed: {type(exc).__name__}: {exc}")
                if provider in {"crossref", "both"}:
                    try:
                        works.extend(search_crossref(topic_id, query, journal_key, from_date, to_date, per_query, cache_only=cache_only))
                    except Exception as exc:
                        print(f"  Crossref search failed: {type(exc).__name__}: {exc}")
                for work in works:
                    key = work.get("id") or normalize_title(work.get("title") or "")
                    if key not in candidates:
                        candidates[key] = (work, query)
                time.sleep(0.1)

        ranked = sorted(
            candidates.values(),
            key=lambda pair: (
                topic_score(
                    topic,
                    pair[0].get("title") or "",
                    pair[0].get("crossref_abstract") or reconstruct_abstract(pair[0].get("abstract_inverted_index")),
                    pair[1],
                ),
                pair[0].get("cited_by_count") or 0,
                pair[0].get("publication_date") or "",
            ),
            reverse=True,
        )[:max_per_topic]

        for idx, (work, query) in enumerate(ranked, start=1):
            title = work.get("title") or ""
            abstract = work.get("crossref_abstract") or reconstruct_abstract(work.get("abstract_inverted_index"))
            if not within_date_window(work.get("publication_date") or "", from_date, to_date):
                continue
            if not is_domain_relevant(title, abstract):
                continue
            if topic_score(topic, title, abstract, query) < 10:
                continue
            source = ((work.get("primary_location") or {}).get("source") or {})
            journal_name = source.get("display_name") or ""
            journal_key = next((k for k, v in JOURNALS.items() if v["display_name"] == journal_name), "unknown")
            paper_slug = f"{topic_id}__{idx:02d}__{safe_slug(title, 80)}"
            pdf_path, pdf_url = ("", "")
            if not no_download:
                pdf_path, pdf_url = download_pdf(work, topic_id, paper_slug)
            text = f"{title} {abstract}"
            rec = HarvestRecord(
                topic_id=topic_id,
                topic_title=topic["planned_title"],
                journal_key=journal_key,
                journal=journal_name,
                paper_id=f"tj_{topic_id}_{idx:02d}_{safe_slug(title, 50)}",
                title=title,
                publication_date=work.get("publication_date") or "",
                year=str(work.get("publication_year") or ""),
                doi=(work.get("ids") or {}).get("doi") or work.get("doi") or "",
                openalex_id=work.get("id") or "",
                landing_page=((work.get("primary_location") or {}).get("landing_page_url") or ""),
                oa_url=((work.get("open_access") or {}).get("oa_url") or ""),
                is_oa=str((work.get("open_access") or {}).get("is_oa") or False).lower(),
                source_pdf_url=pdf_url,
                pdf_path=pdf_path,
                relevance_score=str(work.get("relevance_score") or 0),
                cited_by_count=str(work.get("cited_by_count") or 0),
                method_hits="; ".join(hits(topic["method_terms"], text)),
                task_hits="; ".join(hits(topic["task_terms"], text)),
                query_hit=query,
            )
            records[(topic_id, normalize_title(title))] = rec
    return list(records.values())


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_ara(record: HarvestRecord) -> None:
    root = ARA_PAPERS / record.paper_id
    for sub in [
        "logic/solution",
        "src/code",
        "src/configs",
        "trace",
        "evidence/source",
        "evidence/runs",
        "evidence/tables",
        "evidence/figures",
    ]:
        (root / sub).mkdir(parents=True, exist_ok=True)
    meta = record.__dict__
    meta["collection_status"] = "target_journal_related_external"
    meta["ownership_status"] = "external_published_paper_not_project_original"
    write_text(root / "metadata.json", json.dumps(meta, ensure_ascii=False, indent=2) + "\n")
    title_yaml = record.title.replace('"', '\\"')
    write_text(
        root / "PAPER.md",
        f"""---
title: "{title_yaml}"
year: {record.year or 'null'}
collection: "target_journal_related"
collection_status: "target_journal_related_external"
ownership_status: "external_published_paper_not_project_original"
planned_topic: "{record.topic_id}"
target_journal_source: "{record.journal}"
---

# {record.title}

## Collection Mark

- Paper ID: `{record.paper_id}`
- Collection: `target_journal_related`
- Status: `target_journal_related_external`
- Ownership: `external_published_paper_not_project_original`
- Related planned paper: `{record.topic_id}` / {record.topic_title}

## Bibliographic Metadata

- Journal: {record.journal}
- Publication date: {record.publication_date}
- DOI: {record.doi or 'Not specified in provided sources'}
- OpenAlex: {record.openalex_id}
- Local PDF: `{record.pdf_path or 'Not downloaded'}`

## Reproduction Status

ARA scaffolded from target-journal metadata and available open PDF. Exact methods,
tables, figures, and implementation details require full-text extraction.
""",
    )
    write_text(
        root / "logic/problem.md",
        f"""# Problem Layer

This external paper is included because it was published in a planned target journal
and matches the planned topic `{record.topic_id}`.

## Match Evidence

- Planned topic: {record.topic_title}
- Query hit: {record.query_hit}
- Method terms found: {record.method_hits or 'Not specified in provided sources'}
- Task terms found: {record.task_hits or 'Not specified in provided sources'}
""",
    )
    write_text(
        root / "logic/claims.md",
        """# Claims

| Claim ID | Claim | Status | Proof |
|---|---|---|---|
| C1 | This is a recent external target-journal paper relevant to one planned manuscript direction. | Metadata-supported | E1 |
| C2 | The paper is not one of the project-owned planned manuscripts. | Explicit collection policy | E2 |

Scientific claims from the source paper are not extracted yet.
""",
    )
    write_text(
        root / "logic/concepts.md",
        f"""# Concepts

| Concept | Definition | Source |
|---|---|---|
| Target-journal related paper | A recent paper from Energies, Applied Sciences, Electronics, or IEEE Access related to a planned manuscript direction. | Harvest metadata |
| Planned topic | `{record.topic_id}` | Six-paper portfolio |
| Method clue | `{record.method_hits or 'Not specified in provided sources'}` | Title/abstract metadata |
""",
    )
    write_text(
        root / "logic/experiments.md",
        """# Experiments

| Experiment ID | Purpose | Config | Evidence | Status |
|---|---|---|---|---|
| E1 | Extract exact algorithms, baselines, datasets, and metrics from the paper. | Read local PDF or source page. | `evidence/source/source_overview.md` | Planned |
| E2 | Compare the paper against the matching planned manuscript. | Use `comparison_analysis.md`. | collection-level comparison | Planned |
| E3 | Reproduce or adapt experiments if code/data are available. | To be defined after code search. | `evidence/runs/` | Planned |
""",
    )
    write_text(
        root / "logic/related_work.md",
        f"""# Related Work

- Planned manuscript direction: `{record.topic_id}`
- Journal: {record.journal}
- Relationship: target-journal comparator and positioning reference.
- DOI: {record.doi or 'Not specified in provided sources'}
""",
    )
    write_text(
        root / "logic/solution/constraints.md",
        """# Constraints

- Do not infer exact method details from title-only metadata.
- Do not mark this external paper as project-original.
- Use only open PDF/source material for local storage.
- Exact numerical claims must be extracted into evidence files before reuse.
""",
    )
    write_text(root / "logic/solution/method.md", "# Method\n\nNot extracted yet.\n")
    write_text(root / "src/environment.md", "# Environment\n\nNot specified in provided sources.\n")
    write_text(root / "src/code/README.md", "# Code\n\nNo code repository has been searched or attached for this target-journal ARA yet.\n")
    write_text(
        root / "evidence/README.md",
        f"""# Evidence

- Local PDF: `{record.pdf_path or 'Not downloaded'}`
- PDF source URL: {record.source_pdf_url or 'Not specified in provided sources'}
- Landing page: {record.landing_page or 'Not specified in provided sources'}
- DOI: {record.doi or 'Not specified in provided sources'}
""",
    )
    write_text(
        root / "evidence/source/source_overview.md",
        f"""# Source Overview

## Paper

- Title: {record.title}
- Journal: {record.journal}
- Date: {record.publication_date}
- DOI: {record.doi or 'Not specified in provided sources'}
- Local PDF: `{record.pdf_path or 'Not downloaded'}`

## Planned Topic Match

- Topic: `{record.topic_id}`
- Topic title: {record.topic_title}
- Query: {record.query_hit}
- Method clue: {record.method_hits or 'Not specified in provided sources'}
- Task clue: {record.task_hits or 'Not specified in provided sources'}
""",
    )
    write_text(
        root / "trace/exploration_tree.yaml",
        f"""version: 1
paper_id: {record.paper_id}
collection: target_journal_related
nodes:
  - id: root
    type: import
    status: done
    provenance: ai-executed
    support_level: explicit
    summary: "Create ARA scaffold from target-journal related literature harvest."
    children:
      - metadata_import
      - pdf_status
  - id: metadata_import
    type: evidence
    status: done
    provenance: ai-executed
    support_level: explicit
    summary: "Imported target-journal metadata and planned-topic match."
    children: []
  - id: pdf_status
    type: evidence
    status: {"done" if record.pdf_path else "blocked"}
    provenance: ai-executed
    support_level: explicit
    summary: "Local PDF status: {record.pdf_path or 'not downloaded'}."
    children: []
""",
    )


def write_outputs(records: list[HarvestRecord], from_date: str, to_date: str) -> None:
    ARA_ROOT.mkdir(parents=True, exist_ok=True)
    rows = [r.__dict__ for r in records]
    write_csv(META_DIR / "target_journal_related_candidates.csv", rows)
    write_text(META_DIR / "target_journal_related_candidates.json", json.dumps(rows, ensure_ascii=False, indent=2) + "\n")

    for rec in records:
        build_ara(rec)

    summary = []
    by_topic = defaultdict(list)
    by_journal = Counter()
    for rec in records:
        by_topic[rec.topic_id].append(rec)
        by_journal[rec.journal] += 1
    for topic_id, group in sorted(by_topic.items()):
        summary.append(
            {
                "topic_id": topic_id,
                "planned_title": TOPICS[topic_id]["planned_title"],
                "paper_count": str(len(group)),
                "pdf_count": str(sum(1 for r in group if r.pdf_path)),
                "journals": "; ".join(f"{j}:{sum(1 for r in group if r.journal == j)}" for j in sorted({r.journal for r in group})),
            }
        )
    write_csv(META_DIR / "target_journal_related_summary.csv", summary)

    with (ARA_ROOT / "collection_manifest.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        fields = [
            "paper_id",
            "title",
            "topic_id",
            "journal",
            "publication_date",
            "doi",
            "pdf_path",
            "ara_path",
            "collection_status",
            "ownership_status",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for rec in records:
            writer.writerow(
                {
                    "paper_id": rec.paper_id,
                    "title": rec.title,
                    "topic_id": rec.topic_id,
                    "journal": rec.journal,
                    "publication_date": rec.publication_date,
                    "doi": rec.doi,
                    "pdf_path": rec.pdf_path,
                    "ara_path": str((ARA_PAPERS / rec.paper_id).relative_to(ROOT)).replace("\\", "/"),
                    "collection_status": "target_journal_related_external",
                    "ownership_status": "external_published_paper_not_project_original",
                }
            )

    lines = [
        "# Target Journal Related Literature",
        "",
        f"- Search window: `{from_date}` to `{to_date}`.",
        "- Target journals: Energies, Applied Sciences, Electronics, IEEE Access.",
        "- Collection status: `target_journal_related_external`.",
        "- Ownership status: `external_published_paper_not_project_original`.",
        "- PDF policy: only openly exposed PDF URLs were downloaded.",
        "",
        "## Summary by Planned Topic",
        "",
        "| Topic | Papers | PDFs | Journals |",
        "|---|---:|---:|---|",
    ]
    for item in summary:
        lines.append(f"| `{item['topic_id']}` | {item['paper_count']} | {item['pdf_count']} | {item['journals']} |")
    lines += [
        "",
        "## Journal Counts",
        "",
        "| Journal | Papers |",
        "|---|---:|",
    ]
    for journal, count in by_journal.most_common():
        lines.append(f"| {journal} | {count} |")
    write_text(OUT_ROOT / "README.md", "\n".join(lines) + "\n")
    write_text(ARA_ROOT / "README.md", "\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from-date", default="2023-07-11")
    parser.add_argument("--to-date", default="2026-07-11")
    parser.add_argument("--per-query", type=int, default=8)
    parser.add_argument("--max-per-topic", type=int, default=16)
    parser.add_argument("--provider", choices=["crossref", "openalex", "both"], default="crossref")
    parser.add_argument("--cache-only", action="store_true")
    parser.add_argument("--no-download", action="store_true")
    args = parser.parse_args()
    from_date = args.from_date
    to_date = args.to_date
    records = collect(
        from_date,
        to_date,
        per_query=args.per_query,
        max_per_topic=args.max_per_topic,
        cache_only=args.cache_only,
        no_download=args.no_download,
        provider=args.provider,
    )
    records = sorted(records, key=lambda r: (r.topic_id, r.journal, r.publication_date, r.title))
    write_outputs(records, from_date, to_date)
    print(f"records: {len(records)}")
    print(f"pdfs: {sum(1 for r in records if r.pdf_path)}")
    print(f"output: {OUT_ROOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
