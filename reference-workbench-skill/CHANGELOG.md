# Changelog

All notable changes to Reference Workbench Skill.

## [2.0.0] — 2026-05-14

### Changed
- **Unified pipeline**: replaced Mode A/B binary with single Write → Self-Audit → Safety Check pipeline
- After every write operation, offer citation verification as a safety-net step
- Auto-detect task from user input instead of asking user to choose mode
- `[CITE:xxx]` placeholder format unified across writing and self-audit

### Added
- Rewrite draft scenario (normalize existing citations to `[CITE:xxx]`)
- Phase 3: silent auto quick-check for small drafts (<5 refs)
- Phase 5: final deep-check offer after session completion
- `allowed-tools` field in frontmatter (13 tools)
- `user-invocable: true` declaration
- `metadata` block with author, tags, sources, replaces, mcp-categories
- Optional MCP section (Zotero + DeepL)
- `assets/example-draft-en.md` and `assets/example-draft-zh.md` sample files
- `.gitignore` to exclude PDFs

### Fixed
- `cite_table.py` Unicode crash on Windows (GBK encoding → UTF-8 wrapper)
- `setup.sh` → `setup.py` for cross-platform compatibility
- `citation-placement-rules.md` deferred from startup to on-demand (~1300 tokens saved)

## [1.5.0] — 2026-05-14

### Added
- Auto mode detection from user input keywords
- Rewrite scenario in five writing scenarios
- Consistent `[CITE:xxx]` placeholder format across self-audit checks

## [1.4.0] — 2026-05-14

### Added
- Optional MCP support: Zotero (reference library), DeepL (academic translation)
- Categorized MCP dependencies in README (required vs optional)

## [1.3.0] — 2026-05-14

### Added
- MCP categorization: Search (arxiv, scholar, paper-search, crossref) vs Tool (pdf-reader)
- `mcp-categories` metadata field

## [1.2.0] — 2026-05-14

### Added
- Crossref MCP support (crossref-academic-mcp-server)
- Cross-platform `setup.py` replacing bash-only `setup.sh`

## [1.1.0] — 2026-05-14

### Added
- `allowed-tools` field (13 tools)
- Expanded description with 15+ trigger phrases (Chinese + English)
- Comprehensive `metadata` block

## [1.0.0] — 2026-05-14

### Added
- Initial release: merged citation-check and introduction-review skills
- Mode A: Citation verification with 8-level fallback chain
- Mode B: Literature review writing with `cite_table.py` engine
- 5-column reference table output (bilingual)
- Always-on checks: stacking, format, order, orphan, tone, citation depth
