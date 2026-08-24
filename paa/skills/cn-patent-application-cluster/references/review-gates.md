# Review Gates

## Gate A: 26.3 / 26.4 Support and Disclosure

Check:
- can a person skilled in the art reproduce the claimed feature;
- every claim term appears in the specification;
- formulas have symbol definitions and boundary handling;
- embodiments support broad claim language;
- no unsupported effect is asserted.

## Gate B: 22.2 / 22.3 Novelty and Inventiveness

Run a three-step attack:

1. closest prior art;
2. distinguishing features;
3. actual technical problem and whether prior art gives motivation.

If the differentiator is only a model name, score the claim as weak.

## Gate C: Subject Matter

For algorithms, AI, business rules, and data processing:
- tie the solution to technical data, technical equipment, or technical control;
- describe technical effect in measurable technical terms;
- include system/device claims with processor, memory, interface, and modules when appropriate.

## Gate D: Formal Quality

Check:
- no TODO or placeholders in final application;
- no AI/tool/process meta text in formal sections;
- abstract concise and no claim-style overloading;
- drawings referenced consistently;
- Markdown and DOCX versions match.

## Gate E: Static Check

Run:

```powershell
python .codex/skills/cn-patent-application-cluster/scripts/patent_static_check.py <draft.md>
```

Treat warnings as prompts for review, not automatic legal conclusions.
