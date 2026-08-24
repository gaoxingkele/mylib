# Source Fidelity and Code Evidence

Read this reference when the input includes papers, source code, architecture documents, figures, or benchmark results.

## Source-Fidelity Gate

Patent-style abstraction is allowed; technical invention is not. Every proposed claim feature must map to a source fact or be marked `needs-confirmation`.

Use a transformation ledger:

| Evidence ID | Source path/location | Source fact | Patent abstraction | Status | Risk |
|---|---|---|---|---|---|
| E-001 | file/page/line | exact technical teaching | broader mechanism wording | confirmed/inferred/needs-confirmation | overbreadth or gap |

For papers:

- do not add hardware, deployment environments, datasets, parameters, scenarios, or effects absent from the paper;
- distinguish measured results from predicted or generic effects;
- use paper figures, captions, and nearby method text before inventing a drawing layout;
- if the source is silent, use `【待补充：...】` in an internal draft or record a material gap; do not silently complete it.

## Code-to-Patent Evidence Ladder

For code inputs, preserve both abstraction and enablement:

1. Concrete implementation: file, symbol, line, commit, configuration, and test.
2. Core mechanism: what remains if libraries, frameworks, storage engines, and protocol names are replaced by generic equivalents.
3. Technical problem: the measurable system limitation addressed by the mechanism.
4. Technical effect: benchmark, invariant, failure reduction, latency, resource use, or control result supported by evidence.
5. Claim anchor: the minimum ordered steps or component relationships that preserve the mechanism.
6. Fallback: narrower implementation features for dependent claims.

Prioritize custom algorithms, schedulers, graph logic, concurrency control, data structures, cross-module feedback loops, failure recovery, and non-standard integration. Deprioritize configuration, CRUD, wrappers, standard library use, generated code, and vendor code.

For every candidate patent point, retain:

- `abstract_mechanism` without library names;
- `concrete_reference` with clickable source locations;
- relevant commit or design-decision evidence;
- benchmark or test evidence, if any;
- known design-around and whether the product still retains its value.

Do not treat an engineering distinctiveness score as a legal patentability conclusion. Use it only to prioritize search and attorney-review effort.

## Leakage and Staleness Checks

- Do not evaluate a conversion only by phrase overlap: a patent draft must transform rather than copy the source.
- Do not use a source summary that merely restates the target claims as evidence of drafting quality.
- Record the source revision or commit. If the paper, code, or claim set changes after review, mark downstream analysis stale and rerun the affected gate.
