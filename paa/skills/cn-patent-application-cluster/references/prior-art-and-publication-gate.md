# Prior-Art and Publication Gate

## Publication Gate

Before filing, classify each source:

| Material | Public status | Evidence | Action |
|---|---|---|---|
| paper/doc/code | not public/public/unknown | user confirmation, URL, metadata, email record | file first / analyze grace period / confirm |

If the user confirms a paper is not public, record it in the delivery index and recommend filing before publication. Still request written confirmation from the inventor or project owner.

## Search Tiers and Default Providers

Tier 0: repository evidence and existing reports.

Tier 1: public web discovery defaults to **Tavily and Brave**. Run both when API keys are available, retain provider/query/URL provenance, and mark search snippets as `source-degraded` until the underlying page or patent text is fetched.

Tier 2: CNIPA publication announcement, Google Patents, official patent pages.

Tier 3: professional deep search uses **incoPat** when its API is configured, including semantic/field retrieval and claim/specification verification; CNIPA/智慧芽 may supplement it. Do not claim Tier 3 completion unless it was actually performed.

For agent review, the normal order is Tavily + Brave discovery, incoPat professional retrieval, then a separate citation-verification pass. A failed or quota-exhausted provider must be recorded and must not erase usable evidence from the other lanes.

## Query Plan

For each invention, prepare:
- Chinese terms;
- English terms;
- applicant/assignee guesses only if sourced;
- IPC/CPC hints;
- feature combinations;
- broader and narrower variants.

## Search Output

For every relevant reference:

| Reference | Source URL | Technical teaching | Difference | Claim impact |
|---|---|---|---|---|

Do not paste long abstracts into the final application. Summarize in your own words and keep URLs for attorney review.

## Citation Verification Pass

Before relying on a reference in a novelty or inventiveness conclusion:

1. confirm the publication number occurs in the actual search result set or source response;
2. fetch the patent text used for the assertion, preferably the relevant claim and specification passage rather than only a title;
3. restate the asserted teaching and compare it to the fetched text;
4. mark the assertion `verified`, `partially-verified`, `unverified`, or `source-degraded`;
5. keep a `considered-but-ruled-out` list with the reason a close semantic hit does not teach the claim anchor.

Never let an LLM-generated citation enter a report merely because the publication number looks plausible. Search retrieval and citation verification are separate gates.
