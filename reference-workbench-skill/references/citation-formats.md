# Citation Format Reference by Venue

> Loaded with skill at startup. GB/T 7714-2015 is current (2025 version issued Dec 2025, effective Jul 2026 — not yet mandatory).

## General Principle: Sequential Numbering

All numbered citation systems (IEEE, Vancouver, GB/T 7714, EI, most SCI journals) follow the same core rule:

> **References are numbered in the order they first appear in the text. The reference list at the end mirrors this order. A source keeps the same number every time it is cited.**

## Citation Format Comparison by Venue

| Venue | In-Text Style | Multiple Cites | Reference List Order | Note |
|-------|--------------|----------------|---------------------|------|
| **IEEE** | `[1]` square brackets, inline on text line | `[1,3,5]` or `[1]-[3]` for consecutive | Sequential by appearance | Widely used in engineering, CS |
| **SCI (Vancouver)** | `[1]` or `(1)` depending on journal | `[1,2]` or `[1-3]` | Sequential by appearance | Common in biomedical/physical sciences |
| **SCI (Elsevier numeric)** | `[1]` square brackets | `[1,2,5]` or `[1-3]` | Sequential by appearance | Most Elsevier journals |
| **EI Journal** | `[1]` square brackets, sequential | `[1,2]` or `[1-3]` | Sequential by appearance | 4-8 references minimum recommended |
| **Chinese Thesis (GB/T 7714)** | `[1]` square brackets, or superscript `¹` | `[1,2]` or `[1-3]` for consecutive | **Sequential by appearance** (顺序编码制) | See detailed rules below |
| **APA 7th** | `(Author, Year)` parenthetical | `(Smith, 2020; Jones, 2021)` | **Alphabetical by author** | Not a numbered system; not recommended for theses |
| **MLA 9th** | `(Author Page)` | — | Alphabetical | Humanities |
| **Chicago** | Footnotes or author-date | — | Alphabetical (author-date) or by footnote order | History, arts |
| **ACM** | `[1]` square brackets | `[1,2]` | Sequential by appearance | Computing |

## IEEE Detailed Rules

- In-text: Bracketed numbers `[1]`, inline (not superscript), before punctuation, space before bracket: `...as shown in [1].`
- Reference list: Numbered `[1]`, `[2]`, `[3]`... in order of first appearance
- Author format: Initials + Last name (e.g., `J. Smith`). Up to 6 authors listed, then `et al.`
- Journal article: `[#] A. Author, "Title," *Journal Abbrev.*, vol. X, no. Y, pp. Z, Year.`
- Conference: `[#] A. Author, "Title," in *Proc. Conf. Name*, City, Year, pp. X-Y.`
- Same source reused: use the original number. Do NOT renumber.

## SCI / Vancouver Detailed Rules

- In-text: Numbers in `[1]` brackets or `(1)` parentheses. Check journal Guide for Authors.
- Sequential numbering by first appearance.
- Author format: Last name + Initials. Up to 6 authors, then `et al.`
- Journal titles abbreviated per Index Medicus / NLM.
- Journal article: `[#] Author AB, Author CD. Title. *J Abbrev.* Year;Vol(Issue):Pages.`
- Some Elsevier journals use "numeric, with titles" style — includes article titles in the reference.

## EI Journal Detailed Rules

- In-text: `[1]`, `[2]`, `[3]` square brackets, sequential. NOT author-year, NOT footnotes/endnotes.
- Reference list: sequential numbering matching text order.
- Minimum 4-8 references recommended.
- Journal: `[#] Author, "Title," *Journal Name*, vol. X, no. Y, pp. Z, Year.`
- Conference: `[#] Author, "Title," *Conference Name*, pp. X-Y, Date.`
- Book: `[#] Author, *Title*, Edition. City: Publisher, Year, pp. X-Y.`
- EI收录的中文期刊：优先使用英文题名著录。

## Chinese Thesis (GB/T 7714-2015) Detailed Rules

Chinese academic theses follow the national standard **GB/T 7714-2015** (现行有效, 2025年仍适用).

**Two systems exist**:
1. **顺序编码制 (Sequential Numbering)** — Most common for theses. Citations numbered `[1]`, `[2]`, `[3]` in order of first appearance.
2. **著者-出版年制 (Author-Year)** — Less common. Uses `(Author, Year)` format.

**For theses using 顺序编码制**:

- **In-text citation placement**:
  - 右上角标形式 (superscript): `...已有研究¹表明...`
  - 正文行内方括号: `...已有研究[1]表明...`
  - 引用连续文献: `[1-3]` (consecutive numbers joined by hyphen)
  - 引用不连续文献: `[1,3,5]` (non-consecutive numbers separated by comma)
  - 同时引用连续和不连续: `[1-3,5]`

- **Reference list format** (sequential order matching text):

| 文献类型 | 格式 |
|----------|------|
| 期刊 [J] | `[序号] 作者. 题名[J]. 刊名, 年, 卷(期): 起止页码.` |
| 专著 [M] | `[序号] 作者. 书名[M]. 出版地: 出版社, 年: 页码.` |
| 会议 [C] | `[序号] 作者. 题名[C]. 会议名, 地点, 年: 页码.` |
| 学位论文 [D] | `[序号] 作者. 题名[D]. 学校所在地: 学校, 年.` |
| 专利 [P] | `[序号] 专利权人. 专利名[P]. 专利号, 日期.` |
| 电子资源 [EB/OL] | `[序号] 作者. 题名[EB/OL]. [引用日期]. URL.` |

- **Author formatting**: 3 authors or fewer → list all. More than 3 → list first 3 + "等" (or "et al." for English).
- **English author names**: Last name first, initials after. Example: `Smith J, Jones A B, Lee C, et al.`
- **Bilingual references**: If required, cite in original language first, then in translation.

## APA 7th (Author-Year) — For Reference

APA is NOT a numbered system. References are alphabetical by author last name. Only use APA if:
- The user explicitly requests it
- The target journal requires APA
- The user is in psychology, social sciences, education

**In-text**: `(Smith, 2020)` or `Smith (2020)`
**Reference list**: Alphabetical by author, not numbered.
**Multiple citations**: `(Smith, 2020; Jones, 2021)` — alphabetical, separated by semicolons.

## Determining Which Format to Use

Ask the user (or infer from context):

| User says | Apply |
|-----------|-------|
| "学位论文" / "毕业论文" / "硕士论文" / "博士论文" | GB/T 7714 顺序编码制 |
| "IEEE 期刊" / "IEEE 会议" | IEEE |
| "SCI 期刊" / "Elsevier" / "Springer" | Vancouver / Elsevier numeric |
| "EI 期刊" / "EI 会议" | EI sequential numbering |
| "APA" / "心理学期刊" | APA 7th |
| "BibTeX" / "LaTeX" | BibTeX |
