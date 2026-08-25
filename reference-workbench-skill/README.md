# Reference Workbench Skill

[![Version](https://img.shields.io/badge/version-2.0.0-blue)](https://github.com/haiyichen001/reference-workbench-skill/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow)](LICENSE)
[![Agent Skills](https://img.shields.io/badge/agent--skills-compatible-green)](https://agentskills.io)
[![Platform](https://img.shields.io/badge/platforms-Claude%20Code%20%7C%20Codex%20%7C%20Gemini%20%7C%20Cursor%20%7C%20VS%20Code-lightgrey)](https://agentskills.io)

An agent skill that verifies academic citations and writes literature reviews with auto-generated bibliographies. Checks paper existence, metadata accuracy, and whether cited claims are actually supported. Compatible with Claude Code, Codex, Gemini CLI, Cursor, VS Code, and 20+ other editors that support the Agent Skills standard.

This skill merges and supersedes the former [citation-check-skill](https://github.com/haiyichen001/citation-check-skill) and [introduction-review-skill](https://github.com/haiyichen001/introduction-review-skill).

## What it does

| Feature | Description |
|---------|-------------|
| Citation verification | Checks existence, metadata, and content support for every citation |
| Literature review writing | Guided workflow for introductions and lit reviews with auto-numbered references |
| Reference table generation | Deterministic 5-column table: #, Author, Context, Reference, Status |
| Self-audit | Auto-checks stacking, format, order, orphans, and tone after every edit |
| Multi-format input | PDF, DOCX, TXT, Markdown, LaTeX |

Also useful for: detecting AI-hallucinated references in papers — LLM-generated citations that look real but don't exist.

## Install

### Universal (any agent)

Download and copy the skill folder into your agent's skills directory:

| Agent | Project scope | User scope |
|-------|--------------|------------|
| Claude Code | `.claude/skills/` | `~/.claude/skills/` |
| Codex | `.codex/skills/` | `~/.codex/skills/` |
| Gemini CLI | `.gemini/skills/` | `~/.gemini/skills/` |
| Cursor | `.cursor/skills/` | `~/.cursor/skills/` |
| VS Code / Copilot | `.github/skills/` | `~/.copilot/skills/` |

### CLI quick install

```bash
npx skills add haiyichen001/reference-workbench-skill
```

### Manual

```bash
git clone git@github.com:haiyichen001/reference-workbench-skill.git
cp -r reference-workbench-skill/.claude/skills/reference-workbench ~/.claude/skills/
```

### MCP dependencies

**Required:**

| Category | MCP | Purpose |
|----------|-----|---------|
| Search | arxiv | arXiv paper lookup |
| Search | scholar | Semantic Scholar verification |
| Search | paper-search | PubMed / bioRxiv / Google Scholar |
| Search | crossref | Crossref DOI + OpenAlex + Semantic Scholar |
| Tool | pdf-reader | PDF text extraction |

```bash
npx smithery install @smithery-ai/arxiv
npx smithery install @smithery-ai/scholar
npx smithery install @smithery-ai/paper-search
pip install crossref-academic-mcp-server
```

**Optional (enhanced workflow):**

| MCP | What it adds | Install |
|-----|-------------|---------|
| Zotero | Reference library integration — search your library, import papers, Word citations | `npx smithery install @alisoroushmd/zotero-mcp` |
| DeepL | Academic translation (中文 ↔ English), glossary-locked terminology | `npm install deepl-mcp-server` (free API key) |

## Usage

```
/reference-workbench
```

Single pipeline: **Write → Self-Audit → Auto Quick Check → (when done) Offer Deep Check**.

1. **Writing** — draft/rewrite/audit with `[CITE:xxx]` placeholders, auto-generate reference table
2. **Quick check** — after every write operation, silently verifies each reference exists (no prompt)
3. **Deep check** — when you're done, the agent asks once if you want to upgrade to normal or deep verification

You can also use `/reference-workbench` directly with a file to run a full citation verification.

### Example files

Two real academic texts included in `assets/` to test the skill:

| File | Content | Citations |
|------|---------|-----------|
| `assets/example-draft-en.md` | English journal paper intro (3D-printed concrete, *Commun. Eng.* 2026) | 39 refs, IEEE |
| `assets/example-draft-zh.md` | Chinese doctoral thesis intro (Ce-MOFs, USTB 2025) | 19 refs, GB/T 7714 |

To try the skill: copy either file, then run `/reference-workbench` and paste it. The skill will auto-detect the language and format.

### Verification statuses

| Status | Meaning |
|--------|---------|
| Verified | Paper exists, metadata correct, content supports the claim |
| Metadata Mismatch | Paper exists but author/year/venue differs |
| Content Mismatch | Paper exists but cited content does not support the claim |
| Fabricated | Paper does not exist — likely AI hallucination |
| Unverifiable | Insufficient data (e.g. Chinese thesis not indexed) |

## Limitations

Chinese papers (CNKI/Wanfang/VIP) are not yet supported — no open API or MCP server exists for Chinese academic databases.

## License

MIT
