---
name: academic-humanizer
description: >-
  Review or revise Chinese/English papers, proposals, articles, and patent drafts that read as
  templated or AI-assisted. Restore evidence-bound author voice, concrete reasoning,
  genre conventions, and provenance while preserving numbers, citations, equations,
  claim terminology, and legal scope. Use for “去AI味”, authorial-authenticity audits,
  style cleanup, paper polish, article editing, or patent prose review. This skill does
  not classify authorship, evade detectors, invent human imperfections, or conceal
  required AI-use disclosure.
license: MIT
metadata:
  version: "1.0.0"
  compatibility: "claude-code codex morphmind opencode"
---

# Authorial Authenticity Review

Improve text by restoring the chain from real observation to claim. Do not optimize an
AI-detector score. A phrase hit is a review lead, not proof of authorship.

## Select the mode

- `audit`: locate problems and propose repairs; do not rewrite.
- `rewrite`: return a minimally revised version plus an audit trail.
- `edit`: modify the named file in place, then reopen and verify it.
- `compare`: compare an original and revised file for protected-content drift.

Infer the document profile: `paper`, `proposal`, `article`, or `patent`. Read
[`references/domain-profiles.md`](references/domain-profiles.md) for its gates. If a
prior sample from the same real author or inventor exists, use it as the primary voice
reference. Otherwise preserve the draft's competent passages and default to plain,
precise prose.

## Non-negotiable boundary

Never:

- add typos, colloquialisms, anecdotes, first-person statements, stylistic noise, or
  arbitrary sentence variation to mimic a person;
- translate back and forth, synonym-spin, or repeatedly query detectors;
- fabricate data, citations, experiments, implementation details, inventor statements,
  dates, logs, code history, or manual effort;
- weaken required patent claim repetition merely to vary wording;
- conceal AI assistance where a venue, client, firm, or authority requires disclosure.

When asked to evade detection or misrepresent authorship, decline that objective and
offer the evidence-and-authorship workflow below.

## Workflow

### 1. Freeze protected content

Before editing, inventory:

- numbers, units, dates, equations, symbols, variable names, citations, quotations;
- named datasets, methods, statutes, patent numbers, drawing labels, reference signs;
- patent claim terms, dependencies, steps, components, parameter ranges, and scope.

For file work, run:

```powershell
python scripts/authenticity_audit.py audit <file> --profile paper
python scripts/authenticity_audit.py compare <original> <revised> --profile patent
```

The script reports heuristic signals and protected-token drift. It is not an AI
detector.

### 2. Build a source-of-truth packet

Prefer author or inventor materials over model-generated prose:

- papers: notes, data tables, analysis code, lab records, figures, citation library,
  earlier writing samples, reviewer responses;
- articles: interview notes, source links, firsthand observations, names and dates
  approved for publication, and the intended audience;
- patents: disclosure forms, field tables, state or transaction sequences, version and
  code records, logs, test data, drawings, and inventor confirmations.

Create a compact ledger with columns `claim_or_passage`, `source`, `status`,
`allowed_strength`, and `action`. Status is one of `verified`, `author-confirmed`,
`inferred`, `missing`. Do not turn `inferred` or `missing` into fact.

### 3. Diagnose before rewriting

Review each passage with the roles in
[`references/review-roles.md`](references/review-roles.md):

1. provenance reviewer: where did each concrete assertion come from?
2. logic reviewer: does each conclusion follow from the stated mechanism or evidence?
3. genre reviewer: does the passage do the job of this section and document type?
4. voice reviewer: does it match real author samples without copying phrases?
5. integrity reviewer: did any protected item, uncertainty, or legal scope drift?

Prioritize findings as:

- `P0`: fabricated or unsupported content, claim-scope drift, contradiction, broken
  mechanism-to-effect chain;
- `P1`: generic structure, vague attribution, promotional claims, terminology drift,
  evidence detached from the sentence it supports;
- `P2`: cadence, filler, repeated connectors, inflated vocabulary, formatting habits.

### 4. Repair reasoning, then sentences

Use this order:

1. state the actual problem or observation;
2. name the specific limitation or cause;
3. describe the mechanism, decision, or evidence that addresses it;
4. bound the result or technical effect to the conditions actually supported;
5. state uncertainty, exception, or fallback where it matters.

Rebuild a templated paragraph from verified propositions instead of replacing suspect
individual words. Specificity must come from the source packet, never invention.

### 5. Apply a restrained language pass

Flag, but do not automatically ban:

- generic openings and conclusions;
- significance inflation and promotional adjectives;
- vague actors such as “研究表明”, “业内人士认为”, or “experts believe” without a
  source;
- mechanically balanced three-part lists and repeated paragraph templates;
- strings of `此外/同时/值得注意的是/综上所述` or
  `moreover/furthermore/additionally/notably`;
- abstract nouns where an actor and action are available;
- repeated fashionable verbs or adjectives that carry no technical content;
- uniform sentence or paragraph rhythm caused by template reuse.

Keep the correct term when it is necessary. Human authors also use these forms. The fix
must improve meaning, not merely lower a word count.

### 6. Recheck protected content and provenance

After rewriting:

- compare original and revision with the bundled script;
- trace every new or stronger assertion to the ledger;
- verify cited source metadata and quoted text against the source;
- for patents, recheck antecedent basis, support, claim dependency, terminology,
  reference signs, technical effect, and added-matter risk;
- inspect Word or PDF metadata and revision history only as a disclosure and privacy
  check; report findings rather than silently erasing them.

## Output contract

Return:

1. `profile` and `mode`;
2. findings grouped by P0, P1, and P2, with location and quoted span;
3. evidence-led repair plan;
4. revised text or edited file, if requested;
5. protected-content comparison and unresolved confirmation items;
6. a clear statement that the result is a writing-quality audit, not an authorship
   determination or filing or publication guarantee.

Read [`references/research-basis.md`](references/research-basis.md) when explaining why
detector scores are not the target or when updating the heuristic catalog.
