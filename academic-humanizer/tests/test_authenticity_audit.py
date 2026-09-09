import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "authenticity_audit.py"
SPEC = importlib.util.spec_from_file_location("authenticity_audit", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class AuthenticityAuditTests(unittest.TestCase):
    def write(self, directory: Path, name: str, text: str) -> Path:
        path = directory / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_audit_flags_signals_without_authorship_classification(self):
        with tempfile.TemporaryDirectory() as temp:
            path = self.write(
                Path(temp),
                "draft.md",
                "近年来，随着技术的快速发展，研究表明该方案显著提高效率。\n"
                "实施例记录字段类型、版本、时间戳和异常状态。",
            )
            result = MODULE.audit(path, "patent")
            self.assertIn("not an AI-authorship detector", result["disclaimer"])
            self.assertGreater(len(result["findings"]), 0)
            self.assertEqual(result["patent_evidence_anchors"]["字段"], 1)

    def test_compare_reports_protected_token_drift(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            original = self.write(directory, "original.md", "准确率为 91%，见表 2 和文献[3]。")
            revised = self.write(directory, "revised.md", "准确率较高，见表 3 和文献[3]。")
            result = MODULE.compare(original, revised, "paper")
            self.assertEqual(result["status"], "review_required")
            self.assertIn("91%", result["protected_tokens_removed"])
            self.assertIn("表2", result["protected_tokens_removed"])
            self.assertIn("表3", result["protected_tokens_added"])

    def test_compare_passes_when_protected_tokens_are_stable(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            original = self.write(directory, "original.md", "结果为 12 ms，见图 1。")
            revised = self.write(directory, "revised.md", "测得耗时为 12 ms，结果见图 1。")
            result = MODULE.compare(original, revised, "paper")
            self.assertEqual(result["status"], "token_check_passed")

    def test_audit_ignores_quoted_examples_and_code(self):
        with tempfile.TemporaryDirectory() as temp:
            path = self.write(
                Path(temp),
                "examples.md",
                "正文直接陈述。引用“研究表明显著提高效率”。`Moreover` 也是示例。",
            )
            result = MODULE.audit(path, "article")
            self.assertEqual(result["findings"], [])


if __name__ == "__main__":
    unittest.main()
