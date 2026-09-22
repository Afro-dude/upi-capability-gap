# UPI Capability Gap — Power BI report project

## Current status

Five report pages and the semantic model have been authored. The project passes
Microsoft PBIP/PBIR JSON schema validation, data snapshot reconciliation,
relationship-scope checks and visual-field-reference checks.

**Validated in Power BI Desktop 2.157.1354.0 on 22 September 2026.** All five
pages rendered after Refresh. Headline values matched the analysis; selecting
Rural changed survey metrics and clearing restored national totals. The what-if
calculator was checked at 0%, the default 10%, and 100%. The finished PBIX
contains the loaded aggregate data and opens on Survey findings.

## Open the report

Open **UPI Capability Gap.pbix** in Power BI Desktop to use the finished report.
No source-path setup, credentials or raw-data download is required.

For the editable project:

1. Keep this folder together and open **UPI Capability Gap.pbip**.
2. Select **Refresh** to load the included aggregate snapshot into the model.
   It contains corrected aggregate data, not individual survey records. No
   source-path setup, credentials or raw-data download is required.
3. After making changes, check pages, filter interactions and totals, then save as
   **UPI Capability Gap.pbix** using File > Save As.

If Desktop requests project preview support, enable the Power BI Project and
enhanced report metadata (PBIR) options under File > Options and settings >
Options > Preview features, and restart Desktop.

## Pages

- **Survey findings:** weighted national totals, separate prevalence measures,
  and reported household internet barriers.
- **Capability explorer:** state, sector, sex and age filters; weighted rates,
  sample counts and source notes.
- **NPCI · exploratory:** classified and unclassified volumes, monthly missing
  shares and a labelled state scatter. All 36 points are shown; no fitted line
  is asserted on this page.
- **Population what-if:** national demographic selection and an assumed
  percentage becoming capable. No state scenarios or transaction predictions.
- **Methods & source checks:** source reconciliation, allocation assumptions
  and limitations. The HP note is here rather than a headline on the overview.

## Expected checks after Refresh

- National UPI capability: **48.6%**.
- Estimated not UPI-capable: **46.9 crore**.
- Recent internet users unable to bank online: **19.5 crore**.
- Q1 national transactions: **51.40 billion**; unclassified: **38.1%**.
- Clearing demographic filters restores all recorded sex categories in totals.
- The what-if result is zero when the assumed percentage is zero; at 100% it
  equals the selected baseline. Without one selected percentage, it uses 10%.
- Changing demographic filters must not produce demographic NPCI transaction
  estimates. Each page has its own unsynchronised slicers.
- State comparisons are alphabetical; small displayed cells with n < 30 are
  blanked. This is a display rule, not a statistical precision guarantee.

## Snapshot updates

Refresh reloads the **embedded Jan–Mar 2025 snapshot**, not live source data.
In the repository, run `src/build_powerbi_export.py`, then
`src/build_powerbi_project.py`, after correcting or updating source analysis.
Close Desktop before regenerating project files, then reopen and refresh.
The builder replaces generated report definitions; keep separate copies of
manual report edits before rebuilding.

`aggregate_manifest.json` records the CSV hashes and row counts. The model uses
single-direction dimension-to-fact relationships. National and assumption
tables are disconnected by design.

See the accompanying methodology documents for source definitions and unresolved
sampling uncertainty. The old archived PBIX is not part of this report.
