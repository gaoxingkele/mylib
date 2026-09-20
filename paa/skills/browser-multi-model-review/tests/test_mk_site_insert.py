# -*- coding: utf-8 -*-
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "mk_site_insert.py"
sys.path.insert(0, str(ROOT / "scripts"))
import mk_site_insert  # noqa: E402

PY = sys.executable


class MkSiteInsertTests(unittest.TestCase):
    def test_render_contains_inserttext_and_site_box(self) -> None:
        js = mk_site_insert.render_insert_js("仅评本案：P00-0。正文", "gemini")
        self.assertIn("insertText", js)
        self.assertIn("为 Gemini 输入提示", js)
        self.assertIn("仅评本案：P00-0", js)

    def test_cli_writes_insert_js_from_fulltext(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            batch = Path(tmp)
            (batch / "P00-0_fulltext.txt").write_text("仅评本案：P00-0。全文", encoding="utf-8")
            subprocess.run(
                [
                    PY,
                    str(SCRIPT),
                    "--batch-dir",
                    str(batch),
                    "--case",
                    "P00-0",
                    "--site",
                    "chatgpt",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            js = (batch / "insert_chatgpt.js").read_text(encoding="utf-8")
            self.assertIn("与 ChatGPT 聊天", js)
            self.assertIn("insertText", js)
            self.assertIn("P00-0", js)


if __name__ == "__main__":
    unittest.main()
