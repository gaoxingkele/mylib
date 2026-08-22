# Adapter: Grok (xAI)

Grok loads skills / instructions via its tools / functions mechanism. The PAA core is loadable
as Grok instructions.

## Invocation

Configure Grok to load `./README.md` as instructions when a patent task is triggered:

```
# in your Grok config:
- skill: paa
  instructions_file: /path/to/paa/README.md
  triggers: ["patent", "PAA", "claim drafting", "prior art search","]
```

## Notes

- Grok's tool calling supports the operations PAA needs (file I/O, shell for Python).
- The four-gate structure is a natural fit for Grok's "validation before commit" patterns.

## Validation

After agent runs PAA compile:
- All cited pns must have matching `evidence/prior_art_search/<pn>.json`
- `scripts/validate.py <paa-dir>` must pass all four gates