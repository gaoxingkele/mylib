---
name: literature-review
description: Orchestrate a two-pass literature review for a research question. Phase 1 casts a wide net via scholar-search (and optionally arxiv-search), phase 2 the agent screens candidates by title+abstract, phase 3 the shortlist gets full-text analysis, phase 4 the agent writes a structured synthesis. Persistent session state lives in ./literature-reviews/<slug>/. Use when the user says "literature review", "survey the field", "research question", "what does the literature say about", or "systematic search".
license: MIT
compatibility: Requires Python 3.11+ (stdlib only), internet access to api.openalex.org, and the sibling scholar-search skill installed. Optionally integrates with arxiv-search and arxiv-analyze if those are installed in common locations. No API key required (OpenAlex is free); set OPENALEX_EMAIL for polite-pool access.
---

# Literature Review

Orchestrate a structured two-pass review. The script drives state management and data fetching; the agent drives the judgment calls (screening, synthesis). Each review is a persistent session — you can pause, resume, and revisit.

## Phases

```
1. init      Create session, capture the research question
2. search    Wide net across Semantic Scholar (+ arXiv optional), dedup
3. screen    Agent reads titles/abstracts/tldrs, marks keepers
4. fetch     Script produces a fetch plan (arxiv-analyze or PDF URL per paper)
5. [read]    Agent reads each shortlisted paper via the indicated strategy
6. [synth]   Agent writes the review: established findings, tensions, gaps
```

Steps 5 and 6 are agent-driven (no new subcommand); the script's job is to set up the material.

## Usage

```bash
# 1. Start a session
python3 scripts/literature_review.py init \
    "what makes sparse autoencoders interpretable in practice" \
    [--out-dir /path/to/reviews]

# Returns: {"session": "./literature-reviews/what-makes-sparse-..", "slug": "..."}

# 2. Cast a wide net
python3 scripts/literature_review.py search <session-dir> \
    --limit 50 --year 2023-2026 --min-citations 5 \
    [--venue ICLR,NeurIPS] [--include-arxiv]

# 3. Agent reads candidates.json, picks keepers
python3 scripts/literature_review.py screen <session-dir> \
    --include "a3ec0b75...,2501.11120,10.48550/arXiv.2401.00032" \
    [--reasons-file keep-reasons.json]

# 4. Get the fetch plan
python3 scripts/literature_review.py fetch <session-dir>

# 5-6. Agent reads each paper and writes ./literature-reviews/<slug>/final.md

# Status check at any time
python3 scripts/literature_review.py status <session-dir>
python3 scripts/literature_review.py list-sessions [--out-dir /path]
```

## Session layout

```
./literature-reviews/<slug>/
├── state.json         # phase, question, counters
├── candidates.json    # phase-1 output: full search results
├── shortlist.json     # phase-2 output: papers the agent kept + reasons
├── fetch_plan.json    # phase-3 output: per-paper read strategy
└── final.md           # phase-4 output: agent writes this
```

Everything is JSON except `final.md`. Sessions can be re-run (rerun `search` to refresh, redo `screen` to revise shortlist). Delete the session dir to start over.

## Workflow

### Phase 1: init
Capture the research question clearly. Good questions are specific: "how does X differ from Y under condition Z" beats "X and Y". If the question is vague, prompt the user to sharpen it before running init.

### Phase 2: search
Default limit 50. Use `--year` to scope recency, `--min-citations` to cut noise. Add `--include-arxiv` if arxiv-search is installed and you want preprint coverage the scholar index may lag behind on.

Script dedups by arxiv_id, doi, and lowercased title.

### Phase 3: screen (the agent does this)
Read `candidates.json`. For each paper, decide: include or exclude. Use the first 1-2 sentences of the abstract for fast scanning; drill into the full abstract only for ambiguous calls.

Explicit inclusion criteria help consistency:
- Does the paper address the question directly?
- Is the method/claim specific enough to learn from?
- Is the venue/year/citation count above threshold?

Invoke screen with the comma-separated IDs of keepers. Optionally pass `--reasons-file` mapping each included ID to a one-line reason — these flow into `shortlist.json` and into the final synthesis.

Target shortlist size: 10-25 papers. Fewer and you're missing coverage; more and synthesis gets unwieldy.

### Phase 4: fetch
Script produces `fetch_plan.json`: for each shortlisted paper, the best way to read it:

- `arxiv-analyze` — when `arxiv_id` is present (preferred: tiered markdown → HTML → TeX fallback)
- `open-access-pdf` — direct PDF URL
- `abstract-only` — no full-text available; agent decides whether to keep

### Phase 5: read (agent-driven)
For each paper in the fetch plan, pull the full text using the indicated strategy. Extract: claim, method, result, limitation. Keep notes in memory or in scratch files inside the session dir.

### Phase 6: synthesize (agent-driven)
Write `final.md` with this structure:

```markdown
# Literature Review: <question>

## TL;DR
One paragraph. What does the literature say?

## Established findings
Claims multiple papers converge on, with citations.

## Active debates
Claims papers disagree about. Who holds each position, and on what grounds.

## Methodological patterns
Dominant approaches and their trade-offs.

## Gaps
What's unstudied, understudied, or inconclusive.

## Most important paper to read next
One paper. Why.

## Appendix: included papers
Table: title | authors | year | venue | one-line takeaway | full-text status
```

## Hard rules

- **Never fabricate citations or TLDRs.** If a field is missing in `shortlist.json`, mark it as such in the synthesis.
- **Two-pass screening is not optional.** Skipping the screen phase and going straight to full-text reads for 50 papers is a token disaster and a quality disaster (signal-to-noise).
- **Session state is append-only by convention.** If you need to revise, prefer creating a new session over editing state.json in place.
- **Target ~10-25 shortlist papers.** Fewer misses coverage; more is unwieldy.
- **Note what you couldn't read.** `abstract-only` papers are mentioned in the review with a note that full-text was unavailable — don't pretend you read them.

## Token budget

| Phase | Tokens (rough) |
|---|---|
| search (50 results with abstracts) | 15K-30K |
| screen (agent skim) | 15K-30K in, minimal out |
| fetch plan | 2K |
| read (15 papers via arxiv-analyze md tier) | 150K-300K |
| synthesis | 5K-15K |

Total: a real review burns 200K-400K tokens. Plan accordingly — split phases across sessions if your context budget is tight.

## The One Thing

End every `status` report with the single most impactful next action for the current phase — not a status summary. Example: "Phase: screened (12 shortlisted). **Next: run `fetch`, then start with paper `2501.11120` — it's cited by 6 others in your shortlist, so reading it first will anchor the rest.**"

## Requirements

- Python 3.11+ (stdlib only)
- `scholar-search` skill installed as a sibling (same `skills/` directory)
- Optional: `arxiv-search` and `arxiv-analyze` skills for arxiv integration (install from https://github.com/dsebastien/ai-skill-arxiv)
- Optional: `OPENALEX_EMAIL` env var for polite-pool access (no API key needed; OpenAlex is free)
