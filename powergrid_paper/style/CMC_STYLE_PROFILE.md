# CMC (Computers, Materials & Continua) — Submission Intelligence Profile

Compiled 2026-07-16 from official Tech Science Press (TSP) pages and a 10-paper corpus (2024–2026) downloaded from techscience.com. Purpose: adapt (1) MA-SQLGrid and (2) C2GES from IEEE Access format to CMC.

Journal facts: ISSN 1546-2218 / 1546-2226 (online); monthly; fully Open Access (CC-BY); Impact Factor 2.4 (2025 SCI), CiteScore 6.6; single-blind review, at least 2 reviewers; "Online First" publication after acceptance.

---

## 1. Official Requirements Checklist

### 1.1 Templates (both formats exist — LaTeX preferred for us)
Downloaded to `paper_projects/cmc_style/template/`:

| File | What it is |
|---|---|
| `TSP_template.zip` (unzipped in `latex_unzipped/`) | **Official LaTeX template**: `Definitions/tsp.cls` (class option `cmc` selects the journal; options `journal,article,submit,moreauthors,pdftex`), `Definitions/vancouver.bst`, `TSP_template.tex` sample with all back-matter macros |
| `TSP_CMC_Template.dot` | Official Word template |
| `Vancouver.ens` | EndNote reference style |
| `CMC-Format-Template.doc` | Older Word format sample (legacy) |

LaTeX key macros: `\Title{}`, `\Author{}`, `\AuthorNames{}`, `\address{}`, `\corres{}`, `\abstract{}`, `\keyword{}` then back matter via `\acknowledgement{}`, `\funding{}`, `\authorcontributions{}`, `\availabilityofdataandmaterials{}`, `\ethicsapproval{}`, `\conflictsofinterest{}`, optional `\supplementary{}`, `\abbreviations{}{}`, `\appendixstart\appendix`. References either `\bibliography{...}` with `vancouver.bst` or internal `thebibliography`.

Layout: **single column, US Letter, single spaced**, 0.75 cm first-line indent; headings L1 bold 11pt numbered 1,2,3; L2 bold-italic (3.2); L3 italic (3.2.1); L4 unnumbered, max depth.

### 1.2 Manuscript structure (canonical)
- **Title**: precise, capitalized substantives.
- **Authors**: full first names; superscript affiliations; corresponding author marked * with public email (`Corresponding Author: Name. Email: ...`).
- **Abstract**: research articles **200–400 words** (reviews 150–300), single paragraph, no citations, no inserted line breaks. Structured flow encouraged *without headings*: Background → Methods → Results → Conclusions.
- **Keywords**: **3–10**, semicolon-separated.
- **Main text**: flexible; recommendation "Introduction, Results, Discussion, Methods, Conclusions" is biomedical boilerplate — in practice CS papers use Introduction / Related Work / Method / Experiments / Results (and Discussion) / Conclusion (see §2).
- **Body length**: no hard word limit ("as concise as possible"), but APC adds **$100/page beyond 15 typeset pages** (see §1.5).

### 1.3 Back matter — EXACT canonical order (mandatory, all six statements "truthfully provided")
1. **Acknowledgement** ("Not applicable." if none; **AI-use disclosure lives here** — see §1.6)
2. **Funding Statement** ("The author(s) received no specific funding for this study." if none)
3. **Author Contributions** (mandatory unless single author; CRediT roles; must end "All authors reviewed and approved the final version of the manuscript.")
4. **Availability of Data and Materials** (one of 5 sanctioned formulations: openly available in repository at URL / within article or Supplementary Materials / on request from corresponding author / restricted / not applicable)
5. **Ethics Approval** ("Not applicable." for non-human/animal studies)
6. **Conflicts of Interest** ("The authors declare no conflicts of interest.")
Then optionally: Supplementary Materials → Abbreviations/Glossary → Appendices (Figure A1, Table A1 numbering) → **References** (always last).

All 10 corpus papers follow this block verbatim; Ethics Approval appears in every 2025–2026 paper (absent in the 2024 one — it was added to the template circa 2025).

### 1.4 Reference style (Vancouver / NLM — NOT IEEE)
- In-text: `[1]`, `[2,3]`, `[4–6]`, consecutive by first appearance; ≤5 consecutive refs at one point; "Rhee [1]", "Al-Khshali et al. [2]" when subject of sentence.
- **First 6 authors then "et al."**; abbreviated journal names (LTWA); DOI included where available (rendered as [CrossRef] hyperlink in LaTeX sample).
- **Journal article**: `Author AA, Author BB. Title of article. Abbrev J Name. Year;volume(issue):pagination. doi` — e.g. `Rhee HS. Chosen-ciphertext attack secure public-key encryption with keyword search. Comput Mater Contin. 2022;73(1):69–85.`
- **Conference paper**: `Author AA, Author BB. Title of the paper. In: Proceedings of the xth Name of Conference; Date of Conference; Location.` — e.g. `Nath JS, Bhattacharyya C. Maximum margin classifiers with specified false positive and false negative error rates. In: Proceedings of the 2007 SIAM International Conference on Data Mining; 2007 Apr 26–28; Minneapolis, MN, USA.`
- **arXiv/preprint** (per NLM convention used by TSP): `Author AA, Author BB. Title. arXiv:2401.12345. 2024.` (treat as electronic publication; include identifier and year; a `[Preprint]` tag or "Available from: URL" is acceptable NLM form).
- **Website**: `Title [Internet]. Location: Publisher; Year [cited YYYY Mon D]. Available from: URL.`

### 1.5 APC and policies
- **APC: USD 1,600** per article (effective 2025-01-01), **+ USD 100 per typeset page beyond 15 pages** (mandatory). Waivers discretionary; reviewer vouchers exist. USD only.
- **Review process**: single-blind, ≥2 reviewers; pre-check screens format, scope, ethics, scientific soundness; "inadequately prepared" manuscripts returned for revision; minor revisions have a 5-day turnaround demand. No official days-to-decision claim; corpus received→published spans observed: ~2.5–6 months (e.g., 18 Feb→9 Jun 2025; 29 Dec 2025→15 Jun 2026).
- **Similarity**: iThenticate screening; plagiarism → rejection/retraction (no published % threshold).
- **AI-use disclosure (mandatory)**: statement in Acknowledgement — "During the preparation of this work, the author(s) used [TOOL] in order to [REASON]. After using this tool/service, the author(s) reviewed and edited the content as needed and take(s) full responsibility for the content of the published article." Grammar/spell-check exempt. AI cannot be an author. Corpus precedent: the 2026 SQL-agents paper discloses ChatGPT for readability.
- **Figures**: preferred .tif RGB; Line art ≥900 dpi, Halftone ≥300 dpi, Combo ≥600 dpi; max 16.51 cm × 20 cm; labels Arial/Helvetica 8–11 pt black; combined (non-editable-pieces) images; caption "Figure N:" below (centered if one line); tables editable (never images), caption "Table N:" above, three-line style with `\toprule/\midrule/\bottomrule`; special symbols (*, †) must be explained in footer.
- **English**: professional editing recommended for non-native speakers; TSP sells editing; certificates from other providers accepted.
- **Cover letter**: must state originality, non-simultaneous submission, all-author approval, COI declaration, and **commitment to pay the APC**.
- **Supplementary Materials**: uploaded separately; cited as Fig. S1 / Table S1 / Eq. (S1); refs cited in supplement must also appear in main list.

### 1.6 Scope check
CMC scope: "computer networks, artificial intelligence, big data, software engineering, multimedia, cyber security, internet of things, materials genome, integrated materials science, data analysis, modeling, designing and manufacturing."
- **MA-SQLGrid** (LLM text-to-SQL for power-grid maintenance DBs): fits AI + big data + data analysis. Direct precedent in-journal: "Evaluating Open-Source LLM Agents for SQL Generation and Structured Analytics on Relational Databases" (CMC 2026;88(2)) and an online-first multi-agent SQL-agents paper. Smart-grid application papers are also common (3 in our corpus). **Fit: strong.**
- **C2GES** (causal-role evidence sentence selection over NERC reliability reports): fits AI/NLP + data analysis; precedent: domain NER (musk-deer, cybersecurity OSINT), text classification, AI-text detection — CMC routinely publishes domain-specific IE/ranking with self-built corpora. **Fit: strong.**

---

## 2. Corpus: 10 CMC papers (2024–2026)

PDFs in `papers/literature/target_journal_related/cmc_pdfs/`.

| # | File | Title (short) | Year;Vol(No) | DOI (10.32604/…) | URL (techscience.com/…) |
|---|---|---|---|---|---|
| 1 | cmc_2026_llm_sql_agents.pdf | Evaluating Open-Source LLM Agents for SQL Generation and Structured Analytics | 2026;88(2) | cmc.2026.078330 | cmc/v88n2/67604 |
| 2 | cmc_2025_llm_finetune_payloads.pdf | Fine-Tuning LLMs for Generating Synthetic Payloads (Pen-Testing) | 2025;82(3):4409–30 | cmc.2025.059696 | cmc/v82n3/59905 |
| 3 | cmc_2025_rag_aws_threat.pdf | Retrieval-Augmented LLM for AWS Cloud Threat Detection (MITRE ATT&CK) | 2026;87(2) | cmc.2026.077606 | cmc/v87n2/66657 |
| 4 | cmc_2025_rag_aigc_text_detect.pdf | Enhancing Detection of AI-Generated Text: Retrieval-Augmented Dual-Driven Defense (D3M) | 2026;87(1) | cmc.2025.074005 | cmc/v87n1/66080 |
| 5 | cmc_2025_securebert_ner.pdf | Mitigating Adversarial Obfuscation in NER with Robust SecureBERT Finetuning | 2026;87(1) | cmc.2025.073029 | cmc/v87n1/66046 |
| 6 | cmc_2025_chinese_ner_muskdeer.pdf | Chinese NER for Musk Deer Domain (Cross-Attention Lexicon, CAELF-GP) | 2025;83(2):2989–3005 | cmc.2025.063008 | cmc/v83n2/60592 |
| 7 | cmc_2024_turkish_text_classification.pdf | Relational Turkish Text Classification Using Distant Supervised Entities | 2024;79(2):2209–28 | cmc.2024.050585 | cmc/v79n2/56463 |
| 8 | cmc_2025_load_forecasting_bigru.pdf | Short-Term Load Forecasting: T-CFSFDP + Stacking-BiGRU-CBAM | 2025;84(1):1189–202 | cmc.2025.064509 | cmc/v84n1/61767 |
| 9 | cmc_2025_xgboost_grid_fault.pdf | XGBoost-Based Power Grid Fault Prediction with Feature Enhancement | 2025;82(2):2893–908 | cmc.2024.057074 | cmc/v82n2/59441 |
| 10 | cmc_2025_smartgrid_anomaly_graph.pdf | Multi-Expert Collaboration Information Graph Learning for Smart-Grid Anomaly Diagnosis (MCIG) | 2025;85(3):5359–76 | cmc.2025.069427 | cmc/v85n3/64192 |

### 2.1 Quantitative distillation

| # | Pages | ~Words | Top-level sections | Abs. words | Contribs listed | Refs | Figs | Tables | Datasets (pub/self) | Baselines | Ablation | Sig. testing | Code released |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 SQL agents | 32 | ~10.5k | 8 + appendix | ~340 | prose only | 30 | 5 | 6 | 2 (1 pub Spider / 1 self) | 4 LLMs (no external SOTA rerun) | arch (single vs multi, 8 rows) | partial (Mean±SD expert study) | No |
| 2 Payloads | 22 | ~7k | 7 | ~215 | prose (subsec 1.2) | 32 | 7 | 2 | 1 pub (+DVWA env) | **0** | No | No | No |
| 3 AWS RAG | 25 | ~10k | 8 | ~231 | 4 (own Section 2) | 24 | 6 | 6 | 1 self (synthetic) | 1 (no-RAG vs RAG) | No (future work) | No | No |
| 4 D3M | 19 | ~8k | 6 | ~203 | 3 (intro) | 39 | 6 | 2 | 3 pub | 5 | param sweeps (19 variants) | **Yes** (paired t-tests p<0.01; 95% CI over 30 runs) | No |
| 5 SecureBERT NER | 17 | ~6.8k | 6 | ~290 | 3 (gap bullets) | 22 | 4 | 3 | 1 self | 1 | prose-only (~5 variants) | No | No |
| 6 Musk-deer NER | 17 | ~5.8k | 5 | ~285 | 3 (numbered) | 29 | 4 | 7 | 3 (2 pub / 1 self) | 7 | Yes (2 variants, Table 6) | partial (multi-run averages, no SD) | No |
| 7 Turkish TC | 20 | ~6.4k | 5 | ~265 | 3 (bullets) | 56 | 5 | 6 | 3 pub (+Wikidata) | 4 (×2 conditions) | with/without enrichment | No | No |
| 8 Load BiGRU | 14 | ~5.8k | 5 | ~210 | 3 (numbered) | 24 | 9 | 3 | 1 pub | 5 (+2 literature) | Yes (4 variants) | No | No |
| 9 XGBoost fault | 16 | ~5.8k | 5 | ~155 | 3 (bullets) | 26 | 6 | 2 | 1 self (simulated) | 3 | No (component comparison only) | No | No |
| 10 MCIG grid | 18 | ~6.8k | 5 | ~270 | 3 (bullets) | 33 | 5 | 6 | 4 pub | 7 | Yes (4+2 variants, 2 tables) | **Yes** (Nemenyi post-hoc) | No (data yes) |

### 2.2 Median / typical values

| Metric | Median | Range | Note |
|---|---|---|---|
| Typeset pages | **18–19** | 14–32 | single-column US Letter; >15 pages triggers $100/page |
| Body words | ~6.8k | 5.8k–10.5k | |
| Top-level sections | **5–6** | 5–8 | 5 is the mode |
| Abstract words | **~250** | 155–340 | all single paragraph |
| Contributions listed | **3** | 0–4 | 7/10 have an explicit 3-item list; 2 state in prose |
| References | **30** | 22–56 | |
| Figures | **5–6** | 4–9 | |
| Tables | **4–5** | 2–7 | |
| Datasets | **1–2** | 1–4 | self-built domain corpora common (4/10) and accepted |
| Baselines | **4** | 0–7 | ≥5 only in 4/10 papers |
| Ablation study | 6/10 (proper table only 4/10) | 2–6 variants typical | |
| Statistical significance | **2/10 formal** (t-test/CI, Nemenyi); 2 more partial | | rigorous testing is the exception, not the norm |
| Code released | **0/10** | | data: 2 open, 6 on-request, 2 undisclosed |
| Related Work separate section | 7/10 | | rest fold into Introduction |

---

## 3. Style Fingerprint (CMC vs IEEE Access)

Concrete deltas from the corpus:

1. **Layout**: CMC is **single-column** US Letter with numbered 11pt headings; Access is two-column with its own cls. A 19-page Access paper becomes roughly 28–35 CMC pages.
2. **References**: CMC is **Vancouver/NLM** (`Author AA. Title. Abbrev J. Year;vol(iss):pp.`), first-6-authors-et-al., DOI links; Access is IEEE style. Every reference must be rebuilt (use `vancouver.bst` or the EndNote `.ens`).
3. **Back matter**: CMC mandates the 6-statement block in fixed order; Access has only Acknowledgment/biographies. This block is checked at pre-screening.
4. **Abstract**: CMC 200–400 words, quantitative, often carrying headline numbers (the SQL-agents paper embeds 90.14%/98.59% directly); Access abstracts are typically ~250 max and less numeric.
5. **Intro pattern**: broad macro-motivation opening ("With the rapid development of…", national/industry significance), narrowing to 2–3 explicitly named gaps, ending in a **3-item numbered/bulleted contribution list** plus often a "the rest of this paper is organized as follows" paragraph. Tone is plainer and more didactic than Access.
6. **Related work**: usually a compact separate Section 2 (0.5–3.5 pages), taxonomy-organized with 2–3 subsections or a comparison table; paper-by-paper walkthroughs ending "…in contrast, our work…" are accepted.
7. **Methods**: heavier on numbered equations and Algorithm pseudocode boxes than typical Access AI-application papers; symbol-definition tables appear.
8. **Results**: P/R/F1/Accuracy (or task metric) **tables with best values bolded**, mirrored bar charts, confusion matrices; efficiency/latency/token-cost tables increasingly present in LLM papers. Single-run point estimates are the norm; only 2/10 do formal significance testing — multi-run + CI work reads as *above-norm rigor* here.
9. **Conclusion**: recap + limitations + future work, frequently in one section ("Conclusions and Future Work"); a separate Limitations section is rare (0/10) — limitations live in Discussion or Conclusion.
10. **Reproducibility culture**: no corpus paper releases code; "data on request" is the default. Releasing code/data is a differentiator, not an expectation.
11. **Evolution note**: 2024 papers use legacy CMC reference/layout style; 2025+ use the current Vancouver style and added the Ethics Approval statement. Model the 2025–2026 papers, not older ones.

---

## 4. Adaptation Briefs

### 4.1 MA-SQLGrid (current: 19 pp IEEE Access, ~270-word abstract, 5 keywords, 45 refs, 4 figures, 13 tables, sections: Intro / Related Work / Problem Formulation / Method / Experiments / Results / Discussion / Limitations / Conclusion / Appendix-prompts)

**Positioning**: near-perfect topical precedent (CMC 2026;88(2) SQL-agents paper, DOI 10.32604/cmc.2026.078330). Cite it and position MA-SQLGrid as domain-grounded, validation-augmented text-to-SQL vs. their generic agent evaluation.

Top-5 actions:
1. **Re-typeset into `tsp.cls`** (`journal,article,submit,moreauthors` + journal `cmc`), single column. Expect ~30–35 CMC pages from 19 Access pages → APC ≈ $1,600 + $1,500–2,000 page charges. To control cost, target ≤28 pages: move the appendix prompt templates and the lower-value result tables to Supplementary Materials (corpus max is 32 pages, so length itself is not a risk — only cost).
2. **Rebuild all 45 references in Vancouver style** (vancouver.bst; abbreviated journal names, first 6 authors + et al., DOIs; conference format per §1.4). Convert in-text citation usage: no >5 consecutive refs; "Author et al. [n]" phrasing. 45 refs is comfortably above the CMC median of 30 — no additions needed.
3. **Restructure to 6–7 top-level sections** (current 9 is above the 5–8 norm): fold Problem Formulation into Method (or Experiments preliminaries); merge Results + Discussion into "Results and Discussion"; merge Limitations into Conclusion or Discussion (no corpus paper has a standalone Limitations section). Add an explicit **3–4 bullet contribution list** at the end of the Introduction plus a paper-organization paragraph.
4. **Append the mandatory 6-statement back-matter block** in exact order (§1.3), including: AI-use disclosure in Acknowledgement (LLMs are the research subject; also disclose any drafting assistance), CRediT Author Contributions, and a concrete Availability statement for GridDB-Maintenance-v2 (recommend "openly available at [URL]" or the sanctioned on-request wording); Ethics Approval "Not applicable."
5. **Trim table load and format compliance**: 13 tables ≫ corpus max 7 — keep 6–8 headline tables (main accuracy, per-condition, second-generator replication, token economics, consistency check), push the rest to Supplementary; re-caption as "Table N:" above / "Figure N:" below; ensure figures meet ≥300 dpi (halftone) / ≥900 dpi (line art), Arial labels 8–11 pt; abstract already in the 200–400 window — keep the quantitative style, optionally reflow to Background→Methods→Results→Conclusions; keywords → semicolon list (5 already, fine).

**Experimental intensity vs CMC norms — well above; de-risking minimal**: 2-generator byte-identical replication + 5-condition benchmark + 3-repeat temperature-0 consistency bound + token-economics analysis exceeds the corpus median (4 baselines, 1 dataset, ~half with ablation, 20% with any statistical treatment). The CMC SQL-agents precedent has 4 models, no external SOTA baselines and no significance testing. Do not cut anything; instead surface the rigor explicitly (a "consistency/significance" paragraph mirrors D3M's above-norm style). One de-risk: reviewers here expect a comparison against at least a few named prior text-to-SQL configurations — the 5-condition design already serves this; label conditions clearly as baselines in table headers.

### 4.2 C2GES (current: 17 pp IEEE Access, ~215-word abstract, 5 keywords, 57 refs, 4 figures, 9 tables, sections: Intro / Related Work / Task and Benchmark / Method / Experiments / Results / Qualitative Error Analysis / Discussion / Limitations / Conclusion)

**Positioning**: fits CMC's domain-IE lane (musk-deer NER, SecureBERT NER, Turkish TC all pair a self-built domain corpus with a tailored model). Frame as role-conditioned evidence selection for critical-infrastructure text analytics.

Top-5 actions:
1. **Re-typeset into `tsp.cls`**; expect ~25–30 CMC pages from 17 Access pages → APC ≈ $1,600 + $1,000–1,500. Target ≤25 pages by moving supplement-grade evidence and part of the error analysis to Supplementary Materials.
2. **Rebuild all 57 references in Vancouver style.** 57 is nearly 2× the CMC median (30) and would consume ~3.5 typeset pages (as in the Turkish TC paper) — each reference page beyond page 15 costs $100, so prune ~10–15 marginal citations toward ~45.
3. **Consolidate 10 sections → 6**: Introduction (with 3-bullet contribution list) / Related Work / Task and Benchmark (keep — self-built-corpus papers in CMC always describe corpus construction prominently) / Method / Experiments and Results / Discussion (absorb Qualitative Error Analysis + Limitations) / Conclusions and Future Work. CMC's plainer register also favors renaming heavy formalism headings descriptively.
4. **Append the 6-statement back-matter block**; critical items: (a) Availability of Data and Materials — NERC source reports are public, so state the repository/URL for report list + agent-verified labels (this is a strength vs. the corpus's "on request" default); (b) **AI-use disclosure**: labels are "agent-verified" — the Acknowledgement must disclose the LLM/agent used in benchmark construction per TSP's mandatory AI-tool statement, and the benchmark section must describe human verification; (c) CRediT contributions; Ethics Approval "Not applicable."
5. **De-risk the absolute-score optics**: headline 0.2983 evidence F1 will read as "low" to CMC reviewers accustomed to 90%+ accuracy tables. Mitigate by (i) leading every results table with relative gains (+41% over TF-IDF, +51% over SBERT) and bolding best-per-column, (ii) adding a short calibration paragraph on task hardness (608 gold IDs over 40 documents; sentence-ID exact matching), (iii) keeping the paired document-cluster bootstrap front and center — formal significance appears in only 2/10 CMC papers, so this is a differentiator, and (iv) reporting an auxiliary, more intuitive metric (e.g., hit@k / rank-based) if available. Baseline count (TF-IDF, SBERT, + ablation variants) is at/near the corpus median of 4 — if feasible, add 1–2 cheap rerankers (e.g., BM25, cross-encoder) to sit clearly above the norm.

**Experimental intensity vs CMC norms**: bootstrap significance testing and systematic ablations already exceed the corpus norm; the deterministic, auditable method matches CMC's applied register. The only below-norm optic is absolute score magnitude (handled above) and figure count (4 vs median 5–6 — consider adding a pipeline/architecture figure and a per-role performance bar chart; every corpus paper has an architecture figure as Fig. 1).

---

## 5. Desk-Rejection / Pre-Screening Triggers at TSP

Pre-check explicitly screens: correct formatting, ethical-policy compliance, scope fit, scientific soundness. Concretely avoid:
1. **Wrong template/format** — submitting in IEEE Access layout, IEEE references, or missing the back-matter block gets the manuscript returned/rejected at pre-check. Use `tsp.cls` + Vancouver from day one.
2. **Missing/incomplete mandatory statements** — all six back-matter statements (incl. Ethics Approval "Not applicable" and CRediT contributions) plus a compliant cover letter (originality, non-simultaneous submission, all-author approval, COI, APC commitment).
3. **iThenticate similarity** — plagiarism (including text recycled from earlier arXiv/Access drafts of the same work without transparency) → rejection. Rewrite adapted passages; if a preprint exists, disclose it in the cover letter.
4. **Undisclosed generative-AI use** — both papers are LLM-heavy; omit the mandatory AI-tool statement and it conflicts with TSP's Generative AI policy. Disclose tool + reason in Acknowledgement; never list AI as author.
5. **Simultaneous submission / prior publication in any language** — instant rejection.
6. **Abstract/keyword non-compliance** — abstract outside 200–400 words, citations in abstract, <3 or >10 keywords.
7. **Figure/table violations** — figures as low-res screenshots (<300 dpi), tables embedded as images, unexplained bold/color/symbols, sub-tables "1a/1b", references cited as [xx] inside figure graphics.
8. **English quality** — visibly unedited language triggers a return for professional editing (certificate may be requested).
9. **Data-availability inadequacy** — TSP publication ethics lists "inadequate data availability" as a sanctionable ground; use one of the five sanctioned statement formulations.
10. **Citation manipulation patterns** — long consecutive citation chains (>5 at one point) and gratuitous self/journal citation clusters.

---

## 6. File Inventory Produced by This Profile

- Templates: `paper_projects/cmc_style/template/` (`TSP_template.zip` + unzipped LaTeX in `latex_unzipped/` with `tsp.cls`, `vancouver.bst`, `TSP_template.tex`; `TSP_CMC_Template.dot`; `Vancouver.ens`; legacy `CMC-Format-Template.doc`)
- Corpus PDFs: `papers/literature/target_journal_related/cmc_pdfs/` (10 files, table §2)
- Official pages consulted: techscience.com/journal/CMC, /cmc/info/auth_instru, /cmc/info/article_charge, /cmc/info/editorial_workflow, /cmc/info/publication_ethics
