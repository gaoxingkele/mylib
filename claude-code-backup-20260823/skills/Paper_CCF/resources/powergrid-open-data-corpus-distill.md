# Power-grid open-data corpus distill (local PDF cache)

Source: `powergrid_benchmark/papers/literature/dataset_benchmark_papers/pdfs/`
As-of: 2026-07-27 · Unique PDFs analyzed: **90** (of 245 files; deduped by content digest).
Extraction: first ≤4 pages via pypdf (front-matter bias). Use as **routing/evidence heuristics**, not as WoS-verified journal acceptance rates.

## Topic mix

- `battery`: 60
- `wind_solar`: 31
- `opf_learning`: 20
- `load_forecasting`: 16
- `other`: 13
- `resilience`: 12
- `rl_grid`: 10
- `theft_anomaly`: 6
- `pmu_event`: 5
- `ev_charging`: 4
- `dga`: 3

## Front-matter signal rates (unique PDFs)

- **baseline_compare**: 55/90 (61%)
- **real_grid_case**: 43/90 (48%)
- **limitation_section**: 37/90 (41%)
- **public_dataset_mention**: 37/90 (41%)
- **metrics_named**: 31/90 (34%)
- **numbered_contrib**: 25/90 (28%)
- **code_release**: 24/90 (27%)
- **ablation**: 9/90 (10%)

## OA SCI targets named in curated dataset→journal map

- Energies: 46 dataset rows
- IEEE Access: 43 dataset rows
- Energy Reports: 11 dataset rows
- Sustainability: 9 dataset rows
- Scientific Data: 5 dataset rows
- Applied Sciences: 4 dataset rows
- Electronics: 4 dataset rows
- Batteries: 3 dataset rows
- Processes: 2 dataset rows
- World Electric Vehicle Journal: 2 dataset rows
- Scientific Reports: 2 dataset rows
- Frontiers in Energy Research: 2 dataset rows
- IET GTD: 1 dataset rows
- IET Energy Systems Integration: 1 dataset rows
- APL Machine Learning: 1 dataset rows
- Journal of Energy Storage OA option: 1 dataset rows

## Distilled acceptance patterns for Paper_CCF OA journals

### Shared patterns across this corpus (power × ML / open data)

1. **Public benchmark naming is a first-class contribution signal.** High-fit papers explicitly name ETT/Informer, ACN-Data, NASA PCoE, SDWPF, PGLib-OPF, Grid2Op/L2RPN, MATPOWER/SimBench — and state train/test protocol. Anonymous “a utility dataset” without a release path is weaker for IEEE Access / Energies / Scientific Reports.
2. **Baselines are genre-dependent.** Forecasting/theft papers almost always list named baselines + MAE/RMSE/MAPE or F1/AUC. OPF/RL/planning papers often pass on case-study self-comparison (IEEE-bus / scenario schemes) without a long DL baseline table.
3. **Ablation/sensitivity is uneven.** Present in ~strong forecasting & hybrid-method papers; often absent in survey/framework and pure case studies — Energies historically still accepts those if energy application + validation exist.
4. **Code/data availability statements are common in arXiv/open-data lines; rare as runnable artifacts.** For OA journals, a Data Availability Statement + DOI/GitHub link is enough; artifact badges are optional.
5. **Numbered contribution lists (3–5 bullets)** appear frequently in IEEE-Access-style and applied-energy framing even when novelty is incremental.
6. **Topic→OA journal routing observed in curated map:** load/price/wind/solar forecast → Energies / Energy Reports / IEEE Access; OPF/learning-OPF/GNN → IEEE Access / Energies; battery SOH → IEEE Access / Energies / Electronics; EV/ACN → Energies / IEEE Access (+ WEVJ outside this skill set); theft → Scientific Reports / IEEE Access; PMU/event → IEEE Access / Electronics / Sensors; resilience/planning with SDG narrative → Sustainability / Energies.

### Per-journal skill updates implied by this corpus

| Journal skill | What this corpus adds |
|---|---|
| `ieee-access` | Open power benchmarks (ETT, NASA, ACN, PGLib) + numbered contributions + baseline tables without significance tests remain the norm for DL; private utility data still OK if protocol disclosed. |
| `mdpi-energies` | Strongest catch-all for energy-applied forecasting, DER, BESS markets, SimBench/Ausgrid-style studies; sensitivity preferred; public dataset citation strengthens reproducibility claims. |
| `mdpi-electronics` | Fits PMU/event, DGA/transformer diagnosis, embedded/edge metering ML when EE hardware/signal angle is explicit. |
| `mdpi-applied-sciences` | Application-first case studies (utility planning, field metering) can substitute heavy algorithmic novelty. |
| `mdpi-sustainability` | Only when renewable integration / DR / planning papers quantify sustainability/SDG impact — not pure MAE tables. |
| `mdpi-sensors` | PMU / IoT sensing / condition monitoring must be the core, not a side dataset. |
| `elsevier-energy-reports` | AI-for-energy forecasting/optimization with energy contribution in front; natural Q1 OA companion to Energy/Applied Energy. |
| `frontiers-energy-research` | Route via Smart Grids / Energy Systems sections for BESS balancing, DR, grid optimization. |
| `nature-scientific-reports` | Soundness megajournal path for theft/anomaly and cross-domain ML-on-grid; Nature OA PDF examples exist in corpus (theft, SDWPF→Scientific Data sibling). |
| `ieee-oajpe` / `csee-jpes` / `pcmp` | Prefer when contribution is power-system-first (planning/ops/protection) rather than generic DL-on-ETT. |

## Sample inventory (unique digests)

| Topics | Title (from filename) | Public-data | Baselines | Metrics |
|---|---|:---:|:---:|:---:|
| battery | ACN-Data Analysis and Applications |  | Y |  |
| battery | Adaptive Charging Networks Framework |  |  | Y |
| rl_grid, battery, ev_charging | Out-of-Distribution-Aware Electric Vehicle Charging |  | Y |  |
| other | Smart charging of electric vehicles survey |  |  |  |
| opf_learning, battery | Vehicle-to-grid optimization and forecasting |  |  | Y |
| battery | ACN-Data Analysis and Applications of an Open EV Charging Dataset |  | Y |  |
| battery | Deep learning for solar irradiance forecasting |  |  |  |
| battery | Foundation models for electricity demand |  | Y | Y |
| load_forecasting, theft_anomaly | PatchTST A Time Series is Worth 64 Words |  | Y | Y |
| battery | Probabilistic load forecasting |  |  |  |
| load_forecasting, theft_anomaly | TimesNet Temporal 2D-Variation Modeling | Y |  | Y |
| opf_learning | Closed-loop optimization of fast charging |  |  |  |
| battery | Data-driven battery health estimation review |  |  |  |
| battery | Gaussian process regression battery SOH |  |  |  |
| other | Hybrid PINN Li-ion battery prognosis | Y |  | Y |
| battery | Robust market-based BESS management | Y | Y |  |
| other | Electricity price forecasting deep learning |  |  |  |
| other | Production cost modeling with renewables |  |  | Y |
| battery | Contingency analysis and N-1 security ML |  | Y |  |
| dga | Learning to Solve AC Optimal Power Flow | Y | Y | Y |
| battery | Power system resilience assessment and planning |  | Y |  |
| battery | Review of ML techniques for optimal power flow | Y | Y |  |
| pmu_event, resilience | The Economic Toll of Grid Fragility Quantifying the Costs and National | Y |  |  |
| other | Graph neural networks for power systems |  |  |  |
| battery | Machine learning for power transformer DGA |  |  |  |
| battery | Spatio-temporal wind power forecasting review |  |  |  |
| load_forecasting, battery, theft_anomaly | DLinear Are Transformers Effective for Time Series | Y | Y | Y |
| load_forecasting, battery, ev_charging | Electric Vehicle Scheduling Model With Strategic Siting and Incentive  |  | Y |  |
| load_forecasting | FEDformer Frequency Enhanced Decomposed Transformer | Y | Y |  |
| load_forecasting | Autoformer Decomposition Transformers | Y | Y | Y |
| load_forecasting, battery, pmu_event | Informer Beyond Efficient Transformer |  |  | Y |
| load_forecasting, battery | iTransformer Inverted Transformers | Y | Y | Y |
| rl_grid, battery, wind_solar | Fault Detection for Agents in Power Grid Topology Optimization A Compr | Y | Y | Y |
| battery | Learning to run a power network challenge |  |  |  |
| rl_grid, battery, wind_solar | Optimizing Power Grid Topologies with Reinforcement Learning A Survey  |  | Y |  |
| rl_grid, battery, wind_solar | Power Grid Control with Graph-Based Distributed Reinforcement Learning |  | Y |  |
| rl_grid, battery, wind_solar | State and Action Factorization in Power Grids | Y | Y |  |
| other | Graph neural networks for cascading failure analysis |  | Y |  |
| other | Graph RL for power network topology control |  | Y |  |
| battery | Learning to run a power network challenge |  |  |  |
| battery | PMU-based event detection deep learning |  | Y |  |
| opf_learning, battery, wind_solar | OPFData Large-scale datasets for AC OPF |  | Y |  |
| opf_learning, battery, wind_solar | PGLearn Open-Source Learning Toolkit for OPF | Y | Y |  |
| battery, pmu_event | TokaMind for Power Grid Cross-Domain Transfer from Fusion Plasma | Y | Y | Y |
| battery | Robust market-based BESS management in European balancing markets data | Y | Y |  |
| dga | Learning to Solve AC Optimal Power Flow with Graph Neural Networks | Y | Y | Y |
| opf_learning, battery, wind_solar | OPFData Large-scale datasets for AC OPF |  | Y |  |
| battery | Physics-informed typed GNN OPF related |  | Y | Y |
| battery | Power Grid Control Benchmarks and MATPOWER Cases in Learning | Y | Y |  |
| opf_learning, battery | Power Grid Library for Benchmarking AC OPF | Y | Y |  |
| rl_grid, battery | Multi-period OPF and UC |  |  |  |
| other | Synthetic power grid datasets applications | Y | Y |  |
| load_forecasting, battery, wind_solar | Monash Time Series Forecasting Archive | Y | Y |  |
| other | Prognosis of Li-ion Batteries Under Large Load Variations Using Hybrid | Y |  | Y |
| battery | Machine learning for unit commitment | Y |  |  |
| battery, wind_solar | Integration of a physics-based direct normal irradiance DNI model to e |  | Y | Y |
| battery, wind_solar | Regridding uncertainty for statistical downscaling of solar radiation |  | Y |  |
| opf_learning, battery | Power Grid Library for Benchmarking AC OPF | Y | Y |  |
| battery | Gaussian process regression for forecasting battery state of health |  |  |  |
| opf_learning, battery, wind_solar | Australian Energy Market Operator National Electricity Market Network  |  |  |  |
| wind_solar | Electric Network Topology Optimization with Distributed Generation usi |  |  |  |
| load_forecasting, battery, ev_charging | Leveraging Large Language Models for Analysis and Control of Power Tra | Y | Y |  |
| opf_learning | pandapower open-source python tool | Y |  |  |
| other | RL for distribution grids |  |  |  |
| opf_learning, battery, wind_solar | PGLearn -- An Open-Source Learning Toolkit for Optimal Power Flow | Y | Y |  |
| opf_learning, battery, wind_solar | A Dataset Generation Toolbox for Dynamic Security Assessment On the Ro | Y | Y | Y |
| wind_solar | OptiBench An Optimization Benchmark Tool for Renewable Energy Problems |  | Y |  |
| opf_learning, rl_grid, battery | Optimal Power Flow With Physics-Informed Typed Graph Neural Networks |  | Y | Y |
| opf_learning, resilience | Scalable Heterogeneous Graph Foundation Models for Data-Driven Optimal | Y | Y | Y |
| battery, wind_solar | Advanced Capacity Accreditation of Future Energy System Resources with |  | Y |  |
| load_forecasting, opf_learning, rl_grid | Day-Ahead Scheduling and Online Dispatch of Energy Hubs A Flexibility  |  | Y | Y |
| load_forecasting, rl_grid, wind_solar | MARS-DA A Hierarchical Reinforcement Learning Framework for Risk-Aware | Y | Y |  |
| theft_anomaly | Hybridized Machine Learning based IDS for Anomaly Detection A Systemat |  |  | Y |
| wind_solar | Beyond price taker Conceptual design and optimization of integrated en | Y | Y |  |
| opf_learning, wind_solar | Developing VSC-HVDC Oscillation Damping Control Constraints in Unit Co |  |  |  |
| opf_learning, battery, ev_charging | Frequency Support From Electric Vehicles for Advancing Renewable Energ |  |  |  |
| opf_learning, battery, wind_solar | Probabilistic Sizing of Energy Storage Systems for Reliability and Fre |  |  | Y |
| other | Production cost modeling with renewables |  |  | Y |
| load_forecasting, battery, wind_solar | BUAA BIGSCity Spatial-Temporal Graph Neural Network for Wind Power For | Y | Y | Y |
| load_forecasting, battery, wind_solar | BUAA BIGSCity ST-GNN wind power forecasting | Y | Y | Y |
| load_forecasting, battery, wind_solar | KDD Cup 2022 wind power forecasting solutions | Y | Y | Y |
| load_forecasting, battery, wind_solar | SDWPF wind power forecasting dataset paper | Y | Y | Y |
| rl_grid, battery, wind_solar | Electricity theft detection SCI OA |  | Y | Y |
| battery | Electricity theft detection with deep learning |  |  |  |
| battery, dga | Distributed energy resource optimization |  | Y |  |
| opf_learning | pandapower open-source python tool | Y |  |  |
| other | RL for distribution grids |  |  |  |
| opf_learning, battery, resilience | Vulnerability Analysis Evaluating Bilevel Optimal Power Flow Approache | Y | Y |  |
| opf_learning, battery, resilience | PACR Parameter-Optimized AC Power Flow Restoration for AC Feasible DCO |  | Y | Y |
| other | Synthetic power grid datasets applications | Y | Y |  |
