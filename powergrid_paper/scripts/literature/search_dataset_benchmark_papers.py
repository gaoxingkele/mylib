"""Search recent benchmark papers that mention local public datasets.

The script uses OpenAlex full-text metadata search. It records candidate
papers that mention each dataset alias in the recent three-year window and
downloads only openly accessible PDF URLs exposed by OpenAlex or resolvable
from public repository landing pages.

It does not bypass paywalls. "SCI" and "CCF" labels are heuristic venue
buckets and must be manually verified against WoS/JCR and the CCF list.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "data" / "public_datasets" / "manifests" / "public_dataset_manifest.csv"
OUT_ROOT = ROOT / "papers" / "literature" / "dataset_benchmark_papers"
OPENALEX_URL = "https://api.openalex.org/works"
USER_AGENT = "powergrid-benchmark-literature-harvester/0.2 (mailto:research@localhost; respectful OpenAlex client)"


DATASET_ALIASES: dict[str, list[str]] = {
    "matpower": ["MATPOWER", "MATPOWER case", "MATPOWER cases"],
    "pandapower": ["pandapower", "pandapower networks"],
    "pglib_opf": ["PGLib-OPF", "PGLib OPF", "Power Grid Lib OPF"],
    "rts_gmlc": ["RTS-GMLC", "Reliability Test System Grid Modernization Lab Consortium"],
    "simbench": ["SimBench", "SimBench dataset"],
    "grid2op_datasets": ["Grid2Op", "L2RPN", "Learning to Run a Power Network"],
    "tamu_test_cases": ["Texas A&M electric grid test cases", "ACTIVSg", "TAMU synthetic grid"],
    "opsd_time_series": ["Open Power System Data", "OPSD time series"],
    "eia_opendata": ["EIA Open Data", "U.S. Energy Information Administration open data"],
    "entsoe_transparency": ["ENTSO-E Transparency Platform", "ENTSOE Transparency Platform"],
    "pjm_dataminer": ["PJM Data Miner", "PJM DataMiner"],
    "nsrdb": ["National Solar Radiation Database", "NSRDB"],
    "large_synthetic_power_grid_ml": ["Large Synthetic Power Grid ML dataset", "Synthetic Power Grid ML"],
    "psml": ["Open-source power dataset", "PSML power dataset"],
    "acn_data": ["ACN-Data", "Adaptive Charging Network dataset", "Caltech ACN dataset"],
    "dgann_duval": ["DGANN", "Duval triangle dataset"],
    "dgadb": ["DGADB", "DGA database transformer"],
    "lbnl_pmu_event_library": ["LBNL PMU event library", "PMU event library"],
    "gridstage": ["GridSTAGE", "synthetic PMU GridSTAGE"],
    "c2ges_nerc_reports": ["NERC event analysis reports", "NERC reliability reports"],
    "ett": ["ETT dataset", "ETTh1", "ETTm1", "Electricity Transformer Temperature"],
    "uci_household_power": ["UCI household power consumption", "Individual household electric power consumption"],
    "uci_tetouan_power": ["Tetouan power consumption", "UCI Tetouan"],
    "monash_australian_demand": ["Australian electricity demand dataset", "Monash electricity demand"],
    "panama_load": ["Panama electricity load", "Panama short-term load forecasting"],
    "elia_total_load": ["Elia total load", "Elia load forecast"],
    "ausgrid_solar_home": ["Ausgrid Solar Home", "Ausgrid solar home electricity"],
    "nrel118": ["NREL-118", "NREL 118-bus", "RTS-GMLC NREL 118"],
    "sgsc": ["Smart Grid Smart City", "SGSC customer trial"],
    "sgcc_electricity_theft": ["SGCC electricity theft", "State Grid electricity theft detection"],
    "sdwpf_kddcup2022": ["SDWPF", "KDD Cup 2022 wind", "Spatial Dynamic Wind Power Forecasting"],
    "miso_mtep": ["MISO MTEP", "MTEP transmission expansion"],
    "nasa_pcoe_battery": ["NASA battery dataset", "NASA PCoE battery", "NASA lithium-ion battery aging"],
    "nasa_randomized_recommissioned_battery": ["randomized battery dataset NASA", "recommissioned battery NASA"],
    "oxford_battery_degradation": ["Oxford Battery Degradation Dataset", "Oxford battery aging"],
    "calce_battery": ["CALCE battery", "CALCE lithium-ion", "University of Maryland battery data"],
    "battery_archive": ["Battery Archive", "batteryarchive.org"],
    "stanford_tri_high_power_battery": ["Stanford high-power lithium-ion", "Toyota Research Institute battery dataset"],
    "acn_data_static": ["ACN-Data", "Adaptive Charging Network dataset", "Caltech ACN"],
    "m5bat_bess": ["M5BAT", "large-scale battery storage M5BAT"],
    "finland_afrr_weather": ["Finland aFRR", "aFRR energy market Finland"],
    "bess_european_balancing_inputs": ["battery energy storage balancing market", "FCR aFRR BESS"],
    "renewables_ninja_country_sample": ["Renewables.ninja", "renewables ninja capacity factor"],
    "vce_rare_power": ["RARE Power Dataset", "Vibrant Clean Energy RARE"],
    "eia860_wind_solar_cf": ["EIA-860 wind solar", "EIA 860 generation profiles"],
    "secures_energy": ["SECURES-Energy", "SECURES Energy dataset"],
    "era5_eu_supply_demand": ["ERA5 wind capacity factor Europe", "climate-driven power supply demand Europe"],
    "pglearn_small": ["PGLearn", "PGLearn OPF", "learning toolkit for optimal power flow"],
    "opfdata_landing": ["OPFData", "OPFData AC optimal power flow"],
}


SCI_JOURNAL_HINTS = [
    "IEEE Transactions",
    "IEEE Systems Journal",
    "IEEE Access",
    "Applied Energy",
    "Energy",
    "Electric Power Systems Research",
    "International Journal of Electrical Power",
    "Renewable Energy",
    "Sustainable Energy",
    "IET Generation",
    "IET Smart Grid",
    "CSEE Journal",
    "Protection and Control of Modern Power Systems",
    "Energy Reports",
    "Energies",
    "Journal of Modern Power Systems",
    "International Transactions on Electrical Energy Systems",
    "Journal of Energy Storage",
    "Journal of Power Sources",
    "Journal of The Electrochemical Society",
    "IEEE Transactions on Dielectrics",
    "IEEE Transactions on Transportation Electrification",
    "IEEE Transactions on Vehicular Technology",
    "IEEE Transactions on Industrial Electronics",
    "IEEE Transactions on Smart Grid",
    "IEEE Transactions on Power Systems",
    "Nature Scientific Data",
    "Scientific Reports",
    "Energy and AI",
    "Applied Soft Computing",
    "Expert Systems with Applications",
]


CCF_CONF_HINTS = [
    "AAAI",
    "IJCAI",
    "KDD",
    "SIGKDD",
    "The Web Conference",
    "WWW",
    "SIGIR",
    "CIKM",
    "ICDE",
    "ICDM",
    "SDM",
    "NeurIPS",
    "ICML",
    "ICLR",
    "ACL",
    "EMNLP",
    "NAACL",
    "DAC",
    "ICCAD",
    "INFOCOM",
    "SIGMOD",
    "VLDB",
    "ICSE",
    "FSE",
]


COMPARISON_TERMS = [
    "experiment",
    "experimental",
    "benchmark",
    "baseline",
    "comparison",
    "compare",
    "case study",
    "test case",
    "test cases",
    "dataset",
    "datasets",
    "simulation",
    "evaluated",
]


@dataclass
class DatasetRecord:
    dataset_id: str
    category: str
    status: str
    tasks: str


def http_json(url: str, timeout: int = 45, retries: int = 3) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            last_error = exc
            time.sleep(1.5 * (attempt + 1))
    raise last_error or RuntimeError("unknown JSON fetch error")


def http_bytes(url: str, timeout: int = 90, retries: int = 2) -> tuple[bytes, str]:
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read(), resp.headers.get("Content-Type", "")
        except Exception as exc:
            last_error = exc
            time.sleep(1.5 * (attempt + 1))
    raise last_error or RuntimeError("unknown byte fetch error")


def read_manifest() -> list[DatasetRecord]:
    with MANIFEST.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return [
        DatasetRecord(
            dataset_id=row["dataset_id"],
            category=row["category"],
            status=row["status"],
            tasks=row["main_tasks"],
        )
        for row in rows
    ]


def reconstruct_abstract(inv: dict[str, list[int]] | None) -> str:
    if not inv:
        return ""
    words: list[str] = [""] * (max(pos for positions in inv.values() for pos in positions) + 1)
    for token, positions in inv.items():
        for pos in positions:
            words[pos] = token
    return " ".join(words)


def safe_name(text: str, limit: int = 120) -> str:
    text = re.sub(r"https?://", "", text)
    text = re.sub(r"[^A-Za-z0-9._-]+", "_", text).strip("_")
    return text[:limit] or "paper"


def source_name(work: dict[str, Any]) -> str:
    source = (work.get("primary_location") or {}).get("source") or {}
    return source.get("display_name") or ""


def source_type(work: dict[str, Any]) -> str:
    source = (work.get("primary_location") or {}).get("source") or {}
    return source.get("type") or work.get("type") or ""


def classify_venue(work: dict[str, Any]) -> tuple[str, str]:
    name = source_name(work)
    typ = source_type(work).lower()
    for hint in CCF_CONF_HINTS:
        if hint.lower() in name.lower():
            return "ccf_conference_candidate", "Venue name matches a CCF-list conference hint; verify against the current CCF list."
    if "proceedings" in typ or "conference" in typ:
        for hint in CCF_CONF_HINTS:
            if hint.lower() in (work.get("title") or "").lower():
                return "ccf_conference_candidate", "Proceedings/conference record with CCF hint; verify manually."
    for hint in SCI_JOURNAL_HINTS:
        if hint.lower() in name.lower():
            return "sci_journal_candidate", "Journal name matches a common SCI/SCIE power/energy venue hint; verify in WoS/JCR."
    if typ == "journal":
        return "journal_other_verify", "Journal record; SCI/SCIE status not established by OpenAlex."
    if "proceedings" in typ or "conference" in typ:
        return "conference_other_verify", "Conference record; CCF status not established by OpenAlex."
    return "other", "Not enough venue evidence for SCI/CCF classification."


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
    if "arxiv" in doi.lower():
        urls.append(doi.replace("abs", "pdf"))
    return urls


def find_pdf_from_landing(url: str) -> str | None:
    if url.lower().endswith(".pdf") or "/pdf/" in url.lower():
        return url
    if "arxiv.org/abs/" in url:
        return url.replace("/abs/", "/pdf/")
    try:
        data, content_type = http_bytes(url, timeout=30)
    except Exception:
        return None
    if "pdf" in content_type.lower() or data[:4] == b"%PDF":
        return url
    if "html" not in content_type.lower() and b"<html" not in data[:2048].lower():
        return None
    text = data.decode("utf-8", errors="ignore")
    matches = re.findall(r'href=["\']([^"\']+\.pdf(?:\?[^"\']*)?)["\']', text, flags=re.I)
    if not matches:
        matches = re.findall(r'https?://[^"\'<>\s]+\.pdf(?:\?[^"\'<>\s]+)?', text, flags=re.I)
    if not matches:
        return None
    return urllib.parse.urljoin(url, matches[0])


def download_pdf(work: dict[str, Any], dataset_id: str, out_dir: Path) -> tuple[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    for candidate in pdf_candidates(work):
        pdf_url = find_pdf_from_landing(candidate)
        if not pdf_url:
            continue
        try:
            data, content_type = http_bytes(pdf_url)
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            continue
        if data[:4] != b"%PDF" and "pdf" not in content_type.lower():
            continue
        digest = hashlib.sha1(pdf_url.encode("utf-8")).hexdigest()[:10]
        title = safe_name(work.get("title") or work.get("id") or "paper", 90)
        path = out_dir / f"{dataset_id}__{title}__{digest}.pdf"
        path.write_bytes(data)
        return str(path.relative_to(ROOT)).replace("\\", "/"), pdf_url
    return "", ""


def search_alias(alias: str, from_date: str, to_date: str, per_page: int) -> list[dict[str, Any]]:
    filter_value = f"from_publication_date:{from_date},to_publication_date:{to_date},fulltext.search:{alias!r}"
    params = {
        "filter": filter_value,
        "per-page": str(per_page),
        "sort": "relevance_score:desc",
    }
    url = OPENALEX_URL + "?" + urllib.parse.urlencode(params)
    # OpenAlex accepts double quotes better than Python repr single quotes.
    url = url.replace("%27", "%22")
    data = http_json(url)
    return data.get("results") or []


def collect(args: argparse.Namespace) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    datasets = read_manifest()
    if args.dataset:
        wanted = set(args.dataset)
        datasets = [ds for ds in datasets if ds.dataset_id in wanted]
    raw_dir = OUT_ROOT / "metadata" / "openalex_raw"
    pdf_dir = OUT_ROOT / "pdfs"
    raw_dir.mkdir(parents=True, exist_ok=True)

    records: dict[tuple[str, str], dict[str, Any]] = {}
    download_rows: list[dict[str, Any]] = []

    for ds in datasets:
        aliases = DATASET_ALIASES.get(ds.dataset_id, [ds.dataset_id])
        per_dataset: dict[str, dict[str, Any]] = {}
        for alias in aliases:
            print(f"search {ds.dataset_id}: {alias}")
            try:
                works = search_alias(alias, args.from_date, args.to_date, args.per_alias)
            except urllib.error.HTTPError as exc:
                print(f"  OpenAlex HTTP error: {exc}")
                continue
            except Exception as exc:
                print(f"  OpenAlex error: {type(exc).__name__}: {exc}")
                continue
            (raw_dir / f"{ds.dataset_id}__{safe_name(alias, 40)}.json").write_text(
                json.dumps(works, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            for work in works:
                work_id = work.get("id") or ""
                if work_id:
                    per_dataset[work_id] = work
            time.sleep(args.sleep)

        ranked = sorted(
            per_dataset.values(),
            key=lambda w: (
                w.get("relevance_score") or 0,
                w.get("cited_by_count") or 0,
                w.get("publication_date") or "",
            ),
            reverse=True,
        )[: args.max_per_dataset]

        for work in ranked:
            abstract = reconstruct_abstract(work.get("abstract_inverted_index"))
            haystack = f"{work.get('title') or ''} {abstract}".lower()
            mentioned_aliases = [a for a in aliases if a.lower() in haystack]
            comparison_signal = any(term in haystack for term in COMPARISON_TERMS)
            venue_bucket, verification_note = classify_venue(work)
            key = (ds.dataset_id, work.get("id") or work.get("doi") or work.get("title") or "")
            pdf_path = ""
            pdf_source = ""
            if not args.no_download and ((work.get("open_access") or {}).get("is_oa") or args.try_landing):
                pdf_path, pdf_source = download_pdf(work, ds.dataset_id, pdf_dir / ds.dataset_id)
            record = {
                "dataset_id": ds.dataset_id,
                "dataset_category": ds.category,
                "dataset_status": ds.status,
                "dataset_tasks": ds.tasks,
                "matched_aliases": "; ".join(mentioned_aliases) if mentioned_aliases else "; ".join(aliases),
                "mention_evidence": "title_or_abstract_or_fulltext_search",
                "comparison_signal": "yes" if comparison_signal else "weak_metadata_only",
                "publication_date": work.get("publication_date") or "",
                "year": work.get("publication_year") or "",
                "title": work.get("title") or "",
                "source": source_name(work),
                "source_type": source_type(work),
                "venue_bucket": venue_bucket,
                "verification_note": verification_note,
                "doi": (work.get("ids") or {}).get("doi") or work.get("doi") or "",
                "openalex_id": work.get("id") or "",
                "is_oa": str((work.get("open_access") or {}).get("is_oa") or False).lower(),
                "oa_status": (work.get("open_access") or {}).get("oa_status") or "",
                "oa_url": (work.get("open_access") or {}).get("oa_url") or "",
                "landing_page": ((work.get("primary_location") or {}).get("landing_page_url") or ""),
                "pdf_path": pdf_path,
                "pdf_source_url": pdf_source,
                "cited_by_count": work.get("cited_by_count") or 0,
                "relevance_score": work.get("relevance_score") or 0,
            }
            records[key] = record
            if pdf_path or pdf_source:
                download_rows.append(
                    {
                        "dataset_id": ds.dataset_id,
                        "title": record["title"],
                        "pdf_path": pdf_path,
                        "pdf_source_url": pdf_source,
                    }
                )
    return list(records.values()), download_rows


def write_outputs(records: list[dict[str, Any]], download_rows: list[dict[str, Any]], args: argparse.Namespace) -> None:
    meta_dir = OUT_ROOT / "metadata"
    meta_dir.mkdir(parents=True, exist_ok=True)
    csv_path = meta_dir / "dataset_paper_candidates.csv"
    if args.merge and csv_path.exists():
        with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
            existing = list(csv.DictReader(handle))
        merged: dict[tuple[str, str], dict[str, Any]] = {}
        for row in existing:
            merged[(row.get("dataset_id", ""), row.get("openalex_id") or row.get("doi") or row.get("title") or "")] = row
        for row in records:
            key = (row.get("dataset_id", ""), row.get("openalex_id") or row.get("doi") or row.get("title") or "")
            prev = merged.get(key)
            if prev and prev.get("pdf_path") and not row.get("pdf_path"):
                row = {**row, "pdf_path": prev["pdf_path"], "pdf_source_url": prev.get("pdf_source_url", "")}
            merged[key] = row
        records = list(merged.values())
    records = sorted(records, key=lambda r: (r["dataset_id"], r["venue_bucket"], r["publication_date"], r["relevance_score"]), reverse=True)
    fields = list(records[0].keys()) if records else []
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)
    (meta_dir / "dataset_paper_candidates.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    # Rebuild download log from all records with PDFs when merging.
    if args.merge:
        download_rows = [
            {
                "dataset_id": r["dataset_id"],
                "title": r["title"],
                "pdf_path": r["pdf_path"],
                "pdf_source_url": r.get("pdf_source_url", ""),
            }
            for r in records
            if r.get("pdf_path")
        ]
    with (meta_dir / "download_log.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["dataset_id", "title", "pdf_path", "pdf_source_url"])
        writer.writeheader()
        writer.writerows(download_rows)

    by_dataset: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        by_dataset.setdefault(record["dataset_id"], []).append(record)
    summary_rows = []
    for dataset_id, rows in sorted(by_dataset.items()):
        summary_rows.append(
            {
                "dataset_id": dataset_id,
                "candidate_count": len(rows),
                "sci_journal_candidates": sum(1 for r in rows if r["venue_bucket"] == "sci_journal_candidate"),
                "ccf_conference_candidates": sum(1 for r in rows if r["venue_bucket"] == "ccf_conference_candidate"),
                "downloaded_pdfs": sum(1 for r in rows if r["pdf_path"]),
            }
        )
    with (meta_dir / "dataset_paper_summary.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["dataset_id", "candidate_count", "sci_journal_candidates", "ccf_conference_candidates", "downloaded_pdfs"],
        )
        writer.writeheader()
        writer.writerows(summary_rows)

    lines = [
        "# Dataset Benchmark Paper Search",
        "",
        f"- Search window: `{args.from_date}` to `{args.to_date}`.",
        "- Source: OpenAlex works API full-text metadata search.",
        "- Scope: papers that mention existing local public dataset aliases.",
        "- Download policy: only open-access PDF URLs or public repository PDFs were downloaded; paywalled PDFs were not fetched.",
        "- SCI/CCF status is heuristic and must be verified against WoS/JCR and the current CCF list.",
        "",
        "## Outputs",
        "",
        "- `metadata/dataset_paper_candidates.csv`",
        "- `metadata/dataset_paper_summary.csv`",
        "- `metadata/download_log.csv`",
        "- `pdfs/<dataset_id>/*.pdf` when OA PDF download succeeded",
        "",
        "## Summary",
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
    today = date.today().isoformat()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from-date", default="2023-07-09")
    parser.add_argument("--to-date", default=today)
    parser.add_argument("--per-alias", type=int, default=12)
    parser.add_argument("--max-per-dataset", type=int, default=12)
    parser.add_argument("--sleep", type=float, default=1.0)
    parser.add_argument("--no-download", action="store_true")
    parser.add_argument("--try-landing", action="store_true", help="Try landing pages even when OpenAlex does not mark OA.")
    parser.add_argument("--dataset", nargs="*", default=None, help="Optional dataset_id filter")
    parser.add_argument("--merge", action="store_true", help="Merge into existing candidates CSV instead of overwrite")
    args = parser.parse_args()
    records, download_rows = collect(args)
    write_outputs(records, download_rows, args)
    print(f"records: {len(records)}")
    print(f"downloaded_pdfs: {sum(1 for r in records if r['pdf_path'])}")
    print(f"output: {OUT_ROOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
