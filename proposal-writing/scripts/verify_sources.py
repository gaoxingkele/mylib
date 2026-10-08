"""Verify the complete pinned upstream skill snapshots without network access."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def verify() -> tuple[list[str], int]:
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / "upstream/sources.json").read_text(encoding="utf-8"))
    errors: list[str] = []
    count = 0
    evidence_index = {item["path"]: item for item in manifest["evidence_files"]}
    for skill in manifest["skills"]:
        directory = root / skill["local_path"]
        expected = {item["path"] for item in skill["files"]}
        adapters = {item["path"]: item for item in skill.get("local_adapter_files", [])}
        allowed = expected | set(adapters)
        actual = {
            path.relative_to(directory).as_posix()
            for path in directory.rglob("*")
            if path.is_file()
        }
        for missing in sorted(expected - actual):
            errors.append(f"missing upstream file: {skill['name']}/{missing}")
        for extra in sorted(actual - allowed):
            errors.append(f"unexpected upstream file: {skill['name']}/{extra}")
        for item in skill["files"]:
            if item["path"] not in actual:
                continue
            data = (directory / item["path"]).read_bytes()
            blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
            if blob != item["git_blob_sha"]:
                errors.append(f"upstream blob mismatch: {skill['name']}/{item['path']}")
            if hashlib.sha256(data).hexdigest() != item["sha256"]:
                errors.append(f"SHA-256 mismatch: {skill['name']}/{item['path']}")
            count += 1
        for path, item in sorted(adapters.items()):
            if path not in actual:
                errors.append(f"missing local adapter file: {skill['name']}/{path}")
                continue
            data = (directory / path).read_bytes()
            if hashlib.sha256(data).hexdigest() != item["sha256"]:
                errors.append(f"local adapter SHA-256 mismatch: {skill['name']}/{path}")
        license_evidence = skill.get("license_evidence")
        if license_evidence and license_evidence not in evidence_index:
            errors.append(f"license evidence not listed: {skill['name']}/{license_evidence}")
    for item in manifest["evidence_files"]:
        path = root / item["path"]
        if not path.is_file():
            errors.append(f"missing source evidence: {item['path']}")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            errors.append(f"changed source evidence: {item['path']}")
    return errors, count


if __name__ == "__main__":
    issues, checked = verify()
    print(f"{'FAIL' if issues else 'PASS'}: {checked} upstream files checked")
    for issue in issues:
        print(f"ERROR: {issue}")
    raise SystemExit(bool(issues))
