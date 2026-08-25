# Codex Plan Document Reviewer Prompt Template

Use this template when spawning a reviewer for a completed implementation plan.

```text
Review this implementation plan for execution readiness.

<plan-file>
[PLAN_FILE_PATH]
</plan-file>

<supporting-spec>
[SPEC_FILE_PATH or requirements summary]
</supporting-spec>

<review-focus>
- Missing steps, placeholders, or ambiguous instructions
- Mismatch between spec and plan
- Task decomposition problems
- Missing verification or acceptance criteria
</review-focus>

<output-format>
- Status: APPROVED | ISSUES_FOUND
- Blocking issues:
- Advisory recommendations:
</output-format>
```
