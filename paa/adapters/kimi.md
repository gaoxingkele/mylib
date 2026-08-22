# Adapter: Kimi (Moonshot AI)

Kimi uses skill/agent files that load markdown instructions. The PAA core (`README.md`) is
loadable as Kimi instructions.

## Invocation

In your Kimi config / workspace:

```
# .kimi/skills/paa/README.md → symlink or copy from this repo
```

Or reference PAA as a project-local instruction:

```
# in your Kimi task definition:
- skill: paa
  instructions: read ./README.md from /path/to/paa/
```

## Notes

- Kimi's instruction loader accepts plain markdown; the PAA core is fully readable as-is.
- For tool execution (Python scripts, file I/O), Kimi runs them via its shell tool.
- The four-gate structure is a natural fit for Kimi's "checklist before output" patterns.

## Validation

After agent runs PAA compile:
- Confirm `evidence/prior_art_search/<pn>.json` files exist for every cited pn
- Run `python ./scripts/validate.py <paa-dir>` and inspect gates 1-4