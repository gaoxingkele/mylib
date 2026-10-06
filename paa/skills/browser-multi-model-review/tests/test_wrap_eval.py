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


class WrapEvalSummaryTests(unittest.TestCase):
    def test_summary_file_written_and_small(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            raw = Path(tmp) / "raw.txt"
            raw.write_text(
                "前言\n\n## 结论\n\n新颖性结论：有条件达到。创造性结论：有风险。\n\n## P0\n\n独权过宽，建议收窄。\n",
                encoding="utf-8",
            )
            out_dir = Path(tmp) / "ev"
            subprocess.run(
                [PY, str(SCRIPT), "--case", "P01-1", "--gate", "PPLX-PATENTS",
                 "--url", "https://pplx.ai/x", "--raw", str(raw),
                 "--out-dir", str(out_dir), "--version", "20260927",
                 "--summary-chars", "200"],
                check=True, capture_output=True, text=True,
            )
            sum_out = out_dir / "PPLX-PATENTS_摘要.md"
            self.assertTrue(sum_out.is_file())
            body = sum_out.read_text(encoding="utf-8")
            self.assertIn("结论摘要", body)
            # 摘要应短于全文
            full_out = out_dir / "PPLX-PATENTS_新颖性创造性评估.md"
            self.assertLess(sum_out.stat().st_size, full_out.stat().st_size)

    def test_extract_summary_fallback_to_tail(self) -> None:
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
        from wrap_eval import extract_summary  # noqa: PLC0415
        raw = "段落一\n\n段落二\n\n段落三\n\n段落四"
        s = extract_summary(raw, chars=100)
        # 无结构标记时应返回末尾段落片段
        self.assertTrue(len(s) > 0)
        self.assertIn("段落", s)


if __name__ == "__main__":
    unittest.main()
