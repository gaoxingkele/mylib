# Research and source basis

Retrieved 2026-09-08. These sources inform review heuristics; none supports determining
the authorship of an individual document from a word list.

## Research findings

- Sadasivan et al., *Can AI-Generated Text be Reliably Detected?* (2023): detection can
  be fragile under paraphrasing and spoofing, with a theoretical limit as model and
  human distributions converge. Implication: do not optimize a detector score.
  <https://arxiv.org/abs/2303.11156>
- Liang et al., *GPT detectors are biased against non-native English writers* (Patterns,
  2023): public detectors produced substantial false positives on the studied
  non-native corpus. Implication: style flags require human, evidence-based review.
  <https://doi.org/10.1016/j.patter.2023.100779>
- Jiang et al., *Detecting ChatGPT-generated essays in a large-scale writing assessment*
  (Computers & Education, 2024): carefully sampled, task-matched linguistic models
  performed differently from generic public detectors. Implication: findings are
  domain- and sampling-dependent, not universal markers.
  <https://doi.org/10.1016/j.compedu.2024.105070>
- Kobak et al., *Delving into ChatGPT usage in academic writing through excess
  vocabulary* (2024): corpus-level shifts identified excess style vocabulary in
  biomedical abstracts. Implication: repeated fashionable words are useful corpus and
  editing signals, not individual proof.
  <https://arxiv.org/abs/2406.07016>
- Liang et al., *Monitoring AI-Modified Content at Scale* (2024): mixture estimation was
  designed for corpus-level prevalence in conference reviews. Implication: do not turn
  population estimates into accusations about one manuscript.
  <https://arxiv.org/abs/2403.07183>
- Shardlow and Przybyła, *Why Does ChatGPT “Delve” So Much?* (COLING, 2025): lexical
  overrepresentation varies by context and model behavior. Implication: repeated style
  words are leads, not universal bans.
  <https://aclanthology.org/2025.coling-main.426/>

## Downloaded GitHub skills and agents

The snapshots below were downloaded to
`skills_external/authorial-authenticity-sources/`. That path is intentionally ignored by
the repository manifest: it is a research cache, not four additional installed skills.
All four repositories declare the MIT license.

| Repository and selected material | Commit | Distilled mechanism |
| --- | --- | --- |
| `msimchowitz/writing-skills`: `general-writing`, `humanizer` | `214981fe02326f27b0fc8790d00eb4b731607073` | minimum effective edit, author-corpus calibration, cadence and semantic-usage passes |
| `wshobson/agents`: `avoid-ai-writing` | `a30778f8c4e6b0a87567941b7cca4f534bf642b6` | separate audit/rewrite/edit modes, context profiles, protected spans, prompt-injection boundary |
| `syq-cmdi/Academic-DeAI` | `676468329e72d03502a8b52e2cfd0fef9112aaf4` | preserve scientific meaning, LaTeX, numbers, statistics, citations, and technical terms |
| `andrehuang/academic-writing-agents`: orchestration and review agents | `d4d9d3a21afbccd4aee9237a70611429e7df4fba` | diagnose before editing; separate logic, writing, technical, consistency, and bibliography views |

Primary repository pages:

- <https://github.com/msimchowitz/writing-skills>
- <https://github.com/wshobson/agents/tree/main/plugins/avoid-ai-writing>
- <https://github.com/syq-cmdi/Academic-DeAI>
- <https://github.com/andrehuang/academic-writing-agents>

This merged skill adds the missing cross-domain layer: article and Chinese patent
profiles, a pre-filing engineering evidence ledger, and deterministic comparison of
protected content before and after revision.
