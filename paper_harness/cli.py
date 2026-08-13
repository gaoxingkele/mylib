"""CLI：`python -m paper_harness <command>`。

九个子命令：init / plan / approve / run / status / accept / reject / review / attribute。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

from . import checks, gate, roles, transport
from .runtime import HARNESS_DIRNAME, Runtime, now_iso, today_cn, ts_compact

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SKILLS_SRC = Path(__file__).resolve().parent / "resources" / "skills"

DEFAULT_CONFIG_TEMPLATE = '''\
journal = "{journal}"
manuscript = "{manuscript}"

[checks]
# declarations = ["Funding", "Author Contributions", "Data Availability", "Conflicts of Interest", "Acknowledgments"]
# abstract_word_limit = 220
# placeholder_globs = ["supplementary/*.tex"]
# latex_engine = "pdflatex"

[transport]
command = "codex exec"
'''


# ---------- 通用工具 ----------

def load_config(paper_dir: Path) -> dict:
    cfg_path = paper_dir / HARNESS_DIRNAME / "config.toml"
    if not cfg_path.exists():
        return {}
    with cfg_path.open("rb") as f:
        data = tomllib.load(f)
    cfg: dict = {}
    cfg.update({k: v for k, v in data.items() if not isinstance(v, dict)})
    cfg.update(data.get("checks", {}))
    cfg["transport_command"] = data.get("transport", {}).get("command", "codex exec")
    return cfg


def is_git_repo(paper_dir: Path) -> bool:
    proc = subprocess.run(
        ["git", "-C", str(paper_dir), "rev-parse", "--is-inside-work-tree"],
        capture_output=True, text=True,
    )
    return proc.returncode == 0 and proc.stdout.strip() == "true"


def git_context(paper_dir: Path) -> tuple[Path, Path] | None:
    """Return (repository root, paper path relative to root), including monorepo subdirectories."""
    if not is_git_repo(paper_dir):
        return None
    top = git(paper_dir, "rev-parse", "--show-toplevel")
    prefix = git(paper_dir, "rev-parse", "--show-prefix")
    if top.returncode != 0 or prefix.returncode != 0:
        return None
    root = Path(top.stdout.strip()).resolve()
    relative = Path(prefix.stdout.strip().rstrip("/")) if prefix.stdout.strip() else Path()
    return root, relative


def git(paper_dir: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(paper_dir), *args], capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )


def sanitize_branch_part(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", s).strip("-") or "stage"


def execution_preflight(paper_dir: Path, cfg: dict) -> tuple[bool, str]:
    """Refuse a false-isolated run when the paper subtree is untracked or dirty."""
    context = git_context(paper_dir)
    if context is None:
        return False, "paper directory is not in a Git repository; isolated execution requires a tracked baseline"
    repo_root, paper_prefix = context
    required = [str(cfg.get("manuscript", "main.tex"))]
    required.extend(str(item) for item in cfg.get("required_tracked_files", []))
    missing: list[str] = []
    for rel in required:
        required_path = Path(rel)
        absolute = required_path.resolve() if required_path.is_absolute() else (paper_dir / required_path).resolve()
        try:
            repo_rel = absolute.relative_to(repo_root).as_posix()
        except ValueError:
            missing.append(rel + " (outside repository)")
            continue
        proc = git(repo_root, "ls-files", "--error-unmatch", "--", repo_rel)
        if proc.returncode != 0:
            missing.append(rel)
    if missing:
        return False, (
            "required paper files are not tracked by Git: " + ", ".join(missing)
            + ". Create and commit an explicit baseline before run; the harness will not silently omit untracked manuscripts."
        )
    scope_prefixes = allowed_scope_prefixes(paper_dir, cfg)
    pathspecs = scope_prefixes or [paper_prefix.as_posix() if str(paper_prefix) not in ("", ".") else "."]
    status = git(repo_root, "status", "--porcelain", "--", *pathspecs)
    dirty_lines: list[str] = []
    for line in status.stdout.splitlines():
        candidate = line[3:].strip().strip('"') if len(line) >= 4 else line
        if HARNESS_DIRNAME in candidate or ".codex/" in candidate or _is_build_intermediate(candidate):
            continue
        dirty_lines.append(line)
    if dirty_lines:
        return False, (
            "paper subtree has uncommitted changes; commit an explicit baseline before isolated execution:\n"
            + "\n".join(dirty_lines[:40])
        )
    return True, f"tracked, clean baseline at {repo_root} (prefix={paper_prefix.as_posix() or '.'})"


def allowed_scope_prefixes(paper_dir: Path, cfg: dict) -> list[str]:
    context = git_context(paper_dir)
    if context is None:
        return []
    repo_root, paper_prefix = context
    prefixes = [paper_prefix.as_posix().rstrip("/")]
    for configured in cfg.get("allowed_write_paths", []):
        path = Path(str(configured))
        if path.is_absolute():
            try:
                relative = path.resolve().relative_to(repo_root)
            except ValueError:
                continue
        else:
            try:
                relative = (paper_dir / path).resolve().relative_to(repo_root)
            except ValueError:
                continue
        prefixes.append(relative.as_posix().rstrip("/"))
    return [prefix for prefix in dict.fromkeys(prefixes) if prefix not in ("", ".")]


BUILD_INTERMEDIATE_SUFFIXES = {
    ".aux", ".log", ".out", ".blg", ".bcf", ".toc", ".lof", ".lot", ".fls", ".fdb_latexmk",
    ".synctex.gz", ".nav", ".snm", ".vrb", ".xdv",
}


def _is_build_intermediate(path: str) -> bool:
    lower = path.lower()
    return any(lower.endswith(suffix) for suffix in BUILD_INTERMEDIATE_SUFFIXES) or lower.endswith(".run.xml")


def commit_candidate(workdir: Path, stage_id: str, plan_version: int, config: dict) -> tuple[bool, str]:
    """Commit only paper-subtree changes after checks; reject cross-project drift."""
    context = git_context(workdir)
    if context is None:
        return False, "candidate workdir is not a Git worktree"
    repo_root, paper_prefix = context
    status = git(repo_root, "status", "--porcelain")
    if status.returncode != 0:
        return False, status.stderr.strip() or "git status failed"
    changed: list[str] = []
    outside: list[str] = []
    prefixes = allowed_scope_prefixes(workdir, config)
    prefix = paper_prefix.as_posix().rstrip("/")
    if prefix == ".":
        prefix = ""
    if not prefixes and not prefix:
        prefixes = [""]
    for line in status.stdout.splitlines():
        if len(line) < 4:
            continue
        path = line[3:].strip().strip('"')
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        in_scope = any(not allowed or path == allowed or path.startswith(allowed + "/") for allowed in prefixes)
        if not in_scope:
            outside.append(path)
        elif not _is_build_intermediate(path):
            changed.append(path)
    if outside:
        return False, "executor changed files outside the approved paper subtree: " + ", ".join(outside[:30])
    if not changed:
        if transport.is_mock():
            return True, "mock candidate contains no file changes"
        return False, "executor produced no committable paper changes"
    add = git(repo_root, "add", "--", *changed)
    if add.returncode != 0:
        return False, add.stderr.strip() or "git add failed"
    diff = git(repo_root, "diff", "--cached", "--quiet")
    if diff.returncode == 0:
        return False, "no staged candidate changes after filtering build intermediates"
    commit = git(
        repo_root,
        "-c", "user.name=paper-harness",
        "-c", "user.email=paper-harness@local",
        "commit", "-m", f"paper-harness: candidate {stage_id} (plan v{plan_version})",
    )
    if commit.returncode != 0:
        return False, commit.stderr.strip() or commit.stdout.strip() or "git commit failed"
    return True, commit.stdout.strip().splitlines()[0] if commit.stdout.strip() else "candidate committed"


# ---------- init ----------

def cmd_init(args) -> int:
    paper_dir = Path(args.paper_dir).resolve()
    paper_dir.mkdir(parents=True, exist_ok=True)
    root = paper_dir / HARNESS_DIRNAME
    for sub in ("plans", "approvals", "runs", "reviews", "attributions"):
        (root / sub).mkdir(parents=True, exist_ok=True)
    cfg_path = root / "config.toml"
    if not cfg_path.exists():
        cfg_path.write_text(
            DEFAULT_CONFIG_TEMPLATE.format(journal=args.journal, manuscript=args.manuscript),
            encoding="utf-8",
        )
    # 复制 skills 到 .codex/skills/
    skills_dst = paper_dir / ".codex" / "skills"
    for skill_dir in sorted(SKILLS_SRC.iterdir()) if SKILLS_SRC.is_dir() else []:
        if skill_dir.is_dir():
            dst = skills_dst / skill_dir.name
            dst.mkdir(parents=True, exist_ok=True)
            shutil.copy2(skill_dir / "SKILL.md", dst / "SKILL.md")
    # git 仓库：把 harness 目录加入仓库本地 exclude（支持 monorepo 子目录）
    context = git_context(paper_dir)
    if context:
        repo_root, paper_prefix = context
        exclude_proc = git(paper_dir, "rev-parse", "--path-format=absolute", "--git-path", "info/exclude")
        exclude = Path(exclude_proc.stdout.strip()) if exclude_proc.returncode == 0 else None
        try:
            text = exclude.read_text(encoding="utf-8") if exclude and exclude.exists() else ""
            prefix = paper_prefix.as_posix().strip("/")
            base = f"/{prefix}/" if prefix else "/"
            patterns = [f"{base}{HARNESS_DIRNAME}/", f"{base}.codex/"]
            patterns.extend(f"{base}**/*{suffix}" for suffix in sorted(BUILD_INTERMEDIATE_SUFFIXES))
            patterns.append(f"{base}**/*.run.xml")
            missing_patterns = [pattern for pattern in patterns if pattern not in text.splitlines()]
            if exclude and missing_patterns:
                exclude.parent.mkdir(parents=True, exist_ok=True)
                with exclude.open("a", encoding="utf-8") as f:
                    f.write("\n" + "\n".join(missing_patterns) + "\n")
        except OSError:
            pass
    rt = Runtime(paper_dir)
    rt.event("init", journal=args.journal, manuscript=args.manuscript)
    rt.close()
    print(f"初始化完成: {root}")
    print(f"  journal={args.journal} manuscript={args.manuscript}")
    print(f"  skills 已复制到 {skills_dst}")
    return 0


# ---------- plan ----------

def cmd_plan(args) -> int:
    paper_dir = Path(args.paper_dir).resolve()
    rt = Runtime(paper_dir)
    cfg = load_config(paper_dir)
    try:
        if args.from_file:
            content = Path(args.from_file).read_text(encoding="utf-8")
        else:
            if transport.is_mock():
                print("mock 模式下 planner 不调用 CLI，必须使用 --from-file 提供 plan。", file=sys.stderr)
                return 2
            if not args.goal:
                print("缺少 --goal（或改用 --from-file）。", file=sys.stderr)
                return 2
            content = roles.plan_with_codex(args.goal, paper_dir, args.model, cfg.get("transport_command", "codex exec"))
        version = rt.next_plan_version()
        plan_path = rt.root / "plans" / f"plan_v{version}.md"
        plan_path.write_text(content, encoding="utf-8")
        try:
            stages = gate.parse_plan(plan_path)
        except ValueError as e:
            plan_path.unlink()
            print(f"plan 校验失败: {e}", file=sys.stderr)
            return 2
        digest = gate.plan_digest(plan_path)
        rt.add_plan(version, str(plan_path.relative_to(paper_dir)), digest)
        for st in stages:
            rt.add_stage(st["id"], version, st["title"], st["objective"], st["acceptance"])
        rt.event(
            "plan_created",
            version=version, path=plan_path.name, sha256=digest,
            stages=[s["id"] for s in stages], source="file" if args.from_file else "codex",
        )
        print(f"plan_v{version} 已创建: {plan_path}")
        print(f"SHA-256 digest: {digest}")
        print(f"stages: {', '.join(s['id'] for s in stages)}")
        print("状态: AWAITING_APPROVAL —— 请人工审阅后运行 approve。")
        return 0
    finally:
        rt.close()


# ---------- approve ----------

def cmd_approve(args) -> int:
    paper_dir = Path(args.paper_dir).resolve()
    rt = Runtime(paper_dir)
    try:
        plan = rt.latest_plan()
        if plan is None:
            print("尚无 plan，请先运行 plan。", file=sys.stderr)
            return 2
        plan_path = paper_dir / plan["path"]
        digest = gate.plan_digest(plan_path)
        if digest != plan["sha256"]:
            rt.event("approval_refused", version=plan["version"], reason="registered plan digest changed")
            print(
                "拒绝批准：plan 文件自创建后已被修改。\n"
                f"  创建时: {plan['sha256']}\n  当前:   {digest}\n"
                "请用修改后的内容创建新 plan 版本，再进行人工批准。",
                file=sys.stderr,
            )
            return 2
        approval = {
            "plan_version": plan["version"],
            "plan_path": plan["path"],
            "plan_sha256": digest,
            "approved_by_human": args.by,
            "approval_date": today_cn(),
            "approved_at": now_iso(),
        }
        ap_path = rt.root / "approvals" / f"approval_v{plan['version']}.json"
        ap_path.write_text(json.dumps(approval, ensure_ascii=False, indent=2), encoding="utf-8")
        rt.set_plan_status(plan["version"], "APPROVED")
        rt.event("approved", version=plan["version"], sha256=digest, approved_by_human=args.by)
        print(f"plan_v{plan['version']} 已批准（{args.by}, {approval['approval_date']}）: {ap_path}")
        return 0
    finally:
        rt.close()


# ---------- run ----------

def _stage_branch(paper_dir: Path, stage_id: str, plan_version: int) -> str:
    project = sanitize_branch_part(paper_dir.name.lower())
    return f"paper-harness/{project}/v{plan_version}-{sanitize_branch_part(stage_id)}"


def _worktree_target(rt: Runtime, paper_dir: Path, stage_id: str, plan_version: int) -> Path:
    """Use a short Windows path so unrelated long repository paths can be checked out safely."""
    if os.name == "nt":
        identity = f"{paper_dir.resolve()}|{plan_version}|{stage_id}".encode("utf-8")
        token = hashlib.sha256(identity).hexdigest()[:16]
        return Path(tempfile.gettempdir()) / "paper_harness_worktrees" / token
    return rt.root / "runs" / f"v{plan_version}_{sanitize_branch_part(stage_id)}" / "worktree"


def _safe_remove_worktree_target(repo_root: Path, target: Path, rt_root: Path) -> None:
    """Remove one exact harness-created worktree, rejecting links and broad targets."""
    target = target.resolve()
    allowed_roots = [
        (rt_root / "runs").resolve(),
        (Path(tempfile.gettempdir()) / "paper_harness_worktrees").resolve(),
    ]
    if not any(target != root and target.is_relative_to(root) for root in allowed_roots):
        raise RuntimeError(f"refusing to clean unexpected worktree target: {target}")
    if target.exists():
        if target.is_symlink():
            raise RuntimeError(f"refusing to clean linked worktree target: {target}")
        proc = git(repo_root, "-c", "core.longpaths=true", "worktree", "remove", "--force", str(target))
        if proc.returncode != 0 and target.exists():
            shutil.rmtree(target)
    git(repo_root, "worktree", "prune")


def _prepare_workdir(rt: Runtime, paper_dir: Path, stage_id: str, plan_version: int) -> tuple[Path, str | None, str | None]:
    """Return (paper workdir, branch, worktree root), including monorepo prefixes."""
    run_dir = rt.root / "runs" / f"v{plan_version}_{sanitize_branch_part(stage_id)}"
    run_dir.mkdir(parents=True, exist_ok=True)
    context = git_context(paper_dir)
    if context is None:
        raise RuntimeError("isolated execution requires a Git repository")
    repo_root, paper_prefix = context
    branch = _stage_branch(paper_dir, stage_id, plan_version)
    wt = _worktree_target(rt, paper_dir, stage_id, plan_version)
    if wt.exists():
        _safe_remove_worktree_target(repo_root, wt, rt.root)
    if git(repo_root, "rev-parse", "--verify", branch).returncode == 0:
        git(repo_root, "branch", "-D", branch)
    wt.parent.mkdir(parents=True, exist_ok=True)
    proc = git(repo_root, "-c", "core.longpaths=true", "worktree", "add", str(wt), "-b", branch, "HEAD")
    if proc.returncode != 0:
        try:
            _safe_remove_worktree_target(repo_root, wt, rt.root)
        except RuntimeError:
            pass
        if git(repo_root, "rev-parse", "--verify", branch).returncode == 0:
            git(repo_root, "branch", "-D", branch)
        raise RuntimeError(f"git worktree 创建失败: {proc.stderr.strip()}")
    paper_workdir = (wt / paper_prefix).resolve()
    if not paper_workdir.is_dir():
        git(repo_root, "worktree", "remove", "--force", str(wt))
        git(repo_root, "branch", "-D", branch)
        raise RuntimeError(f"paper prefix is absent from worktree: {paper_prefix}")
    return paper_workdir, branch, str(wt)


def cmd_retry(args) -> int:
    """Return one preserved infrastructure failure to PENDING without changing its approved plan."""
    paper_dir = Path(args.paper_dir).resolve()
    rt = Runtime(paper_dir)
    try:
        plan = rt.latest_plan()
        if plan is None:
            print("尚无 plan。", file=sys.stderr)
            return 2
        try:
            gate.verify_approval(
                paper_dir / plan["path"],
                rt.root / "approvals" / f"approval_v{plan['version']}.json",
            )
        except gate.GateError as exc:
            print(f"Hard Gate 拒绝 retry:\n{exc}", file=sys.stderr)
            return 2
        st = rt.get_stage(args.stage_id, plan["version"])
        if st is None or st["status"] not in ("BLOCKED", "FAILED"):
            print("只有当前计划中的 BLOCKED/FAILED stage 可以 retry。", file=sys.stderr)
            return 2
        context = git_context(paper_dir)
        if context is None:
            print("无法解析 Git 仓库根目录。", file=sys.stderr)
            return 1
        repo_root, _ = context
        targets = []
        if st["worktree"]:
            targets.append(Path(st["worktree"]))
        targets.extend(
            [
                _worktree_target(rt, paper_dir, args.stage_id, plan["version"]),
                rt.root / "runs" / f"v{plan['version']}_{sanitize_branch_part(args.stage_id)}" / "worktree",
            ]
        )
        for target in dict.fromkeys(str(path.resolve()) for path in targets):
            _safe_remove_worktree_target(repo_root, Path(target), rt.root)
        branch = st["branch"] or _stage_branch(paper_dir, args.stage_id, plan["version"])
        if git(repo_root, "rev-parse", "--verify", branch).returncode == 0:
            proc = git(repo_root, "branch", "-D", branch)
            if proc.returncode != 0:
                print(f"无法清理失败分支 {branch}: {proc.stderr.strip()}", file=sys.stderr)
                return 1
        rt.reset_stage_for_retry(args.stage_id, plan["version"])
        rt.event(
            "stage_retry_requested",
            stage_id=args.stage_id,
            plan_version=plan["version"],
            reason=args.reason,
        )
        print(f"[{args.stage_id}] 已从 {st['status']} 重置为 PENDING；批准计划和失败现场记录保持不变。")
        return 0
    finally:
        rt.close()


def cmd_run(args) -> int:
    paper_dir = Path(args.paper_dir).resolve()
    rt = Runtime(paper_dir)
    cfg = load_config(paper_dir)
    try:
        plan = rt.latest_plan()
        if plan is None:
            print("尚无 plan，请先运行 plan。", file=sys.stderr)
            return 2
        # Hard Gate
        plan_path = paper_dir / plan["path"]
        approval_path = rt.root / "approvals" / f"approval_v{plan['version']}.json"
        try:
            approval = gate.verify_approval(plan_path, approval_path)
        except gate.GateError as e:
            rt.event("run_refused", version=plan["version"], reason=str(e))
            print(f"Hard Gate 拒绝执行:\n{e}", file=sys.stderr)
            return 2
        print(f"Hard Gate 通过: plan_v{plan['version']} approved by {approval['approved_by_human']}")

        stages = rt.stages_for_plan(plan["version"])
        if args.stage:
            stages = [s for s in stages if s["stage_id"] == args.stage]
            if not stages:
                print(f"plan_v{plan['version']} 中不存在 stage: {args.stage}", file=sys.stderr)
                return 2
        all_plan_stages = rt.stages_for_plan(plan["version"])
        candidates = [s for s in all_plan_stages if s["status"] == "CANDIDATE"]
        if candidates:
            ids = ", ".join(s["stage_id"] for s in candidates)
            print(f"存在等待人工裁决的 CANDIDATE stage（{ids}）；accept/reject 后才能运行下一阶段。", file=sys.stderr)
            return 2
        pending = [s for s in stages if s["status"] == "PENDING"]
        if not pending:
            print("没有 PENDING 的 stage。")
            return 0
        first_pending = next((s for s in all_plan_stages if s["status"] == "PENDING"), None)
        if first_pending is None:
            print("没有 PENDING 的 stage。")
            return 0
        if args.stage and first_pending["stage_id"] != args.stage:
            print(
                f"阶段必须按计划顺序执行；当前首个 PENDING stage 是 {first_pending['stage_id']}，不是 {args.stage}。",
                file=sys.stderr,
            )
            return 2
        prior = []
        for stage_row in all_plan_stages:
            if stage_row["stage_id"] == first_pending["stage_id"]:
                break
            prior.append(stage_row)
        if any(stage_row["status"] != "ACCEPTED" for stage_row in prior):
            detail = ", ".join(f"{s['stage_id']}={s['status']}" for s in prior)
            print(f"前置阶段尚未全部 ACCEPTED：{detail}", file=sys.stderr)
            return 2
        ok, detail = execution_preflight(paper_dir, cfg)
        if not ok:
            rt.event("run_refused", version=plan["version"], reason=detail)
            print(f"执行预检拒绝运行:\n{detail}", file=sys.stderr)
            return 2
        print(f"执行预检通过: {detail}")
        # Exactly one stage becomes CANDIDATE. The next stage cannot start until human accept/reject.
        return _run_one_stage(rt, paper_dir, cfg, first_pending, plan["version"], args.model)
    finally:
        rt.close()


def _run_one_stage(rt: Runtime, paper_dir: Path, cfg: dict, st, plan_version: int, model: str | None) -> int:
    stage_id = st["stage_id"]
    stage = {
        "id": stage_id,
        "title": st["title"],
        "objective": st["objective"],
        "acceptance": json.loads(st["acceptance"] or "[]"),
    }
    rt.set_stage_status(stage_id, plan_version, "RUNNING")
    rt.event("stage_started", stage_id=stage_id, plan_version=plan_version)
    print(f"[{stage_id}] RUNNING — {st['title']}")
    try:
        workdir, branch, wt = _prepare_workdir(rt, paper_dir, stage_id, plan_version)
    except RuntimeError as e:
        rt.set_stage_status(stage_id, plan_version, "BLOCKED")
        rt.event("stage_blocked", stage_id=stage_id, reason=str(e))
        print(f"[{stage_id}] BLOCKED: {e}", file=sys.stderr)
        return 1
    rt.set_stage_status(stage_id, plan_version, "RUNNING", branch=branch, worktree=wt)
    if branch:
        rt.event("worktree_created", stage_id=stage_id, branch=branch, worktree=wt)
        print(f"[{stage_id}] worktree: {wt} (branch {branch})")
    else:
        print(f"[{stage_id}] 非 git 目录，原地执行（见 runs/{stage_id}/NOTE.txt）")

    run_dir = rt.root / "runs" / f"v{plan_version}_{sanitize_branch_part(stage_id)}"
    log_path = run_dir / "executor.log"
    try:
        ok = roles.execute_stage(stage, workdir, model, cfg.get("transport_command", "codex exec"), log_path)
    except Exception as e:  # executor 调用本身异常 → BLOCKED 固定现场
        ok = False
        log_path.write_text(f"executor 异常: {e}\n", encoding="utf-8")
    if not ok:
        rt.set_stage_status(stage_id, plan_version, "BLOCKED")
        rt.event("stage_blocked", stage_id=stage_id, reason="executor 未成功完成", log=str(log_path))
        print(f"[{stage_id}] BLOCKED: executor 失败，现场保留于 {run_dir}", file=sys.stderr)
        return 1

    acceptance = stage["acceptance"]
    results = checks.run_checks(acceptance, workdir, cfg) if acceptance else []
    acc_path = run_dir / "acceptance.json"
    acc_path.write_text(
        json.dumps({"stage_id": stage_id, "ts": now_iso(), "results": results}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    for r in results:
        print(f"[{stage_id}] check {r['name']}: {r['status']}" + (f" — {r['detail'].splitlines()[0]}" if r["detail"] else ""))
    if results and not checks.all_ok(results):
        rt.set_stage_status(stage_id, plan_version, "BLOCKED")
        rt.event("stage_blocked", stage_id=stage_id, reason="验收检查未通过", acceptance=str(acc_path))
        print(f"[{stage_id}] BLOCKED: 验收未通过，现场保留于 {run_dir}", file=sys.stderr)
        return 1
    committed, commit_detail = commit_candidate(workdir, stage_id, plan_version, cfg)
    if not committed:
        rt.set_stage_status(stage_id, plan_version, "BLOCKED")
        rt.event("stage_blocked", stage_id=stage_id, reason="candidate commit failed", detail=commit_detail)
        print(f"[{stage_id}] BLOCKED: 候选提交失败：{commit_detail}", file=sys.stderr)
        return 1
    rt.event("candidate_committed", stage_id=stage_id, detail=commit_detail)
    rt.set_stage_status(stage_id, plan_version, "CANDIDATE")
    rt.event("candidate_ready", stage_id=stage_id, acceptance=str(acc_path))
    print(f"[{stage_id}] CANDIDATE — 等待人工 accept/reject。")
    return 0


# ---------- status ----------

def cmd_status(args) -> int:
    paper_dir = Path(args.paper_dir).resolve()
    rt = Runtime(paper_dir)
    try:
        plan = rt.latest_plan()
        print(f"论文目录: {paper_dir}")
        print(f"当前 plan: " + (f"plan_v{plan['version']} [{plan['status']}] sha256={plan['sha256'][:12]}…" if plan else "（无）"))
        stages = rt.all_stages()
        if stages:
            print("\nstages:")
            for s in stages:
                line = f"  {s['stage_id']:<12} v{s['plan_version']}  {s['status']:<10} {s['title'] or ''}"
                if s["branch"]:
                    line += f"  [{s['branch']}]"
                print(line)
        events = rt.tail_events(10)
        if events:
            print("\n最近事件:")
            for ev in events:
                detail = ", ".join(f"{k}={v}" for k, v in list(ev.get("data", {}).items())[:3])
                print(f"  {ev['ts']}  {ev['type']:<18} {detail}")
        return 0
    finally:
        rt.close()


# ---------- accept / reject ----------

def _get_candidate(rt: Runtime, stage_id: str):
    st = rt.get_stage(stage_id)
    if st is None:
        print(f"stage 不存在: {stage_id}", file=sys.stderr)
        return None
    if st["status"] != "CANDIDATE":
        print(f"stage {stage_id} 当前状态 {st['status']}，只有 CANDIDATE 可以 accept/reject。", file=sys.stderr)
        return None
    return st


def cmd_accept(args) -> int:
    paper_dir = Path(args.paper_dir).resolve()
    rt = Runtime(paper_dir)
    try:
        st = _get_candidate(rt, args.stage_id)
        if st is None:
            return 2
        branch, wt = st["branch"], st["worktree"]
        if branch and is_git_repo(paper_dir):
            context = git_context(paper_dir)
            if context is None:
                print("无法解析 Git 仓库根目录。", file=sys.stderr)
                return 1
            repo_root, _ = context
            ok, detail = execution_preflight(paper_dir, load_config(paper_dir))
            if not ok:
                rt.set_stage_status(args.stage_id, st["plan_version"], "BLOCKED")
                rt.event("accept_blocked", stage_id=args.stage_id, reason="main baseline changed", detail=detail)
                print(f"accept 前主工作区不再是候选生成时的干净基线：\n{detail}", file=sys.stderr)
                return 1
            proc = git(repo_root, "merge", "--no-ff", branch, "-m", f"paper-harness: accept {args.stage_id} (plan v{st['plan_version']})")
            if proc.returncode != 0:
                rt.set_stage_status(args.stage_id, st["plan_version"], "BLOCKED")
                rt.event("accept_blocked", stage_id=args.stage_id, reason="merge 冲突", branch=branch)
                print(
                    f"merge 冲突，stage 标记 BLOCKED。现场保留：分支 {branch}、worktree {wt}、"
                    "合并中的工作区。人工解决后可重新 accept。",
                    file=sys.stderr,
                )
                return 1
            if wt:
                git(repo_root, "worktree", "remove", "--force", wt)
        rt.set_stage_status(args.stage_id, st["plan_version"], "ACCEPTED")
        rt.event("accepted", stage_id=args.stage_id, plan_version=st["plan_version"], branch=branch)
        print(f"[{args.stage_id}] ACCEPTED" + (f"，分支 {branch} 已合并（--no-ff）。" if branch else "（非 git 目录，改动已在原目录）。"))
        return 0
    finally:
        rt.close()


def cmd_reject(args) -> int:
    paper_dir = Path(args.paper_dir).resolve()
    rt = Runtime(paper_dir)
    try:
        st = _get_candidate(rt, args.stage_id)
        if st is None:
            return 2
        branch, wt = st["branch"], st["worktree"]
        if wt and is_git_repo(paper_dir):
            context = git_context(paper_dir)
            repo_root = context[0] if context else paper_dir
            git(repo_root, "worktree", "remove", "--force", wt)
        if branch and is_git_repo(paper_dir):
            context = git_context(paper_dir)
            repo_root = context[0] if context else paper_dir
            git(repo_root, "branch", "-D", branch)
        rt.set_stage_status(args.stage_id, st["plan_version"], "REJECTED")
        rt.event("rejected", stage_id=args.stage_id, plan_version=st["plan_version"], branch=branch)
        print(f"[{args.stage_id}] REJECTED" + (f"，worktree 与分支 {branch} 已清理。" if branch else "。"))
        return 0
    finally:
        rt.close()


# ---------- review ----------

def cmd_review(args) -> int:
    paper_dir = Path(args.paper_dir).resolve()
    rt = Runtime(paper_dir)
    cfg = load_config(paper_dir)
    try:
        venue = cfg.get("journal", "unknown")
        manuscript = cfg.get("manuscript", "main.tex")
        out = roles.review(paper_dir, venue, manuscript, args.model, cfg.get("transport_command", "codex exec"))
        ts = ts_compact()
        out_path = rt.root / "reviews" / f"review_{ts}.json"
        out_path.write_text(out + "\n", encoding="utf-8")
        rt.event("review_completed", venue=venue, path=out_path.name)
        print(f"评审完成: {out_path}")
        return 0
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        return 1
    finally:
        rt.close()


# ---------- attribute ----------

def cmd_attribute(args) -> int:
    paper_dir = Path(args.paper_dir).resolve()
    rt = Runtime(paper_dir)
    cfg = load_config(paper_dir)
    try:
        st = rt.get_stage(args.stage_id)
        if st is None:
            print(f"stage 不存在: {args.stage_id}", file=sys.stderr)
            return 2
        if st["status"] not in ("BLOCKED", "FAILED"):
            print(f"警告: stage {args.stage_id} 状态为 {st['status']}（通常对 BLOCKED 做归因）。", file=sys.stderr)
        # 组装现场：日志 + acceptance + timeline 节选 + plan
        scene_parts = []
        run_dir = rt.root / "runs" / f"v{st['plan_version']}_{sanitize_branch_part(args.stage_id)}"
        if run_dir.is_dir():
            for f in sorted(run_dir.glob("*")):
                if f.is_file() and f.suffix in (".log", ".json", ".txt"):
                    scene_parts.append(f"### {f.name}\n```\n{f.read_text(encoding='utf-8', errors='replace')[:5000]}\n```")
        events = rt.tail_events(50)
        scene_parts.append("### timeline 节选\n```json\n" + "\n".join(json.dumps(e, ensure_ascii=False) for e in events) + "\n```")
        plan = rt.get_plan(st["plan_version"])
        if plan:
            plan_path = paper_dir / plan["path"]
            if plan_path.exists():
                scene_parts.append(f"### plan_v{plan['version']}\n" + plan_path.read_text(encoding="utf-8")[:5000])
        scene = "\n\n".join(scene_parts)
        stage = {"id": st["stage_id"], "title": st["title"], "objective": st["objective"],
                 "status": st["status"], "plan_version": st["plan_version"]}
        md = roles.attribute(stage, scene, paper_dir, args.model, cfg.get("transport_command", "codex exec"))
        out_path = rt.root / "attributions" / f"attribution_{sanitize_branch_part(args.stage_id)}_{ts_compact()}.md"
        out_path.write_text(md + "\n", encoding="utf-8")
        rt.event("attribution_created", stage_id=args.stage_id, path=out_path.name)
        print(f"归因完成: {out_path}")
        return 0
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        return 1
    finally:
        rt.close()


# ---------- 入口 ----------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="paper_harness", description="论文写作/实验 Harness（Codex CLI 执行层）")
    sub = p.add_subparsers(dest="command", required=True)

    sp = sub.add_parser("init", help="脚手架 + 复制 skills")
    sp.add_argument("paper_dir")
    sp.add_argument("--journal", required=True, help="venue 名（对应 paper_reviews/config/journals/<venue>.yaml）")
    sp.add_argument("--manuscript", required=True, help="manuscript tex 相对路径")
    sp.set_defaults(func=cmd_init)

    sp = sub.add_parser("plan", help="生成 plan_vN，打印 digest，状态 AWAITING_APPROVAL")
    sp.add_argument("paper_dir")
    sp.add_argument("--goal", default=None)
    sp.add_argument("--from-file", dest="from_file", default=None)
    sp.add_argument("--model", default=None)
    sp.set_defaults(func=cmd_plan)

    sp = sub.add_parser("approve", help="写 approval_vN.json（date 自动 Asia/Shanghai）")
    sp.add_argument("paper_dir")
    sp.add_argument("--by", required=True, help="批准人姓名")
    sp.set_defaults(func=cmd_approve)

    sp = sub.add_parser("run", help="Hard Gate 校验后串行执行 PENDING stages")
    sp.add_argument("paper_dir")
    sp.add_argument("--stage", default=None)
    sp.add_argument("--model", default=None)
    sp.set_defaults(func=cmd_run)

    sp = sub.add_parser("retry", help="清理失败 worktree，将当前计划的 BLOCKED/FAILED stage 重置为 PENDING")
    sp.add_argument("paper_dir")
    sp.add_argument("stage_id")
    sp.add_argument("--reason", required=True, help="可审计的重试原因")
    sp.set_defaults(func=cmd_retry)

    sp = sub.add_parser("status", help="看板投影：stage 状态 + 最近事件")
    sp.add_argument("paper_dir")
    sp.set_defaults(func=cmd_status)

    sp = sub.add_parser("accept", help="接受 candidate（git 仓库做 --no-ff merge）")
    sp.add_argument("paper_dir")
    sp.add_argument("stage_id")
    sp.set_defaults(func=cmd_accept)

    sp = sub.add_parser("reject", help="拒绝 candidate（清理 worktree 与分支）")
    sp.add_argument("paper_dir")
    sp.add_argument("stage_id")
    sp.set_defaults(func=cmd_reject)

    sp = sub.add_parser("review", help="期刊画像评审 → reviews/review_<ts>.json")
    sp.add_argument("paper_dir")
    sp.add_argument("--model", default=None)
    sp.set_defaults(func=cmd_review)

    sp = sub.add_parser("attribute", help="BLOCKED 归因 → attributions/")
    sp.add_argument("paper_dir")
    sp.add_argument("stage_id")
    sp.add_argument("--model", default=None)
    sp.set_defaults(func=cmd_attribute)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)
