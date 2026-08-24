---
name: cn-patent-application-cluster
description: Use when Codex needs to mine patent points, plan Chinese patent portfolios, draft or review CNIPA-style invention, utility-model, or design-patent materials, generate technical disclosures, run prior-art preparation, or package patent deliverables from papers, code, product docs, designs, meeting notes, or existing drafts.
---

# CN Patent Application Cluster

<Purpose>
Turn technical materials into review-ready Chinese patent deliverables by using a Codex-native agent cluster pattern: planner, disclosure analyst, prior-art researcher, claim drafter, specification drafter, drawing planner, examiner, quality reviewer, and packager.
</Purpose>

<Use_When>
- The user asks to write, improve, or plan a Chinese patent application.
- Inputs include papers, code repositories, product documents, technical disclosures, meeting notes, prior drafts, or mixed folders.
- The task needs patent-point mining, CNIPA-style drafting, claim strategy, prior-art search planning, office-action preparation, DOCX/Markdown packaging, or review loops.
- The input is source code or a paper whose conversion must remain traceable to concrete evidence.
- The user needs Chinese design-patent routing for product appearance, GUI, dynamic GUI, color, or partial designs.
</Use_When>

<Do_Not_Use_When>
- The task is only a legal conclusion such as patentability, infringement, or freedom-to-operate with no drafting work. Provide a scoped caveat and recommend qualified counsel.
- The user wants a non-Chinese jurisdiction-specific filing unless they explicitly ask to adapt this workflow.
</Do_Not_Use_When>

<Execution_Policy>
- Work in the current repository. Do not modify external reference repositories under `references/` unless the user asks.
- Preserve existing `.claude/` assets; this skill is Codex-native and lives under `.codex/`.
- Prefer evidence over invention. Mark facts as `confirmed`, `inferred`, or `needs-confirmation`.
- Do not list AI as an inventor. Require natural-person inventor confirmation.
- Do not claim CNIPA/INCOPAT/智慧芽 deep search is complete unless those systems were actually searched.
- If a paper is not public, prioritize patent filing before publication; still capture written confirmation.
- Keep deliverables separate from internal checks. Do not paste self-check tables into formal patent text unless the user asks for an audit artifact.
</Execution_Policy>

<Workflow>
1. **Intake and Evidence Map**
   - Read `references/workflow-blueprint.md`.
   - Create an evidence table with source path, fact, confidence, and filing relevance.
   - For paper or code inputs, read `references/source-fidelity-and-code-evidence.md`; retain both the abstract mechanism and the concrete source/commit evidence.
   - If inputs include `.docx`, `.pptx`, `.pdf`, or images, use available document tools or existing repository scripts before drafting.

2. **Patent Point Tree**
   - Use `references/claim-strategy.md`.
   - Produce 3-5 candidate patent points, then merge or rank them.
   - Build a PGTree-style hierarchy: problem -> mechanism -> differentiator -> implementation support -> claim anchor.

3. **Prior-Art and Publication Gate**
   - Use `references/prior-art-and-publication-gate.md`.
   - Search current repository evidence first.
   - Prepare CNIPA/INCOPAT/智慧芽 query plans when deep search cannot be run directly.
   - Record whether papers/materials are public, confidential, or unconfirmed.

4. **Disclosure Draft**
   - Draft a technical disclosure before a full application unless the user already supplied one.
   - Use `references/disclosure-and-application-structure.md`.
   - Include technical problem, detailed solution, embodiments, technical effects, drawings, and claim preference points.

5. **Application Draft**
   - Route appearance, GUI, dynamic-GUI, color, and partial-design matters through `references/design-patent-routing.md`; do not generate invention claims or a five-section invention specification for a design patent.
   - Draft claims first, then specification, abstract, drawing description, and sequence/figure list as applicable.
   - Keep claim terms aligned with the specification.
   - Anchor algorithm inventions to technical data, devices, control actions, diagnosis, scheduling, manufacturing, or operations.

6. **Examiner Loop**
   - Use `references/review-gates.md`.
   - Read `references/claim-formal-validation.md` after drafting or materially changing a claim set.
   - Run novelty/inventiveness/support/clarity/subject-matter review.
   - Apply at least one revision pass before declaring a draft ready.

7. **Package and Verify**
   - Run `scripts/patent_static_check.py <draft.md>` for Markdown drafts when applicable.
   - Run `scripts/claim_formal_check.py <claims.md> --json` for a separate Chinese claim set and resolve every deterministic error.
   - Produce a delivery index listing files, versions, remaining risks, and external confirmations.
   - For DOCX deliverables, use the document rendering/verification workflow available in this environment.
</Workflow>

<Agent_Roles>
Role prompt files live in project `.codex/agents/`:
- `cn-patent-orchestrator.toml`: routes and integrates the workflow.
- `cn-patent-disclosure-analyst.toml`: extracts invention facts and missing evidence.
- `cn-patent-prior-art-researcher.toml`: prepares and interprets prior-art searches.
- `cn-patent-claim-drafter.toml`: writes claim sets and fallback positions.
- `cn-patent-specification-drafter.toml`: writes the specification and embodiments.
- `cn-patent-examiner.toml`: attacks novelty, inventiveness, support, clarity, and subject matter.
- `cn-patent-packager.toml`: prepares Markdown/DOCX handoff and audit indices.
</Agent_Roles>

<Quality_Bar>
- Every independent claim has a clear differentiator.
- Every differentiator has specification support.
- Every key formula has symbol definitions and an embodiment path.
- Every prior-art assertion has a source or is marked as a search hypothesis.
- Every source-derived feature has a paper page, code location/commit, design asset, or explicit confirmation; unsupported additions are gaps rather than invented facts.
- Every claim set passes deterministic numbering, dependency, and one-sentence checks before a legal-quality conclusion is made.
- Every final report includes changed/generated files, simplifications or upgrades made, and remaining risks.
</Quality_Bar>
