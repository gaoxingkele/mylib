# -*- coding: utf-8 -*-
"""Write insert_<site>.js that insertText-s a case fulltext into a composer."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

BOXES = {
    "gemini": "page.getByRole('textbox', { name: '为 Gemini 输入提示' })",
    "chatgpt": "page.getByRole('textbox', { name: '与 ChatGPT 聊天' })",
    "grok": "page.getByRole('textbox', { name: 'Ask Grok anything' })",
    "pplx": "page.locator('[contenteditable=\"true\"]').last()",
}


def render_insert_js(text: str, site: str) -> str:
    box = BOXES[site]
    return (
        "async (page) => {\n"
        f"  const text = {json.dumps(text, ensure_ascii=False)};\n"
        f"  const box = {box};\n"
        "  await box.click({ force: true });\n"
        "  await page.keyboard.insertText(text);\n"
        "  await page.waitForTimeout(400);\n"
        "  const shown = await box.innerText().catch(async () => '');\n"
        "  return { fileLen: text.length, shownLen: String(shown||'').length, "
        "head: String(shown||'').slice(0, 50) };\n"
        "}\n"
    )


def write_insert_js(batch_dir: Path, case_id: str, site: str) -> Path:
    if site not in BOXES:
        raise SystemExit(f"unknown site {site}; want {sorted(BOXES)}")
    text = (batch_dir / f"{case_id}_fulltext.txt").read_text(encoding="utf-8")
    out = batch_dir / f"insert_{site}.js"
    out.write_text(render_insert_js(text, site), encoding="utf-8")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch-dir", required=True)
    ap.add_argument("--case", required=True)
    ap.add_argument("--site", required=True, choices=sorted(BOXES))
    args = ap.parse_args()
    out = write_insert_js(Path(args.batch_dir), args.case, args.site)
    print(out, out.stat().st_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
