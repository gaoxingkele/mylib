import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "deai.py"

ORIG = """# 说明书

> 备注行不计入。

[0001] 本发明所要解决的技术问题是：降低欠煮率。

[0002] 平均绝对相对误差由 5.97% 降至 2.34%，结果见 [0001]；此外，比值标准差为 1.9%。
"""


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, encoding="utf-8")


def test_gate_pass_on_wording_only(tmp_path):
    a, b = tmp_path / "a.md", tmp_path / "b.md"
    a.write_text(ORIG, encoding="utf-8")
    b.write_text(ORIG.replace("此外，", "").replace("备注行不计入。", "备注行 v2.8 [0002] 改动。"), encoding="utf-8")
    r = run("gate", str(a), str(b), "--profile", "patent")
    assert r.returncode == 0, r.stdout


def test_gate_fail_on_number_and_noise(tmp_path):
    a, b = tmp_path / "a.md", tmp_path / "b.md"
    a.write_text(ORIG, encoding="utf-8")
    b.write_text(ORIG.replace("2.34%", "2.3%").replace("此外，", "说实话，"), encoding="utf-8")
    r = run("gate", str(a), str(b), "--profile", "patent")
    assert r.returncode == 1
    assert "受保护片段变化" in r.stdout and "禁用手段新增" in r.stdout


def test_statutory_phrase_not_flagged(tmp_path):
    a = tmp_path / "a.md"
    a.write_text(ORIG, encoding="utf-8")
    r = run("check", str(a), "--profile", "patent")
    assert "QSL-05" not in r.stdout
