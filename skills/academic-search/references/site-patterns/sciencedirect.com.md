---
domain: sciencedirect.com
aliases: [ScienceDirect, Elsevier]
updated: 2026-05-01
---

## Platform Characteristics

- Elsevier publisher platform.
- Article landing pages may be public, but PDFs often require institutional entitlement.
- Some open-access articles expose a PDF link, but closed articles should be marked `needs_institution`.

## Effective Pattern

1. Resolve DOI to the article page.
2. Check metadata and open-access labels.
3. Prefer Unpaywall before attempting publisher PDF routes.
4. If a PDF URL returns HTML, login, or entitlement pages, set `full_text_status=html_not_pdf` or `needs_institution`.

## Known Traps

- HTTP 403 or redirected login pages are access restrictions, not retryable download failures.
- A visible article abstract does not imply PDF access.
- Do not use third-party paywall bypass services.

## Observed 2026-10-09 — one open-access article, not a platform guarantee

- DOI `10.1016/j.apenergy.2022.120493`: normal Chrome initially showed abstract-only content; a later DOM observation showed main sections, tables and figures without sign-in. Inspect the actual loaded state before classifying full-text coverage.
- Publisher/repository aria2 attempts failed. Chrome `content.export()` was unsupported; normal `downloadMedia()` returned without an error, but no matching or recent local PDF was verified. Do not equate a successful UI call with successful acquisition, a file hash, or PDF preflight PASS.
- Repository discovery metadata can disagree with its PDF cover and embedded body. Preserve those version/identity conflicts; DOI equality alone does not settle them. Captchas were not solved, signed asset URLs were not retained, and access controls were not bypassed.

## Observed 2026-10-09 — native objects on the same OA full HTML

- The supported CUA `pageAssets` inventory/bundle successfully retained 17 already-observed public JPEG objects for `S0306261922017500`: 16 numbered figures and one Algorithm 1 image. All were subsequently viewed and copied with SHA-256 bindings. This is not a PDF download, a complete HTML byte archive, or a high-resolution page/layout certificate.
- Native tables are `div` objects (`tbl1`–`tbl9`, `tblA.10`), not `table[id]`; counting only HTML table tags would incorrectly report none. The appendix table was nested in the rendered architecture section but counted once by its actual label.
- Numbered formula `fd5` holds only the latter lines of Eq. 5. The initial lines are visible immediately before that span in `sec2.3.2`; read the whole displayed group rather than treating a selector's fragment as the complete formula. Ten footnote texts were visible in the parent paragraphs of their `#bfnN` backlinks despite missing `fnN` element ids.
- An explicitly declared source-format amendment can support a selected semantic consultation on the lawful full HTML and actual objects. It must retain the failed PDF history, remote text/byte-archive limitation, conflicts, and unverified algebra/reference/reproduction scope. It must not lower the requested final manuscript PDF/LaTeX verification gates or imply a journal population calibration.

## Observed 2026-10-09 — additional planning article, partial read only

- DOI `10.1016/j.apenergy.2022.119942` displayed the CC-BY 4.0 label in normal Chrome. Its initial snapshot was abstract-only; later DOM inspection exposed sections 1–5, an appendix and native tables. Check the loaded state before declaring the source inaccessible. Eight native table contents and selected engineering/experimental sections were read; this was not complete semantic or figure coverage, a local PDF, or an archived full HTML file.
- The observed EPFL deposit link failed aria2 with HTTP 405. The Cardiff deposit for DOI `10.1016/j.apenergy.2024.123207` failed aria2 with HTTP 403, although the public landing page was readable. A normal browser download call and opening a blank PDF-reader iframe did not establish a local file. Preserve failed receipts; do not turn successful UI calls or public metadata into download/preflight PASS.
- Cardiff's landing-page “Accepted Post-Print Version” conflicted with OpenAlex's `submittedVersion`. Preserve both until actual file/version comparison; do not relabel the deposit as a publisher version of record by assumption.
