"""Hard Gate：plan 全文 SHA-256 digest + approval 校验（小写 hex 精确比对）。"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover - 视环境而定
    yaml = None


def plan_digest(plan_path: str | Path) -> str:
    """plan 文件全文的 SHA-256 小写 hexdigest。"""
    return hashlib.sha256(Path(plan_path).read_bytes()).hexdigest()


def _unquote(v: str) -> str:
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in ("'", '"'):
        return v[1:-1]
    return v


def _parse_frontmatter_simple(text: str) -> dict:
    """无 PyYAML 时的简易解析：只解析顶层 `stages` 列表（id/title/objective/acceptance）。"""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    fm: list[str] = []
    for line in lines[1:]:
        if line.strip() in ("---", "..."):
            break
        fm.append(line)

    stages: list[dict] = []
    cur: dict | None = None
    in_acceptance = False
    acceptance_indent = -1
    for raw in fm:
        if not raw.strip():
            continue
        indent = len(raw) - len(raw.lstrip())
        s = raw.strip()
        if indent == 0:
            in_acceptance = False
            continue  # 只支持 stages: 顶层键
        if s.startswith("- "):
            if in_acceptance and indent > acceptance_indent and cur is not None:
                cur.setdefault("acceptance", []).append(_unquote(s[2:]))
            else:
                cur = {}
                stages.append(cur)
                in_acceptance = False
                rest = s[2:].strip()
                if rest and ":" in rest:
                    k, _, v = rest.partition(":")
                    cur[k.strip()] = _unquote(v)
        elif ":" in s and cur is not None:
            k, _, v = s.partition(":")
            k, v = k.strip(), v.strip()
            if v == "" and k == "acceptance":
                cur["acceptance"] = []
                in_acceptance = True
                acceptance_indent = indent
            else:
                cur[k] = _unquote(v)
                in_acceptance = False
    return {"stages": stages}


def split_frontmatter(text: str) -> tuple[str, str]:
    """返回 (frontmatter_text, body)。"""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return "", text
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() in ("---", "..."):
            return "\n".join(lines[1:i]), "\n".join(lines[i + 1:])
    return "", text


def parse_plan(plan_path: str | Path) -> list[dict]:
    """解析 plan 的 YAML frontmatter，返回 stages 列表；无 stages 或解析失败抛 ValueError。"""
    text = Path(plan_path).read_text(encoding="utf-8")
    if yaml is not None:
        fm, _ = split_frontmatter(text)
        data = yaml.safe_load(fm) if fm.strip() else {}
    else:
        data = _parse_frontmatter_simple(text)
    stages = (data or {}).get("stages")
    if not stages or not isinstance(stages, list):
        raise ValueError(f"plan 缺少 stages 列表: {plan_path}")
    norm = []
    for st in stages:
        if not isinstance(st, dict) or not st.get("id") or not st.get("objective"):
            raise ValueError(f"stage 缺少 id/objective: {st!r}")
        acc = st.get("acceptance") or []
        if isinstance(acc, str):
            acc = [acc]
        norm.append(
            {
                "id": str(st["id"]),
                "title": str(st.get("title") or st["id"]),
                "objective": str(st["objective"]),
                "acceptance": [str(a) for a in acc],
            }
        )
    return norm


class GateError(Exception):
    """Hard Gate 校验失败。"""


def verify_approval(plan_path: str | Path, approval_path: str | Path) -> dict:
    """校验 approval 文件。通过则返回 approval dict，否则抛 GateError。"""
    plan_path, approval_path = Path(plan_path), Path(approval_path)
    if not approval_path.exists():
        raise GateError(f"缺少 approval 文件: {approval_path}（run 前必须先 approve）")
    try:
        approval = json.loads(approval_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise GateError(f"approval 文件不是合法 JSON: {e}")
    if not approval.get("approved_by_human"):
        raise GateError("approval 缺少非空 approved_by_human 字段")
    if not approval.get("approval_date"):
        raise GateError("approval 缺少 approval_date 字段")
    actual = plan_digest(plan_path)
    expected = approval.get("plan_sha256", "")
    if expected != actual:
        raise GateError(
            "plan digest 不匹配（plan 在批准后被修改？）：\n"
            f"  approval 记录: {expected}\n  当前 plan 实际: {actual}\n"
            "  计划变更需要生成新 plan 版本并重新批准。"
        )
    return approval
