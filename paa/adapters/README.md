# PAA Tool Adapters

The core of PAA (`README.md`) is intentionally tool-agnostic — written as plain markdown instructions that
any LLM-based tool can load directly. The adapters here are thin wrappers that ingest the core and
format it for specific tools.

## The principle

PAA core = `README.md` (~7 KB) + references/ + scripts/.

To use PAA in a new tool, in order of effort:

1. **First**: can the tool load `README.md` directly as instructions? If yes, you're done.
2. **Otherwise**: write a thin adapter that:
   - Tells the tool to read `./README.md` as the methodology
   - Adds tool-specific config (e.g., Claude Code frontmatter, Codex CLI plugin.json schema)
   - Keeps the reference docs the same (they're already tool-neutral)

The reference docs (`references/paa-schema.md`, `references/gates-checklist.md`,
`references/validation-checklist.md`, `references/exploration-tree-spec.md`) are loaded on demand by
any tool — they're plain markdown, no special parsing.

## Per-tool adapters

| Tool | Adapter file | Status | Notes |
|---|---|---|---|
| Claude Code | `../SKILL.md` | ready | Frontmatter + tools spec; lives at skill root |
| Codex CLI | `codex.md` | ready | Plugin manifest format reference |
| Generic AI Agent SDKs | `agent.md` | ready | Plain instructions; works with any agent that loads markdown |
| Kimi | `kimi.md` | ready | Wraps core for Kimi's skill/agent format |
| Grok | `grok.md` | ready | Wraps core for Grok plugin format |
| Pi | `pi.md` | ready | Wraps for Pi assistant format |

When loading PAA in a new tool, prefer to copy the `README.md` content as the system prompt / instructions
directly. The per-tool wrappers exist for compatibility with discovery mechanisms (how a tool finds
its skills/plugins), not for behavior modification.