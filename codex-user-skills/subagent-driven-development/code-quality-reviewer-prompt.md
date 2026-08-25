# Codex Code Quality Reviewer Prompt Template

Use this template when spawning a reviewer to inspect implementation quality after spec compliance is acceptable.

```text
Your task is to review code quality for a bounded change set.

<scope>
[Describe the diff, files, or branch range.]
</scope>

<requirements>
[Paste the relevant task summary or requirements.]
</requirements>

<review-focus>
- Correctness risks
- Maintainability and clarity
- Test adequacy
- Error handling
- Performance or security issues if relevant
- Whether the change introduced unnecessary complexity
</review-focus>

<output-format>
- Verdict: APPROVE | REQUEST_FIXES
- Critical findings:
- Important findings:
- Minor findings:
- File references:
- Overall assessment:
</output-format>
```
