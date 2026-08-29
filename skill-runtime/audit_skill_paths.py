#!/usr/bin/env python3
"""Audit the curated Codex skill runtime without recursively loading vendor catalogs."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

import yaml


FRONTMATTER_RE = re.compile(r"^---\r?\n(.*?)\r?\n---", re.DOTALL)
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
ABSOLUTE_MYLIB_RE = re.compile(r"D:/aicoding/mylib/[^\s`'\"\])]+")
DEPRECATED_LIB_ROOT_RE = re.compile(
    r"D:[/\\]aicoding[/\\]Lib(?:[/\\]|\b)", re.IGNORECASE
)
FORBIDDEN_PATHS = ("/Users/lingzhi", "~/.claude/skills")


def load_frontmatter(skill_file: Path) -> tuple[dict, str]:
    text = skill_file.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError("missing or malformed YAML frontmatter")
    data = yaml.safe_load(match.group(1))
    if not isinstance(data, dict):
        raise ValueError("frontmatter is not a mapping")
    return data, text


def resolve_source(manifest_dir: Path, raw: str) -> Path:
    path = Path(raw)
    if not path.is_absolute():
        path = manifest_dir / path
    return path.resolve()


def check_relative_links(skill_file: Path, text: str) -> list[str]:
    errors: list[str] = []
    for raw in MARKDOWN_LINK_RE.findall(text):
        target = raw.strip().split("#", 1)[0]
        if not target or target.startswith(("http://", "https://", "mailto:", "#", "skill://")):
            continue
        if any(char in target for char in ("<", ">", "*")) or " " in target:
            continue
        if not target.startswith((".", "references/", "scripts/", "resources/", "docs/", "prompts/", "tools/", "data/", "skills/", "journals/")):
            continue
        resolved = (skill_file.parent / target).resolve()
        if not resolved.exists():
            errors.append(f"broken relative link: {skill_file} -> {raw}")
    return errors


def check_stale_paths(skill_file: Path, text: str) -> list[str]:
    errors: list[str] = []
    if DEPRECATED_LIB_ROOT_RE.search(text):
        errors.append(f"deprecated Lib-root reference: {skill_file}")
    for token in FORBIDDEN_PATHS:
        if token in text:
            errors.append(f"stale path token {token!r}: {skill_file}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path(__file__).with_name("manifest.json"),
    )
    parser.add_argument(
        "--install-root",
        type=Path,
        default=Path.home() / ".codex" / "skills",
    )
    parser.add_argument("--source-only", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    manifest_file = args.manifest.resolve()
    manifest_dir = manifest_file.parent
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    repo_root = manifest_dir.parent.resolve()
    errors: list[str] = []
    warnings: list[str] = []
    names: list[str] = []
    descriptions = 0
    discovered = 0
    routed_modules = 0

    for entry in manifest["skills"]:
        name = entry["name"]
        names.append(name)
        source = resolve_source(manifest_dir, entry["source"])
        try:
            source.relative_to(repo_root)
        except ValueError:
            errors.append(f"source escapes mylib: {name} -> {source}")
            continue
        skill_file = source / "SKILL.md"
        if not skill_file.is_file():
            errors.append(f"missing SKILL.md: {name} -> {skill_file}")
            continue
        try:
            frontmatter, text = load_frontmatter(skill_file)
        except (OSError, UnicodeError, ValueError, yaml.YAMLError) as exc:
            errors.append(f"invalid frontmatter: {skill_file}: {exc}")
            continue
        if frontmatter.get("name") != name:
            errors.append(
                f"name mismatch: manifest={name!r}, frontmatter={frontmatter.get('name')!r}, file={skill_file}"
            )
        description = frontmatter.get("description")
        if not isinstance(description, str) or not description.strip():
            errors.append(f"missing description: {skill_file}")
        else:
            descriptions += len(description.strip())
        nested = sum(1 for _ in source.rglob("SKILL.md"))
        discovered += nested
        if nested != 1:
            errors.append(f"runtime source recursively exposes {nested} skills: {name} -> {source}")
        errors.extend(check_stale_paths(skill_file, text))
        errors.extend(check_relative_links(skill_file, text))
        for raw_path in ABSOLUTE_MYLIB_RE.findall(text):
            if any(char in raw_path for char in ("<", ">", "*", "{")):
                continue
            if not Path(raw_path).exists():
                warnings.append(f"unresolved absolute reference: {skill_file} -> {raw_path}")

        if not args.source_only:
            installed = args.install_root / name
            if not installed.exists():
                errors.append(f"missing installed skill: {installed}")
            elif installed.resolve() != source:
                errors.append(f"wrong installed target: {installed} -> {installed.resolve()} (expected {source})")

    duplicates = [name for name, count in Counter(names).items() if count > 1]
    if duplicates:
        errors.append("duplicate manifest names: " + ", ".join(sorted(duplicates)))
    if discovered > int(manifest["max_discovered_skills"]):
        errors.append(
            f"discovered skill count {discovered} exceeds {manifest['max_discovered_skills']}"
        )
    if descriptions > int(manifest["description_budget_chars"]):
        errors.append(
            f"description characters {descriptions} exceed {manifest['description_budget_chars']}"
        )

    for entry in manifest.get("project_only", []):
        source = resolve_source(manifest_dir, entry["source"])
        if not (source / "SKILL.md").is_file():
            errors.append(f"missing project-only skill source: {entry['name']} -> {source}")
    for entry in manifest.get("resource_only", []):
        source = resolve_source(manifest_dir, entry["source"])
        if not source.is_dir():
            errors.append(f"missing resource-only source: {entry['name']} -> {source}")
        if (source / "SKILL.md").exists():
            warnings.append(f"resource-only entry now contains SKILL.md: {entry['name']} -> {source}")

    routed_names: list[str] = []
    for raw_catalog in manifest.get("routed_catalogs", []):
        catalog = resolve_source(manifest_dir, raw_catalog)
        try:
            catalog.relative_to(repo_root)
        except ValueError:
            errors.append(f"routed catalog escapes mylib: {catalog}")
            continue
        if not catalog.is_dir():
            errors.append(f"missing routed catalog: {catalog}")
            continue
        for skill_file in catalog.rglob("SKILL.md"):
            routed_modules += 1
            try:
                frontmatter, text = load_frontmatter(skill_file)
            except (OSError, UnicodeError, ValueError, yaml.YAMLError) as exc:
                errors.append(f"invalid routed frontmatter: {skill_file}: {exc}")
                continue
            routed_name = frontmatter.get("name")
            if isinstance(routed_name, str):
                routed_names.append(routed_name)
            else:
                errors.append(f"missing routed skill name: {skill_file}")
            errors.extend(check_stale_paths(skill_file, text))
            errors.extend(check_relative_links(skill_file, text))

    routed_duplicates = [
        name for name, count in Counter(routed_names).items() if count > 1
    ]
    if routed_duplicates:
        errors.append("duplicate routed skill names: " + ", ".join(sorted(routed_duplicates)))

    report = {
        "status": "PASS" if not errors else "FAIL",
        "manifest_skills": len(names),
        "discovered_skills": discovered,
        "description_characters": descriptions,
        "routed_modules": routed_modules,
        "errors": errors,
        "warnings": warnings,
    }
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(
            f"{report['status']}: manifest={len(names)}, discovered={discovered}, "
            f"description_chars={descriptions}, routed_modules={routed_modules}, "
            f"errors={len(errors)}, warnings={len(warnings)}"
        )
        for issue in errors:
            print(f"ERROR: {issue}")
        for issue in warnings:
            print(f"WARN: {issue}")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
