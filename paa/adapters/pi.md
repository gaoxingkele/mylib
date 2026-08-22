# Adapter: Pi (Pi AI by Inflection)

Pi uses a context-loading mechanism for instructions. The PAA core is loadable as a custom
context/instructions block.

## Invocation

Provide PAA's `README.md` content to Pi as context / custom instructions when initiating a
patent-drafting task. Pi's context handling will load the methodology.

## Notes

- Pi's conversational style complements PAA's gate-driven approach: ask Pi to first scaffold,
  then compile, then validate.
- For tool execution (file I/O, Python), Pi calls external tools through its own integration layer.

## Validation

After Pi processes a PAA compile task:
- Verify `evidence/prior_art_search/<pn>.json` exists for every pn in `logic/prior_art.md`
- Run `python ./scripts/validate.py <paa-dir>` to confirm gate 1-4 PASS

## Cross-tool consistency note

PAA's core methodology is designed to be portable across tools. If you see inconsistent PAA
behavior between tools (e.g., Claude Code produces a PAA that fails Gate 4 while Pi produces one
that passes), the divergence is in tool-specific behavior, not in PAA. The validate.py script
is the deterministic arbiter — run it locally regardless of which tool produced the artifact.