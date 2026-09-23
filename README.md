# India's Digital Payments Capability Gap

An exploration of UPI capability among persons aged 15+, using the NSS 80th
Round Comprehensive Modular Survey: Telecom (January–March 2025). NPCI's
state-attributed transaction volumes are a separate, exploratory comparison.

## Website

[Open the local app](http://127.0.0.1:3000) · [Deployment instructions](docs/DEPLOYMENT.md)

Public deployment is pending hosting setup. The verified live URL will be added here after deployment.

## Results and their limits

- The supplied survey microdata yields **48.6% UPI-capable** and an estimated
  **46.9 crore persons aged 15+ not UPI-capable**, using MLT/100 weights.
- **19.5 crore recent internet users report being unable to transact online**.
  This is calculated from respondent intersections, not subtraction of unrelated totals.
- Survey state geography is decoded from NSS-Region; it is not imputed from NPCI.
- **38.1% of Q1 NPCI transaction volume has no state classification**. It remains
  in national totals and is excluded from observed state totals. State-specific
  missing shares are unknown; complete-volume rankings are not established.
- Confidence intervals are unavailable. The official variance formula needs
  sampling-frame/listing quantities absent from the supplied extracts. A sample
  threshold is a display guard, not a precision guarantee.

The indicators are not a sequential adoption funnel. Household internet
barriers do not identify UPI-specific causes. Regression residuals do not
diagnose merchant acceptance, individual behaviour, or intervention needs.
Allocation rules which preserve rankings by construction cannot establish
robustness to the unknown real missing-data pattern.

## MERN web application

The [UPI Observatory](web/README.md) uses **MongoDB, Express, React and Node.js**,
with GraphQL. It provides six pages: overview, capability explorer, classified
NPCI transactions, a what-if calculator, methods, and saved comparisons.

```sh
cd web
npm ci
npm run dev
```

Open http://127.0.0.1:3000. The first run downloads a local MongoDB binary;
subsequent runs reuse it and retain saved notes. See the [app guide](web/README.md)
for configuration, production builds, data imports and browser-scoped saves.

## Reproduce the analysis

Place `CMST80PER.dta` and `CMST80HH.dta` in `data/raw/`. Place the original
January, February and March NPCI workbooks in `data/raw/npci/`, named
`upi_statewise_2025-Jan.xlsx`, `upi_statewise_2025-Feb.xlsx`, and
`upi_statewise_2025-Mar.xlsx`. Raw data are ignored by Git.

```sh
python src/build_analysis.py
python src/build_npci_analysis.py
python src/build_powerbi_export.py
pip install -r requirements-dev.txt
python -m pytest
```

Builds check eligible Q12 responses, positive weights, state mappings, exact
quarter coverage, unique state-month rows, complete joins and official state
reconciliation. Unexpected state discrepancies stop the survey build. The
documented HP discrepancy is flagged, never replaced with an assumed correction.

The official online-banking cross-check matches 35 of 36 states/UTs at displayed
precision. Himachal Pradesh differs by 1.8 percentage points; its estimates are
retained, with a note, and omitted from the exploratory regression pending
reconciliation. Details are in the [source audit](docs/AUDIT.md).

## Files

| Location | Purpose |
|---|---|
| `src/cmst.py`, `src/build_analysis.py` | Survey loading and weighted indicators |
| `src/validation.py`, `data/reference/` | Official Table 12 reconciliation |
| `src/npci.py`, `src/build_npci_analysis.py` | Classified transaction comparison and assumption demonstrations |
| `web/` | React UI, Express/GraphQL API and MongoDB persistence |
| `render.yaml` | Production hosting configuration |
| `data/processed/` | Reproducible app inputs, overlap checks and validation outputs |
| `data/powerbi/` | Corrected Power BI exports, including scope and review flags |
| `DATA_NOTES.md` | Definitions, limitations, variance requirements and source links |
| `docs/AUDIT.md` | What was checked, corrected and left unresolved |
| `docs/MERN_PLAN.md` | Revised MERN scope based on defensible measures |

## Power BI report

The corrected five-page [Power BI report](powerbi/UPI%20Capability%20Gap.pbix)
is now built and checked in Power BI Desktop. Its [editable project and guide](powerbi/START_HERE.md)
include the model, native visuals, demographic filters and population what-if
calculator. Refresh reloads the embedded aggregate snapshot; it is not live data.
See the [build instructions](docs/POWERBI_BUILD.md) to regenerate the project.

## Sources

- [CMS-T official materials](https://microdata.gov.in/NADA/index.php/catalog/239/related-materials)
- [Official CMS-T report, Table 12, page A85](https://mospi.gov.in/sites/default/files/publication_reports/CMST_report_m.pdf#page=124)
- [NPCI ecosystem statistics](https://www.npci.org.in/what-we-do/upi/upi-ecosystem-statistics)

Original NPCI workbooks supplied by the project owner match the analysis inputs
cell-for-cell. They have not been independently re-downloaded from NPCI.
