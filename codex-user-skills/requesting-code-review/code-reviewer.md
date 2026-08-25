# Codex Code Reviewer Template

Use this template as the body for a `code-reviewer` subagent or equivalent review workflow.

```text
Review the following change set for production readiness.

<what-was-implemented>
{WHAT_WAS_IMPLEMENTED}
</what-was-implemented>

<requirements>
{PLAN_OR_REQUIREMENTS}
</requirements>

<diff-scope>
Base: {BASE_SHA}
Head: {HEAD_SHA}
</diff-scope>

<review-checklist>
- Correctness and regressions
- Security and trust-boundary issues
- Maintainability and unnecessary complexity
- Test coverage and test relevance
- Requirement alignment and scope control
</review-checklist>

<output-format>
### Findings
- Severity: Critical | High | Medium | Low
- File reference
- Problem
- Why it matters
- Suggested fix

### Overall Assessment
- Ready to merge: Yes | No | With fixes
- Short rationale
</output-format>
```
