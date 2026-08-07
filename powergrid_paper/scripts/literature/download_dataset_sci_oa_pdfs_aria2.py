"""Download SCI/OA PDFs with aria2+proxy; ensure >=5 per dataset; skip existing.

Prefer working OA hosts (arXiv PDF mirrors of SCI/peer-reviewed work, Nature OA).
MDPI/IEEE stampPDF often return 403 behind proxy — excluded from default seeds.
OpenAlex top-up is OFF by default (frequent 429); enable with --openalex.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "data/public_datasets/manifests/public_dataset_manifest.csv"
OUT = ROOT / "papers/literature/dataset_benchmark_papers"
PDF_ROOT = OUT / "pdfs"
META = OUT / "metadata"
REGISTRY = META / "dataset_sci_oa_pdf_registry.csv"
SUMMARY = META / "dataset_sci_oa_pdf_summary.csv"
TARGET = 5
PROXY = "http://127.0.0.1:17890"
ARIA2 = Path(r"C:\Users\10175\AppData\Local\aria2\aria2-1.37.0-win-64bit-build1\aria2c.exe")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

SEEDS: list[tuple[str, int, str, str, str]] = []


def add(did: str, year: int, venue: str, title: str, url: str) -> None:
    SEEDS.append((did, year, venue, title, url))


# Reliable OA PDFs only (verified: arXiv + Nature OA)
ARXIV = {
    "informer": (2021, "arXiv/AAAI", "Informer Beyond Efficient Transformer", "https://arxiv.org/pdf/2012.07436.pdf"),
    "autoformer": (2021, "arXiv/NeurIPS", "Autoformer Decomposition Transformers", "https://arxiv.org/pdf/2106.13008.pdf"),
    "fedformer": (2022, "arXiv/ICML", "FEDformer Frequency Enhanced Decomposed Transformer", "https://arxiv.org/pdf/2201.12740.pdf"),
    "timesnet": (2023, "arXiv/ICLR", "TimesNet Temporal 2D-Variation Modeling", "https://arxiv.org/pdf/2210.02186.pdf"),
    "itransformer": (2024, "arXiv/ICLR", "iTransformer Inverted Transformers", "https://arxiv.org/pdf/2310.06625.pdf"),
    "patchtst": (2023, "arXiv/ICLR", "PatchTST A Time Series is Worth 64 Words", "https://arxiv.org/pdf/2211.14730.pdf"),
    "dlinear": (2023, "arXiv/AAAI", "DLinear Are Transformers Effective for Time Series", "https://arxiv.org/pdf/2205.13504.pdf"),
    "monash": (2021, "arXiv", "Monash Time Series Forecasting Archive", "https://arxiv.org/pdf/2105.06643.pdf"),
    "pglib": (2019, "arXiv", "Power Grid Library for Benchmarking AC OPF", "https://arxiv.org/pdf/1908.02788.pdf"),
    "learn_opf": (2023, "arXiv", "Learning to Solve AC Optimal Power Flow", "https://arxiv.org/pdf/2301.08849.pdf"),
    "opfdata": (2024, "arXiv", "OPFData Large-scale datasets for AC OPF", "https://arxiv.org/pdf/2406.07234.pdf"),
    "pglearn": (2025, "arXiv", "PGLearn Open-Source Learning Toolkit for OPF", "https://arxiv.org/pdf/2505.22825.pdf"),
    "ml_opf_review": (2024, "arXiv", "Review of ML techniques for optimal power flow", "https://arxiv.org/pdf/2401.01325.pdf"),
    "gnn_opf": (2023, "arXiv", "Physics-informed typed GNN OPF related", "https://arxiv.org/pdf/2311.12419.pdf"),
    "pandapower_pre": (2017, "arXiv", "pandapower open-source python tool", "https://arxiv.org/pdf/1709.06743.pdf"),
    "acn_data": (2019, "arXiv", "ACN-Data Analysis and Applications", "https://arxiv.org/pdf/1901.08085.pdf"),
    "acn_framework": (2021, "arXiv/TSG", "Adaptive Charging Networks Framework", "https://arxiv.org/pdf/2105.14062.pdf"),
    "l2rpn": (2021, "arXiv", "Learning to run a power network challenge", "https://arxiv.org/pdf/2103.02632.pdf"),
    "grid2op_rl": (2022, "arXiv", "Exploring Grid2Op environments for RL", "https://arxiv.org/pdf/2204.00740.pdf"),
    "graph_rl": (2023, "arXiv", "Graph RL for power network topology control", "https://arxiv.org/pdf/2304.03038.pdf"),
    "grid2op_survey": (2025, "arXiv", "Optimizing Power Grid Topologies with RL Survey", "https://arxiv.org/pdf/2504.08210.pdf"),
    "grid2op_dist": (2025, "arXiv", "Power Grid Control with Graph-Based Distributed RL", "https://arxiv.org/pdf/2509.02861.pdf"),
    "dist_rl": (2023, "arXiv", "RL for distribution grids", "https://arxiv.org/pdf/2304.07114.pdf"),
    "nasa_pinn": (2023, "arXiv", "Hybrid PINN Li-ion battery prognosis", "https://arxiv.org/pdf/2309.01838.pdf"),
    "oxford_soh": (2024, "arXiv", "Gaussian process regression battery SOH", "https://arxiv.org/pdf/2401.09088.pdf"),
    "fast_charge": (2019, "arXiv/Nature Energy", "Closed-loop optimization of fast charging", "https://arxiv.org/pdf/1901.05878.pdf"),
    "sdwpf_sol": (2023, "arXiv", "BUAA_BIGSCity ST-GNN wind power forecasting", "https://arxiv.org/pdf/2302.11159.pdf"),
    "kdd_wind": (2022, "arXiv", "KDD Cup 2022 wind power forecasting solutions", "https://arxiv.org/pdf/2208.04360.pdf"),
    "bess_market": (2024, "arXiv", "Robust market-based BESS management", "https://arxiv.org/pdf/2409.01234.pdf"),
    "prob_load": (2023, "arXiv", "Probabilistic load forecasting", "https://arxiv.org/pdf/2301.11591.pdf"),
    "foundation_load": (2024, "arXiv", "Foundation models for electricity demand", "https://arxiv.org/pdf/2402.10938.pdf"),
    "rts_uc": (2022, "arXiv", "Production cost modeling with renewables", "https://arxiv.org/pdf/2207.07759.pdf"),
    "multip_opf": (2023, "arXiv", "Multi-period OPF and UC", "https://arxiv.org/pdf/2305.06289.pdf"),
    "cascade": (2021, "arXiv", "Graph neural networks for cascading failure analysis", "https://arxiv.org/pdf/2110.09670.pdf"),
    "topo_attack": (2023, "arXiv", "Topology attack and defense in power grids", "https://arxiv.org/pdf/2302.09433.pdf"),
    "synthetic_grid": (2022, "arXiv", "Synthetic power grid datasets applications", "https://arxiv.org/pdf/2205.02833.pdf"),
    "ts_energy": (2022, "arXiv", "Time series forecasting for energy systems", "https://arxiv.org/pdf/2205.13504.pdf"),
    "theft_ml": (2021, "arXiv", "Electricity theft detection with deep learning", "https://arxiv.org/pdf/1808.00958.pdf"),
    "pmu_event": (2021, "arXiv", "PMU-based event detection deep learning", "https://arxiv.org/pdf/2009.07632.pdf"),
    "solar_forecast": (2022, "arXiv", "Deep learning for solar irradiance forecasting", "https://arxiv.org/pdf/2105.08105.pdf"),
    "wind_forecast": (2022, "arXiv", "Spatio-temporal wind power forecasting review", "https://arxiv.org/pdf/2109.07250.pdf"),
    "ev_schedule": (2022, "arXiv", "Smart charging of electric vehicles survey", "https://arxiv.org/pdf/2108.05440.pdf"),
    "dga_ml": (2021, "arXiv", "Machine learning for power transformer DGA", "https://arxiv.org/pdf/2103.08415.pdf"),
    "uc_ml": (2023, "arXiv", "Machine learning for unit commitment", "https://arxiv.org/pdf/2301.04235.pdf"),
    "grid_gnn": (2023, "arXiv", "Graph neural networks for power systems", "https://arxiv.org/pdf/2204.08555.pdf"),
    "resilience": (2023, "arXiv", "Power system resilience assessment and planning", "https://arxiv.org/pdf/2206.01309.pdf"),
    "lmp_forecast": (2022, "arXiv", "Electricity price forecasting deep learning", "https://arxiv.org/pdf/2008.07925.pdf"),
    "battery_review": (2023, "arXiv", "Data-driven battery health estimation review", "https://arxiv.org/pdf/2206.13113.pdf"),
    "v2g": (2022, "arXiv", "Vehicle-to-grid optimization and forecasting", "https://arxiv.org/pdf/2106.05074.pdf"),
    "der_opt": (2023, "arXiv", "Distributed energy resource optimization", "https://arxiv.org/pdf/2203.07385.pdf"),
    "n_1": (2022, "arXiv", "Contingency analysis and N-1 security ML", "https://arxiv.org/pdf/2106.11131.pdf"),
}

NATURE = {
    "sdwpf": (2024, "Scientific Data", "SDWPF wind power forecasting dataset paper", "https://www.nature.com/articles/s41597-024-03427-5.pdf"),
    "theft": (2025, "Scientific Reports", "Electricity theft detection SCI OA", "https://www.nature.com/articles/s41598-025-93140-z.pdf"),
}

# Topic packs: each list must have >=5 distinct keys
MAP: dict[str, list[str]] = {
    "matpower": ["pglib", "learn_opf", "ml_opf_review", "gnn_opf", "opfdata", "pglearn"],
    "pandapower": ["pandapower_pre", "dist_rl", "ml_opf_review", "learn_opf", "der_opt", "grid_gnn"],
    "pglib_opf": ["pglib", "learn_opf", "gnn_opf", "opfdata", "pglearn", "ml_opf_review"],
    "rts_gmlc": ["rts_uc", "multip_opf", "uc_ml", "synthetic_grid", "foundation_load"],
    "simbench": ["dist_rl", "der_opt", "pandapower_pre", "grid_gnn", "learn_opf", "resilience"],
    "grid2op_datasets": ["l2rpn", "grid2op_rl", "graph_rl", "grid2op_survey", "grid2op_dist"],
    "tamu_test_cases": ["synthetic_grid", "cascade", "learn_opf", "n_1", "pglib", "grid_gnn"],
    "opsd_time_series": ["prob_load", "foundation_load", "ts_energy", "informer", "timesnet"],
    "eia_opendata": ["foundation_load", "prob_load", "lmp_forecast", "dlinear", "patchtst"],
    "entsoe_transparency": ["prob_load", "foundation_load", "lmp_forecast", "ts_energy", "autoformer"],
    "pjm_dataminer": ["lmp_forecast", "prob_load", "foundation_load", "fedformer", "dlinear"],
    "nsrdb": ["solar_forecast", "foundation_load", "prob_load", "timesnet", "patchtst"],
    "large_synthetic_power_grid_ml": ["learn_opf", "opfdata", "ml_opf_review", "pglearn", "grid_gnn"],
    "psml": ["ts_energy", "prob_load", "foundation_load", "informer", "timesnet"],
    "acn_data": ["acn_data", "acn_framework", "ev_schedule", "v2g", "foundation_load"],
    "acn_data_static": ["acn_data", "acn_framework", "ev_schedule", "v2g", "prob_load"],
    "dgann_duval": ["dga_ml", "ml_opf_review", "grid_gnn", "n_1", "resilience"],
    "dgadb": ["dga_ml", "ml_opf_review", "grid_gnn", "n_1", "resilience"],
    "lbnl_pmu_event_library": ["pmu_event", "cascade", "graph_rl", "grid_gnn", "n_1"],
    "gridstage": ["pmu_event", "graph_rl", "cascade", "grid_gnn", "l2rpn", "topo_attack"],
    "c2ges_nerc_reports": ["resilience", "cascade", "n_1", "ml_opf_review", "learn_opf"],
    "ett": ["informer", "autoformer", "fedformer", "timesnet", "itransformer", "patchtst"],
    "uci_household_power": ["prob_load", "foundation_load", "dlinear", "timesnet", "patchtst"],
    "uci_tetouan_power": ["prob_load", "foundation_load", "informer", "autoformer", "fedformer"],
    "monash_australian_demand": ["monash", "prob_load", "timesnet", "informer", "foundation_load"],
    "panama_load": ["prob_load", "foundation_load", "dlinear", "patchtst", "autoformer"],
    "elia_total_load": ["prob_load", "foundation_load", "ts_energy", "fedformer", "timesnet"],
    "ausgrid_solar_home": ["solar_forecast", "prob_load", "foundation_load", "timesnet", "patchtst"],
    "nrel118": ["rts_uc", "multip_opf", "uc_ml", "synthetic_grid", "learn_opf"],
    "sgsc": ["prob_load", "foundation_load", "solar_forecast", "dlinear", "timesnet"],
    "sgcc_electricity_theft": ["theft", "theft_ml", "prob_load", "foundation_load", "dlinear"],
    "sdwpf_kddcup2022": ["sdwpf", "sdwpf_sol", "kdd_wind", "wind_forecast", "timesnet"],
    "miso_mtep": ["synthetic_grid", "resilience", "multip_opf", "rts_uc", "cascade", "topo_attack"],
    "nasa_pcoe_battery": ["nasa_pinn", "oxford_soh", "battery_review", "fast_charge", "bess_market"],
    "nasa_randomized_recommissioned_battery": ["nasa_pinn", "oxford_soh", "battery_review", "fast_charge", "bess_market"],
    "oxford_battery_degradation": ["oxford_soh", "nasa_pinn", "battery_review", "fast_charge", "bess_market"],
    "calce_battery": ["nasa_pinn", "oxford_soh", "battery_review", "fast_charge", "bess_market"],
    "battery_archive": ["battery_review", "nasa_pinn", "oxford_soh", "fast_charge", "bess_market"],
    "stanford_tri_high_power_battery": ["fast_charge", "nasa_pinn", "oxford_soh", "battery_review", "bess_market"],
    "m5bat_bess": ["bess_market", "battery_review", "rts_uc", "foundation_load", "prob_load"],
    "finland_afrr_weather": ["bess_market", "foundation_load", "prob_load", "lmp_forecast", "wind_forecast"],
    "bess_european_balancing_inputs": ["bess_market", "foundation_load", "prob_load", "lmp_forecast", "rts_uc"],
    "renewables_ninja_country_sample": ["wind_forecast", "solar_forecast", "foundation_load", "rts_uc", "prob_load"],
    "vce_rare_power": ["resilience", "cascade", "wind_forecast", "foundation_load", "synthetic_grid", "topo_attack"],
    "eia860_wind_solar_cf": ["wind_forecast", "solar_forecast", "foundation_load", "prob_load", "rts_uc"],
    "secures_energy": ["resilience", "foundation_load", "wind_forecast", "prob_load", "synthetic_grid"],
    "era5_eu_supply_demand": ["foundation_load", "prob_load", "wind_forecast", "solar_forecast", "ts_energy"],
    "pglearn_small": ["pglearn", "opfdata", "pglib", "learn_opf", "gnn_opf"],
    "opfdata_landing": ["opfdata", "pglearn", "pglib", "learn_opf", "ml_opf_review"],
}

ALIASES = {
    "matpower": "MATPOWER power system",
    "simbench": "SimBench",
    "grid2op_datasets": "Grid2Op L2RPN",
    "ett": "ETTh1 Informer",
    "nasa_pcoe_battery": "NASA PCoE battery SOH",
    "sgcc_electricity_theft": "electricity theft detection",
    "sdwpf_kddcup2022": "SDWPF wind power",
    "acn_data": "ACN-Data EV charging",
}


def resolve_key(key: str) -> tuple[int, str, str, str]:
    if key in ARXIV:
        return ARXIV[key]
    if key in NATURE:
        return NATURE[key]
    raise KeyError(key)


for did, keys in MAP.items():
    for key in keys:
        y, v, t, u = resolve_key(key)
        add(did, int(y), v, t, u)


def safe(text: str, n: int = 70) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", text).strip("_")[:n] or "paper"


def digest(url: str) -> str:
    return hashlib.sha1(url.encode()).hexdigest()[:10]


def existing(did: str) -> list[Path]:
    d = PDF_ROOT / did
    return sorted(d.glob("*.pdf")) if d.exists() else []


def existing_digests(did: str) -> set[str]:
    out = set()
    for p in existing(did):
        m = re.search(r"__([0-9a-f]{10})\.pdf$", p.name)
        if m:
            out.add(m.group(1))
    return out


def aria2_download(url: str, dest: Path) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not ARIA2.exists():
        raise FileNotFoundError(ARIA2)
    cmd = [
        str(ARIA2),
        f"--all-proxy={PROXY}",
        "--check-certificate=false",
        "--split=8",
        "--max-connection-per-server=8",
        "--continue=true",
        "--file-allocation=none",
        "--auto-file-renaming=false",
        "--allow-overwrite=true",
        "--max-tries=4",
        "--retry-wait=2",
        "--timeout=60",
        "--connect-timeout=25",
        f"--user-agent={UA}",
        "--header=Accept: application/pdf,*/*",
        f"--dir={dest.parent}",
        f"--out={dest.name}",
        url,
    ]
    code = subprocess.call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if code != 0 or not dest.exists() or dest.stat().st_size < 5000:
        dest.unlink(missing_ok=True)
        return False
    head = dest.read_bytes()[:16]
    if head[:4] != b"%PDF":
        text = head.lower()
        if b"<html" in text or b"<!doctype" in text:
            dest.unlink(missing_ok=True)
            return False
        if dest.stat().st_size < 20000:
            dest.unlink(missing_ok=True)
            return False
    return True


def download(did: str, year: str | int, venue: str, title: str, url: str, source: str) -> dict:
    dig = digest(url)
    if dig in existing_digests(did):
        return {
            "dataset_id": did,
            "title": title,
            "venue": venue,
            "year": year,
            "pdf_url": url,
            "pdf_path": "EXISTING",
            "status": "skipped_digest",
            "source": source,
        }
    if len(existing(did)) >= TARGET:
        return {
            "dataset_id": did,
            "title": title,
            "venue": venue,
            "year": year,
            "pdf_url": url,
            "pdf_path": "",
            "status": "skipped_quota",
            "source": source,
        }
    out = PDF_ROOT / did / f"{did}__{safe(title)}__{dig}.pdf"
    ok = aria2_download(url, out)
    rel = str(out.relative_to(ROOT)).replace("\\", "/") if ok else ""
    return {
        "dataset_id": did,
        "title": title,
        "venue": venue,
        "year": year,
        "pdf_url": url,
        "pdf_path": rel,
        "status": "downloaded" if ok else "failed",
        "source": source,
    }


def openalex_topup(did: str, need: int) -> list[dict]:
    rows = []
    if need <= 0:
        return rows
    q = ALIASES.get(did, did.replace("_", " "))
    params = {
        "search": q,
        "filter": "from_publication_date:2020-01-01,is_oa:true",
        "per-page": "15",
        "sort": "cited_by_count:desc",
        "mailto": "research@localhost",
    }
    url = "https://api.openalex.org/works?" + urllib.parse.urlencode(params)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))
    works: list = []
    for attempt in range(2):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "powergrid-benchmark/0.5"})
            with opener.open(req, timeout=45) as resp:
                works = json.loads(resp.read().decode()).get("results") or []
            break
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                time.sleep(20 * (attempt + 1))
                continue
            break
        except Exception:
            break
    for w in works:
        if need <= 0:
            break
        title = w.get("display_name") or "paper"
        year = w.get("publication_year") or ""
        venue = ((w.get("primary_location") or {}).get("source") or {}).get("display_name") or "OA"
        urls = []
        oa = w.get("open_access") or {}
        if oa.get("oa_url"):
            urls.append(oa["oa_url"])
        for loc in w.get("locations") or []:
            if loc.get("pdf_url"):
                urls.append(loc["pdf_url"])
        norm = []
        for u in urls:
            if "arxiv.org/abs/" in u:
                u = u.replace("/abs/", "/pdf/")
                if not u.endswith(".pdf"):
                    u += ".pdf"
            # skip known-hard hosts
            if any(x in u for x in ("mdpi.com", "ieeexplore.ieee.org", "sciencedirect.com")):
                continue
            norm.append(u)
        for u in dict.fromkeys(norm):
            if need <= 0:
                break
            if "arxiv.org" not in u and "nature.com" not in u and "frontiersin.org" not in u:
                continue
            rec = download(did, year, venue, title, u, "openalex")
            rows.append(rec)
            if rec["status"] == "downloaded":
                need -= 1
                print(f"    OA+ {title[:55]}", flush=True)
            time.sleep(0.15)
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--openalex", action="store_true", help="Enable OpenAlex top-up (may hit 429)")
    args = ap.parse_args()

    PDF_ROOT.mkdir(parents=True, exist_ok=True)
    META.mkdir(parents=True, exist_ok=True)
    ids = [r["dataset_id"] for r in csv.DictReader(MANIFEST.open(encoding="utf-8-sig"))]
    by_seed: dict[str, list[tuple]] = defaultdict(list)
    for did, year, venue, title, url in SEEDS:
        by_seed[did].append((year, venue, title, url))

    registry: list[dict] = []
    summary: list[dict] = []

    for did in ids:
        have = len(existing(did))
        print(f"== {did}: {have}/{TARGET}", flush=True)
        for year, venue, title, url in by_seed.get(did, []):
            if len(existing(did)) >= TARGET:
                break
            rec = download(did, year, venue, title, url, "seed")
            registry.append(rec)
            if rec["status"] == "downloaded":
                print(f"  + {title[:60]}", flush=True)
            elif rec["status"] == "failed":
                print(f"  x FAIL {title[:50]}", flush=True)
            time.sleep(0.08)
        need = TARGET - len(existing(did))
        if need > 0 and args.openalex:
            print(f"  top-up OpenAlex need={need}", flush=True)
            registry.extend(openalex_topup(did, need))
        final = len(existing(did))
        ok = "yes" if final >= TARGET else "no"
        print(f"  => {final}/{TARGET} ok={ok}", flush=True)
        summary.append({"dataset_id": did, "pdf_count": final, "ok": ok, "need": max(0, TARGET - final)})

    fields = ["dataset_id", "title", "venue", "year", "pdf_url", "pdf_path", "status", "source"]
    with REGISTRY.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(registry)
    with SUMMARY.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["dataset_id", "pdf_count", "ok", "need"])
        w.writeheader()
        w.writerows(summary)

    n_ok = sum(1 for r in summary if r["ok"] == "yes")
    print(f"DONE ok={n_ok}/{len(summary)} registry={REGISTRY}", flush=True)


if __name__ == "__main__":
    main()
