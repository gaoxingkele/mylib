# Codex Spec Document Reviewer Prompt Template

Use this template when spawning a reviewer for a written spec or design document.

```text
Review this spec document for planning readiness.

<spec-file>
[SPEC_FILE_PATH]
</spec-file>

<review-focus>
- Missing sections, placeholders, or unresolved ambiguity
- Internal contradictions
- Scope that is too broad for one implementation plan
- Unnecessary complexity or speculative extras
</review-focus>

<calibration>
Only flag issues that would cause an implementation plan to be wrong, incomplete, or misleading.
</calibration>

<output-format>
- Status: APPROVED | ISSUES_FOUND
- Blocking issues:
- Advisory recommendations:
</output-format>
```
