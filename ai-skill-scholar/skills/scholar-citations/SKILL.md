---
name: scholar-citations
description: Fetch the citation graph for a research paper via OpenAlex. Returns the papers it cites (references - what preceded it) and the papers that cite it (citations - what built on it). Accepts OpenAlex work ID, DOI, arXiv ID, PMID, or OpenAlex/DOI URL. No API key required. Use when the user says "what does this paper cite", "who cites this paper", "references of", "citation graph", "papers that built on", or "trace this idea backward/forward".
license: MIT
compatibility: Requires Python 3.11+ (stdlib only) and internet access to api.openalex.org. No API key needed. Optional OPENALEX_EMAIL env var joins the polite pool.
---

# Scholar Citations

Traverse the citation graph of a research paper via [OpenAlex](https://openalex.org). Two directions:

- **References** — what this paper cites (its intellectual ancestry)
- **Citations** — what cites this paper (its intellectual descendants)

One subprocess call returns a structured list of papers with titles, abstracts, citation counts, and external IDs.

## Usage

```bash
# References — what this paper cites
python3 scripts/scholar_citations.py references 2501.11120 --limit 100

# Citations — what cites this paper
python3 scripts/scholar_citations.py citations 2501.11120 --limit 100

# Both at once
python3 scripts/scholar_citations.py both 2501.11120 --limit 50

# Filter to recent, high-impact descendants
python3 scripts/scholar_citations.py citations 1706.03762 \
    --min-year 2024 --min-citations 10 --limit 100

# Accepts many ID formats
python3 scripts/scholar_citations.py citations W4395065622
python3 scripts/scholar_citations.py citations "10.48550/arxiv.2404.14082"
python3 scripts/scholar_citations.py citations "doi:10.48550/arxiv.2404.14082"
python3 scripts/scholar_citations.py citations "https://openalex.org/W4395065622"
```

**Subcommands:**
- `references <id>` — papers cited by the target
- `citations <id>` — papers citing the target
- `both <id>` — both directions in one payload

**Flags:**
- `--limit N` — max results per direction (default 100)
- `--min-year YYYY` — drop older entries
- `--min-citations N` — drop low-impact entries (useful for surfacing important follow-ups)

## When to use

- **Tracing an idea backward** — given a paper, find the key work it builds on (`references` + `--min-citations 50`)
- **Finding follow-ups** — see what built on an important paper (`citations` + `--min-year 2024`)
- **Gap analysis** — intersect references and citations across multiple anchor papers to find unexplored neighborhoods
- **Reviewer context** — get the citation neighborhood before reviewing a paper

## Data completeness caveat

OpenAlex's reference lists are complete for well-indexed papers (journal articles, conference proceedings, older arxiv submissions) but often sparse for very recent preprints. If `references` returns empty, it's usually OpenAlex data coverage, not a script bug. For arxiv-only ancestry, fall back to parsing the paper's own reference list via `arxiv-analyze` with `--tier tex`.

## Workflow

### 1. Identify the anchor paper
Accept OpenAlex W-id, DOI, arxiv id (auto-converts to arxiv's DOI), PMID (as `pmid:<n>`), or any OpenAlex/DOI URL. The script auto-normalizes.

### 2. Pick direction
- Understanding how a paper emerged? → `references`
- Tracking impact or finding new work? → `citations`
- Building a full neighborhood view? → `both`

### 3. Filter aggressively
Reference and citation lists can be 100-1000 entries. Use `--min-citations` and `--min-year` generously — 1000 low-signal entries are worse than 20 high-signal ones.

### 4. Feed into analysis
For each interesting paper: hand off `arxiv_id` to arxiv-analyze, or use the `open_access_pdf` URL directly.

## Rate limits

OpenAlex is generous: 10 req/sec anonymous, more in the polite pool (set `OPENALEX_EMAIL`). Script self-throttles at 5 req/sec.

A single `references` or `citations` call with `--limit 100` is typically 2-3 API requests (one for the root work, one or two for the batched resolution of related works).

## Token efficiency

- 100 references/citations ≈ 15K-30K tokens (abstracts dominate)
- For graph exploration where breadth > depth, pipe through `jq 'del(.*.abstract)'` before feeding to context

## Hard rules

- **Don't explode the graph.** 100 × 100 references-of-references is 10k papers. If you need n-hop traversal, do it in explicit staged passes with user confirmation.
- **Respect the rate limit.** The script's self-throttle is load-bearing.
- **Sparse data is data.** If `references` or `citations` is empty, report it as empty; don't fabricate.

## Requirements

- Python 3.11+ (stdlib only)
- Internet access to `api.openalex.org`
- Optional: `OPENALEX_EMAIL` for polite-pool access
