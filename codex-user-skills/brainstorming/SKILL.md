---
name: brainstorming
description: Use when a feature, behavior change, UX idea, or broad request needs design clarification before implementation.
---

<Purpose>
Turn an idea into an approved design before writing code. In Codex, this skill is a design gate: gather context, clarify the problem, compare options, then produce a design the user can approve.
</Purpose>

<Use_When>
- The user wants to build something new but the shape is still fuzzy
- A request changes behavior across multiple files or subsystems
- UX, product, workflow, or architecture decisions need to be made first
- The repo would benefit from a short written spec before planning or coding
</Use_When>

<Do_Not_Use_When>
- The task is already concrete and can be implemented safely right away
- The user explicitly wants immediate implementation and the scope is narrow
- The request is a small, obvious bug fix with clear acceptance criteria
</Do_Not_Use_When>

<Codex_Notes>
- Use normal repository inspection tools first: `rg`, `Get-ChildItem`, file reads, and code search
- Ask at most one clarifying question at a time when clarification is truly needed
- Prefer concise design artifacts over long speculative documents
- If the repo already has a planning workflow, hand off to that instead of inventing a new one
</Codex_Notes>

<Execution_Policy>
- Explore the current codebase and docs before proposing designs
- If the idea is too broad, decompose it into smaller deliverables before going deeper
- Present 2-3 viable approaches when tradeoffs matter; otherwise present one recommended design directly
- Do not start implementation until the design is sufficiently approved for the task's risk level
- If a written artifact is useful, save it in the repo's preferred planning/spec location
</Execution_Policy>

<Steps>
1. Inspect the relevant code, docs, and existing patterns.
2. Identify unknowns: user intent, constraints, success criteria, risks, and integration points.
3. Ask one focused question only if inspection cannot answer the unknown safely.
4. Propose the recommended design, and include alternatives when the choice is materially branching.
5. Confirm the design with the user when approval is needed.
6. If requested or useful, write a short design/spec document in the repo's planning location.
7. Hand off to `writing-plans`, the native `plan` workflow, or direct execution depending on the user's intent.
</Steps>

<Outputs>
- A clear statement of the problem being solved
- The recommended design and key tradeoffs
- Explicit constraints and assumptions
- A written spec only when it adds real value
</Outputs>
