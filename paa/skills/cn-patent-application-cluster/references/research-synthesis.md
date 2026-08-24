# Research Synthesis: External Patent Agent Systems

## Sources Captured Locally

- AutoPatent: `references/AutoPatent/`, paper PDF at `references/papers/AutoPatent_arxiv_2412.09796.pdf`.
- patent-disclosure-skill: `references/patent-disclosure-skill/`.
- patentGPT: `references/patentGPT/`.
- patent_creator: `references/patent_creator/`.
- Paper2Patent: `references/github-patent-ecosystem/paper2patent/` at `6a37c3a` (MIT).
- cn-patent: `references/github-patent-ecosystem/cn-patent/` at `3731017` (MIT; compared against the existing disclosure skill rather than installed twice).
- Obviously-Not patent-skills: `references/github-patent-ecosystem/patent-skills/` at `396050a` (MIT).
- patent-cn-spec: `references/github-patent-ecosystem/patent-cn-spec/` at `ae041f1` (MIT).
- claim_drafter: `references/github-patent-ecosystem/claim_drafter/` at `80f8700` (MIT).

## AutoPatent

Useful pattern: planner/writer/examiner separation, Draft2Patent framing, long-form patent generation, PGTree planning, RRAG retrieval augmentation, and examiner loop. The public repository currently contains paper/demo assets and examples rather than full runnable framework code, so reuse the architecture pattern rather than importing code.

Adopted ideas:
- Build a patent-point tree before writing.
- Separate planning, writing, and examination.
- Treat full patent generation as a long-context structured task, not a single prompt.
- Track repetition and long-document coherence.

## patent-disclosure-skill

Useful pattern: nine-step disclosure workflow, project scanning, patent-point mining, CNIPA publication-site first search, Markdown/DOCX delivery, mermaid drawings, timestamped iteration, and self-check separation.

Adopted ideas:
- Use disclosure before full application when facts are incomplete.
- Keep prior-art search before final drafting.
- Preserve iteration logs and avoid overwriting old drafts.
- Keep self-check internal and do not pollute final disclosure text.

## patentGPT

Useful pattern: simple input-folder-first flow and interaction to fill missing disclosure facts.

Adopted ideas:
- Read user-provided `input/` or project material first.
- Generate an initial disclosure skeleton, then ask only for missing facts that materially affect claims.
- Split generation into claims, specification, abstract, and figure description.

## patent_creator

Useful pattern: agent workbench, stable document model, section/block edits, tool boundaries, context compression, event logs, DOCX export, and benchmark-driven quality loops.

Adopted ideas:
- Treat patent deliverables as structured documents with stable sections.
- Read before editing; avoid whole-document blind rewrites.
- Use benchmark/rubric-style review gates rather than judging by length.
- Maintain a delivery index and audit artifacts.

## 2026 GitHub Patent-Skill Distillation

### Paper2Patent

Useful pattern: a source-fidelity gate for paper conversion, explicit material-gap placeholders, source-figure-first drawing derivation, and cross-document terminology checks.

Adopted ideas:
- Keep a transformation ledger from paper fact to patent abstraction.
- Treat unsupported hardware, scenarios, parameters, and effects as gaps rather than plausible completions.
- Mark downstream reviews stale when the source paper or claim set changes.

### patent-skills

Useful pattern: preserve a lossy abstract mechanism and a concrete code reference together; prioritize custom algorithms, feedback loops, concurrency, failure recovery, and architecture over boilerplate; map each candidate to files, commits, design decisions, and benchmarks.

Adopted ideas:
- Add a code-to-patent evidence ladder.
- Separate engineering distinctiveness from legal patentability.
- Record design-around pressure and product centrality for attorney-review prioritization.

### patent-cn-spec

Useful pattern: explicit invention/design routing, multi-theme Chinese claim templates, and design-patent rules for six-view products, dynamic GUI key frames, color, partial designs, and similar-design unity.

Adopted ideas:
- Add a design-patent routing reference instead of forcing every matter through invention claims.
- Preserve separate formal gates for invention and design applications.

### claim_drafter

Useful pattern: programmatic validation for claim numbering, dependency direction, self-reference, and single-sentence form; calibration against granted claims; keeping noisy antecedent-basis regexes diagnostic rather than absolute.

Adopted ideas:
- Add a standard-library Chinese claim-form checker and regression tests.
- Treat prosecution state as data provenance: as-filed is not automatically as-allowed.
- Do not turn an uncalibrated antecedent parser into a hard drafting score.

### Excluded from Code Integration

- `abhirajthakur/provenance`: useful independent citation-verification architecture, but no repository license was declared at review time. Only the general two-gate idea was restated; no code or text was copied.
- `gfodor/legal-skills`: GPL-3.0 and US-law-specific. Kept as a research lead, not mixed into this project's skill/code surface.

## Our System Direction

This project should not become a heavy web app by default. The right Codex-native form is:

1. A project skill that tells Codex when and how to execute the workflow.
2. Role prompts under `.codex/agents/` for specialized passes.
3. Reference files for claim strategy, prior-art gates, drafting structure, and review gates.
4. Lightweight scripts for static checks that are useful without API keys.
5. Wiki capture for project-specific lessons and filing state.
