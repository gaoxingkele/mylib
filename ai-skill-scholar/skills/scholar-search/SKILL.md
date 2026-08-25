---
name: scholar-search
description: Search scholarly works across arXiv, conferences, journals, and books via OpenAlex. Returns citation counts, reconstructed abstracts, venue, open-access PDF links, and external IDs (arXiv/DOI/PMID). No API key required. Use when the user says "search scholar", "search papers", "find papers with citations", "papers by author", "cross-discipline search", or "papers from <venue>". Complements arxiv-search (preprints-only).
license: MIT
compatibility: Requires Python 3.11+ (stdlib only) and internet access to api.openalex.org. No API key needed. Optional OPENALEX_EMAIL env var joins OpenAlex's polite pool for priority routing and higher rate limits.
---

# Scholar Search

Search [OpenAlex](https://openalex.org) — an open catalog of 250M+ scholarly works — for papers across every major venue (not just arXiv). Returns structured JSON including citation counts, venue, reconstructed abstracts, and external IDs linking to arXiv / DOI / PubMed.

## Why OpenAlex (not Semantic Scholar)

Both cover roughly the same data. OpenAlex wins on:

- **No API key required.** The free public endpoint just works.
- **Generous rate limits.** 10 req/sec anonymous, higher in the polite pool.
- **Actually usable at scale.** Semantic Scholar's public tier is shared and 429s are constant.

## Why this over arxiv-search

| | arxiv-search | scholar-search |
|---|---|---|
| Preprints | yes | yes |
| Conferences (ICLR, NeurIPS, ACL, ...) | no | yes |
| Journals | no | yes |
| Books, chapters | no | yes |
| Citation counts | no | yes |
| Venue filtering | no | yes |
| Concept/topic tags | no | yes |

Use both together when doing a broad review (via `literature-review`).

## Usage

```bash
# Basic query
python3 scripts/scholar_search.py "mechanistic interpretability" --limit 25

# Year + venue filter
python3 scripts/scholar_search.py "sparse autoencoders" \
    --year 2024-2026 --venue "ICLR" --limit 30

# Citation floor (quality filter)
python3 scripts/scholar_search.py "scaling laws" --min-citations 50 --limit 20

# Open-access only (when you want readable papers)
python3 scripts/scholar_search.py "mixture of experts" --open-access --limit 20

# Concept filter (uses OpenAlex's topic taxonomy)
python3 scripts/scholar_search.py "alignment" \
    --concepts "Machine learning" --limit 20
```

**Flags:**
- `--limit N` — max results (1-200; default 25)
- `--year YYYY` or `YYYY-YYYY` — publication year filter
- `--venue NAME` — case-insensitive partial match on venue name
- `--concepts NAME` — OpenAlex concept (e.g. `Machine learning`, `Computer vision`)
- `--min-citations N` — quality floor
- `--open-access` — only works with a public PDF

**Output JSON shape** (per result):

```json
{
  "paper_id": "W4395065622",
  "openalex_url": "https://openalex.org/W4395065622",
  "title": "...",
  "authors": ["Alice", "Bob"],
  "year": 2024,
  "venue": "ICLR 2024",
  "work_type": "article",
  "citation_count": 150,
  "reference_count": 42,
  "abstract": "...",
  "concepts": ["Interpretability", "Machine learning"],
  "arxiv_id": "2404.14082",
  "doi": "10.48550/arxiv.2404.14082",
  "is_open_access": true,
  "open_access_pdf": "https://arxiv.org/pdf/2404.14082",
  "landing_url": "http://arxiv.org/abs/2404.14082"
}
```

## Polite pool (optional)

For heavy use, join OpenAlex's polite pool by setting an email:

```bash
export OPENALEX_EMAIL="you@example.com"
```

Priority routing + higher effective rate limits. No registration needed — the email just has to be valid so they can reach you if your traffic misbehaves.

## Workflow

### 1. Parse intent
- "find papers on X" → basic query
- "high-citation papers on X" → add `--min-citations 50+`
- "recent papers on X" → `--year 2024-2026`
- "papers from venue Y" → `--venue "ICLR"`
- "open access only" → `--open-access`

### 2. Run the search
Default `--limit 25`. Bump to 50-100 for broad reviews. OpenAlex is fast, so larger pages are fine.

### 3. Present results
Compact table: citation count | year | venue | authors | title | first-sentence-of-abstract. Sort by citation count unless the user asked for recency.

OpenAlex has no TLDR field (like Semantic Scholar did). Use the first ~50 words of the reconstructed abstract for fast screening instead.

### 4. Offer handoffs
- "Analyze paper X" → hand off to arxiv-analyze (if `arxiv_id` present) or fetch `open_access_pdf` directly
- "Who cites this?" / "What does this cite?" → hand off to scholar-citations
- "Literature review" → hand off to literature-review

## Token efficiency

- 25 results ≈ 8K-15K tokens (abstracts dominate). Override `--select` via a future flag for screening-only passes.
- OpenAlex abstracts are "inverted index" format server-side; this script reconstructs them to normal prose on the way through.

## Rate limits

- **Anonymous:** 10 req/sec, 100k/day across shared pool
- **Polite pool** (with `OPENALEX_EMAIL`): same limits but higher priority + fewer throttling events

Script self-throttles at 5 req/sec per process (shared via a cooldown file in `~/.cache/ai-skill-scholar/`).

## Hard rules

- **No key-scraping**: never prompt for an API key. OpenAlex doesn't have one; `OPENALEX_EMAIL` is optional and documented.
- **Don't hammer**: the 5 req/sec throttle is load-bearing. Don't remove it.
- **Abstracts can be missing**: OpenAlex doesn't always have them. Report as empty, don't fabricate.

## Requirements

- Python 3.11+ (stdlib only)
- Internet access to `api.openalex.org`
- Optional: `OPENALEX_EMAIL` env var for polite-pool access
