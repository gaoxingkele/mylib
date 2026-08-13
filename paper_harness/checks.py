"""Deterministic acceptance checks for academic-paper stages."""

from __future__ import annotations

import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

PLACEHOLDER_RE = re.compile(
    r"\bTODO\b|\bTBD\b|\bXXX\b|AUTHOR INPUT REQUIRED|author-email-required|"
    r"\[CORRESPONDING AUTHOR[^\]]*\]|\[FUND(?:ER|ING)[^\]]*\]",
    re.IGNORECASE,
)
LATEX_LOG_FAIL_RE = re.compile(
    r"(?:Citation|Reference).*(?:undefined)|There were undefined references|Fatal error|Emergency stop",
    re.IGNORECASE,
)
MOJIBAKE_RE = re.compile(r"(?:锛|鈥|绔|璁烘|鍥|鏂囩|閫|楠|妫€|�)")
CORE_SECTION_GROUPS = {
    "introduction": ("introduction", "background"),
    "method": ("method", "materials", "framework", "model", "approach", "formulation", "algorithm"),
    "results": ("result", "evaluation", "experiment"),
    "discussion": ("discussion", "interpretation"),
    "conclusion": ("conclusion",),
}
DEFAULT_DECLARATIONS = [
    "Funding",
    "Author Contributions",
    "Data Availability",
    "Conflicts of Interest",
    "Acknowledgments",
]
DECLARATION_ALIASES = {
    "funding": ("funding", "funding statement"),
    "author contributions": ("author contributions", "credit author statement"),
    "data availability": ("data availability", "availability of data and materials"),
    "conflicts of interest": ("conflicts of interest", "conflict of interest"),
    "acknowledgments": ("acknowledgments", "acknowledgment"),
}


def _result(name: str, status: str, detail: str = "") -> dict:
    return {"name": name, "status": status, "detail": detail}


def _manuscript(workdir: str | Path, config: dict) -> Path:
    return Path(workdir) / config.get("manuscript", "main.tex")


def _plain_tex(text: str) -> str:
    text = re.sub(r"(?<!\\)%.*", " ", text)
    text = re.sub(r"\\(?:cite|ref|label|url|href)\*?(?:\[[^\]]*\])?\{[^{}]*\}", " ", text)
    text = re.sub(r"\\[A-Za-z@]+\*?(?:\[[^\]]*\])?", " ", text)
    text = re.sub(r"[{}$\\]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _balanced_argument(text: str, command: str) -> str | None:
    """Extract a brace-balanced command argument, allowing nested TeX commands."""
    candidates: list[str] = []
    for match in re.finditer(r"\\" + re.escape(command) + r"\s*\{", text, re.IGNORECASE):
        start = match.end()
        depth = 1
        escaped = False
        for index in range(start, len(text)):
            char = text[index]
            if escaped:
                escaped = False
                continue
            if char == "\\":
                escaped = True
                continue
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    candidates.append(text[start:index])
                    break
    return max(candidates, key=len) if candidates else None


def check_latex_build(workdir: str | Path, config: dict) -> dict:
    """Compile from the manuscript directory and reject unresolved citations/references."""
    name = "latex_build"
    tex = _manuscript(workdir, config)
    if not tex.exists():
        return _result(name, "fail", f"manuscript not found: {tex}")
    engine = str(config.get("latex_engine", "pdflatex"))
    if shutil.which(engine) is None:
        return _result(name, "skip", f"{engine} not found; LaTeX build skipped")
    tex_dir, stem = tex.parent, tex.stem
    log_lines: list[str] = []

    def run(argv: list[str]) -> int:
        try:
            proc = subprocess.run(
                argv,
                cwd=str(tex_dir),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=600,
            )
        except subprocess.TimeoutExpired:
            log_lines.append(f"TIMEOUT: {' '.join(argv)}")
            return 124
        log_lines.append(f"$ {' '.join(argv)} -> exit {proc.returncode}")
        return proc.returncode

    latex_argv = [engine, "-interaction=nonstopmode", "-halt-on-error", tex.name]
    rc = run(latex_argv)
    if rc == 0:
        aux = tex.with_suffix(".aux")
        aux_text = aux.read_text(encoding="utf-8", errors="replace") if aux.exists() else ""
        if "\\bibdata" in aux_text and shutil.which("bibtex"):
            run(["bibtex", stem])
        elif tex.with_suffix(".bcf").exists() and shutil.which("biber"):
            run(["biber", stem])
        rc = run(latex_argv)
    if rc == 0:
        rc = run(latex_argv)
    if rc != 0:
        return _result(name, "fail", f"LaTeX exited with {rc}\n" + "\n".join(log_lines))
    log_file = tex.with_suffix(".log")
    if log_file.exists():
        bad = [
            line.strip()
            for line in log_file.read_text(encoding="utf-8", errors="replace").splitlines()
            if LATEX_LOG_FAIL_RE.search(line)
        ]
        if bad:
            return _result(name, "fail", "unresolved LaTeX diagnostics:\n" + "\n".join(bad[:30]))
    pdf = tex.with_suffix(".pdf")
    if not pdf.exists() or pdf.stat().st_size < 1024:
        return _result(name, "fail", f"compiled PDF missing or too small: {pdf}")
    return _result(name, "pass", f"compiled {pdf.name} from {tex_dir}; no unresolved citation/reference diagnostics")


def _placeholder_sources(workdir: Path, config: dict) -> list[Path]:
    manuscript = _manuscript(workdir, config)
    sources = [manuscript] if manuscript.exists() else []
    for pattern in config.get("placeholder_globs", []):
        sources.extend(path for path in workdir.glob(pattern) if path.is_file())
    return sorted(set(sources))


def check_no_placeholders(workdir: str | Path, config: dict) -> dict:
    name = "no_placeholders"
    workdir = Path(workdir)
    sources = _placeholder_sources(workdir, config)
    if not sources:
        return _result(name, "fail", f"manuscript not found: {_manuscript(workdir, config)}")
    hits: list[str] = []
    for source in sources:
        for line_no, line in enumerate(source.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
            if PLACEHOLDER_RE.search(line):
                hits.append(f"{source.relative_to(workdir)}:{line_no}: {line.strip()[:160]}")
    if hits:
        return _result(name, "fail", f"found {len(hits)} unresolved placeholders:\n" + "\n".join(hits[:40]))
    return _result(name, "pass", f"no unresolved author/funding/TODO placeholders in {len(sources)} source file(s)")


def check_declarations(workdir: str | Path, config: dict) -> dict:
    name = "declarations"
    manuscript = _manuscript(workdir, config)
    if not manuscript.exists():
        return _result(name, "fail", f"manuscript not found: {manuscript}")
    required = config.get("declarations")
    if not required:
        if config.get("journal") == "ieee_access":
            required = ["Funding", "Data Availability", "Acknowledgments"]
        else:
            required = DEFAULT_DECLARATIONS
    text = manuscript.read_text(encoding="utf-8", errors="replace").lower()
    missing: list[str] = []
    for item in required:
        aliases = DECLARATION_ALIASES.get(str(item).lower(), (str(item).lower(),))
        if not any(alias in text for alias in aliases):
            missing.append(str(item))
    if missing:
        return _result(name, "fail", "missing required declarations: " + ", ".join(missing))
    return _result(name, "pass", f"all {len(required)} configured declaration groups are present")


def check_narrative_structure(workdir: str | Path, config: dict) -> dict:
    name = "narrative_structure"
    manuscript = _manuscript(workdir, config)
    if not manuscript.exists():
        return _result(name, "fail", f"manuscript not found: {manuscript}")
    raw = manuscript.read_text(encoding="utf-8", errors="replace")
    section_names = [s.lower() for s in re.findall(r"\\(?:sub)*section\*?\{([^{}]+)\}", raw)]
    missing = [
        group
        for group, aliases in CORE_SECTION_GROUPS.items()
        if not any(any(alias in section for alias in aliases) for section in section_names)
    ]
    if missing:
        return _result(name, "fail", "missing core narrative sections: " + ", ".join(missing))
    abstract_match = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", raw, re.DOTALL | re.IGNORECASE)
    abstract_text = abstract_match.group(1) if abstract_match else _balanced_argument(raw, "abstract")
    if abstract_text is None:
        return _result(name, "fail", "abstract not detected")
    abstract_words = len(re.findall(r"\b[A-Za-z][A-Za-z0-9'-]*\b", _plain_tex(abstract_text)))
    venue = str(config.get("journal", ""))
    default_limit = 250 if venue == "ieee_access" else 220
    limit = int(config.get("abstract_word_limit", default_limit))
    if abstract_words > limit:
        return _result(name, "fail", f"abstract has {abstract_words} words; configured limit is {limit}")
    return _result(name, "pass", f"core narrative sections present; abstract={abstract_words} words (limit {limit})")


def _resolve_graphic(tex_dir: Path, reference: str) -> Path | None:
    if "\\" in reference or "#" in reference:
        return None
    candidate = tex_dir / reference
    if candidate.exists():
        return candidate
    if candidate.suffix:
        return None
    for ext in (".pdf", ".png", ".jpg", ".jpeg", ".eps", ".svg"):
        with_ext = candidate.with_suffix(ext)
        if with_ext.exists():
            return with_ext
    return None


def check_artifact_consistency(workdir: str | Path, config: dict) -> dict:
    name = "artifact_consistency"
    manuscript = _manuscript(workdir, config)
    if not manuscript.exists():
        return _result(name, "fail", f"manuscript not found: {manuscript}")
    raw = manuscript.read_text(encoding="utf-8", errors="replace")
    refs = re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^{}]+)\}", raw)
    refs += re.findall(r"\\includesvg(?:\[[^\]]*\])?\{([^{}]+)\}", raw)
    missing = [ref for ref in refs if _resolve_graphic(manuscript.parent, ref) is None and "\\" not in ref]
    if missing:
        return _result(name, "fail", "missing referenced graphics: " + ", ".join(missing[:30]))
    labels = re.findall(r"\\label\{([^{}]+)\}", raw)
    duplicate_labels = sorted({label for label in labels if labels.count(label) > 1})
    if duplicate_labels:
        return _result(name, "fail", "duplicate LaTeX labels: " + ", ".join(duplicate_labels[:30]))
    return _result(name, "pass", f"resolved {len(refs)} graphic reference(s); {len(labels)} labels are unique")


def check_pdf_integrity(workdir: str | Path, config: dict) -> dict:
    name = "pdf_integrity"
    manuscript = _manuscript(workdir, config)
    pdf = manuscript.with_suffix(".pdf")
    if not pdf.exists() or pdf.stat().st_size < 1024:
        return _result(name, "fail", f"PDF missing or too small: {pdf}")
    page_count: int | None = None
    if shutil.which("pdfinfo"):
        proc = subprocess.run(
            ["pdfinfo", str(pdf)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60
        )
        match = re.search(r"^Pages:\s+(\d+)", proc.stdout or "", re.MULTILINE)
        if match:
            page_count = int(match.group(1))
    if shutil.which("pdftotext"):
        proc = subprocess.run(
            ["pdftotext", "-layout", str(pdf), "-"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
        text = proc.stdout or ""
        if len(re.sub(r"\s+", "", text)) < 200:
            return _result(name, "fail", "PDF contains too little extractable text")
        if PLACEHOLDER_RE.search(text):
            return _result(name, "fail", "compiled PDF still contains author/funding/TODO placeholders")
        pages = text.split("\f")
        sparse = [i + 1 for i, page in enumerate(pages) if page.strip() and len(re.findall(r"\w+", page)) < 12]
        detail = f"; sparse-page warning={sparse}" if sparse else ""
    else:
        detail = "; pdftotext unavailable"
    return _result(name, "pass", f"PDF size={pdf.stat().st_size} bytes, pages={page_count or 'unknown'}{detail}")


def check_manuscript_hygiene(workdir: str | Path, config: dict) -> dict:
    name = "manuscript_hygiene"
    manuscript = _manuscript(workdir, config)
    if not manuscript.exists():
        return _result(name, "fail", f"manuscript not found: {manuscript}")
    raw = manuscript.read_text(encoding="utf-8", errors="replace")
    if MOJIBAKE_RE.search(raw):
        match = MOJIBAKE_RE.search(raw)
        return _result(name, "fail", f"possible mojibake near character {match.start() if match else '?'}")
    meta_phrases = [
        "for editors and reviewers",
        "rather than presenting a licence table",
        "scope conditions are revisited once",
    ]
    found = [phrase for phrase in meta_phrases if phrase in raw.lower()]
    if found:
        return _result(name, "fail", "submission-process meta-narrative remains: " + ", ".join(found))
    return _result(name, "pass", "no mojibake or known submission-process meta-narrative detected")


def check_custom(script: str, workdir: str | Path, config: dict) -> dict:
    name = f"custom:{script}"
    workdir = Path(workdir)
    try:
        parts = shlex.split(script, posix=False)
    except ValueError as exc:
        return _result(name, "fail", f"invalid custom command: {exc}")
    if not parts:
        return _result(name, "fail", "empty custom command")
    path = Path(parts[0].strip('"'))
    if not path.is_absolute():
        path = workdir / path
    if not path.exists():
        return _result(name, "fail", f"custom script not found: {path}")
    argv = ([sys.executable, str(path)] if path.suffix.lower() == ".py" else [str(path)]) + parts[1:]
    try:
        proc = subprocess.run(
            argv,
            cwd=str(workdir),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=1200,
        )
    except subprocess.TimeoutExpired:
        return _result(name, "fail", "custom script timed out (>1200 s)")
    if proc.returncode == 0:
        return _result(name, "pass", (proc.stdout or "").strip()[:1000])
    return _result(name, "fail", f"exit {proc.returncode}: {(proc.stderr or proc.stdout or '').strip()[:1000]}")


CHECKS = {
    "latex_build": check_latex_build,
    "no_placeholders": check_no_placeholders,
    "declarations": check_declarations,
    "narrative_structure": check_narrative_structure,
    "artifact_consistency": check_artifact_consistency,
    "pdf_integrity": check_pdf_integrity,
    "manuscript_hygiene": check_manuscript_hygiene,
}


def run_checks(check_names: list[str], workdir: str | Path, config: dict) -> list[dict]:
    results: list[dict] = []
    for name in check_names:
        if name in CHECKS:
            results.append(CHECKS[name](workdir, config))
        elif name.startswith("custom:"):
            results.append(check_custom(name[len("custom:") :], workdir, config))
        else:
            results.append(_result(name, "fail", f"unknown acceptance check: {name}"))
    return results


def all_ok(results: list[dict]) -> bool:
    """Skipped optional environmental checks do not fail a stage."""
    return all(result["status"] in ("pass", "skip") for result in results)
