# -*- coding: utf-8 -*-
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "wiki_log.py"
sys.path.insert(0, str(ROOT / "scripts"))
import wiki_log  # noqa: E402

PY = sys.executable


class WikiLogTests(unittest.TestCase):
    def test_insert_lands_before_next_heading(self) -> None:
        prev = (
            "# Wiki\n\n"
            "## [2026-09-20] review | 八案四端审核 源稿版本 20260918\n\n"
            "intro\n"
            "\n"
            "## [2026-09-20] review | P06-2\n\n"
            "other\n"
        )
        line = wiki_log.format_line("P01-1", "GEMINI", "20260918", "verify", day="2026-09-21")
        out = wiki_log.insert_line(prev, line, "八案四端审核")
        eight, _, rest = out.partition("## [2026-09-20] review | P06-2")
        self.assertIn("`GEMINI` `P01-1` 版本 `20260918`", eight)
        self.assertNotIn("`GEMINI`", rest)
        self.assertIn("other", rest)

    def test_duplicate_line_not_appended(self) -> None:
        line = wiki_log.format_line("P01-1", "GEMINI", "20260918", day="2026-09-21")
        prev = "# Wiki\n\n## 八案四端审核\n\n" + line + "\n## next\n"
        again = wiki_log.insert_line(prev, line, "八案四端审核")
        self.assertEqual(again.count("`GEMINI` `P01-1`"), 1)

    def test_cli_stdout_contains_gate_case_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "log.md"
            log.write_text(
                "# Wiki\n\n## review | 八案四端审核\n\nbody\n\n## later\n",
                encoding="utf-8",
            )
            proc = subprocess.run(
                [
                    PY,
                    str(SCRIPT),
                    "--case",
                    "P01-1",
                    "--gate",
                    "GEMINI",
                    "--version",
                    "20260918",
                    "--note",
                    "verify",
                    "--log",
                    str(log),
                    "--section",
                    "八案四端审核",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("`GEMINI`", proc.stdout)
            self.assertIn("`P01-1`", proc.stdout)
            self.assertIn("`20260918`", proc.stdout)
            text = log.read_text(encoding="utf-8")
            before, _, after = text.partition("## later")
            self.assertIn("`GEMINI` `P01-1` 版本 `20260918`", before)
            self.assertNotIn("GEMINI", after)


if __name__ == "__main__":
    unittest.main()
