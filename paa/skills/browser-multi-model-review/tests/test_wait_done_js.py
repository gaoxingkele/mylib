# -*- coding: utf-8 -*-
from __future__ import annotations

import unittest
from pathlib import Path

JS = Path(__file__).resolve().parents[1] / "scripts" / "js" / "wait_done.js"


class WaitDoneJsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.src = JS.read_text(encoding="utf-8")

    def test_is_run_code_function(self) -> None:
        self.assertTrue(self.src.lstrip().startswith("async (page) =>"))

    def test_bounded_and_returns_small_status(self) -> None:
        self.assertIn("MAX_MS", self.src)
        for key in ("done:", "reason:", "elapsedSec:", "len:"):
            self.assertIn(key, self.src)

    def test_never_returns_page_text(self) -> None:
        # 只回传长度，不回传正文
        self.assertNotIn("text:", self.src)
        self.assertNotIn("snapshot", self.src)

    def test_knows_all_five_sites(self) -> None:
        for site in ("chatgpt", "gemini", "grok", "perplexity", "kimi"):
            self.assertIn(site, self.src)


if __name__ == "__main__":
    unittest.main()
