# Review Gates

## Gate A: 26.3 / 26.4 Support and Disclosure

Check:
- can a person skilled in the art reproduce the claimed feature;
- every claim term appears in the specification;
- formulas have symbol definitions and boundary handling;
- embodiments support broad claim language;
- no unsupported effect is asserted;
- a per-feature anchor table exists mapping every claim term to a specification paragraph + figure reference numeral + at least one embodiment;
- numbers correspond strictly across claim range, specification, and embodiment (4W118464: mismatched ranges → lack of support; component totals must use a single accounting basis).

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
- include system/device claims with processor, memory, interface, and modules when appropriate;
- the technical problem is stated explicitly in the background section (three-dimensional path drawing case: an effect is only recognized as a technical effect when anchored to a stated technical problem);
- algorithmic features and technical features "mutually support each other functionally and interact" (Examination Guidelines, Part II, Chapter 9, Section 6);
- remove business-inducement wording (vendor/transaction-type terms trigger subject-matter rejection);
- never write "applicable to any system".

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

## Gate F: OA Response Preparedness

Check:
- is the fallback tier ladder ready if the independent claim falls (dependent claims positioned for staged narrowing);
- does every distinguishing feature have a pre-embedded second function/effect record in the specification (ammunition for the "common general knowledge" rebuttal);
- for combination inventions, is synergy comparison data pre-embedded in the specification;
- when answering an OA, follow the five-step method in `../../references/oa-response-playbook.md` (fact check → second-function mining → technical-problem reframing → three-step argument → prosecution estoppel check).
