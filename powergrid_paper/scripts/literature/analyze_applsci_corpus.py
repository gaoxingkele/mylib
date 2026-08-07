#!/usr/bin/env python3
"""Extract reproducible structural statistics from an MDPI JATS/PDF corpus."""

from __future__ import annotations

import csv
import json
import re
import statistics
from pathlib import Path

from lxml import etree
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "papers/literature/applied_sciences_power_ai_10"
XML_DIR = CORPUS / "xml"
PDF_DIR = CORPUS / "pdf"
OUT_DIR = CORPUS / "analysis"
WORD_RE = re.compile(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*")


# Counts below are human-audited from captions and experimental sections.  They
# intentionally distinguish evidence plots/tables from method diagrams, which
# cannot be recovered reliably from the word "Figure" alone.
CURATED: dict[str, dict[str, object]] = {
    "applsci-13-11074": {
        "evaluation_datasets": 1, "method_framework_diagrams": 2,
        "experimental_result_figures": 0, "experimental_result_tables": 2,
        "dataset_note": "One self-constructed Guangxi grid-domain relation corpus (2316 samples).",
    },
    "applsci-13-12690": {
        "evaluation_datasets": 1, "method_framework_diagrams": 2,
        "experimental_result_figures": 12, "experimental_result_tables": 3,
        "dataset_note": "One integrated two-year feeder dataset; real smart-meter load plus PVGIS/SARAH2 irradiance, with PowerFactory labels.",
    },
    "applsci-14-06486": {
        "evaluation_datasets": 1, "method_framework_diagrams": 2,
        "experimental_result_figures": 3, "experimental_result_tables": 6,
        "dataset_note": "One planning case family based on IEEE RTS-24 and regional wind/PV/load histories.",
    },
    "applsci-14-10368": {
        "evaluation_datasets": 1, "method_framework_diagrams": 1,
        "experimental_result_figures": 4, "experimental_result_tables": 1,
        "dataset_note": "One emergency-dispatch case: IEEE 14-bus system under Typhoon Maria observations.",
    },
    "applsci-14-11797": {
        "evaluation_datasets": 1, "method_framework_diagrams": 1,
        "experimental_result_figures": 11, "experimental_result_tables": 0,
        "dataset_note": "One case family composed of three modified IEEE 33-bus distribution networks.",
    },
    "applsci-15-02435": {
        "evaluation_datasets": 3, "method_framework_diagrams": 4,
        "experimental_result_figures": 5, "experimental_result_tables": 3,
        "dataset_note": "Three public load datasets: Panama, Victoria daily demand/price, and household electric power consumption.",
    },
    "applsci-15-04498": {
        "evaluation_datasets": 3, "method_framework_diagrams": 4,
        "experimental_result_figures": 2, "experimental_result_tables": 1,
        "dataset_note": "Three UCP benchmark sets (50, 100, and 1080 units) generated from one year of real demand profiles.",
    },
    "applsci-15-07003": {
        "evaluation_datasets": 3, "method_framework_diagrams": 2,
        "experimental_result_figures": 17, "experimental_result_tables": 5,
        "dataset_note": "Three public forecasting datasets: ETTh1, ETTm1, and an Australian electricity-load dataset.",
    },
    "applsci-16-00466": {
        "evaluation_datasets": 1, "method_framework_diagrams": 4,
        "experimental_result_figures": 5, "experimental_result_tables": 2,
        "dataset_note": "One real wind-farm SCADA dataset (50,688 ten-minute samples, 2024).",
    },
    "applsci-16-04476": {
        "evaluation_datasets": 1, "method_framework_diagrams": 2,
        "experimental_result_figures": 15, "experimental_result_tables": 5,
        "dataset_note": "One generated DEL evaluation dataset, driven by 2015 measurements from one 48-turbine wind farm and OpenFAST/Simulink simulations.",
    },
}


def words(text: str) -> int:
    return len(WORD_RE.findall(text or ""))


def text_of(node: etree._Element | None) -> str:
    if node is None:
        return ""
    return re.sub(r"\s+", " ", " ".join(node.itertext())).strip()


def first(node: etree._Element, xpath: str) -> etree._Element | None:
    result = node.xpath(xpath)
    return result[0] if result else None


def tag_name(node: etree._Element) -> str:
    return etree.QName(node).localname


def direct_children(node: etree._Element, name: str) -> list[etree._Element]:
    return [child for child in node if tag_name(child) == name]


def figure_kind(caption: str) -> tuple[bool, bool]:
    low = caption.lower()
    framework_terms = (
        "framework", "architecture", "workflow", "flowchart", "flow chart",
        "schematic", "overall structure", "model structure", "system structure",
        "network structure", "methodology", "research process", "calculation process",
    )
    result_terms = (
        "result", "performance", "comparison", "forecast", "prediction", "error",
        "accuracy", "loss", "convergence", "sensitivity", "ablation", "curve",
        "profile", "distribution", "heatmap", "boxplot", "scatter", "pareto",
        "voltage", "power", "load", "cost", "frequency", "response", "dispatch",
    )
    return any(term in low for term in framework_terms), any(term in low for term in result_terms)


def section_role(title: str) -> str:
    low = re.sub(r"^\s*\d+(?:\.\d+)*\.?\s*", "", title.lower())
    if "introduction" in low:
        return "Introduction"
    if "related work" in low or "literature" in low:
        return "Related work"
    if "conclusion" in low:
        return "Conclusion"
    if low.startswith("discussion"):
        return "Discussion"
    if any(term in low for term in ("experiment", "case stud", "numerical", "simulation system and results", "analysis of experimental")):
        return "Experiments/results"
    if any(term in low for term in ("data", "creating loads", "quasi-dynamic")):
        return "Data/simulation setup"
    return "Method/model"


def summary(values: list[float]) -> dict[str, float]:
    quartiles = (
        statistics.quantiles(values, n=4, method="inclusive")
        if len(values) > 1 else [values[0], values[0], values[0]]
    )
    return {
        "mean": round(statistics.mean(values), 1),
        "median": round(statistics.median(values), 1),
        "q1": round(quartiles[0], 1),
        "q3": round(quartiles[2], 1),
        "min": round(min(values), 1),
        "max": round(max(values), 1),
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    papers: list[dict[str, object]] = []
    sections_out: list[dict[str, object]] = []
    figures_out: list[dict[str, object]] = []

    for xml_path in sorted(XML_DIR.glob("*.xml")):
        paper_id = xml_path.stem
        root = etree.parse(str(xml_path)).getroot()
        body = first(root, ".//*[local-name()='body']")
        if body is None:
            raise RuntimeError(f"missing body: {xml_path}")
        title = text_of(first(root, ".//*[local-name()='article-title']"))
        doi_node = first(root, ".//*[local-name()='article-id'][@pub-id-type='doi']")
        doi = text_of(doi_node)
        year_node = first(root, ".//*[local-name()='pub-date']/*[local-name()='year']")
        year = int(text_of(year_node)) if text_of(year_node).isdigit() else None
        abstract = first(root, ".//*[local-name()='abstract']")
        abstract_words = words(text_of(abstract))

        top_sections = direct_children(body, "sec")
        body_paragraphs = body.xpath(".//*[local-name()='p']")
        paragraph_lengths = [words(text_of(p)) for p in body_paragraphs if words(text_of(p))]
        body_words = sum(paragraph_lengths)

        for index, section in enumerate(top_sections, start=1):
            heading = text_of(first(section, "./*[local-name()='title']")) or f"Section {index}"
            paragraphs = section.xpath(".//*[local-name()='p']")
            lengths = [words(text_of(p)) for p in paragraphs if words(text_of(p))]
            nested_sections = section.xpath(".//*[local-name()='sec']")
            sections_out.append(
                {
                    "paper_id": paper_id,
                    "doi": doi,
                    "section_index": index,
                    "section_title": heading,
                    "section_role": section_role(heading),
                    "subsection_count": len(nested_sections),
                    "paragraph_count": len(lengths),
                    "word_count": sum(lengths),
                    "mean_words_per_paragraph": round(sum(lengths) / len(lengths), 1) if lengths else 0,
                    "min_words_per_paragraph": min(lengths, default=0),
                    "max_words_per_paragraph": max(lengths, default=0),
                }
            )

        # MDPI JATS places floated figures/tables in a root-level floats-group,
        # so count them across the article rather than only under <body>.
        figures = root.xpath(".//*[local-name()='fig']")
        for index, fig in enumerate(figures, start=1):
            label = text_of(first(fig, "./*[local-name()='label']")) or f"Figure {index}"
            caption = text_of(first(fig, "./*[local-name()='caption']"))
            framework_candidate, result_candidate = figure_kind(caption)
            figures_out.append(
                {
                    "paper_id": paper_id,
                    "doi": doi,
                    "figure_index": index,
                    "label": label,
                    "caption": caption,
                    "framework_candidate": int(framework_candidate),
                    "result_candidate": int(result_candidate),
                }
            )

        formulas = body.xpath(".//*[local-name()='disp-formula']")
        numbered_formulas = [
            f for f in formulas
            if text_of(first(f, "./*[local-name()='label']")) or f.get("id")
        ]
        tables = root.xpath(".//*[local-name()='table-wrap']")
        refs = root.xpath(".//*[local-name()='ref-list']//*[local-name()='ref']")
        pdf_path = PDF_DIR / f"{paper_id}.pdf"
        page_count = len(PdfReader(str(pdf_path)).pages)
        papers.append(
            {
                "paper_id": paper_id,
                "year": year,
                "doi": doi,
                "doi_url": f"https://doi.org/{doi}",
                "official_pdf_url": f"https://mdpi-res.com/d_attachment/applsci/{paper_id}/article_deploy/{paper_id}.pdf",
                "local_pdf": str(pdf_path.relative_to(ROOT)).replace("\\", "/"),
                "local_xml": str(xml_path.relative_to(ROOT)).replace("\\", "/"),
                "title": title,
                "pages": page_count,
                "abstract_words": abstract_words,
                "body_words": body_words,
                "top_level_sections": len(top_sections),
                "body_paragraphs": len(paragraph_lengths),
                "mean_words_per_paragraph": round(body_words / len(paragraph_lengths), 1) if paragraph_lengths else 0,
                "median_words_per_paragraph": round(statistics.median(paragraph_lengths), 1) if paragraph_lengths else 0,
                "display_formulas": len(formulas),
                "numbered_formulas": len(numbered_formulas),
                "figures": len(figures),
                "tables": len(tables),
                "references": len(refs),
                "auto_framework_figures": sum(figure_kind(text_of(first(f, "./*[local-name()='caption']")))[0] for f in figures),
                "auto_result_figures": sum(figure_kind(text_of(first(f, "./*[local-name()='caption']")))[1] for f in figures),
                **CURATED[paper_id],
                "experimental_evidence_visuals": (
                    int(CURATED[paper_id]["experimental_result_figures"])
                    + int(CURATED[paper_id]["experimental_result_tables"])
                ),
            }
        )

    def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
        if not rows:
            return
        with path.open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    write_csv(OUT_DIR / "paper_stats_raw.csv", papers)
    write_csv(OUT_DIR / "section_stats.csv", sections_out)
    write_csv(OUT_DIR / "figure_inventory.csv", figures_out)
    role_rows: list[dict[str, object]] = []
    for role in dict.fromkeys(row["section_role"] for row in sections_out):
        subset = [row for row in sections_out if row["section_role"] == role]
        per_paper: list[dict[str, float]] = []
        for paper_id in dict.fromkeys(str(row["paper_id"]) for row in subset):
            items = [row for row in subset if row["paper_id"] == paper_id]
            paragraph_count = sum(float(row["paragraph_count"]) for row in items)
            word_count = sum(float(row["word_count"]) for row in items)
            per_paper.append(
                {
                    "paragraph_count": paragraph_count,
                    "word_count": word_count,
                    "mean_words_per_paragraph": word_count / paragraph_count if paragraph_count else 0,
                }
            )
        role_rows.append(
            {
                "section_role": role,
                "section_instances": len(subset),
                "papers_represented": len(per_paper),
                "median_paragraphs_per_paper": summary([row["paragraph_count"] for row in per_paper])["median"],
                "q1_paragraphs_per_paper": summary([row["paragraph_count"] for row in per_paper])["q1"],
                "q3_paragraphs_per_paper": summary([row["paragraph_count"] for row in per_paper])["q3"],
                "median_words_per_paper": summary([row["word_count"] for row in per_paper])["median"],
                "median_words_per_paragraph": summary([row["mean_words_per_paragraph"] for row in per_paper])["median"],
            }
        )
    write_csv(OUT_DIR / "section_role_summary.csv", role_rows)
    (OUT_DIR / "paper_stats_raw.json").write_text(json.dumps(papers, indent=2), encoding="utf-8")
    numeric_fields = (
        "pages", "abstract_words", "body_words", "top_level_sections",
        "body_paragraphs", "median_words_per_paragraph", "numbered_formulas",
        "evaluation_datasets", "figures", "tables", "method_framework_diagrams",
        "experimental_result_figures", "experimental_result_tables",
        "experimental_evidence_visuals",
    )
    corpus_summary = {
        field: summary([float(paper[field]) for paper in papers])
        for field in numeric_fields
    }
    (OUT_DIR / "corpus_summary.json").write_text(
        json.dumps(corpus_summary, indent=2), encoding="utf-8"
    )
    print(json.dumps({"papers": len(papers), "sections": len(sections_out), "figures": len(figures_out)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
