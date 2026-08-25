# Citation Placement Rules — Mandatory

> Loaded with skill at startup. **Every citation in the body text must pass these checks. The agent must check each one individually — no batch-skipping, no "looks fine overall".**

## Rule 1: Two Valid Positions Only

A citation `[N]` may ONLY appear in two positions:

1. **Sentence-end as evidence**: the citation sits after a complete claim, before the period.
   - Correct: `"...reduced errors by 23% [5]."`
   - Correct: `"...demonstrated significant improvements [6,7]."`

2. **Natural pause (mid-sentence anchor)**: the citation is anchored to a specific noun phrase, not floating between commas.
   - Correct: `"...as demonstrated in prior studies [5,6], the trend holds across domains."`
   - Here `[5,6]` refers to "prior studies" — it has a grammatical anchor.

## Rule 2: Forbidden Patterns (Instant Fail)

These patterns must never appear. The script's position checker flags them, but the agent must also manually scan.

| Pattern | Example | Why |
|---------|---------|-----|
| **Comma sandwich** | `"...recent work, [5], has shown..."` | `[5]` floats between two commas with no anchor |
| **Author-attached** | `"Smith [5] proposed..."` | Citation is glued to author name — rewrite to sentence-end |
| **Bare dangling** | `"...is important [5]."` | No evidence clause before the citation — what exactly did [5] show? |
| **Citation-as-sentence** | `"[5]."` (a citation standing alone as a full sentence) | Never. A citation is evidence for a claim, not a claim itself |
| **Stacked >3** | `"...improved results [4,5,6,7]."` | Four citations stacked. Split claims or reduce to most relevant 3 |

## Rule 3: One Claim, One Citation Group

A claim gets its own citation. Don't pile unrelated work into one bracket at the end of a paragraph.

Bad:
```
Segmentation is important. GNNs handle meshes well. Transformers process point clouds. Recent methods combine both [1-4].
```

Good:
```
Segmentation is critical for 3D understanding [1,2]. GNNs capture mesh topology via edge convolutions [3]. Transformers model long-range dependencies in point clouds but require large training sets [4].
```

## Rule 4: Stacking Limit

- Default max: 3 citations per bracket
- Absolute max: 5
- Over 3 → agent MUST ask user before accepting

## Rule 5: No Anonymous Citations

A reader should understand WHAT each cited paper contributed without looking at the reference list.

Bad: "Several approaches have been proposed [8-11]."
Good: "Smith [8] reduced latency by 40%, Jones [9] improved accuracy on noisy inputs, Lee [10] extended the method to multi-GPU, and Wang [11] provided a comprehensive benchmark."

## Enforcing These Rules

The agent's workflow:

1. Run `cite_table.py` — the script flags `⚠️sandwich` and `⚠️author` patterns
2. For each citation in the table, read its context aloud
3. If it sounds wrong → it is wrong → rewrite the sentence
4. Re-run the table after edits → verify all `⚠️` are gone
5. Report in conversation: "N citations checked, M placement issues fixed"

This is NOT a guideline. It is the core purpose of this skill — preventing LLMs from writing lazy citations.
