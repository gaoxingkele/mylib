# Review roles

Run these roles sequentially in one-agent environments. In a platform that supports
delegation, they may be assigned independently, but the final integrity reviewer must
receive all findings and the protected-content inventory.

## Provenance reviewer

- Map concrete claims to notes, data, citations, logs, code, interviews, or inventor
  confirmations.
- Separate direct source statements from editor inference.
- Treat polished specificity without a source as a P0 issue.

Output: evidence ledger and missing-confirmation list.

## Logic reviewer

- Reduce each section to propositions and links: cause, contrast, condition,
  consequence, exception.
- Find conclusions unsupported by premises and sections that promise one question but
  answer another.
- For patents, require a problem-mechanism-effect-support chain.

Output: flow breaks, unsupported inferences, and the smallest repair.

## Genre reviewer

- Apply the appropriate domain profile.
- Distinguish legitimate conventions from generic LLM habits: passive Methods prose,
  patent antecedent repetition, and calibrated hedging may be required.
- Reject one-size-fits-all rules such as banning every long sentence or every triad.

Output: convention violations and false-positive exemptions.

## Voice reviewer

- Use two or more genuine author samples when available.
- Record stable tendencies: sentence-length distribution, paragraph openings,
  connective use, abstraction level, hedge strength, preferred terminology, and first
  person.
- Match tendencies without copying memorable phrases or deliberately adding mistakes.

Output: short voice profile and deviations that affect readability or authenticity.

## Integrity reviewer

- Compare protected tokens and meaning before and after.
- Verify every added detail against the evidence ledger.
- Identify disclosure, quotation, privacy, metadata, copyright, and added-matter risks.
- Reject a revision if it is smoother but less accurate.

Output: pass or fail gate, remaining risks, and items requiring author confirmation.
