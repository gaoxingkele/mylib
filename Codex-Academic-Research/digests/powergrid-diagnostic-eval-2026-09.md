# Diagnostic / negative-result evaluation: distillation from C²GES (Information, 2026-09)

Source campaign: `F:\aicoding\powergrid_benchmark\paper_projects\C2GES\Workspace`
(project AGENTS.md: release scopes `01_Manuscript`, `02_Revision_and_QA`, `03_Reproducibility`;
everything else — corpora, wiki, scratch — stays outside the release).

Use this digest when a paper's contribution is a **diagnosis** ("component X carries no
measurable information") rather than a win, and when the evidence is *paired
per-document ROUGE-style differences*.

---

## 1. The five statistical traps and the standard answer

| Trap | How it shows up | Standard answer |
|---|---|---|
| **Budget confound** | The winning arm returns 50–60 % more text because the protocol counts *units*, not words | Re-run every arm at both equal-word and equal-unit budgets; report both. In C²GES the "role layer win" was entirely a length artefact: +0.0108 at K = 10 units versus **−0.0351** at 110 words |
| **Zero inflation** | Same candidate pool, only the score weights change → many exactly tied documents (13/24 in one contrast) | Report the **zero mass** and the discordant split next to every mean; use sign-based inference alongside the mean |
| **Heavy tails** | One document supplies 92 % of a mean (−0.152 of −0.0069 over 24 docs) | Always run a **leave-one-out envelope** for both the mean and the bound; if the mean moves by >50 %, say so and switch the headline to the bound |
| **Power ceiling** | n = 7 series cannot reject under Holm even at 7/7 sign agreement (min adjusted p = 0.0625 with k = 4) | Publish the ceiling: `k · 2 / 2ⁿ`. "Not significant" then stops reading as "no effect" |
| **Ranking flips** | TextRank first at equal words, last at equal units | Never state "method A beats B" without naming the budget type |

## 2. Turning a null into a bound (the highest-value move)

A one-sided 95 % bootstrap **upper limit** on the paired mean difference converts
"we did not detect a gain" into "a gain larger than X is excluded". Recipe:

1. Report the limit per budget and per contrast, with the realised zero mass.
2. Run the same limit under **leave-one-out** and quote the worst case.
3. Pre-register the equivalence margin (C²GES used ±0.005 ROUGE-L for a corpus of
   20–110-page reports) *before* running if the claim is to be confirmatory;
   otherwise label the bound **post hoc** in the text, the caption, and the reply letter.
4. Tooling: `tools/paired_diagnostic_stats.py` in this directory (stdlib only,
   `--self-test` reproduces the published C²GES numbers).

## 3. Layered evidence table (claim bounds, not accuracy)

One table listing every evidence layer with **n / budget / main contrast / may support ·
may not support** replaced three separate "results" sections and removed the reviewer's
main objection ("which of these numbers may I trust?"). C²GES ends with seven layers
(historical retained test, pilot + factorial, external prospective, held-out revision,
synthetic stress, adjacent-corpus construct audit, out-of-domain transfer). Rules that
made it work:

* every layer carries its own `n`, budget type, and an explicit **not**-statement;
* no two layers are ever pooled into one accuracy;
* layers added after the freeze are labelled *sensitivity*, never *confirmatory*;
* a layer whose construct is out of domain (C²GES: a power-domain cue lexicon applied
  to government reports) is labelled **risk bound**, not mechanism evidence.

## 4. Pre-registration that survives review

Freeze, with a hash, **before** running: the corpus list, the sampling rule (strata and
seed), the unit construction rule, the arm set and weights, the budgets, the endpoint,
the criteria (H1/H2/H3 with numeric thresholds), and the decision rule for each outcome.
The C²GES external protocol went through v1.0–v1.4 revisions *before* scores existed and
the GovReport transfer protocol added the sampling seed and the "what this layer cannot
show" section first. Reviewers accepted both because the freeze is dated and hashed.

## 5. Release-boundary engineering (learned the hard way)

Two real defects were found in a *green* build, which is the point:

1. A shipped JSONL held **verbatim third-party passages** (`selected_text`,
   `reference_text`) while the manuscript promised verbatim text was excluded.
   Fix: ship a rights-safe companion (ids, budgets, lengths, scores) and exclude the
   verbatim file in the manifest generator.
2. A new supplementary figure was **not packaged** because the packer hard-coded the
   earlier figure name. Fix: pack `figures/*` and assert that every
   `\includegraphics` target of the shipped `.tex` exists in the archive.

Make both machine-checked, not aspirational:

* *verbatim guard*: no shipped data record may contain a ≥300-character run with ≥40
  alphabetic words (skip author-written prose files and the synthetic corpus);
* *float guard*: extract `\includegraphics{...}` from the shipped `.tex` and require each
  basename in the zip namelist;
* *derived-table guard*: the script that emits a data record refuses any field longer
  than ~400 characters (this caught a bug where a candidate **list** was written instead
  of its **count** — a silent verbatim leak).

## 6. Reproducibility plumbing that paid off

* Emit the LaTeX tables **from** the machine-readable records, never retype numbers:
  `emit_supplementary_tables.py` regenerates the supplement region between markers.
* Add one verification group per evidence layer, and bind the manuscript tokens to the
  data (`arm_numbers_bound_to_manuscript` asserts that the numbers printed in the prose
  exist in the record).
* Re-run the whole chain after the last text edit: `pdflatex ×2` → docx → packages →
  `run_public_verification.py --route diagnostic` → `generate_release_manifest.py
  --check`. A stale package is worse than a stale draft.
* Keep the corpus out of the release and publish the **protocol + derived records**;
  that is what makes the negative result citable without rights risk.

## 7. Length discipline for a "diagnostic" paper

`tools/manuscript_display_audit.py` reports the last page's free space, so "will this
paragraph cost a page?" becomes arithmetic. When over the target:

1. move detail to the supplement and keep a **bound + pointer** in the main text
   (C²GES kept two sentences and pushed the table to S18);
2. delete sentences that repeat their own table caption or a methods sentence verbatim;
3. do **not** shrink fonts or drop figures to gain a page.

## 8. Checklist before submission

- [ ] every claim has a layer with `n`, budget type, and a not-statement
- [ ] zero mass and discordant split reported for every paired contrast
- [ ] a one-sided bound wherever the headline is a null
- [ ] leave-one-out envelope on any mean used in the abstract
- [ ] power ceiling stated for any family with n ≤ 12
- [ ] freezes hashed and dated before outcomes; post-hoc items labelled post hoc
- [ ] verbatim-text guard, float guard and derived-table guard green
- [ ] verification re-run after the last text edit; manifest `--check` PASS
- [ ] page count measured against same-journal comparators, not against taste
