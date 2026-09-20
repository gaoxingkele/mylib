# -*- coding: utf-8 -*-
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "wrap_eval.py"
PY = sys.executable


class WrapEvalTests(unittest.TestCase):
    def test_cli_writes_eval_named_by_gate_and_only_that_case(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            raw = Path(tmp) / "raw.txt"
            raw.write_text("六节：仅评 P04-2。新颖性有条件达到。\n", encoding="utf-8")
            out_dir = Path(tmp) / "P04-2"
            proc = subprocess.run(
                [
                    PY,
                    str(SCRIPT),
                    "--case",
                    "P04-2",
                    "--gate",
                    "GROK-EXPERT",
                    "--url",
                    "https://grok.com/c/example",
                    "--raw",
                    str(raw),
                    "--note",
                    "Expert",
                    "--out-dir",
                    str(out_dir),
                    "--version",
                    "20260918",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            out = out_dir / "GROK-EXPERT_新颖性创造性评估.md"
            self.assertTrue(out.is_file(), proc.stdout)
            body = out.read_text(encoding="utf-8")
            self.assertIn("GROK-EXPERT 对 P04-2", body)
            self.assertIn("本会话只评 P04-2", body)
            self.assertIn("六节：仅评 P04-2", body)
            self.assertNotIn("仅评 P01-1", body)
            self.assertIn("https://grok.com/c/example", body)


if __name__ == "__main__":
    unittest.main()
