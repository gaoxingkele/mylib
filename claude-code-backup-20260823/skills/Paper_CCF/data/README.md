# Paper_CCF — machine-readable venue export (for other projects)

This folder makes the **Paper_CCF** skill callable by *code*, not just by Claude Code.
It exports the skill's venue knowledge (15 journals + 155 CS conferences) to a global,
dependency-free JSON plus a tiny reader, so any project (e.g. `paper_reviews`) can consume it.

## Files
| File | What |
|---|---|
| `venues.json` | The export: `journals[]` (rich) + `conferences[]` (routing fields). Single machine-readable source. |
| `paper_ccf.py` | Zero-dependency reader/API (stdlib only). Import it or run as CLI. |
| `build_venues.py` | Regenerates `venues.json` from the authored profiles + `../resources/conference-roster.md`. Run after editing profiles. |

Global location on this machine: `C:\Users\10175\.claude\skills\Paper_CCF\data\`
(the skill lives in the user-global `~/.claude/skills/`, so this path is stable across projects).

## Two ways any project can call it

**1) Read the JSON directly** (no code dependency):
```python
import json
V = json.load(open(r"C:\Users\10175\.claude\skills\Paper_CCF\data\venues.json", encoding="utf-8"))
energies = next(j for j in V["journals"] if j["slug"] == "mdpi-energies")
print(energies["apc"], energies["review"]["first_decision"])
```

**2) Use the reader API** (fuzzy lookup, ranking, paper_reviews mapping):
```python
import sys
sys.path.insert(0, r"C:\Users\10175\.claude\skills\Paper_CCF\data")
import paper_ccf

paper_ccf.find("IEEE Access")            # fuzzy by name / acronym / slug
paper_ccf.get("pcmp")                    # exact by slug
paper_ccf.fastest(power_cs="high", top=5)# journals ranked by review speed, power+CS fit
paper_ccf.to_paper_reviews("ieee-access")# dict shaped like config/journals/*.yaml
```

CLI:
```bash
py paper_ccf.py "IEEE Access"      # print a venue record
py paper_ccf.py --list journals    # list journal slugs
py paper_ccf.py --pr mdpi-energies # print the paper_reviews-shaped mapping
```

## Locating the data from another machine / path

The reader resolves `venues.json` in this order:
1. `$PAPER_CCF_DATA` — full path to a `venues.json`
2. `$PAPER_CCF_HOME/data/venues.json`
3. next to `paper_ccf.py` (if you copy both files together)
4. `~/.claude/skills/Paper_CCF/data/venues.json` (default global)

So other projects can either import from the global path above, **or** copy
`paper_ccf.py` + `venues.json` into their repo, **or** set `PAPER_CCF_HOME`.

## Mapping to `paper_reviews` (config/journals schema)

`to_paper_reviews(slug)` returns the fields `paper_reviews` expects at the top of a
`config/journals/<venue>.yaml` (`venue`, `full_name`, `level`, `decision_model`
[binary|tiered], `decision_threshold`, `aims_scope`, `policies`) **plus** the extras its
`VenueMatchAgent` currently lacks: `alt_venues` (re-routing map), `apc`, `free_to_publish`,
`review_speed`, `metrics`, `power_cs_fit`, `hard_gates`, `desk_reject`, `official_url`.

Note: the authored `journals/<slug>/SKILL.md` profile (see each record's `profile_path`)
remains the human-readable source of nuance; this JSON is the structured projection.
The `dimensions`/rubric that `paper_reviews` scores on stays owned by `paper_reviews`;
this export feeds venue *facts + routing*, not the review rubric.

## Freshness
All IF / quartile / APC / review-time values are **2026-07 snapshots** flagged `verify: true`.
Confirm on each record's `official_url` before quoting. Regenerate with `py build_venues.py`
after editing the authored profiles.
