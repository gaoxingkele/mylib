# ResearchStudio-Idea → powergrid journal distill adaptation

Paper: https://arxiv.org/abs/2607.04439
Code: D:/aicoding/lib/ResearchStudio/ResearchStudio-Idea
Skills: D:/aicoding/lib/skills/ResearchStudio-Idea (+ ~/.claude/skills junctions)

## What we reused
- 15 ideation pattern vocabulary + operational-signature thinking
- lit_table tagging schema (pattern tags / bottleneck / open issue)
- Pattern cards with success conditions + failure modes
- Multi-pattern composition (companion combos)

## What we changed for journals
- Corpus = accepted OA full-texts per target journal (not Oral/Reject conference labels)
- Added journal-house patterns (named stack+case, survey, hardware, IoT/security, storage)
- Outputs feed Paper_CCF `journals/*/SKILL.md` for manuscript routing/writing

Run script: `D:\aicoding\powergrid_benchmark/scripts/literature/ideaspark_journal_pattern_distill.py`