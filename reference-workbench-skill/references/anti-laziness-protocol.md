# Anti-Laziness Protocol — Mandatory Verification Gate

> Loaded with skill at startup. **The agent MUST pass this gate before declaring any task complete. No exceptions.**

## The Problem

LLMs optimize for "looking done", not "being correct". They will:
- Skip individual checks and report "all good" after checking only the first two
- Fabricate verification results ("✅ all 10 citations verified")
- Batch-report: "citations 1-10 all look fine" without checking each one
- Say "the rest look similar" after checking one or two

This is academic fraud if the citations are wrong.

## The Protocol: Itemized Verification Only

Every verification report MUST follow this format. No other format is accepted.

```
Check [N]: <specific item checked> → <finding>
```

**Valid examples:**
- `Check [1]: citation [3] in paragraph 2, sentence-end placement → ✅ correct`
- `Check [2]: citation [7] in paragraph 4, comma-sandwich detected → ⚠️ rewrote sentence`
- `Check [3]: citation count 12 in-text vs 12 in reference list → ✅ match`

**INVALID (reject immediately):**
- `"All citations look good"` — BATCHED. Reject.
- `"Citations 1-10: verified"` — BATCHED. Reject.
- `"I checked everything and it's fine"` — BATCHED. Reject.
- `"The rest are similar to the first two"` — LAZY SKIP. Reject.
- `"No issues found"` without listing each check — INCOMPLETE. Reject.

## The 5-Step Gate

Before the agent may output the final table, it must report these 5 steps explicitly.

### Step 1: Citation Count Match
Count unique in-text citations vs reference entries. Report number.
Output: `Step 1: N in-text citations, M reference entries → match/mismatch`

### Step 2: Placement Check (every citation)
For EACH citation number in order, read its context in the draft. Report position.
Output: `[1] sentence-end ✅ | [2] natural pause ✅ | [3] ⚠️ comma sandwich → fixed | [4] sentence-end ✅ | ...`

### Step 3: Stacking Check
Scan every bracket group. Flag any with >3.
Output: `Step 3: max per bracket = N. No violations / ⚠️ [5,6,7,8] has 4 citations`

### Step 4: Tone Scan
Scan for forbidden phrases. Load `references/diplomatic-critique.md` for full list.
Output: `Step 4: scanned for forbidden phrases. N found / none found.`

### Step 5: Depth Check
Scan for bare/anonymous citations. Flag any citation that appears as just `[N]` without a specific claim before it.
Output: `Step 5: N bare citations found (max 3 allowed). ⚠️ or ✅`

## Execution Rules

1. **Never skip a step.** All 5 must be reported.
2. **Never batch.** Each citation in Step 2 gets its own `[N] status` entry.
3. **Never fabricate.** If uncertain, say "⚠️ uncertain, manual review needed".
4. **Report before table, not after.** The gate output comes first, then the table.

## Why This Works

Research shows:
- Agents that must itemize their checks are far less likely to skip them (Chain of Verification, 2023)
- Pre-completion checklists improve task scores by ~14% with no model change (LangChain benchmarks)
- "Checklists are better than reward models for aligning language models" (Viswanathan et al., 2025)

This is not a suggestion. It is the structural countermeasure to LLM laziness.
