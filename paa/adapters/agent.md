# Adapter: Generic AI Agent SDKs

For generic AI Agent frameworks (e.g., custom agents built on Claude API / OpenAI / local models), the
PAA core loads as plain markdown instructions. No special adapter required.

## Invocation

When the agent's system prompt / task instruction includes PAA's `README.md`, the agent can:

1. **Compile a PAA from inputs**: user provides prior-art, claims, disclosure, etc. → agent produces the
   four-layer artifact under `./<paa-dir>/`.
2. **Validate an existing PAA**: run `python ./scripts/validate.py <paa-dir>` and report results.
3. **Scaffold a new PAA**: run `python ./scripts/scaffold.py <paa-dir> --case-id X --case-name "..."`.

## Recommended system-prompt snippet

```
# PAA Compiler

You have access to a PAA (Patent Application Artifact) methodology in
`<skill-path>/README.md`. Load that file first when the user requests any
patent-drafting task. Use `references/paa-schema.md` for field-level format.
Use `references/gates-checklist.md` for the four hard gates.
Use `references/validation-checklist.md` for structural checks.
Run `scripts/validate.py <paa-dir>` programmatically.
```

## Tools expected to be available

- File I/O (read/write/edit any path)
- Bash / shell (run scripts)
- Glob / Grep (search for pn patterns, file existence)
- Task delegation (for parallel evidence collection)

## Verification

After agent runs validate.py, output should include:
- Per-check PASS/WARN/FAIL counts
- Per-gate status (1-4)
- Cross-layer binding resolution confirmation

If any FAIL, agent must NOT silently lower gate threshold; surface the gap and pause.