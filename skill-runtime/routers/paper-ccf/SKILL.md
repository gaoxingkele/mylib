---
name: paper-ccf
description: Route computer-science and engineering manuscripts to maintained conference or journal profiles. Use for venue selection, fit, evidence expectations, review model, submission-cycle, desk-reject risk, or fallback venue analysis.
metadata:
  source-root: "D:/aicoding/mylib/Paper_CCF"
---

# Paper CCF router

The maintained catalog is `D:/aicoding/mylib/Paper_CCF`.

1. Identify the venue name, acronym, or selection criteria.
2. Use `D:/aicoding/mylib/Paper_CCF/data/venues.json` or the indexes in
   `D:/aicoding/mylib/Paper_CCF/SKILL.md` to resolve the slug.
3. Read exactly one matching profile:
   - Conference: `D:/aicoding/mylib/Paper_CCF/skills/<slug>/SKILL.md`
   - Journal: `D:/aicoding/mylib/Paper_CCF/journals/<slug>/SKILL.md`
4. Load additional shared resources only when the selected profile requires them.
5. Verify current deadlines, fees, templates, and policies against the official venue site.

Do not recursively load or register the full venue catalog; it contains more than 180 profiles and is
designed for on-demand routing.
