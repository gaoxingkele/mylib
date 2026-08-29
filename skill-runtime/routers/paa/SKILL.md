---
name: paa
description: Route Chinese invention-patent work through the Patent Application Artifact framework. Use to compile a four-layer PAA, run evidence and CNIPA gates, validate cross-layer bindings, or select a PAA patent sub-skill.
metadata:
  source-root: "D:/aicoding/mylib/paa"
---

# PAA router

The maintained framework is `D:/aicoding/mylib/paa`.

- To compile or validate a PAA, read `D:/aicoding/mylib/paa/SKILL.md`, then only the referenced schema
  or gate files needed for the task.
- To select a patent sub-skill, read `D:/aicoding/mylib/paa/skills/README.md` and then the one selected
  `SKILL.md`.
- Keep incoPat credentials in the runtime environment or the ignored local credentials file. Never
  copy credentials into this router or generated artifacts.

This lightweight entry deliberately does not contain a junction to the full `paa` tree, because the
patent sub-skills are installed independently and recursive discovery would register them twice.
