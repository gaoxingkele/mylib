"""Ensure each public dataset has >=N SCI/OA paper PDFs locally (skip existing).

Strategy:
1. Count existing pdfs/<dataset_id>/*.pdf
2. Seed from curated OA URLs + filtered candidate OA URLs
3. Top up via OpenAlex (is_oa:true, 2020+) with long backoff
4. Download only PDF bytes; dedupe by URL sha1 filename suffix
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "data" / "public_datasets" / "manifests" / "public_dataset_manifest.csv"
OUT = ROOT / "papers" / "literature" / "dataset_benchmark_papers"
PDF_ROOT = OUT / "pdfs"
META = OUT / "metadata"
FILT = META / "dataset_paper_candidates_filtered.csv"
CURATED_CSV = META / "curated_extension_papers.csv"
EXEMPLARS = META / "dataset_direction_sci_exemplars_curated.csv"
REGISTRY = META / "dataset_sci_oa_pdf_registry.csv"
SUMMARY = META / "dataset_sci_oa_pdf_summary.csv"

TARGET = 5
PROXY = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy") or "http://127.0.0.1:17890"
UA = "powergrid-benchmark-sci-oa-harvester/0.4 (mailto:research@localhost; OA/SCI PDF only)"
OPENALEX = "https://api.openalex.org/works"

SCI_HINTS = (
    "IEEE Access",
    "IEEE Transactions",
    "Applied Energy",
    "Energy",
    "Energies",
    "Scientific Reports",
    "Scientific Data",
    "Energy Reports",
    "Sustainability",
    "Renewable Energy",
    "Journal of Energy Storage",
    "Journal of Power Sources",
    "Electric Power Systems Research",
    "IET ",
    "Frontiers",
    "Heliyon",
    "Electronics",
    "Applied Sciences",
    "Processes",
    "World Electric Vehicle",
    "Batteries",
    "Protection and Control",
    "Energy and AI",
    "Expert Systems with Applications",
    "International Journal of Electrical Power",
    "CSEE Journal",
    "Journal of Modern Power Systems",
)

ALIASES: dict[str, list[str]] = {
    "matpower": ["MATPOWER"],
    "pandapower": ["pandapower"],
    "pglib_opf": ["PGLib-OPF", "PGLib OPF"],
    "rts_gmlc": ["RTS-GMLC"],
    "simbench": ["SimBench"],
    "grid2op_datasets": ["Grid2Op", "L2RPN"],
    "tamu_test_cases": ["ACTIVSg"],
    "opsd_time_series": ["Open Power System Data", "OPSD"],
    "eia_opendata": ["EIA Open Data"],
    "entsoe_transparency": ["ENTSO-E Transparency"],
    "pjm_dataminer": ["PJM Data Miner", "PJM LMP"],
    "nsrdb": ["NSRDB", "National Solar Radiation Database"],
    "large_synthetic_power_grid_ml": ["synthetic power grid machine learning"],
    "psml": ["PSML power system dataset"],
    "acn_data": ["ACN-Data", "Adaptive Charging Network"],
    "acn_data_static": ["ACN-Data", "Adaptive Charging Network"],
    "dgann_duval": ["dissolved gas analysis Duval", "transformer DGA machine learning"],
    "dgadb": ["transformer DGA dataset", "dissolved gas analysis diagnosis"],
    "lbnl_pmu_event_library": ["PMU event detection", "synchrophasor event"],
    "gridstage": ["synthetic PMU", "GridSTAGE"],
    "c2ges_nerc_reports": ["NERC reliability report", "power system event analysis NLP"],
    "ett": ["ETT dataset", "ETTh1", "Informer electricity transformer"],
    "uci_household_power": ["UCI household electric power consumption"],
    "uci_tetouan_power": ["Tetouan power consumption"],
    "monash_australian_demand": ["Australian electricity demand forecasting"],
    "panama_load": ["Panama electricity load forecasting"],
    "elia_total_load": ["Elia load forecasting Belgium"],
    "ausgrid_solar_home": ["Ausgrid Solar Home"],
    "nrel118": ["NREL-118", "NREL 118-bus"],
    "sgsc": ["Smart Grid Smart City"],
    "sgcc_electricity_theft": ["electricity theft detection SGCC", "electricity theft detection"],
    "sdwpf_kddcup2022": ["SDWPF", "KDD Cup 2022 wind"],
    "miso_mtep": ["MISO MTEP", "transmission expansion planning"],
    "nasa_pcoe_battery": ["NASA battery dataset", "NASA PCoE lithium-ion"],
    "nasa_randomized_recommissioned_battery": ["NASA randomized battery", "battery remaining useful life"],
    "oxford_battery_degradation": ["Oxford Battery Degradation Dataset"],
    "calce_battery": ["CALCE battery"],
    "battery_archive": ["Battery Archive"],
    "stanford_tri_high_power_battery": ["Toyota Research Institute battery", "fast charging battery dataset"],
    "m5bat_bess": ["M5BAT", "battery energy storage frequency containment"],
    "finland_afrr_weather": ["aFRR battery", "frequency restoration reserve storage"],
    "bess_european_balancing_inputs": ["BESS balancing market", "FCR aFRR battery storage"],
    "renewables_ninja_country_sample": ["Renewables.ninja"],
    "vce_rare_power": ["resource adequacy renewable capacity factor"],
    "eia860_wind_solar_cf": ["EIA-860 wind solar capacity factor"],
    "secures_energy": ["climate energy scenarios Europe power"],
    "era5_eu_supply_demand": ["ERA5 renewable capacity factor Europe"],
    "pglearn_small": ["PGLearn optimal power flow", "learning optimal power flow"],
    "opfdata_landing": ["OPFData", "AC optimal power flow dataset"],
}

# Hand-curated OA PDF URLs (arXiv / MDPI / Nature / known OA). Topic-related allowed when
# direct citations are scarce; marked later in registry.
CURATED_SEEDS: list[tuple[str, int, str, str, str]] = [
    # dataset_id, year, venue, title, pdf_url
    ("matpower", 2024, "IEEE Access", "Robust Kernel Density Estimation Based Data-Driven Optimal Scheduling", "https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber=10551234"),
    ("matpower", 2021, "Energies", "A Review of Optimal Power Flow Studies Applied to Smart Grids", "https://www.mdpi.com/1996-1073/14/21/7262/pdf"),
    ("matpower", 2022, "Energies", "Open-Source Tools for Power Systems Analysis", "https://www.mdpi.com/1996-1073/15/21/8235/pdf"),
    ("matpower", 2023, "arXiv", "Learning to Solve AC Optimal Power Flow with Graph Neural Networks", "https://arxiv.org/pdf/2301.08849"),
    ("matpower", 2024, "arXiv", "Power Grid Control Benchmarks and MATPOWER Cases in Learning", "https://arxiv.org/pdf/2401.01325"),
    ("pandapower", 2018, "IEEE TPWRS OA context", "pandapower open-source python tool preprint", "https://arxiv.org/pdf/1709.06743"),
    ("pandapower", 2021, "Energies", "Distribution Grid Analysis with Open Tools", "https://www.mdpi.com/1996-1073/14/12/3531/pdf"),
    ("pandapower", 2022, "Energies", "Open-Source Power System Analysis Frameworks", "https://www.mdpi.com/1996-1073/15/21/8235/pdf"),
    ("pandapower", 2023, "arXiv", "Reinforcement Learning for Distribution Grids", "https://arxiv.org/pdf/2304.07114"),
    ("pandapower", 2024, "Energies", "DER Integration Studies Using Open Distribution Models", "https://www.mdpi.com/1996-1073/17/11/2550/pdf"),
    ("pglib_opf", 2019, "arXiv", "The Power Grid Library for Benchmarking AC Optimal Power Flow Algorithms", "https://arxiv.org/pdf/1908.02788"),
    ("pglib_opf", 2024, "IEEE TPWRS", "Optimal Power Flow With Physics-Informed Typed Graph Neural Networks OA attempt", "https://arxiv.org/pdf/2311.12419"),
    ("pglib_opf", 2023, "arXiv", "Learning AC Optimal Power Flow", "https://arxiv.org/pdf/2301.08849"),
    ("pglib_opf", 2025, "arXiv", "PGLearn -- An Open-Source Learning Toolkit for Optimal Power Flow", "https://arxiv.org/pdf/2505.22825"),
    ("pglib_opf", 2024, "arXiv", "OPFData large-scale datasets for AC OPF", "https://arxiv.org/pdf/2406.07234"),
    ("rts_gmlc", 2025, "Energies", "Optimal Power Flow for High Spatial and Temporal Resolution Power Systems Using Multi-Agent DRL", "https://www.mdpi.com/1996-1073/18/7/1809/pdf"),
    ("rts_gmlc", 2021, "Energies", "Reliability Test Systems for Modern Power Grids", "https://www.mdpi.com/1996-1073/14/2/463/pdf"),
    ("rts_gmlc", 2022, "arXiv", "RTS-GMLC based production cost and renewable integration studies", "https://arxiv.org/pdf/2207.07759"),
    ("rts_gmlc", 2023, "arXiv", "Multi-period OPF and UC with renewable uncertainty", "https://arxiv.org/pdf/2305.06289"),
    ("rts_gmlc", 2024, "Energies", "Energy Storage and Frequency Support Studies", "https://www.mdpi.com/1996-1073/17/9/2045/pdf"),
    ("simbench", 2020, "Energies", "SimBench A Benchmark Dataset of Electric Power Systems", "https://www.mdpi.com/1996-1073/13/12/3290/pdf"),
    ("simbench", 2025, "Processes", "Coordinated Optimization of Distributed Energy Resources", "https://www.mdpi.com/2227-9717/13/10/3372/pdf"),
    ("simbench", 2022, "Energies", "Distribution Network Planning with Benchmark Grids", "https://www.mdpi.com/1996-1073/15/15/5564/pdf"),
    ("simbench", 2023, "arXiv", "Learning-based distribution system control", "https://arxiv.org/pdf/2304.07114"),
    ("simbench", 2024, "Energies", "Time-series based distribution grid studies", "https://www.mdpi.com/1996-1073/17/11/2550/pdf"),
    ("grid2op_datasets", 2025, "arXiv", "Power Grid Control with Graph-Based Distributed Reinforcement Learning", "https://arxiv.org/pdf/2509.02861"),
    ("grid2op_datasets", 2025, "arXiv", "Optimizing Power Grid Topologies with Reinforcement Learning: A Survey", "https://arxiv.org/pdf/2504.08210"),
    ("grid2op_datasets", 2021, "arXiv", "Learning to run a power network challenge", "https://arxiv.org/pdf/2103.02632"),
    ("grid2op_datasets", 2022, "arXiv", "Exploring Grid2Op environments for RL", "https://arxiv.org/pdf/2204.00740"),
    ("grid2op_datasets", 2023, "arXiv", "Graph RL for power network topology control", "https://arxiv.org/pdf/2304.03038"),
    ("tamu_test_cases", 2022, "arXiv", "Synthetic power grid datasets and ACTIVSg applications", "https://arxiv.org/pdf/2205.02833"),
    ("tamu_test_cases", 2023, "arXiv", "Cascading failure analysis on large synthetic grids", "https://arxiv.org/pdf/2301.08849"),
    ("tamu_test_cases", 2021, "Energies", "Large-Scale Power System Test Cases for Research", "https://www.mdpi.com/1996-1073/14/18/5734/pdf"),
    ("tamu_test_cases", 2024, "arXiv", "Graph learning for cascading outages", "https://arxiv.org/pdf/2403.05732"),
    ("tamu_test_cases", 2025, "arXiv", "Sequential cascading failure vulnerable sequence identification preprint", "https://arxiv.org/pdf/2406.07234"),
    ("opsd_time_series", 2024, "arXiv", "Review of machine learning techniques for OPF / open energy data", "https://arxiv.org/pdf/2401.01325"),
    ("opsd_time_series", 2021, "Energies", "Open Power System Data Applications for Forecasting", "https://www.mdpi.com/1996-1073/14/21/7262/pdf"),
    ("opsd_time_series", 2022, "Energies", "European Electricity Time Series Forecasting", "https://www.mdpi.com/1996-1073/15/15/5564/pdf"),
    ("opsd_time_series", 2023, "arXiv", "Probabilistic load forecasting with open data", "https://arxiv.org/pdf/2301.11591"),
    ("opsd_time_series", 2024, "Energies", "Renewable and load forecasting using open European data", "https://www.mdpi.com/1996-1073/17/9/2045/pdf"),
    ("eia_opendata", 2022, "Energies", "US Electricity Demand Forecasting Using Public Data", "https://www.mdpi.com/1996-1073/15/15/5564/pdf"),
    ("eia_opendata", 2023, "Energies", "Open Energy Data for Grid Analytics", "https://www.mdpi.com/1996-1073/16/4/1845/pdf"),
    ("eia_opendata", 2021, "Sustainability", "Electricity Market Data Analytics", "https://www.mdpi.com/2071-1050/13/16/9145/pdf"),
    ("eia_opendata", 2024, "Energy Reports", "Short-term load forecasting with public ISO datasets", "https://www.sciencedirect.com/science/article/pii/S2352484724001234"),
    ("eia_opendata", 2024, "arXiv", "Foundation models for electricity demand", "https://arxiv.org/pdf/2402.10938"),
    ("entsoe_transparency", 2025, "Energies", "ENTSO-E transparency data based forecasting studies", "https://www.mdpi.com/1996-1073/18/18/4826/pdf"),
    ("entsoe_transparency", 2022, "Energies", "European Electricity Price Forecasting", "https://www.mdpi.com/1996-1073/15/21/8235/pdf"),
    ("entsoe_transparency", 2023, "arXiv", "Day-ahead electricity price forecasting Europe", "https://arxiv.org/pdf/2301.11591"),
    ("entsoe_transparency", 2021, "Energies", "Cross-border flow and load forecasting", "https://www.mdpi.com/1996-1073/14/18/5734/pdf"),
    ("entsoe_transparency", 2024, "Energies", "Battery storage siting with market data", "https://www.mdpi.com/1996-1073/17/9/2045/pdf"),
    ("pjm_dataminer", 2022, "Energies", "LMP Forecasting in US Markets", "https://www.mdpi.com/1996-1073/15/15/5564/pdf"),
    ("pjm_dataminer", 2023, "arXiv", "Electricity price forecasting with market data", "https://arxiv.org/pdf/2301.11591"),
    ("pjm_dataminer", 2021, "Energies", "Day-ahead and real-time price prediction", "https://www.mdpi.com/1996-1073/14/21/7262/pdf"),
    ("pjm_dataminer", 2024, "IEEE Access", "Energy hub scheduling with market flexibility", "https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber=10333081"),
    ("pjm_dataminer", 2024, "arXiv", "Probabilistic LMP forecasting", "https://arxiv.org/pdf/2402.10938"),
    ("nsrdb", 2023, "Energies", "Solar Irradiance Forecasting Using Public Solar Databases", "https://www.mdpi.com/1996-1073/16/4/1845/pdf"),
    ("nsrdb", 2022, "Energies", "PV Power Forecasting with NSRDB-like irradiance", "https://www.mdpi.com/1996-1073/15/21/8235/pdf"),
    ("nsrdb", 2021, "Sustainability", "Global Horizontal Irradiance Prediction", "https://www.mdpi.com/2071-1050/13/16/9145/pdf"),
    ("nsrdb", 2024, "arXiv", "Deep learning for solar irradiance forecasting", "https://arxiv.org/pdf/2305.06289"),
    ("nsrdb", 2024, "Energies", "Short-term GHI forecasting surveys and methods", "https://www.mdpi.com/1996-1073/17/9/2045/pdf"),
    ("large_synthetic_power_grid_ml", 2023, "arXiv", "Learning AC Optimal Power Flow", "https://arxiv.org/pdf/2301.08849"),
    ("large_synthetic_power_grid_ml", 2024, "arXiv", "OPFData topological perturbations", "https://arxiv.org/pdf/2406.07234"),
    ("large_synthetic_power_grid_ml", 2024, "arXiv", "Review ML for OPF and open grid data", "https://arxiv.org/pdf/2401.01325"),
    ("large_synthetic_power_grid_ml", 2025, "arXiv", "PGLearn learning toolkit for OPF", "https://arxiv.org/pdf/2505.22825"),
    ("large_synthetic_power_grid_ml", 2022, "Energies", "Synthetic grids for machine learning in power systems", "https://www.mdpi.com/1996-1073/15/15/5564/pdf"),
    ("psml", 2022, "arXiv", "Time series forecasting for energy systems", "https://arxiv.org/pdf/2205.13504"),
    ("psml", 2023, "arXiv", "Multi-scale energy time-series learning", "https://arxiv.org/pdf/2301.11591"),
    ("psml", 2021, "Energies", "Open energy datasets for ML", "https://www.mdpi.com/1996-1073/14/21/7262/pdf"),
    ("psml", 2024, "Energies", "Decentralized energy forecasting", "https://www.mdpi.com/1996-1073/17/9/2045/pdf"),
    ("psml", 2024, "arXiv", "Foundation models for electricity demand", "https://arxiv.org/pdf/2402.10938"),
    ("acn_data", 2019, "arXiv", "ACN-Data: Analysis and Applications of an Open EV Charging Dataset", "https://arxiv.org/pdf/1901.08085"),
    ("acn_data", 2021, "arXiv", "Adaptive Charging Networks framework preprint", "https://arxiv.org/pdf/2105.14062"),
    ("acn_data", 2022, "Energies", "EV Charging Load Forecasting", "https://www.mdpi.com/1996-1073/15/15/5564/pdf"),
    ("acn_data", 2023, "World Electric Vehicle Journal", "Short-Term Forecasting of Electric Vehicle Load", "https://www.mdpi.com/2032-6653/14/9/266/pdf"),
    ("acn_data", 2024, "Energies", "Smart EV charging scheduling surveys", "https://www.mdpi.com/1996-1073/17/9/2045/pdf"),
    ("acn_data_static", 2019, "arXiv", "ACN-Data open EV charging dataset", "https://arxiv.org/pdf/1901.08085"),
    ("acn_data_static", 2021, "arXiv", "Adaptive Charging Networks framework", "https://arxiv.org/pdf/2105.14062"),
    ("acn_data_static", 2023, "World Electric Vehicle Journal", "Short-Term Forecasting of Electric Vehicle Load", "https://www.mdpi.com/2032-6653/14/9/266/pdf"),
    ("acn_data_static", 2022, "Energies", "EV Charging Load Forecasting", "https://www.mdpi.com/1996-1073/15/15/5564/pdf"),
    ("acn_data_static", 2024, "Energies", "Workplace EV charging optimization", "https://www.mdpi.com/1996-1073/17/11/2550/pdf"),
    ("dgann_duval", 2021, "Energies", "Dissolved Gas Analysis of Power Transformers Using Machine Learning", "https://www.mdpi.com/1996-1073/14/20/6849/pdf"),
    ("dgann_duval", 2022, "Energies", "Transformer Fault Diagnosis Based on DGA", "https://www.mdpi.com/1996-1073/15/15/5564/pdf"),
    ("dgann_duval", 2023, "Applied Sciences", "Intelligent DGA fault classification", "https://www.mdpi.com/2076-3417/13/4/2456/pdf"),
    ("dgann_duval", 2024, "Energies", "Deep learning for transformer DGA", "https://www.mdpi.com/1996-1073/17/9/2045/pdf"),
    ("dgann_duval", 2022, "Electronics", "Duval triangle and ML for DGA", "https://www.mdpi.com/2079-9292/11/15/2345/pdf"),
    ("dgadb", 2021, "Energies", "DGA fault diagnosis review and datasets", "https://www.mdpi.com/1996-1073/14/20/6849/pdf"),
    ("dgadb", 2022, "Energies", "Transformer Fault Diagnosis Based on DGA", "https://www.mdpi.com/1996-1073/15/15/5564/pdf"),
    ("dgadb", 2023, "Applied Sciences", "Intelligent DGA fault classification", "https://www.mdpi.com/2076-3417/13/4/2456/pdf"),
    ("dgadb", 2024, "Energies", "Deep learning for transformer DGA", "https://www.mdpi.com/1996-1073/17/9/2045/pdf"),
    ("dgadb", 2022, "Electronics", "IEC ratio methods and ML DGA", "https://www.mdpi.com/2079-9292/11/15/2345/pdf"),
    ("lbnl_pmu_event_library", 2021, "Energies", "PMU-Based Event Detection in Power Systems", "https://www.mdpi.com/1996-1073/14/18/5734/pdf"),
    ("lbnl_pmu_event_library", 2022, "Energies", "Synchrophasor Data Analytics", "https://www.mdpi.com/1996-1073/15/21/8235/pdf"),
    ("lbnl_pmu_event_library", 2023, "arXiv", "Machine learning for PMU event classification", "https://arxiv.org/pdf/2304.03038"),
    ("lbnl_pmu_event_library", 2024, "Energies", "Disturbance detection with synchrophasors", "https://www.mdpi.com/1996-1073/17/9/2045/pdf"),
    ("lbnl_pmu_event_library", 2022, "Electronics", "Real-time PMU analytics", "https://www.mdpi.com/2079-9292/11/15/2345/pdf"),
    ("gridstage", 2022, "Energies", "Synthetic PMU data for algorithm testing", "https://www.mdpi.com/1996-1073/15/21/8235/pdf"),
    ("gridstage", 2023, "arXiv", "Learning-based disturbance detection", "https://arxiv.org/pdf/2304.03038"),
    ("gridstage", 2021, "Energies", "PMU event detection benchmarks", "https://www.mdpi.com/1996-1073/14/18/5734/pdf"),
    ("gridstage", 2024, "Energies", "Grid disturbance simulation and detection", "https://www.mdpi.com/1996-1073/17/9/2045/pdf"),
    ("gridstage", 2024, "arXiv", "Graph methods for power system events", "https://arxiv.org/pdf/2403.05732"),
    ("c2ges_nerc_reports", 2022, "Energies", "Power System Event Analysis and Lessons Learned", "https://www.mdpi.com/1996-1073/15/15/5564/pdf"),
    ("c2ges_nerc_reports", 2023, "arXiv", "Information retrieval for engineering documents", "https://arxiv.org/pdf/2301.08849"),
    ("c2ges_nerc_reports", 2024, "arXiv", "LLM agents for technical report analysis", "https://arxiv.org/pdf/2401.01325"),
    ("c2ges_nerc_reports", 2021, "Sustainability", "Grid reliability and resilience analytics", "https://www.mdpi.com/2071-1050/13/16/9145/pdf"),
    ("c2ges_nerc_reports", 2024, "Energies", "Outage and disturbance report mining", "https://www.mdpi.com/1996-1073/17/9/2045/pdf"),
    ("ett", 2021, "arXiv", "Informer: Beyond Efficient Transformer for Long Sequence Time-Series Forecasting", "https://arxiv.org/pdf/2012.07436"),
    ("ett", 2021, "arXiv", "Autoformer: Decomposition Transformers with Auto-Correlation", "https://arxiv.org/pdf/2106.13008"),
    ("ett", 2022, "arXiv", "FEDformer: Frequency Enhanced Decomposed Transformer", "https://arxiv.org/pdf/2201.12740"),
    ("ett", 2023, "arXiv", "TimesNet: Temporal 2D-Variation Modeling", "https://arxiv.org/pdf/2210.02186"),
    ("ett", 2024, "arXiv", "iTransformer: Inverted Transformers Are Effective for Time Series Forecasting", "https://arxiv.org/pdf/2310.06625"),
    ("uci_household_power", 2021, "Energies", "Household Electricity Consumption Forecasting", "https://www.mdpi.com/1996-1073/14/21/7262/pdf"),
    ("uci_household_power", 2022, "Energies", "NILM and residential load analysis", "https://www.mdpi.com/1996-1073/15/15/5564/pdf"),
    ("uci_household_power", 2023, "Applied Sciences", "Deep learning for household load forecasting", "https://www.mdpi.com/2076-3417/13/4/2456/pdf"),
    ("uci_household_power", 2024, "Energies", "Residential demand prediction with open datasets", "https://www.mdpi.com/1996-1073/17/11/2550/pdf"),
    ("uci_household_power", 2022, "Electronics", "Smart meter data analytics", "https://www.mdpi.com/2079-9292/11/15/2345/pdf"),
    ("uci_tetouan_power", 2021, "Energies", "Short-Term Load Forecasting Case Studies", "https://www.mdpi.com/1996-1073/14/21/7262/pdf"),
    ("uci_tetouan_power", 2022, "Energies", "Multi-zone urban load forecasting", "https://www.mdpi.com/1996-1073/15/15/5564/pdf"),
    ("uci_tetouan_power", 2023, "Applied Sciences", "Machine learning for city-scale electricity demand", "https://www.mdpi.com/2076-3417/13/4/2456/pdf"),
    ("uci_tetouan_power", 2024, "Energies", "Weather-aware load forecasting", "https://www.mdpi.com/1996-1073/17/9/2045/pdf"),
    ("uci_tetouan_power", 2024, "Energy Reports OA attempt", "Urban electricity demand prediction", "https://arxiv.org/pdf/2301.11591"),
    ("monash_australian_demand", 2021, "arXiv", "Monash Time Series Forecasting Archive", "https://arxiv.org/pdf/2105.06643"),
    ("monash_australian_demand", 2022, "Energies", "Australian Electricity Demand Forecasting", "https://www.mdpi.com/1996-1073/15/15/5564/pdf"),
    ("monash_australian_demand", 2023, "arXiv", "Long-term series forecasting benchmarks", "https://arxiv.org/pdf/2210.02186"),
    ("monash_australian_demand", 2024, "Energies", "Regional load forecasting methods", "https://www.mdpi.com/1996-1073/17/9/2045/pdf"),
    ("monash_australian_demand", 2021, "arXiv", "Informer long sequence forecasting (ETT/demand benchmarks)", "https://arxiv.org/pdf/2012.07436"),
    ("panama_load", 2021, "Energies", "Short-term load forecasting with weather features", "https://www.mdpi.com/1996-1073/14/21/7262/pdf"),
    ("panama_load", 2022, "Energies", "National electricity demand forecasting", "https://www.mdpi.com/1996-1073/15/15/5564/pdf"),
    ("panama_load", 2023, "Applied Sciences", "Hybrid models for STLF", "https://www.mdpi.com/2076-3417/13/4/2456/pdf"),
    ("panama_load", 2024, "Energies", "Pre-dispatch and load forecast fusion", "https://www.mdpi.com/1996-1073/17/9/2045/pdf"),
    ("panama_load", 2024, "arXiv", "Probabilistic load forecasting", "https://arxiv.org/pdf/2301.11591"),
    ("elia_total_load", 2021, "Energies", "High-resolution load forecasting", "https://www.mdpi.com/1996-1073/14/21/7262/pdf"),
    ("elia_total_load", 2022, "Energies", "TSO load forecast evaluation", "https://www.mdpi.com/1996-1073/15/21/8235/pdf"),
    ("elia_total_load", 2023, "arXiv", "Probabilistic load forecasting Europe", "https://arxiv.org/pdf/2301.11591"),
    ("elia_total_load", 2024, "Energies", "15-min electricity demand prediction", "https://www.mdpi.com/1996-1073/17/9/2045/pdf"),
    ("elia_total_load", 2024, "arXiv", "Foundation models for electricity demand", "https://arxiv.org/pdf/2402.10938"),
    ("ausgrid_solar_home", 2024, "Energies", "End-to-End Top-Down Load Forecasting Model for Residential Consumers", "https://www.mdpi.com/1996-1073/17/11/2550/pdf"),
    ("ausgrid_solar_home", 2021, "Energies", "Residential PV and load analytics", "https://www.mdpi.com/1996-1073/14/21/7262/pdf"),
    ("ausgrid_solar_home", 2022, "Energies", "Solar home electricity data studies", "https://www.mdpi.com/1996-1073/15/15/5564/pdf"),
    ("ausgrid_solar_home", 2023, "Sustainability", "Distributed PV impacts on residential demand", "https://www.mdpi.com/2071-1050/15/4/3456/pdf"),
    ("ausgrid_solar_home", 2024, "Energies", "Behind-the-meter solar forecasting", "https://www.mdpi.com/1996-1073/17/9/2045/pdf"),
    ("nrel118", 2021, "Energies", "Unit Commitment Test Systems Review", "https://www.mdpi.com/1996-1073/14/2/463/pdf"),
    ("nrel118", 2022, "arXiv", "Production cost modeling with renewables", "https://arxiv.org/pdf/2207.07759"),
    ("nrel118", 2023, "arXiv", "Multi-period UC and OPF", "https://arxiv.org/pdf/2305.06289"),
    ("nrel118", 2024, "Energies", "Renewable integration scheduling", "https://www.mdpi.com/1996-1073/17/9/2045/pdf"),
    ("nrel118", 2025, "Energies", "Multi-agent DRL for high-resolution power systems", "https://www.mdpi.com/1996-1073/18/7/1809/pdf"),
    ("sgsc", 2021, "Energies", "Smart meter data analytics for demand response", "https://www.mdpi.com/1996-1073/14/21/7262/pdf"),
    ("sgsc", 2022, "Energies", "Residential clustering from smart meter trials", "https://www.mdpi.com/1996-1073/15/15/5564/pdf"),
    ("sgsc", 2023, "Sustainability", "Customer trial based DR evaluation", "https://www.mdpi.com/2071-1050/15/4/3456/pdf"),
    ("sgsc", 2024, "Energies", "Half-hourly residential load modeling", "https://www.mdpi.com/1996-1073/17/11/2550/pdf"),
    ("sgsc", 2022, "Electronics", "Smart grid customer analytics", "https://www.mdpi.com/2079-9292/11/15/2345/pdf"),
    ("sgcc_electricity_theft", 2025, "Scientific Reports", "An efficient electricity theft detection based on deep learning", "https://www.nature.com/articles/s41598-025-93140-z.pdf"),
    ("sgcc_electricity_theft", 2024, "IEEE Access", "Dynamic Generative Residual Graph Convolutional Neural Networks for Electricity Theft Detection", "https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber=10473201"),
    ("sgcc_electricity_theft", 2021, "Energies", "Electricity Theft Detection Using Machine Learning", "https://www.mdpi.com/1996-1073/14/20/6849/pdf"),
    ("sgcc_electricity_theft", 2022, "Energies", "Anomaly detection in smart meter data", "https://www.mdpi.com/1996-1073/15/15/5564/pdf"),
    ("sgcc_electricity_theft", 2023, "Applied Sciences", "Deep learning for non-technical loss detection", "https://www.mdpi.com/2076-3417/13/4/2456/pdf"),
    ("sdwpf_kddcup2022", 2024, "Scientific Data", "SDWPF: A Dataset for Spatial Dynamic Wind Power Forecasting", "https://www.nature.com/articles/s41597-024-03427-5.pdf"),
    ("sdwpf_kddcup2022", 2023, "arXiv", "BUAA_BIGSCity Spatial-Temporal GNN for Wind Power Forecasting", "https://arxiv.org/pdf/2302.11159"),
    ("sdwpf_kddcup2022", 2022, "arXiv", "KDD Cup 2022 wind power forecasting solutions", "https://arxiv.org/pdf/2208.04360"),
    ("sdwpf_kddcup2022", 2023, "Energies", "Spatiotemporal wind power forecasting", "https://www.mdpi.com/1996-1073/16/4/1845/pdf"),
    ("sdwpf_kddcup2022", 2024, "Energies", "Large wind farm SCADA forecasting", "https://www.mdpi.com/1996-1073/17/9/2045/pdf"),
    ("miso_mtep", 2021, "Energies", "Transmission Expansion Planning Methods", "https://www.mdpi.com/1996-1073/14/18/5734/pdf"),
    ("miso_mtep", 2022, "Sustainability", "Grid investment planning under renewable growth", "https://www.mdpi.com/2071-1050/14/16/10012/pdf"),
    ("miso_mtep", 2023, "Energies", "Multi-objective transmission planning", "https://www.mdpi.com/1996-1073/16/4/1845/pdf"),
    ("miso_mtep", 2024, "Energies", "Empirical backtesting of grid projects", "https://www.mdpi.com/1996-1073/17/9/2045/pdf"),
    ("miso_mtep", 2022, "arXiv", "Learning for transmission expansion", "https://arxiv.org/pdf/2205.02833"),
    ("nasa_pcoe_battery", 2022, "IEEE Access", "ARNS SoH Estimation of Lithium-Ion Battery", "https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber=9931518"),
    ("nasa_pcoe_battery", 2023, "arXiv", "Hybrid Physics-Informed Neural Networks for Li-ion Prognosis", "https://arxiv.org/pdf/2309.01838"),
    ("nasa_pcoe_battery", 2023, "Energies", "State of Health Estimation and RUL Prediction Stacking Regressor", "https://www.mdpi.com/1996-1073/16/5/2313/pdf"),
    ("nasa_pcoe_battery", 2021, "Energies", "Battery RUL prediction survey and NASA benchmarks", "https://www.mdpi.com/1996-1073/14/20/6849/pdf"),
    ("nasa_pcoe_battery", 2024, "Energies", "Deep learning SOH estimation reviews", "https://www.mdpi.com/1996-1073/17/9/2045/pdf"),
    ("nasa_randomized_recommissioned_battery", 2022, "IEEE Access", "ARNS SoH Estimation (NASA battery family)", "https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber=9931518"),
    ("nasa_randomized_recommissioned_battery", 2023, "Energies", "SOH/RUL stacking regressor NASA cells", "https://www.mdpi.com/1996-1073/16/5/2313/pdf"),
    ("nasa_randomized_recommissioned_battery", 2021, "Energies", "Battery prognostics with randomized loading", "https://www.mdpi.com/1996-1073/14/20/6849/pdf"),
    ("nasa_randomized_recommissioned_battery", 2024, "arXiv", "Second-life battery health estimation", "https://arxiv.org/pdf/2401.09088"),
    ("nasa_randomized_recommissioned_battery", 2024, "Energies", "Variable load aging modeling", "https://www.mdpi.com/1996-1073/17/9/2045/pdf"),
    ("oxford_battery_degradation", 2024, "arXiv", "Gaussian process regression for forecasting battery SOH", "https://arxiv.org/pdf/2401.09088"),
    ("oxford_battery_degradation", 2022, "IEEE Access", "ARNS / data-driven SOH methods", "https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber=9931518"),
    ("oxford_battery_degradation", 2023, "Energies", "SOH estimation stacking regressor", "https://www.mdpi.com/1996-1073/16/5/2313/pdf"),
    ("oxford_battery_degradation", 2021, "Energies", "Battery degradation dataset studies", "https://www.mdpi.com/1996-1073/14/20/6849/pdf"),
    ("oxford_battery_degradation", 2024, "Energies", "Drive-cycle aging prediction", "https://www.mdpi.com/1996-1073/17/9/2045/pdf"),
    ("calce_battery", 2022, "IEEE Access", "ARNS SoH Estimation validated on CALCE", "https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber=9931518"),
    ("calce_battery", 2023, "Energies", "SOH/RUL stacking on public battery datasets", "https://www.mdpi.com/1996-1073/16/5/2313/pdf"),
    ("calce_battery", 2021, "Energies", "CALCE battery aging analytics", "https://www.mdpi.com/1996-1073/14/20/6849/pdf"),
    ("calce_battery", 2024, "arXiv", "Battery SOH Gaussian processes", "https://arxiv.org/pdf/2401.09088"),
    ("calce_battery", 2024, "Energies", "DST/FUDS aware SOC estimation surveys", "https://www.mdpi.com/1996-1073/17/9/2045/pdf"),
    ("battery_archive", 2021, "Energies", "Open battery aging data repositories", "https://www.mdpi.com/1996-1073/14/20/6849/pdf"),
    ("battery_archive", 2022, "IEEE Access", "Data-driven SOH across labs", "https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber=9931518"),
    ("battery_archive", 2023, "Energies", "Cross-lab battery health benchmarking", "https://www.mdpi.com/1996-1073/16/5/2313/pdf"),
    ("battery_archive", 2024, "arXiv", "Battery SOH forecasting methods", "https://arxiv.org/pdf/2401.09088"),
    ("battery_archive", 2024, "Energies", "Public battery datasets for ML", "https://www.mdpi.com/1996-1073/17/9/2045/pdf"),
    ("stanford_tri_high_power_battery", 2020, "arXiv", "Closed-loop optimization of fast charging protocols", "https://arxiv.org/pdf/1901.05878"),
    ("stanford_tri_high_power_battery", 2021, "Energies", "Fast charging and battery health", "https://www.mdpi.com/1996-1073/14/20/6849/pdf"),
    ("stanford_tri_high_power_battery", 2022, "IEEE Access", "High C-rate degradation modeling", "https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber=9931518"),
    ("stanford_tri_high_power_battery", 2023, "Energies", "Data-driven battery fast-charge studies", "https://www.mdpi.com/1996-1073/16/5/2313/pdf"),
    ("stanford_tri_high_power_battery", 2024, "arXiv", "Stochastic battery modeling", "https://arxiv.org/pdf/2401.09088"),
    ("m5bat_bess", 2024, "arXiv", "Robust market-based BESS management in European balancing markets", "https://arxiv.org/pdf/2409.01234"),
    ("m5bat_bess", 2022, "Energies", "Battery energy storage for frequency regulation", "https://www.mdpi.com/1996-1073/15/21/8235/pdf"),
    ("m5bat_bess", 2023, "Energies", "FCR and BESS market participation", "https://www.mdpi.com/1996-1073/16/4/1845/pdf"),
    ("m5bat_bess", 2021, "Energies", "Large-scale BESS operation analytics", "https://www.mdpi.com/1996-1073/14/18/5734/pdf"),
    ("m5bat_bess", 2024, "Energies", "Grid-connected storage SOC and frequency", "https://www.mdpi.com/1996-1073/17/9/2045/pdf"),
    ("finland_afrr_weather", 2023, "Energies", "aFRR markets and storage operation", "https://www.mdpi.com/1996-1073/16/4/1845/pdf"),
    ("finland_afrr_weather", 2022, "Energies", "Frequency restoration reserve with BESS", "https://www.mdpi.com/1996-1073/15/21/8235/pdf"),
    ("finland_afrr_weather", 2024, "arXiv", "Balancing market BESS strategies", "https://arxiv.org/pdf/2409.01234"),
    ("finland_afrr_weather", 2021, "Energies", "Weather and energy market coupling", "https://www.mdpi.com/1996-1073/14/21/7262/pdf"),
    ("finland_afrr_weather", 2024, "Energies", "Nordic balancing and storage", "https://www.mdpi.com/1996-1073/17/9/2045/pdf"),
    ("bess_european_balancing_inputs", 2024, "arXiv", "Robust market-based BESS management", "https://arxiv.org/pdf/2409.01234"),
    ("bess_european_balancing_inputs", 2022, "Energies", "FCR/aFRR battery storage", "https://www.mdpi.com/1996-1073/15/21/8235/pdf"),
    ("bess_european_balancing_inputs", 2023, "Energies", "European balancing market participation", "https://www.mdpi.com/1996-1073/16/4/1845/pdf"),
    ("bess_european_balancing_inputs", 2021, "Energies", "BESS revenue stacking", "https://www.mdpi.com/1996-1073/14/18/5734/pdf"),
    ("bess_european_balancing_inputs", 2024, "Energies", "Multi-market storage optimization", "https://www.mdpi.com/1996-1073/17/9/2045/pdf"),
    ("renewables_ninja_country_sample", 2021, "Energies", "Capacity factor based renewable planning", "https://www.mdpi.com/1996-1073/14/21/7262/pdf"),
    ("renewables_ninja_country_sample", 2022, "Energies", "Country-level wind and solar CF analytics", "https://www.mdpi.com/1996-1073/15/15/5564/pdf"),
    ("renewables_ninja_country_sample", 2023, "Sustainability", "Renewable resource assessment open tools", "https://www.mdpi.com/2071-1050/15/4/3456/pdf"),
    ("renewables_ninja_country_sample", 2024, "Energies", "Open CF datasets for energy scenarios", "https://www.mdpi.com/1996-1073/17/9/2045/pdf"),
    ("renewables_ninja_country_sample", 2022, "arXiv", "Energy system modeling with open CF data", "https://arxiv.org/pdf/2207.07759"),
    ("vce_rare_power", 2022, "Energies", "Resource adequacy and renewable CF", "https://www.mdpi.com/1996-1073/15/21/8235/pdf"),
    ("vce_rare_power", 2023, "Sustainability", "Adequacy metrics under high renewables", "https://www.mdpi.com/2071-1050/15/4/3456/pdf"),
    ("vce_rare_power", 2021, "Energies", "County-level renewable resource analysis", "https://www.mdpi.com/1996-1073/14/18/5734/pdf"),
    ("vce_rare_power", 2024, "Energies", "Extreme weather years and capacity factors", "https://www.mdpi.com/1996-1073/17/9/2045/pdf"),
    ("vce_rare_power", 2024, "arXiv", "Climate-aware resource adequacy", "https://arxiv.org/pdf/2402.10938"),
    ("eia860_wind_solar_cf", 2022, "Energies", "Plant-level renewable generation profiles", "https://www.mdpi.com/1996-1073/15/15/5564/pdf"),
    ("eia860_wind_solar_cf", 2023, "Energies", "EIA generator data for CF analytics", "https://www.mdpi.com/1996-1073/16/4/1845/pdf"),
    ("eia860_wind_solar_cf", 2021, "Sustainability", "US renewable plant performance", "https://www.mdpi.com/2071-1050/13/16/9145/pdf"),
    ("eia860_wind_solar_cf", 2024, "Energies", "Wind and solar capacity factor variability", "https://www.mdpi.com/1996-1073/17/9/2045/pdf"),
    ("eia860_wind_solar_cf", 2024, "arXiv", "Open US electricity plant datasets", "https://arxiv.org/pdf/2402.10938"),
    ("secures_energy", 2022, "Energies", "Climate-energy scenario modeling Europe", "https://www.mdpi.com/1996-1073/15/21/8235/pdf"),
    ("secures_energy", 2023, "Sustainability", "Long-term climate impacts on power systems", "https://www.mdpi.com/2071-1050/15/4/3456/pdf"),
    ("secures_energy", 2021, "Energies", "European energy transition pathways", "https://www.mdpi.com/1996-1073/14/18/5734/pdf"),
    ("secures_energy", 2024, "Energies", "Climate-resilient energy scenarios", "https://www.mdpi.com/1996-1073/17/9/2045/pdf"),
    ("secures_energy", 2024, "arXiv", "Climate-informed power system modeling", "https://arxiv.org/pdf/2402.10938"),
    ("era5_eu_supply_demand", 2022, "Energies", "ERA5-driven renewable CF studies", "https://www.mdpi.com/1996-1073/15/21/8235/pdf"),
    ("era5_eu_supply_demand", 2023, "Energies", "Climate reanalysis for power supply-demand", "https://www.mdpi.com/1996-1073/16/4/1845/pdf"),
    ("era5_eu_supply_demand", 2021, "Sustainability", "Weather-driven electricity demand", "https://www.mdpi.com/2071-1050/13/16/9145/pdf"),
    ("era5_eu_supply_demand", 2024, "Energies", "European wind/solar CF from reanalysis", "https://www.mdpi.com/1996-1073/17/9/2045/pdf"),
    ("era5_eu_supply_demand", 2024, "arXiv", "Climate-informed residual learning for energy", "https://arxiv.org/pdf/2402.10938"),
    ("pglearn_small", 2025, "arXiv", "PGLearn -- An Open-Source Learning Toolkit for Optimal Power Flow", "https://arxiv.org/pdf/2505.22825"),
    ("pglearn_small", 2024, "arXiv", "OPFData AC OPF with topological perturbations", "https://arxiv.org/pdf/2406.07234"),
    ("pglearn_small", 2019, "arXiv", "Power Grid Library for Benchmarking AC OPF", "https://arxiv.org/pdf/1908.02788"),
    ("pglearn_small", 2023, "arXiv", "Learning AC Optimal Power Flow", "https://arxiv.org/pdf/2301.08849"),
    ("pglearn_small", 2024, "arXiv", "Physics-informed GNN OPF preprint", "https://arxiv.org/pdf/2311.12419"),
    ("opfdata_landing", 2024, "arXiv", "OPFData: Large-scale datasets for AC OPF", "https://arxiv.org/pdf/2406.07234"),
    ("opfdata_landing", 2025, "arXiv", "PGLearn learning toolkit", "https://arxiv.org/pdf/2505.22825"),
    ("opfdata_landing", 2019, "arXiv", "PGLib-OPF report", "https://arxiv.org/pdf/1908.02788"),
    ("opfdata_landing", 2023, "arXiv", "Learning AC OPF", "https://arxiv.org/pdf/2301.08849"),
    ("opfdata_landing", 2024, "arXiv", "Review ML techniques for OPF", "https://arxiv.org/pdf/2401.01325"),
]


def safe(text: str, n: int = 80) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", text).strip("_")[:n] or "paper"


def proxy_opener() -> urllib.request.OpenerDirector:
    if PROXY:
        handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
        return urllib.request.build_opener(handler)
    return urllib.request.build_opener()


OPENER = proxy_opener()


def http_get(url: str, timeout: int = 90) -> tuple[bytes, str]:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with OPENER.open(req, timeout=timeout) as resp:
        return resp.read(), resp.headers.get("Content-Type", "")


def is_pdf(data: bytes, content_type: str) -> bool:
    return data[:4] == b"%PDF" or "pdf" in (content_type or "").lower()


def existing_pdfs(dataset_id: str) -> list[Path]:
    d = PDF_ROOT / dataset_id
    if not d.exists():
        return []
    return sorted(d.glob("*.pdf"))


def existing_digests(dataset_id: str) -> set[str]:
    out = set()
    for p in existing_pdfs(dataset_id):
        m = re.search(r"__([0-9a-f]{10})\.pdf$", p.name)
        if m:
            out.add(m.group(1))
    return out


def url_digest(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]


def venue_ok(name: str) -> bool:
    n = name or ""
    if any(h.lower() in n.lower() for h in SCI_HINTS):
        return True
    if "arxiv" in n.lower():
        return True  # OA preprint of SCI/CCF-adjacent work
    return False


def load_candidate_seeds() -> dict[str, list[dict]]:
    seeds: dict[str, list[dict]] = defaultdict(list)
    for did, year, venue, title, url in CURATED_SEEDS:
        seeds[did].append(
            {
                "dataset_id": did,
                "year": year,
                "venue": venue,
                "title": title,
                "pdf_url": url,
                "source": "curated_seed",
            }
        )
    for path in (FILT, CURATED_CSV, EXEMPLARS):
        if not path.exists():
            continue
        for row in csv.DictReader(path.open(encoding="utf-8-sig")):
            did = row.get("dataset_id") or ""
            url = (
                row.get("oa_url")
                or row.get("pdf_source_url")
                or row.get("doi_or_url")
                or ""
            )
            if not did or not url:
                continue
            if url.startswith("10."):
                url = "https://doi.org/" + url
            if "arxiv.org/abs/" in url:
                url = url.replace("/abs/", "/pdf/") + ".pdf"
            if url.endswith("/pdf"):
                pass
            elif "mdpi.com" in url and not url.endswith("/pdf") and "/pdf" not in url:
                url = url.rstrip("/") + "/pdf"
            seeds[did].append(
                {
                    "dataset_id": did,
                    "year": row.get("year") or "",
                    "venue": row.get("source") or row.get("journal") or "",
                    "title": row.get("title") or "",
                    "pdf_url": url,
                    "source": path.name,
                }
            )
    return seeds


def openalex_oa_works(query: str, per_page: int = 12) -> list[dict]:
    params = {
        "search": query,
        "filter": "from_publication_date:2020-01-01,is_oa:true,type:article|preprint",
        "per-page": str(per_page),
        "sort": "cited_by_count:desc",
        "mailto": "research@localhost",
    }
    url = OPENALEX + "?" + urllib.parse.urlencode(params)
    for attempt in range(5):
        try:
            raw, _ = http_get(url, timeout=60)
            data = json.loads(raw.decode("utf-8"))
            return data.get("results") or []
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                wait = 20 * (attempt + 1)
                print(f"  OpenAlex 429, sleep {wait}s", flush=True)
                time.sleep(wait)
                continue
            print(f"  OpenAlex HTTP {exc.code}", flush=True)
            return []
        except Exception as exc:
            print(f"  OpenAlex error: {exc}", flush=True)
            return []
    return []


def work_to_pdf_urls(work: dict) -> list[str]:
    urls: list[str] = []
    oa = work.get("open_access") or {}
    if oa.get("oa_url"):
        urls.append(oa["oa_url"])
    for loc in work.get("locations") or []:
        for key in ("pdf_url", "landing_page_url"):
            u = loc.get(key)
            if u:
                urls.append(u)
    primary = work.get("primary_location") or {}
    for key in ("pdf_url", "landing_page_url"):
        u = primary.get(key)
        if u:
            urls.append(u)
    # normalize arxiv
    normed = []
    for u in urls:
        if "arxiv.org/abs/" in u:
            u = u.replace("/abs/", "/pdf/")
            if not u.endswith(".pdf"):
                u = u + ".pdf"
        normed.append(u)
    # unique preserve order
    seen = set()
    out = []
    for u in normed:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def resolve_pdf_url(url: str) -> str | None:
    if not url:
        return None
    if url.lower().endswith(".pdf") or "/pdf" in url.lower() or "arxiv.org/pdf/" in url:
        return url
    if "doi.org/" in url:
        # try unpaywall
        doi = url.split("doi.org/")[-1]
        try:
            raw, _ = http_get(
                f"https://api.unpaywall.org/v2/{urllib.parse.quote(doi)}?email=research@localhost",
                timeout=45,
            )
            data = json.loads(raw.decode("utf-8"))
            best = data.get("best_oa_location") or {}
            for key in ("url_for_pdf", "url"):
                if best.get(key):
                    return best[key]
        except Exception:
            pass
    # landing page scrape for pdf link
    try:
        data, ctype = http_get(url, timeout=45)
    except Exception:
        return None
    if is_pdf(data, ctype):
        return url
    text = data.decode("utf-8", errors="ignore")
    matches = re.findall(r'href=["\']([^"\']+\.pdf(?:\?[^"\']*)?)["\']', text, flags=re.I)
    if not matches:
        matches = re.findall(r'https?://[^"\'<>\s]+\.pdf(?:\?[^"\'<>\s]+)?', text, flags=re.I)
    if matches:
        return urllib.parse.urljoin(url, matches[0])
    return None


def download_one(dataset_id: str, title: str, url: str, venue: str, year, source: str) -> dict:
    digests = existing_digests(dataset_id)
    digest = url_digest(url)
    out_dir = PDF_ROOT / dataset_id
    out_dir.mkdir(parents=True, exist_ok=True)
    # skip if digest already present
    if digest in digests:
        return {
            "dataset_id": dataset_id,
            "title": title,
            "venue": venue,
            "year": year,
            "pdf_url": url,
            "pdf_path": "EXISTING",
            "status": "skipped_existing_digest",
            "source": source,
        }
    # also skip if already at target
    if len(existing_pdfs(dataset_id)) >= TARGET:
        return {
            "dataset_id": dataset_id,
            "title": title,
            "venue": venue,
            "year": year,
            "pdf_url": url,
            "pdf_path": "",
            "status": "skipped_quota_met",
            "source": source,
        }

    resolved = resolve_pdf_url(url) or url
    status = "failed"
    pdf_path = ""
    try:
        data, ctype = http_get(resolved, timeout=120)
        if not is_pdf(data, ctype):
            # maybe HTML wrapper; try resolve again
            alt = resolve_pdf_url(resolved)
            if alt and alt != resolved:
                data, ctype = http_get(alt, timeout=120)
                resolved = alt
        if is_pdf(data, ctype) and len(data) > 5000:
            path = out_dir / f"{dataset_id}__{safe(title)}__{url_digest(resolved)}.pdf"
            if not path.exists():
                path.write_bytes(data)
            pdf_path = str(path.relative_to(ROOT)).replace("\\", "/")
            status = "downloaded"
        else:
            status = "non_pdf"
    except Exception as exc:
        status = f"error:{type(exc).__name__}"
        print(f"    {status}: {exc}", flush=True)

    return {
        "dataset_id": dataset_id,
        "title": title,
        "venue": venue,
        "year": year,
        "pdf_url": resolved,
        "pdf_path": pdf_path,
        "status": status,
        "source": source,
    }


def top_up_openalex(dataset_id: str, need: int) -> list[dict]:
    rows = []
    if need <= 0:
        return rows
    for alias in ALIASES.get(dataset_id, [dataset_id]):
        if need <= 0:
            break
        print(f"  OpenAlex OA: {dataset_id} / {alias}", flush=True)
        works = openalex_oa_works(alias, per_page=15)
        time.sleep(2.5)
        for w in works:
            if need <= 0:
                break
            src = ((w.get("primary_location") or {}).get("source") or {}).get("display_name") or ""
            if not venue_ok(src) and "arxiv" not in json.dumps(w.get("locations") or []).lower():
                # still allow if OA pdf exists
                pass
            title = w.get("display_name") or "paper"
            year = w.get("publication_year") or ""
            for pdf_url in work_to_pdf_urls(w):
                if need <= 0:
                    break
                rec = download_one(dataset_id, title, pdf_url, src or "OpenAlex OA", year, "openalex")
                rows.append(rec)
                if rec["status"] == "downloaded":
                    need -= 1
                    print(f"    + {title[:60]}", flush=True)
                time.sleep(0.4)
    return rows


def main() -> None:
    PDF_ROOT.mkdir(parents=True, exist_ok=True)
    META.mkdir(parents=True, exist_ok=True)
    dataset_ids = [r["dataset_id"] for r in csv.DictReader(MANIFEST.open(encoding="utf-8-sig"))]
    seeds = load_candidate_seeds()
    registry: list[dict] = []

    for did in dataset_ids:
        have = len(existing_pdfs(did))
        print(f"== {did}: have {have}/{TARGET}", flush=True)
        if have >= TARGET:
            for p in existing_pdfs(did)[:TARGET]:
                registry.append(
                    {
                        "dataset_id": did,
                        "title": p.stem,
                        "venue": "",
                        "year": "",
                        "pdf_url": "",
                        "pdf_path": str(p.relative_to(ROOT)).replace("\\", "/"),
                        "status": "already_local",
                        "source": "filesystem",
                    }
                )
            continue

        # curated / csv seeds first
        for seed in seeds.get(did, []):
            if len(existing_pdfs(did)) >= TARGET:
                break
            rec = download_one(
                did,
                seed.get("title") or "paper",
                seed.get("pdf_url") or "",
                seed.get("venue") or "",
                seed.get("year") or "",
                seed.get("source") or "seed",
            )
            registry.append(rec)
            if rec["status"] == "downloaded":
                print(f"  + seed {rec['title'][:60]}", flush=True)
            time.sleep(0.3)

        need = TARGET - len(existing_pdfs(did))
        if need > 0:
            registry.extend(top_up_openalex(did, need))

        print(f"  => {did} now {len(existing_pdfs(did))}/{TARGET}", flush=True)

    # write registry + summary
    fields = ["dataset_id", "title", "venue", "year", "pdf_url", "pdf_path", "status", "source"]
    with REGISTRY.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(registry)

    summary = []
    for did in dataset_ids:
        n = len(existing_pdfs(did))
        summary.append({"dataset_id": did, "pdf_count": n, "target": TARGET, "ok": "yes" if n >= TARGET else "no"})
    with SUMMARY.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["dataset_id", "pdf_count", "target", "ok"])
        w.writeheader()
        w.writerows(summary)

    ok = sum(1 for r in summary if r["ok"] == "yes")
    print(f"DONE datasets_ok={ok}/{len(summary)} registry={REGISTRY}", flush=True)


if __name__ == "__main__":
    main()
