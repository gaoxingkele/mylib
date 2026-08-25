---
name: test-driven-development
description: Use when implementing a feature, bug fix, or behavior change where a failing test should define the work first.
---

<Purpose>
Apply Red-Green-Refactor in Codex. Write the failing test first, prove it fails for the right reason, then write the minimal implementation to pass.
</Purpose>

<Use_When>
- New behavior is being added
- A bug fix should be locked by regression coverage
- Refactoring must preserve behavior under test
</Use_When>

<Do_Not_Use_When>
- The change is documentation-only
- The repo genuinely has no reasonable automated test surface for the work
- The user explicitly rejects TDD for a low-value throwaway path
</Do_Not_Use_When>

<Execution_Policy>
- No production code before a failing test or equivalent executable check
- The red phase must fail for the intended reason, not a setup mistake
- The green phase should use the smallest change that satisfies the test
- Refactor only after green, and keep the suite green throughout
</Execution_Policy>

<Cycle>
1. Write one focused failing test.
2. Run it and confirm the failure is correct.
3. Implement the minimum code needed to pass.
4. Re-run the targeted test.
5. Run broader regression checks as appropriate.
6. Refactor while keeping the suite green.
</Cycle>

<Codex_Notes>
- Use existing test patterns from the repo rather than inventing a new style
- For bug fixes, prefer a regression test that fails on the old behavior
- If the repo lacks tests, create the smallest viable executable proof before editing
</Codex_Notes>
