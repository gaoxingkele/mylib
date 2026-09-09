# Academic Humanizer 1.0

`academic-humanizer` is retained as the stable skill identifier. Version 1.0 broadens
the skill into an authorial-authenticity and evidence review for Chinese or English
papers, proposals, articles, and patent drafts.

The goal is not to defeat an AI detector. The skill improves the properties that a
serious author, reviewer, patent attorney, or editor can actually verify:

- every substantive statement has a source;
- reasoning connects observations, mechanisms, and bounded conclusions;
- the prose follows the conventions of its genre;
- revisions preserve numbers, citations, equations, terminology, and patent scope;
- the result remains attributable to real author or inventor materials.

## Files

- `SKILL.md`: routing, boundaries, and end-to-end workflow.
- `references/domain-profiles.md`: separate gates for papers, articles, and patents.
- `references/review-roles.md`: provenance, logic, genre, voice, and integrity roles.
- `references/research-basis.md`: papers, downloaded GitHub sources, versions, and
  distilled findings.
- `scripts/authenticity_audit.py`: deterministic text or DOCX audit and original versus
  revision protected-token comparison.
- `tests/test_authenticity_audit.py`: regression tests.

## Examples

```powershell
python scripts/authenticity_audit.py audit manuscript.docx --profile paper
python scripts/authenticity_audit.py audit application.docx --profile patent --format json
python scripts/authenticity_audit.py compare original.docx revised.docx --profile patent
```

Supported inputs are `.txt`, `.md`, `.tex`, and `.docx`. The tool deliberately reports
heuristic signals rather than an “AI probability”. Metadata is reported for manual
privacy and disclosure review and is never erased automatically.

## Source and license

This repository keeps the original MIT license and attribution. Version 1.0 is an
original synthesis informed by the MIT-licensed projects and research listed in
`references/research-basis.md`. The downloaded source snapshots are stored under the
repository's ignored `skills_external/authorial-authenticity-sources` research cache;
they are not independently registered skills.
