# ai-skill-scholar

A suite of three [Agent Skills](https://agentskills.io) for research paper discovery and literature review across arXiv, conferences, journals, and books — via the [OpenAlex](https://openalex.org) Graph API. **No API key required.** Stdlib Python only, zero dependencies. Works with any skills-compatible agent (Claude, Cursor, Gemini CLI, OpenCode, Goose, and [many more](https://agentskills.io)).

## What you get

| Skill | Purpose |
|---|---|
| `scholar-search` | Search OpenAlex by topic, venue, year, citations, concepts. Returns structured metadata with reconstructed abstracts and external IDs (arXiv/DOI/PMID). Cross-discipline — not just preprints. |
| `scholar-citations` | Citation graph: given a paper, fetch its references (ancestry) and citing papers (descendants). Filter by year and min-citations. |
| `literature-review` | Two-pass review orchestrator: wide search → agent screens titles/abstracts → full-text on shortlist → structured synthesis. Persistent session state. |

Ask an agent things like:

- "Find high-citation papers on mechanistic interpretability from ICLR and NeurIPS"
- "What papers cite 2501.11120?"
- "What does 2501.11120 build on?"
- "Do a literature review on sparse autoencoders in practice"

## Why this exists

[`ai-skill-arxiv`](https://github.com/dsebastien/ai-skill-arxiv) handles preprints brilliantly but misses everything published in journals, conferences (post-proceedings), or books. It also has no citation counts — which are the first-order signal for quality when wading through a field.

OpenAlex's Graph API has all of that, plus a structured citation graph, plus it's completely free with no API key. This suite is the natural companion to the arxiv skills.

The `literature-review` skill is where they compose: it orchestrates scholar-search and (optionally) arxiv-search into a single two-pass review with deduplication, screening, and structured synthesis.

## Why OpenAlex and not Semantic Scholar

Semantic Scholar offers similar data but requires an API key for anything beyond very light usage (the public rate limit is shared and aggressive). OpenAlex is free, no-key, and has generous rate limits — the better choice when you want skills to Just Work.

## Installation

### Via the `skills` CLI ([vercel-labs/skills](https://github.com/vercel-labs/skills))

```bash
# All three
npx skills add dsebastien/ai-skill-scholar --skill '*'

# Or pick one
npx skills add dsebastien/ai-skill-scholar --skill scholar-search
npx skills add dsebastien/ai-skill-scholar --skill scholar-citations
npx skills add dsebastien/ai-skill-scholar --skill literature-review

# Preview what's available
npx skills add dsebastien/ai-skill-scholar --list
```

Note: `literature-review` invokes `scholar-search` as a subprocess. Install them together. It also integrates with `arxiv-search` and `arxiv-analyze` if installed (from [`ai-skill-arxiv`](https://github.com/dsebastien/ai-skill-arxiv)) — install those for broader preprint coverage.

### Manual install

Skills follow the standard [Agent Skills](https://agentskills.io) layout. Copy what you want to your agent's skills directory (e.g. `~/.claude/skills/` for Claude Code):

```bash
git clone https://github.com/dsebastien/ai-skill-scholar.git
cp -r ai-skill-scholar/skills/scholar-search     ~/.claude/skills/
cp -r ai-skill-scholar/skills/scholar-citations  ~/.claude/skills/
cp -r ai-skill-scholar/skills/literature-review  ~/.claude/skills/
```

### Validate

```bash
npx skills-ref validate ai-skill-scholar/skills/scholar-search
```

## Requirements

- Python 3.11+ — stdlib only, no `pip install`.
- Internet access to `api.openalex.org`.
- **No API key.** OpenAlex is free and open.
- Optional: `OPENALEX_EMAIL` env var to join OpenAlex's [polite pool](https://docs.openalex.org/how-to-use-the-api/rate-limits-and-authentication#the-polite-pool) for priority routing:

  ```bash
  export OPENALEX_EMAIL="you@example.com"
  ```

## Usage from the CLI (without an agent)

### scholar-search

```bash
python3 skills/scholar-search/scripts/scholar_search.py "mechanistic interpretability" \
    --limit 25 --year 2024-2026 --min-citations 10

python3 skills/scholar-search/scripts/scholar_search.py "alignment" \
    --venue "ICLR" --open-access
```

### scholar-citations

```bash
# References (what preceded the paper)
python3 skills/scholar-citations/scripts/scholar_citations.py references 1706.03762

# Citations (what builds on the paper)
python3 skills/scholar-citations/scripts/scholar_citations.py citations 1706.03762 \
    --min-year 2024 --min-citations 5

# Both at once
python3 skills/scholar-citations/scripts/scholar_citations.py both 1706.03762 --limit 50
```

Accepts OpenAlex W-ids, arXiv IDs, DOIs, `doi:`/`pmid:` prefixes, or OpenAlex/DOI URLs.

### literature-review

```bash
# 1. Start
python3 skills/literature-review/scripts/literature_review.py init \
    "what makes sparse autoencoders interpretable in practice"

# 2. Search
python3 skills/literature-review/scripts/literature_review.py search \
    ./literature-reviews/what-makes-sparse-... --limit 50 --year 2023-2026

# 3. Screen (agent chooses IDs after reading candidates.json)
python3 skills/literature-review/scripts/literature_review.py screen \
    ./literature-reviews/what-makes-sparse-... \
    --include "W123,W456,W789"

# 4. Get fetch plan
python3 skills/literature-review/scripts/literature_review.py fetch \
    ./literature-reviews/what-makes-sparse-...

# 5-6. Agent reads each paper using the plan, writes final.md
```

See each skill's `SKILL.md` for full CLI reference and agent workflow.

## Design notes

### Rate limiting (deterministic)

Both `scholar-search` and `scholar-citations` self-throttle at 5 req/sec (a shared cooldown file in the cache dir coordinates concurrent invocations). OpenAlex's public ceiling is 10 req/sec — we leave headroom.

### Abstract reconstruction

OpenAlex stores abstracts as inverted indexes (word → positions) for search efficiency. These scripts reconstruct them to normal prose on the way through.

### Session persistence (literature-review)

Each review is a self-contained directory under `./literature-reviews/<slug>/`:

```
state.json      # phase + counters
candidates.json # wide-net search results
shortlist.json  # agent-screened keepers with reasons
fetch_plan.json # per-paper read strategy
final.md        # agent-written synthesis
```

Sessions are pause/resume/revise.

### Source composition

`literature-review` calls `scholar-search` first (broad coverage via OpenAlex), optionally chains `arxiv-search` (preprints from `ai-skill-arxiv`), dedups by arxiv_id / DOI / lowercased title. The `fetch` subcommand produces per-paper read hints pointing at `arxiv-analyze` for arxiv papers or the `openAccessPdf` URL for others.

### Data completeness

OpenAlex coverage is excellent for journal articles, conference proceedings, and older arXiv submissions. For very recent preprints (last ~6 months), reference lists can be sparse — if `scholar-citations references` returns empty, try `arxiv-analyze --tier tex` on the paper instead to parse its own bibliography.

## License

MIT. See `LICENSE`.

## Credits

- [Agent Skills](https://agentskills.io) — the open standard these skills conform to
- [OpenAlex](https://openalex.org/) — free, open scholarly database (250M+ works). The reason these skills can be key-free.
- [`ai-skill-arxiv`](https://github.com/dsebastien/ai-skill-arxiv) — sibling suite for arXiv-specific workflows; recommended companion
- [`aiming-lab/AutoResearchClaw`](https://github.com/aiming-lab/AutoResearchClaw) — the two-pass screening pattern comes from formal systematic-review methodology (PRISMA); this skill strips the biomedical overhead and keeps the useful core
- [vercel-labs/skills](https://github.com/vercel-labs/skills) — the `skills add` CLI
- [skills-ref](https://github.com/agentskills/agentskills/tree/main/skills-ref) — spec validator
