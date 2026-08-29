"""paper_harness smoke 测试（mock 模式，绝不调用 codex CLI）。

运行方式：
    python -m pytest D:/aicoding/mylib/paper_harness/tests/test_smoke.py
    python D:/aicoding/mylib/paper_harness/tests/test_smoke.py
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # 直接运行时也能 import paper_harness

from paper_harness import checks, cli, roles, transport  # noqa: E402
from paper_harness.runtime import Runtime  # noqa: E402

REAL_RUN_CODEX = transport._run_codex

MINIMAL_TEX = r"""\documentclass{article}
\begin{document}
\title{Smoke Test Paper}
\author{Tester}
\maketitle
\section{Introduction}
Hello harness.
\section*{Funding}
None.
\section*{Author Contributions}
T. did everything.
\section*{Data Availability}
Data in article.
\section*{Conflicts of Interest}
None.
\section*{Acknowledgments}
None.
\end{document}
"""

PLAN_MD = """---
stages:
  - id: s1
    title: mock 执行一个 stage
    objective: "mock executor 记录目标即可"
    acceptance:
      - latex_build
      - no_placeholders
      - declarations
---
# 测试计划
"""

TWO_STAGE_PLAN_MD = """---
stages:
  - id: s1
    title: first stage
    objective: "first mock stage"
    acceptance: []
  - id: s2
    title: second stage
    objective: "second mock stage"
    acceptance: []
---
# Sequential plan
"""


def make_paper_project(root: Path, use_git: bool = True) -> Path:
    paper = root / "paper"
    paper.mkdir(parents=True)
    (paper / "main.tex").write_text(MINIMAL_TEX, encoding="utf-8")
    if use_git:
        env = dict(os.environ)
        subprocess.run(["git", "init"], cwd=paper, capture_output=True, check=True, env=env)
        subprocess.run(["git", "add", "."], cwd=paper, capture_output=True, check=True)
        subprocess.run(
            ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com",
             "commit", "-m", "init"],
            cwd=paper, capture_output=True, check=True,
        )
    return paper


def timeline_types(paper: Path) -> list[str]:
    path = paper / ".paper_harness" / "timeline.jsonl"
    return [json.loads(l)["type"] for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def assert_subsequence(seq: list, sub: list) -> bool:
    it = iter(seq)
    return all(any(x == y for x in it) for y in sub)


class PaperHarnessSmokeTest(unittest.TestCase):
    def setUp(self):
        if shutil.which("git") is None:
            self.skipTest("git 不可用")
        self.tmp = Path(tempfile.mkdtemp(prefix="paper_harness_test_"))
        self.addCleanup(lambda: shutil.rmtree(self.tmp, ignore_errors=True))
        # mock 模式 + 一旦触碰真实 codex 子进程立即失败
        self.env_patch = mock.patch.dict(os.environ, {"PAPER_HARNESS_TRANSPORT": "mock"})
        self.env_patch.start()
        self.addCleanup(self.env_patch.stop)
        self.codex_patcher = mock.patch.object(
            transport, "_run_codex",
            side_effect=AssertionError("mock 模式下不应调用真实 codex"),
        )
        self.codex_guard = self.codex_patcher.start()
        self.addCleanup(self.codex_patcher.stop)

    def _init_plan(self, paper: Path) -> None:
        plan_file = self.tmp / f"plan_{paper.name}.md"
        plan_file.write_text(PLAN_MD, encoding="utf-8")
        self.assertEqual(cli.main(["init", str(paper), "--journal", "mdpi_applied_sciences", "--manuscript", "main.tex"]), 0)
        self.assertEqual(cli.main(["plan", str(paper), "--from-file", str(plan_file)]), 0)

    def test_mock_end_to_end(self):
        paper = make_paper_project(self.tmp / "e2e")
        self._init_plan(paper)
        self.assertEqual(cli.main(["approve", str(paper), "--by", "Tester"]), 0)
        self.assertEqual(cli.main(["run", str(paper)]), 0)

        rt = Runtime(paper)
        stage = rt.get_stage("s1")
        self.assertIsNotNone(stage)
        self.assertEqual(stage["status"], "CANDIDATE")
        rt.close()

        self.assertEqual(cli.main(["status", str(paper)]), 0)
        self.assertEqual(cli.main(["accept", str(paper), "s1"]), 0)

        rt = Runtime(paper)
        self.assertEqual(rt.get_stage("s1")["status"], "ACCEPTED")
        rt.close()

        # timeline 事件链完整
        types = timeline_types(paper)
        self.assertTrue(
            assert_subsequence(types, ["plan_created", "approved", "stage_started", "candidate_ready", "accepted"]),
            f"事件链不完整: {types}",
        )
        # mock 传输未被真实触发
        self.codex_guard.assert_not_called()
        # review（mock）：空 issue matrix
        self.assertEqual(cli.main(["review", str(paper)]), 0)
        reviews = list((paper / ".paper_harness" / "reviews").glob("review_*.json"))
        self.assertTrue(reviews)
        data = json.loads(reviews[-1].read_text(encoding="utf-8"))
        self.assertEqual(data["issues"], [])

    def test_declarations_accepts_reproducibility_data_boundary_heading(self):
        paper = self.tmp / "declaration_alias"
        paper.mkdir()
        manuscript = paper / "main.tex"
        manuscript.write_text(
            r"""\section*{Funding}
None.
\section{Reproducibility and Data Boundary}
The source data and release boundary are stated here.
\section*{Acknowledgments}
None.
""",
            encoding="utf-8",
        )
        result = checks.check_declarations(
            paper,
            {"manuscript": "main.tex", "journal": "ieee_access"},
        )
        self.assertEqual(result["status"], "pass", result["detail"])

    def test_hard_gate_rejects_tampered_plan(self):
        paper = make_paper_project(self.tmp / "tamper")
        self._init_plan(paper)
        self.assertEqual(cli.main(["approve", str(paper), "--by", "Tester"]), 0)
        # 篡改已批准的 plan
        plan_path = paper / ".paper_harness" / "plans" / "plan_v1.md"
        plan_path.write_text(plan_path.read_text(encoding="utf-8") + "\n篡改一行\n", encoding="utf-8")
        rc = cli.main(["run", str(paper)])
        self.assertEqual(rc, 2, "篡改 plan 后 run 必须拒绝")
        rt = Runtime(paper)
        self.assertEqual(rt.get_stage("s1")["status"], "PENDING")
        rt.close()
        self.assertIn("run_refused", timeline_types(paper))
        self.codex_guard.assert_not_called()

    def test_hard_gate_rejects_missing_approval(self):
        paper = make_paper_project(self.tmp / "noapproval")
        self._init_plan(paper)
        rc = cli.main(["run", str(paper)])  # 未 approve
        self.assertEqual(rc, 2, "无 approval 时 run 必须拒绝")
        rt = Runtime(paper)
        self.assertEqual(rt.get_stage("s1")["status"], "PENDING")
        rt.close()
        self.codex_guard.assert_not_called()

    def test_approve_rejects_registered_plan_mutation(self):
        paper = make_paper_project(self.tmp / "preapproval_tamper")
        self._init_plan(paper)
        plan_path = paper / ".paper_harness" / "plans" / "plan_v1.md"
        plan_path.write_text(plan_path.read_text(encoding="utf-8") + "\nchanged before approval\n", encoding="utf-8")
        self.assertEqual(cli.main(["approve", str(paper), "--by", "Tester"]), 2)
        self.assertFalse((paper / ".paper_harness" / "approvals" / "approval_v1.json").exists())
        rt = Runtime(paper)
        self.assertEqual(rt.latest_plan()["status"], "AWAITING_APPROVAL")
        rt.close()

    def test_mock_transport_short_circuit(self):
        code, out = transport.codex_exec("hello", cwd=self.tmp, sandbox="read-only")
        self.assertEqual(code, 0)
        self.assertIn("MOCK", out)
        self.codex_guard.assert_not_called()

    def test_transport_timeout_can_be_extended_by_environment(self):
        os.environ["PAPER_HARNESS_CODEX_TIMEOUT"] = "2700"
        previous_transport = os.environ.pop(transport.MOCK_ENV, None)
        try:
            with mock.patch("paper_harness.transport._run_codex", return_value=(0, "ok")) as runner:
                code, out = transport.codex_exec("hello", cwd=self.tmp)
            self.assertEqual((code, out), (0, "ok"))
            self.assertEqual(runner.call_args.args[-1], 2700)
        finally:
            os.environ.pop("PAPER_HARNESS_CODEX_TIMEOUT", None)
            if previous_transport is not None:
                os.environ[transport.MOCK_ENV] = previous_transport

    def test_transport_timeout_terminates_controlled_process_tree(self):
        previous_transport = os.environ.pop(transport.MOCK_ENV, None)
        fake_proc = mock.Mock()
        fake_proc.communicate.side_effect = subprocess.TimeoutExpired(cmd="codex", timeout=1)
        try:
            with (
                mock.patch("paper_harness.transport._command_argv", return_value=["codex", "exec"]),
                mock.patch("paper_harness.transport.subprocess.Popen", return_value=fake_proc),
                mock.patch("paper_harness.transport._terminate_process_tree") as terminate,
            ):
                code, out = REAL_RUN_CODEX("prompt", self.tmp, "read-only", None, "codex exec", 1)
            self.assertEqual(code, 124)
            self.assertIn("process tree terminated", out)
            terminate.assert_called_once_with(fake_proc)
        finally:
            if previous_transport is not None:
                os.environ[transport.MOCK_ENV] = previous_transport

    def test_two_stage_plan_requires_accept_between_stages(self):
        paper = make_paper_project(self.tmp / "sequential")
        plan_file = self.tmp / "two_stage.md"
        plan_file.write_text(TWO_STAGE_PLAN_MD, encoding="utf-8")
        self.assertEqual(cli.main(["init", str(paper), "--journal", "mdpi_applied_sciences", "--manuscript", "main.tex"]), 0)
        self.assertEqual(cli.main(["plan", str(paper), "--from-file", str(plan_file)]), 0)
        self.assertEqual(cli.main(["approve", str(paper), "--by", "Tester"]), 0)
        self.assertEqual(cli.main(["run", str(paper)]), 0)
        rt = Runtime(paper)
        self.assertEqual(rt.get_stage("s1")["status"], "CANDIDATE")
        self.assertEqual(rt.get_stage("s2")["status"], "PENDING")
        rt.close()
        self.assertEqual(cli.main(["run", str(paper)]), 2)
        self.assertEqual(cli.main(["accept", str(paper), "s1"]), 0)
        self.assertEqual(cli.main(["run", str(paper)]), 0)
        rt = Runtime(paper)
        self.assertEqual(rt.get_stage("s2")["status"], "CANDIDATE")
        rt.close()

    def test_retry_resets_only_blocked_stage_under_same_approval(self):
        paper = make_paper_project(self.tmp / "retry")
        self._init_plan(paper)
        self.assertEqual(cli.main(["approve", str(paper), "--by", "Tester"]), 0)
        rt = Runtime(paper)
        rt.set_stage_status("s1", 1, "BLOCKED")
        rt.event("stage_blocked", stage_id="s1", reason="simulated infrastructure failure")
        rt.close()
        self.assertEqual(
            cli.main(["retry", str(paper), "s1", "--reason", "fixed worktree infrastructure"]),
            0,
        )
        rt = Runtime(paper)
        self.assertEqual(rt.get_stage("s1")["status"], "PENDING")
        rt.close()
        self.assertIn("stage_retry_requested", timeline_types(paper))

    def test_retry_can_preserve_locked_worktree_and_rotate_target(self):
        paper = make_paper_project(self.tmp / "retry_locked")
        self._init_plan(paper)
        self.assertEqual(cli.main(["approve", str(paper), "--by", "Tester"]), 0)
        rt = Runtime(paper)
        old_target = cli._worktree_target(rt, paper, "s1", 1)
        old_target.mkdir(parents=True, exist_ok=True)
        (old_target / "incident.txt").write_text("preserve", encoding="utf-8")
        rt.set_stage_status("s1", 1, "BLOCKED", worktree=str(old_target))
        rt.close()
        self.assertEqual(
            cli.main([
                "retry", str(paper), "s1", "--reason", "legacy lock",
                "--preserve-locked-worktree",
            ]),
            0,
        )
        rt = Runtime(paper)
        new_target = cli._worktree_target(rt, paper, "s1", 1)
        self.assertNotEqual(old_target, new_target)
        self.assertTrue((old_target / "incident.txt").exists())
        self.assertEqual(rt.get_stage("s1")["status"], "PENDING")
        rt.close()
        self.assertIn("locked_worktree_preserved", timeline_types(paper))

    def test_status_does_not_fail_live_running_stage(self):
        paper = make_paper_project(self.tmp / "live_lease")
        self._init_plan(paper)
        rt = Runtime(paper)
        rt.set_stage_status("s1", 1, "RUNNING")
        run_dir = paper / ".paper_harness" / "runs" / "v1_s1"
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "lease.json").write_text(json.dumps({"pid": os.getpid()}), encoding="utf-8")
        rt.close()
        self.assertEqual(cli.main(["status", str(paper)]), 0)
        rt = Runtime(paper)
        self.assertEqual(rt.get_stage("s1")["status"], "RUNNING")
        self.assertEqual(rt.recover_stale_running(), [])
        self.assertEqual(rt.get_stage("s1")["status"], "RUNNING")
        rt.close()

    def test_monorepo_subdirectory_worktree_uses_paper_prefix(self):
        repo = self.tmp / "monorepo"
        paper = repo / "paper_projects" / "p1"
        paper.mkdir(parents=True)
        (paper / "main.tex").write_text(MINIMAL_TEX, encoding="utf-8")
        subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=True)
        subprocess.run(
            ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "init"],
            cwd=repo, capture_output=True, check=True,
        )
        plan_file = self.tmp / "monorepo_plan.md"
        plan_file.write_text(TWO_STAGE_PLAN_MD.replace("  - id: s2\n    title: second stage\n    objective: \"second mock stage\"\n    acceptance: []\n", ""), encoding="utf-8")
        self.assertEqual(cli.main(["init", str(paper), "--journal", "mdpi_applied_sciences", "--manuscript", "main.tex"]), 0)
        self.assertEqual(cli.main(["plan", str(paper), "--from-file", str(plan_file)]), 0)
        self.assertEqual(cli.main(["approve", str(paper), "--by", "Tester"]), 0)
        self.assertEqual(cli.main(["run", str(paper)]), 0)
        rt = Runtime(paper)
        stage = rt.get_stage("s1")
        self.assertIn("paper-harness/p1/v1-s1", stage["branch"])
        self.assertTrue((Path(stage["worktree"]) / "paper_projects" / "p1" / "main.tex").exists())
        rt.close()

    def test_execution_preflight_rejects_untracked_manuscript(self):
        repo = self.tmp / "untracked"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)
        (repo / "anchor.txt").write_text("tracked", encoding="utf-8")
        subprocess.run(["git", "add", "anchor.txt"], cwd=repo, capture_output=True, check=True)
        subprocess.run(
            ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "init"],
            cwd=repo, capture_output=True, check=True,
        )
        paper = repo / "paper"
        paper.mkdir()
        (paper / "main.tex").write_text(MINIMAL_TEX, encoding="utf-8")
        ok, detail = cli.execution_preflight(paper, {"manuscript": "main.tex"})
        self.assertFalse(ok)
        self.assertIn("not tracked", detail)

    def test_read_only_sparse_paths_do_not_widen_write_scope(self):
        repo = self.tmp / "read_only_scope"
        paper = repo / "paper_projects" / "p1"
        shared = repo / "shared" / "evidence"
        paper.mkdir(parents=True)
        shared.mkdir(parents=True)
        (paper / "main.tex").write_text(MINIMAL_TEX, encoding="utf-8")
        (shared / "tracked.txt").write_text("evidence", encoding="utf-8")
        subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=True)
        subprocess.run(
            ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "init"],
            cwd=repo, capture_output=True, check=True,
        )
        (shared / "user-note.txt").write_text("untracked and unrelated", encoding="utf-8")
        cfg = {"manuscript": "main.tex", "read_only_paths": ["../../shared/evidence"]}
        ok, detail = cli.execution_preflight(paper, cfg)
        self.assertTrue(ok, detail)
        sparse = cli._repo_relative_paths_for_sparse(paper, cfg)
        self.assertIn("shared/evidence", sparse)
        self.assertNotIn("shared/evidence", cli.allowed_scope_prefixes(paper, cfg))

    def test_repository_accept_lock_serializes_merges(self):
        repo = self.tmp / "accept_lock"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)
        first = cli._RepoAcceptLock(repo, timeout=1.0)
        second = cli._RepoAcceptLock(repo, timeout=0.2)
        with first:
            with self.assertRaises(TimeoutError):
                second.__enter__()
        with second:
            self.assertTrue(second.path.exists())

    def test_mock_review_records_full_manuscript_coverage(self):
        paper = make_paper_project(self.tmp / "review")
        out = roles.review(paper, "mdpi_applied_sciences", "main.tex", None, "codex exec")
        data = json.loads(out)
        self.assertEqual(data["schema_version"], "paper_harness.review.v2")
        self.assertTrue(data["coverage"]["complete"])
        self.assertEqual(data["coverage"]["characters_total"], len(MINIMAL_TEX))

    def test_artifact_consistency_detects_missing_graphic(self):
        paper = self.tmp / "missing_graphic"
        paper.mkdir()
        (paper / "main.tex").write_text(MINIMAL_TEX.replace("Hello harness.", r"Hello.\\includegraphics{figures/missing}"), encoding="utf-8")
        result = checks.check_artifact_consistency(paper, {"manuscript": "main.tex"})
        self.assertEqual(result["status"], "fail")
        self.assertIn("missing", result["detail"])

    def test_custom_check_imports_from_isolated_worktree_src(self):
        worktree = self.tmp / "custom_src"
        package = worktree / "src" / "stage_local_package"
        package.mkdir(parents=True)
        (package / "__init__.py").write_text("VALUE = 'worktree'\n", encoding="utf-8")
        script = worktree / "verify.py"
        script.write_text(
            "from stage_local_package import VALUE\n"
            "assert VALUE == 'worktree'\n"
            "print('isolated import ok')\n",
            encoding="utf-8",
        )
        result = checks.check_custom("verify.py", worktree, {})
        self.assertEqual(result["status"], "pass", result["detail"])
        self.assertIn("isolated import ok", result["detail"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
