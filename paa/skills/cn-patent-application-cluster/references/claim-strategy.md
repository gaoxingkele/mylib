# Claim Strategy

## Independent Claim Test

An independent claim should contain:
- technical field context;
- concrete input or object;
- ordered core steps or structural modules;
- the differentiating mechanism;
- output or technical action;
- enough constraints to avoid pure result claiming.

Avoid independent claims that only say:
- use an AI model;
- optimize, classify, predict, or generate;
- improve accuracy or efficiency;
- apply a known algorithm to a known domain.

## Independent Claim Minimization

- The independent claim should recite only the essential technical features indispensable for solving the technical problem. Every extra feature is both a grant obstacle (one more surface the examiner can hit with prior art) and an infringement loophole (all-elements rule, Art. 59).
- Use-environment features do not belong in the independent claim ((2012) 民提字第1号, the Shimano/岛野 case). If such a feature must appear, place it in a dependent claim or draft dual independent claims.
- Each independent claim should differ from the closest prior art by exactly one distinguishing feature.

## Dependent Claim Ladder

Build fallback positions:

1. data acquisition / preprocessing;
2. core computation or structural relationship;
3. threshold, formula, constraint, or decision rule;
4. exception handling and safety gate;
5. output action and interface;
6. system/device/computer-readable medium;
7. numerical embodiment or parameter range.

## Star Topology and Fallback Tiers

- Attach dependent claims directly to the independent claim in a star ("circle") layout rather than a chain; chain-style accumulation compounds dependencies and collapses faster under attack.
- Reserve a "second generalization" (二次概括) intermediate tier for later narrowing amendments, so a fallback does not have to retreat straight to the fine details.

## Software and AI Inventions

For China-facing drafting, anchor software/AI claims to technical application:
- power dispatch, equipment diagnosis, industrial control, communication, storage, sensing, manufacturing, safety verification, or maintenance;
- specific technical data and interfaces;
- hardware or system modules;
- technical effect measurable in the domain.

## Review Questions

- What would the examiner cite as the closest prior art?
- What feature survives after replacing model names with generic equivalents?
- Does the specification teach how to reproduce the feature?
- Can a narrower dependent claim preserve value if the independent claim is attacked?

## Evidence and Formal Gates

For paper or code inputs, read `source-fidelity-and-code-evidence.md` before deciding the independent-claim abstraction level. Preserve a concrete enablement reference even when the claim uses a broader mechanism description.

After drafting or materially revising claims, read `claim-formal-validation.md` and run the deterministic claim checker. Mechanical validity is a prerequisite, not a substitute for support, clarity, unity, novelty, or inventiveness review.

## Functional Features

- Prefer embodiments self-evident within the claim itself (杨明: a feature whose implementation can be determined by reading the claim alone is not treated as a functional feature).
- Functional limitations must be supported by layered specification disclosure — describe the "indispensable" (不可缺少) features as a separate layer.
- Never claim pure function without structural support (度彼 ZL201010137843.8, invalidated; Invalidation Decision No. 37737).
- The scope of a functional feature is construed down to the features in the specification that are indispensable for implementing the function (SPC Interpretation II, Art. 8).
