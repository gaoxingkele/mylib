# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "prepare_case.py"
PROMPT = ROOT / "prompts" / "six_section_review.zh.txt"
PY = sys.executable


def _write_src(src: Path) -> None:
    src.mkdir(parents=True)
    (src / "05_说明书摘要.md").write_text("# 摘要\nCASE-ID-TOKEN\n", encoding="utf-8")
    (src / "02_权利要求书.md").write_text("# 权\n独权1因果链\n", encoding="utf-8")
    (src / "04_附图清单与描述.md").write_text("# 图\n图1\n", encoding="utf-8")
    (src / "03_说明书.md").write_text("# 说明书\n实施例\n", encoding="utf-8")


class PrepareCaseTests(unittest.TestCase):
    def test_cli_writes_batch_with_case_id_and_six_section_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            out = Path(tmp) / "batch"
            _write_src(src)
            proc = subprocess.run(
                [
                    PY,
                    str(SCRIPT),
                    "--case",
                    "P00-0",
                    "--title",
                    "一种示例方法及系统",
                    "--short",
                    "示例简写",
                    "--version",
                    "20260918",
                    "--src",
                    str(src),
                    "--out",
                    str(out),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("full_chars", proc.stdout)
            full = (out / "P00-0_fulltext.txt").read_text(encoding="utf-8")
            ask = (out / "P00-0_ask_with_file.txt").read_text(encoding="utf-8")
            title = (out / "P00-0_thread_title.txt").read_text(encoding="utf-8")
            prompt = PROMPT.read_text(encoding="utf-8")
            self.assertIn("仅评本案：P00-0", full)
            self.assertIn("CASE-ID-TOKEN", full)
            self.assertIn("独权1因果链", full)
            self.assertIn(prompt.strip().splitlines()[0], full)
            self.assertIn("第22条第2款", full)
            self.assertIn("P00-0", ask)
            self.assertEqual(title.strip(), "P00-0 示例简写")
            self.assertGreater(int(proc.stdout.strip().split()[-1]), 0)

    def test_cases_json_fills_meta(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            out = Path(tmp) / "batch"
            _write_src(src)
            cases = Path(tmp) / "cases.json"
            cases.write_text(
                json.dumps(
                    {
                        "queue": [
                            {
                                "id": "P00-0",
                                "short": "示例简写",
                                "title": "一种示例方法及系统",
                                "source_version": "20260918",
                            }
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            subprocess.run(
                [
                    PY,
                    str(SCRIPT),
                    "--case",
                    "P00-0",
                    "--cases-json",
                    str(cases),
                    "--src",
                    str(src),
                    "--out",
                    str(out),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            full = (out / "P00-0_fulltext.txt").read_text(encoding="utf-8")
            self.assertIn("一种示例方法及系统", full)
            self.assertIn("版本：20260918", full)


if __name__ == "__main__":
    unittest.main()
