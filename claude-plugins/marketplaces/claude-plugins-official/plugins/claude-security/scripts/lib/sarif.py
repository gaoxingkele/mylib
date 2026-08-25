"""SARIF 2.1.0 for one scan: the log encoder."""

from __future__ import annotations

import hashlib
import json
import posixpath
import re
from bisect import bisect_right
from dataclasses import dataclass
from itertools import accumulate
from typing import TYPE_CHECKING, NamedTuple
from urllib.parse import quote

from . import cwe, secret

if TYPE_CHECKING:
    import uuid
    from collections.abc import Mapping, Sequence

    from .finding import Finding, Panel

SCHEMA_ID = (
    "https://docs.oasis-open.org/sarif/sarif/v2.1.0/errata01/os/schemas/sarif-schema-2.1.0.json"
)
# The driver name GitHub keys alert identity on; renaming it orphans every open alert.
TOOL_NAME = "Claude Security Plugin for Claude Code"
TOOL_URI = "https://claude.com/product/claude-security"
PROPERTY_BAG = "claudeSecurityPlugin"
ID_PREFIX = "claude-security-plugin"
FINGERPRINT_KEY = ID_PREFIX + "/v2"
CONTEXT_LINES = 3
SRCROOT = "%SRCROOT%"
# error is SARIF's highest level, so CRITICAL and HIGH both map to it.
LEVEL = {"CRITICAL": "error", "HIGH": "error", "MEDIUM": "warning", "LOW": "note"}


@dataclass(frozen=True)
class Scan:
    """The one scan a log describes: its identity, where it ran, and the repository it names."""

    id: uuid.UUID
    mode: str
    # The scan root below the repository top level, slash-terminated; "" when there is none.
    prefix: str
    # The credential-free https form of the repository's remote; None when there is not one.
    remote: str | None
    # The directories the scan was limited to, relative to the scan root; empty for all of it.
    scope: tuple[str, ...]
    # The commit the scanned tree was exactly at; None when it was dirty, unversioned or unknown.
    revision: str | None


def log(
    findings: Sequence[Finding],
    scan: Scan,
    tool_version: str | None,
    run_properties: Mapping[str, object],
    panels: Mapping[str, Panel],
    sources: Mapping[str, str],
    notifications: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """The SARIF 2.1.0 log for one scan: one run, one rule per category, one result per finding.

    `sources` is the text of each scanned file a finding names, keyed by the
    finding's `file`; a finding whose file is absent from it is fingerprinted
    on its own quote of the code instead.
    """
    filed = [(item, category_of(item)) for item in findings]
    categories = list(dict.fromkeys(category for _, category in filed))
    index = {category: position for position, category in enumerate(categories)}
    driver: dict[str, object] = {
        "name": TOOL_NAME,
        "organization": "Anthropic",
        "informationUri": TOOL_URI,
        **({"version": tool_version} if tool_version else {}),
        "rules": [rule(category) for category in categories],
    }
    invocation: dict[str, object] = {"executionSuccessful": True}
    if notifications:
        invocation["toolExecutionNotifications"] = list(notifications)
    base_description = (
        "The top level of the scanned repository, or the scanned directory when the scan did "
        "not run inside a git checkout."
    )
    run: dict[str, object] = {
        "tool": {"driver": driver},
        "automationDetails": {"id": automation_id(scan), "guid": str(scan.id)},
        "invocations": [invocation],
        "originalUriBaseIds": {SRCROOT: {"description": {"text": base_description}}},
        "results": [
            result(
                item,
                category,
                index[category],
                scan,
                panels.get(item["id"]),
                sources.get(item["file"]),
            )
            for item, category in filed
        ],
        "properties": {
            PROPERTY_BAG: {
                **run_properties,
                "target_kind": "git-remote" if scan.remote else "local-path",
            }
        },
    }
    if scan.remote:
        provenance: dict[str, object] = {"repositoryUri": scan.remote}
        if scan.revision:
            provenance["revisionId"] = scan.revision
        run["versionControlProvenance"] = [provenance]
    return {"$schema": SCHEMA_ID, "version": "2.1.0", "runs": [run]}


def automation_id(scan: Scan) -> str:
    """The run's automation id: the plugin prefix, the mode, the scan's extent if any, its id."""
    category = f"{ID_PREFIX}/{scan.mode}"
    if scan.scope:
        extent = ",".join(scan.prefix + entry.strip("/") for entry in sorted(scan.scope))
    else:
        extent = scan.prefix.rstrip("/")
    if extent:
        category += "/" + quote(uri_bytes(extent))
    return f"{category}/{scan.id}"


def category_of(finding: Finding) -> cwe.Category | None:
    """The Simplified Mapping entry the finding's CWE rolls up to; None for Uncategorized."""
    return cwe.catalog.category(cwe.id_number(finding["cwe_id"]))


def rule_id(category: cwe.Category | None) -> str:
    """A rule's id: its entry's CWE id (`CWE-89`), or `uncategorized`."""
    return category.id if category is not None else cwe.UNCATEGORIZED.lower()


def rule(category: cwe.Category | None) -> dict[str, object]:
    """The reporting descriptor for one entry: the catalog's names, its page, its fixed tags."""
    help_text = (
        "Each alert's message names the finding's own CWE and states the impact, exploit "
        "scenario, preconditions and recommended fix; the finding appears under its F<n> id "
        "in CLAUDE-SECURITY-RESULTS.md."
    )
    if category is None:
        return {
            "id": rule_id(None),
            "name": cwe.UNCATEGORIZED,
            "shortDescription": {"text": cwe.UNCATEGORIZED},
            "fullDescription": {
                "text": "Findings whose CWE is not an entry of the CWE Simplified Mapping view "
                f"and rolls up to none, reported by {TOOL_NAME} from static review of the "
                "source."
            },
            "help": {"text": help_text},
            "properties": {"tags": ["security"]},
        }
    return {
        "id": category.id,
        "name": rule_name(category.name),
        "shortDescription": {"text": category.name},
        "fullDescription": {
            "text": f"{category.title} ({category.id}, CWE {cwe.catalog.version}): findings whose "
            f"CWE is this entry of the Simplified Mapping view or rolls up to it, reported by "
            f"{TOOL_NAME} from static review of the source."
        },
        "help": {"text": help_text},
        "helpUri": f"https://cwe.mitre.org/data/definitions/{category.number}.html",
        "properties": {"tags": ["security", f"external/cwe/cwe-{category.number}"]},
    }


def fingerprint(
    finding: Finding, category: cwe.Category | None, scan: Scan, source: str | None
) -> str:
    """The finding's partial fingerprint: a sha256 over its rule, its path and the code it names.

    `source` is the text of the finding's file. The code is the file's own
    lines around the one that places the finding (see code_at); when the file
    was not read, or no line of it places the finding, the finding's symbol
    and snippet stand in for them, and the line when it has neither. A
    hard-coded credential finding is the exception: its symbol and the number
    of the line that places it stand in for the code always, so no text of a
    file that holds a credential enters the hash.
    """
    parts = [scan.remote or "", rule_id(category), repository_path(scan, finding)]
    symbol = finding["symbol"].strip()
    snippet = quoted_line(finding)
    if secret.is_credential(finding):
        lines = None if source is None else normalized_lines(source)
        placed = None if lines is None else placing_row(lines, finding["line"], snippet)
        parts += [symbol, str(finding["line"] if placed is None else placed + 1)]
        return hashlib.sha256(json.dumps(parts).encode()).hexdigest()
    code = None if source is None else code_at(source, finding["line"], snippet)
    if code is not None:
        parts.append(code)
    else:
        parts += [symbol, snippet]
        if not symbol and not snippet:
            parts.append(str(finding["line"]))
    return hashlib.sha256(json.dumps(parts).encode()).hexdigest()


class Site(NamedTuple):
    """What one result stands for: a rule at a line of a file; the log holds one result per site."""

    rule: str
    path: str
    line: int


def site(finding: Finding, scan: Scan, source: str | None) -> Site | None:
    """The finding's site: its rule id, its repository path, and the line that places it.

    The line is the one of `source`, the finding's file, that places the
    finding (placing_row), so two findings that quote one line of code are one
    site whatever lines they declare; it is the declared line when the file
    was not read or no line of it places the finding. A finding left with no
    line (it declared none, line < 1, and none places it) has no site: None.
    """
    line = finding["line"]
    if source is not None:
        row = placing_row(normalized_lines(source), line, quoted_line(finding))
        if row is not None:
            line = row + 1
    if line < 1:
        return None
    return Site(rule_id(category_of(finding)), repository_path(scan, finding), line)


def quoted_line(finding: Finding) -> str:
    """The finding's snippet with its whitespace normalized, the form placing_row looks for."""
    return " ".join(finding["snippet"].split())


def normalized_lines(source: str) -> list[str]:
    """A file's lines, split on the newline alone, each with its whitespace normalized."""
    return [" ".join(each.split()) for each in source.split("\n")]


def placing_row(lines: Sequence[str], line: int, quoted: str) -> int | None:
    """The index into the normalized `lines` of the one placing a finding; None when none does.

    The finding is placed on the line nearest its declared `line` where
    `quoted`, its normalized snippet, appears, whitespace aside, and on the
    declared line itself when it appears nowhere.
    """
    declared = line - 1
    at = min(
        (min(max(declared, first), last) for first, last in occurrences(lines, quoted)),
        key=lambda row: abs(row - declared),
        default=declared,
    )
    return at if 0 <= at < len(lines) else None


def code_at(source: str, line: int, quoted: str) -> str | None:
    """The normalized lines of `source` around the one placing a finding; None when none does."""
    lines = normalized_lines(source)
    at = placing_row(lines, line, quoted)
    if at is None:
        return None
    return "\n".join(lines[max(at - CONTEXT_LINES, 0) : at + CONTEXT_LINES + 1])


def occurrences(lines: Sequence[str], quoted: str) -> list[tuple[int, int]]:
    """The (first, last) index into the normalized `lines` of each occurrence of `quoted`."""
    if not quoted:
        return []
    filled = [row for row, line in enumerate(lines) if line]
    starts = list(accumulate((len(lines[row]) + 1 for row in filled), initial=0))
    flat = " ".join(lines[row] for row in filled)

    def row_at(offset: int) -> int:
        return filled[bisect_right(starts, offset) - 1]

    return [
        (row_at(found.start()), row_at(found.end() - 1))
        for found in re.finditer(re.escape(quoted), flat)
    ]


def result(
    finding: Finding,
    category: cwe.Category | None,
    rule_index: int,
    scan: Scan,
    panel: Panel | None,
    source: str | None,
) -> dict[str, object]:
    """One result: the finding under its rule, its partial fingerprint, and its JSONL record."""
    shown = secret.withheld(finding)
    record: dict[str, object] = {**shown}
    if panel is not None:
        record["verification"] = {"panel": panel}
    return {
        "ruleId": rule_id(category),
        "ruleIndex": rule_index,
        "level": LEVEL[finding["severity"]],
        "message": {"text": message(finding)},
        "locations": [location(shown, scan)],
        "partialFingerprints": {FINGERPRINT_KEY: fingerprint(finding, category, scan, source)},
        "properties": {PROPERTY_BAG: record},
    }


def location(finding: Finding, scan: Scan) -> dict[str, object]:
    """A result's one location: the file relative to SRCROOT, the line, the snippet, the symbol."""
    line = finding["line"]
    region: dict[str, object] = {"startLine": max(line, 1)}
    if line >= 1 and finding["snippet"].strip():
        region["snippet"] = {"text": finding["snippet"]}
    place: dict[str, object] = {
        "physicalLocation": {
            "artifactLocation": {
                "uri": quote(uri_bytes(repository_path(scan, finding))),
                "uriBaseId": SRCROOT,
            },
            "region": region,
        }
    }
    if symbol := finding["symbol"].strip():
        place["logicalLocations"] = [{"name": symbol, "fullyQualifiedName": symbol}]
    return place


def repository_path(scan: Scan, finding: Finding) -> str:
    """The finding's file relative to the repository top level, with any leading climb folded."""
    return posixpath.normpath(scan.prefix + finding["file"])


def uri_bytes(text: str) -> bytes:
    """`text` as the bytes its uri must name; byte-faithful for a filesystem name."""
    try:
        return text.encode("utf-8", "surrogateescape")
    except UnicodeEncodeError:
        return text.encode("utf-8", "surrogatepass")


def notification(descriptor_id: str, level: str, text: str) -> dict[str, object]:
    """One invocation notification: its namespaced descriptor id, its level, and its message."""
    return {"descriptor": {"id": descriptor_id}, "level": level, "message": {"text": text}}


def message(finding: Finding) -> str:
    """A result's message: the finding's prose, its stated parts labeled, then its ratings."""
    parts = [sentence(finding["title"]), sentence(finding["description"])]
    labeled = (
        ("Impact", finding["impact"]),
        ("Exploit scenario", finding["exploit_scenario"]),
        ("Preconditions", "; ".join(finding["preconditions"])),
        ("Recommendation", finding["recommendation"]),
    )
    parts += [f"{label}: {text}" for label, value in labeled if (text := sentence(value))]
    if finding["line"] < 1:
        parts.append("The exact line was not determined; see the description.")
    if secret.is_credential(finding):
        parts.append("The source line is not quoted because it holds the credential.")
    parts.append(
        f"{finding['cwe_id']}. Severity {finding['severity']}, confidence {finding['confidence']}."
    )
    return "\n\n".join(parts)


def rule_name(category: str) -> str:
    """A category's common name in PascalCase, for a rule name: `SQLInjection`."""
    return "".join(word[:1].upper() + word[1:] for word in re.split(r"[^A-Za-z0-9]+", category))


def sentence(text: str) -> str:
    """`text` stripped and closed with a period unless it already ends in punctuation."""
    text = text.strip()
    return text if not text or text[-1] in ".!?" else text + "."
