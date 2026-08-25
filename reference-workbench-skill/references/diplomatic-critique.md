# Diplomatic Critique Phrase Bank

> Loaded with skill at startup. **Mandatory tone guard. Never write harsh critique.**

## Core Principle

Critique the work, not the authors. Every limitation statement should be paired with evidence. Use comparison ("whereas", "while", "in contrast") instead of attack ("fails", "wrong", "ignores").

## FORBIDDEN Phrases (Never Use)

These are absolute bans. The script's position checker may flag them.

| Forbidden | Why | Replacement |
|-----------|-----|-------------|
| "X fails to..." | Implies incompetence | "X does not..." / "X is limited in..." |
| "X ignores..." | Accusatory | "X does not account for..." |
| "X is fundamentally flawed" | Personal attack on the work | "X has limitations when applied to..." |
| "X makes no attempt to..." | Dismissive | "Y was not within the scope of X" |
| "X is wrong about..." | Confrontational | "Findings by X differ from..." / "X's conclusion has been challenged by..." |
| "Surprisingly, X did not consider..." | Condescending | Remove "Surprisingly" — state the gap factually |
| "It is astonishing that..." | Subjective, unprofessional | Never use |
| "X completely overlooks..." | Hyperbolic | "X was not designed to address..." |
| "To the best of our knowledge, no prior work has..." | Risky absolute claim | "We are not aware of prior work that specifically addresses..." |
| "X's approach is naive" | Insulting | "X's approach trades off complexity for..." |
| "X neglects to mention..." | Implies dishonesty | "X's analysis did not include..." |
| "X's results are questionable" | Undermines credibility | "X's results have not been replicated in..." / "Independent validation of X's findings would strengthen..." |

## Highlighting Gaps (Diplomatic)

| Situation | Recommended Phrasing |
|-----------|---------------------|
| A topic is understudied | "Few studies have explored..." / "Research on X remains limited..." / "The literature on X is still emerging..." |
| A method has a limitation | "While effective for [scenario A], this approach may not generalize to [scenario B]..." |
| Conflicting findings exist | "Findings on X remain inconclusive. Smith [1] reports A, whereas Jones [2] finds B, suggesting that..." |
| A study used small data | "The generalizability of these findings is constrained by the limited sample size..." |
| An assumption is restrictive | "This framework operates under the assumption that..., which may not hold in..." |
| A method is outdated | "Early approaches to X primarily relied on [old method]. Recent advances in [new method] offer opportunities to..." |
| Results are inconsistent | "There is no consensus on X. Studies using method A report Y [1,2], while those using method B find Z [3]." |
| Computational cost is high | "The computational demands of this approach challenge real-time deployment..." |
| Dataset is narrow | "The dataset focuses exclusively on [domain], limiting generalizability to [other domains]..." |
| Accuracy trade-off | "The trade-off is a N% drop in accuracy compared to offline methods, which may be unacceptable for precision-critical applications..." |
| Missing baseline comparison | "A direct comparison with [standard baseline] would contextualize these results..." |
| Only tested in simulation | "Validation has been limited to simulated environments; physical testing would confirm real-world applicability..." |

## Acknowledging Contributions Before Critiquing

The structure is always: "X achieved [positive], however/although/despite [limitation]."

### Templates

- **Pioneer but limited scope**: "Smith [1] pioneered the use of GNNs for mesh segmentation, achieving state-of-the-art results on clean synthetic data. However, their method assumes watertight input meshes, which rarely occur in real-world 3D scans."
- **Good benchmark but narrow**: "The dataset introduced by Jones [2] has become a standard benchmark. While comprehensive, it focuses exclusively on indoor objects and does not represent outdoor or large-scale scenes."
- **Elegant but costly**: "Lee [3] proposed an elegant solution for real-time segmentation. The trade-off is a 15% drop in accuracy compared to offline methods."
- **Novel but unvalidated**: "Wang [4] introduced a creative architecture for multi-modal fusion. Independent replication on diverse datasets would strengthen confidence in the reported results."
- **Comprehensive survey but dated**: "Chen [5] provided a thorough survey of pre-2020 methods. Since then, transformer architectures have reshaped the field, warranting an updated review."
- **Strong theory, weak experiments**: "The theoretical framework of Zhang [6] is rigorous. Empirical validation on real-world benchmarks would bridge the gap between theory and practice."

## Common Situations and Diplomatic Responses

| You want to say... | Say instead... |
|-------------------|----------------|
| "Nobody has done X" | "X has received limited attention in the literature" |
| "X's method is worse than Y's" | "Y's method outperforms X's in [specific metric] by [amount]" |
| "X's paper is incomplete" | "X's analysis could be extended to include [missing aspect]" |
| "X didn't cite Y" | "Connecting X's findings with Y's framework would enrich the discussion" |
| "X is a bad paper" | Do not say this. Critique specific methodological choices with evidence |
| "This field is stuck" | "Progress in this field has been constrained by [specific bottleneck]" |

## Self-Admitted Limitations (Gold Standard)

The strongest critique uses the authors' own words. If a paper acknowledges a limitation, cite it directly:
- "As noted by the authors themselves [5], their approach does not scale beyond 10K vertices."
- "Smith [1] acknowledged that their training data underrepresents edge cases."
- "The authors caution that their results depend on the assumption of [X]."

This is the gold standard for diplomatic critique — it's both accurate and unassailable.
