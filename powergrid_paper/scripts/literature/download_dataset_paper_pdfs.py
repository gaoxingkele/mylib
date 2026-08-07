"""Resume open PDF downloads for dataset benchmark paper candidates."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from search_dataset_benchmark_papers import (
    OUT_ROOT,
    ROOT,
    find_pdf_from_landing,
    http_bytes,
    safe_name,
)


CSV_PATH = OUT_ROOT / "metadata" / "dataset_paper_candidates.csv"
PDF_ROOT = OUT_ROOT / "pdfs"
DOWNLOAD_LOG = OUT_ROOT / "metadata" / "download_log.csv"


def candidate_urls(row: dict[str, str]) -> list[str]:
    urls: list[str] = []
    for key in ["pdf_source_url", "oa_url", "landing_page"]:
        url = row.get(key, "").strip()
        if url and url not in urls:
            urls.append(url)
    doi = row.get("doi", "")
    if "arxiv.org/abs/" in doi and doi not in urls:
        urls.append(doi.replace("/abs/", "/pdf/"))
    return urls


def existing_pdf_for(row: dict[str, str]) -> str:
    dataset_id = row["dataset_id"]
    title_prefix = safe_name(row["title"], 60)
    dataset_dir = PDF_ROOT / dataset_id
    if not dataset_dir.exists():
        return ""
    matches = sorted(dataset_dir.glob(f"{dataset_id}__{title_prefix}*.pdf"))
    if matches:
        return str(matches[0].relative_to(ROOT)).replace("\\", "/")
    return ""


def download_row(row: dict[str, str]) -> tuple[str, str]:
    existing = row.get("pdf_path") or existing_pdf_for(row)
    if existing:
        return existing, row.get("pdf_source_url", "")
    if row.get("is_oa") != "true":
        return "", ""

    dataset_id = row["dataset_id"]
    out_dir = PDF_ROOT / dataset_id
    out_dir.mkdir(parents=True, exist_ok=True)
    for url in candidate_urls(row):
        pdf_url = find_pdf_from_landing(url)
        if not pdf_url:
            continue
        try:
            data, content_type = http_bytes(pdf_url, timeout=90, retries=2)
        except Exception:
            continue
        if data[:4] != b"%PDF" and "pdf" not in content_type.lower():
            continue
        import hashlib

        digest = hashlib.sha1(pdf_url.encode("utf-8")).hexdigest()[:10]
        title = safe_name(row["title"], 90)
        path = out_dir / f"{dataset_id}__{title}__{digest}.pdf"
        path.write_bytes(data)
        return str(path.relative_to(ROOT)).replace("\\", "/"), pdf_url
    return "", ""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-attempts", type=int, default=0, help="0 means all rows")
    args = parser.parse_args()

    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    fields = list(rows[0].keys()) if rows else []
    attempts = 0
    downloaded = 0
    for row in rows:
        if row.get("pdf_path"):
            continue
        if row.get("is_oa") != "true":
            continue
        if args.max_attempts and attempts >= args.max_attempts:
            break
        attempts += 1
        safe_title = row["title"][:80].encode("ascii", errors="replace").decode("ascii")
        print(f"download attempt {attempts}: {row['dataset_id']} | {safe_title}")
        path, source = download_row(row)
        if path:
            row["pdf_path"] = path
            row["pdf_source_url"] = source
            downloaded += 1

    with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    log_rows = [
        {
            "dataset_id": row["dataset_id"],
            "title": row["title"],
            "pdf_path": row["pdf_path"],
            "pdf_source_url": row["pdf_source_url"],
        }
        for row in rows
        if row.get("pdf_path")
    ]
    with DOWNLOAD_LOG.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["dataset_id", "title", "pdf_path", "pdf_source_url"])
        writer.writeheader()
        writer.writerows(log_rows)

    print(f"attempted: {attempts}")
    print(f"new_downloaded_or_matched: {downloaded}")
    print(f"total_pdf_rows: {len(log_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
