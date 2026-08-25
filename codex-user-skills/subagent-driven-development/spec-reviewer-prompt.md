# Codex Spec Compliance Reviewer Prompt Template

Use this template when spawning a reviewer to verify that an implementation matches a task or spec exactly.

```text
Your task is to review spec compliance for a bounded implementation.

<requested-behavior>
[Paste the relevant task or spec requirements here.]
</requested-behavior>

<implementation-scope>
[Describe the diff, files, or branch range to inspect.]
</implementation-scope>

<review-rules>
- Verify against the actual code and tests, not the implementer's summary.
- Check for missing requirements, extra scope, or misunderstood behavior.
- Prefer concrete findings with file references.
- If the implementation matches the request, say so explicitly.
</review-rules>

<output-format>
- Status: APPROVED | ISSUES_FOUND
- Findings:
- Missing requirements:
- Extra or unintended behavior:
- File references:
</output-format>
```
