# Target-journal LaTeX templates

Downloaded from the publishers' current author pages on 2026-07-23. Original
archives are preserved unchanged under each `official/` directory; `extracted/`
contains the corresponding unpacked files.

## Template inventory

| Target | Official archive | Publisher source | Key files | SHA-256 |
|---|---|---|---|---|
| IEEE Access | `ieee-access/official/ACCESS_latex_template_2026-05-13.zip` | [IEEE Access: Preparing Your Article](https://ieeeaccess.ieee.org/authors/preparing-your-article/) ([direct ZIP](https://ieeeaccess.ieee.org/wp-content/uploads/2026/05/ACCESS_latex_template_20260513-1-1.zip)) | `access.tex`, `ieeeaccess.cls`, `IEEEtran.bst` | `60C7EFC9DB8AC9E8BDB31C550AD4E03CB6F258A878ECECC0BC690B6203E45A67` |
| MDPI ACS numbered style | `mdpi-acs/official/MDPI_template_ACS_2026-06-23.zip` | [MDPI: Preparing Manuscripts in LaTeX](https://www.mdpi.com/authors/latex) ([direct ZIP](https://mdpi-res.com/data/MDPI_template_ACS.zip)) | `template.tex`, `Definitions/mdpi.cls`, `Definitions/mdpi.bst` | `BAF827D7D2048A69142232CB422CFB74865ADAE70BFF3EAC9F821C6DAD823568` |
| Computers, Materials & Continua (CMC) | `cmc/official/TSP_template_2026-01-19.zip` | [CMC: Instructions for Authors](https://www.techscience.com/cmc/info/auth_instru) ([direct ZIP](https://www.techscience.com/files/template/TSP_template.zip)) | `TSP_template.tex`, `Definitions/tsp.cls`, `Definitions/vancouver.bst` | `DBEDA234E419D7EB87C24A3B2D27A6A0A784DA66CFEA108DFD027E196D553D3F` |

The downloaded MDPI class identifies itself as
`\ProvidesClass{Definitions/mdpi}[23/06/2026 MDPI paper class]` and explicitly
supports the `energies`, `electronics`, and `applsci` journal options. The CMC
package identifies its class as dated 2026-01-05 and includes the `cmc` option.

## Manuscript mapping

| Manuscript | Presubmission journal | Template |
|---|---|---|
| `mintou_p1_dstar_gru_dispatch` | IEEE Access | `ieee-access/official/extracted/ACCESS_latex_template_20260513/` |
| `mintou_p2_hygraph_load_forecasting` | Electronics | `mdpi-acs/official/extracted/` with journal option `electronics` |
| `mintou_p3_samode_distribution_planning` | Energies | `mdpi-acs/official/extracted/` with journal option `energies` |
| `mintou_p4_shield_resilience_planning` | Energies | `mdpi-acs/official/extracted/` with journal option `energies` |
| `mintou_p5_trace_moea_feasibility_review` | Energies | `mdpi-acs/official/extracted/` with journal option `energies` |
| `mintou_p6_bilonsga_project_review` | Applied Sciences | `mdpi-acs/official/extracted/` with journal option `applsci` |
| `2026_ma_sqlgrid_cmc` | CMC | `cmc/official/extracted/` with journal option `cmc` |
| `2026_c2ges_engineeringletters` | CMC | `cmc/official/extracted/` with journal option `cmc` |

## Validation performed

- All three downloads returned ZIP content and opened successfully.
- Archive inventories contain 56 files (IEEE Access), 12 files (MDPI), and
  12 files (CMC).
- The class, example manuscript, and bibliography-style files listed above
  are present after extraction.
- A TeX engine is not installed on the current PATH, so this check validates
  archive integrity and required source files but does not compile the untouched
  publisher examples.
