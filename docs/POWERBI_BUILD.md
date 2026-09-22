# Power BI migration and rebuild

The previous PBIX and screenshot in `docs/legacy/` are superseded. They contain
old text, measures and cached data. **Do not present them as the corrected
analysis.** The corrected five-page report is now available at
`powerbi/UPI Capability Gap.pbix`, with an editable project in the same folder.
It was loaded, refreshed, visually checked and saved in Power BI Desktop
2.157.1354.0. All five pages rendered; national headlines, demographic filtering
and the 0%/10%/100% population what-if results were checked.

Run `python src/build_powerbi_project.py` after generating the CSV exports to
rebuild the PBIP/PBIR definitions. Refresh in Desktop, verify the report and save
the PBIX. The project embeds a portable aggregate snapshot; Refresh does not
download new survey or NPCI data. Regeneration replaces generated definitions;
preserve manual design edits separately. See `powerbi/START_HERE.md`.

## Load and model

Run `python src/build_powerbi_export.py`. Load the CSVs in `data/powerbi/`.
Relate `dim_state[state]` to both state and segment facts, `dim_sector[sector]`
to segment and barrier facts, `dim_age_band[age_band]` to segment facts and
`dim_sex[sex]` to segment facts. Use single-direction, one-to-many relationships.
Keep national indicators, conditional-national, source-validation, national
NPCI, allocation assumptions and unclassified tables disconnected.

Keep demographic slicers on the survey page. They must not be applied to a
state transaction chart: state transaction totals cannot be attributed to the
selected demographic group. Keep all three recorded sex categories in the
model; suppress small displayed cells without removing their contribution to
national totals.

## Measures

```dax
Adults = SUM(fct_segment[adults])
Capable Adults = SUM(fct_segment[capable_adults])
Excluded Adults = [Adults] - [Capable Adults]
Capability Rate = DIVIDE([Capable Adults], [Adults])
Sample Size = SUM(fct_segment[sample_n])
Displayed Capability Rate = IF([Sample Size] >= 30, [Capability Rate], BLANK())

Classified Transactions (mn) = SUM(fct_state[txn_volume_mn])
Classified Transactions per Resident 15+ =
DIVIDE([Classified Transactions (mn)] * 1000000, SUM(fct_state[adults]))

Selected State Residual =
IF(HASONEVALUE(dim_state[state]), SELECTEDVALUE(fct_state[residual]), BLANK())
```

The sample-size guard is only a display rule. Do not name it a valid-ranking
measure. Do not average rates across segments or sum residuals across states.
`review_status`, `uncertainty_status`, `included_in_fit` and `transaction_scope`
must remain visible in appropriate tables/tooltips. HP remains provisional.

## Pages

1. **Survey findings:** dynamic survey totals, independent prevalence bars and
   household internet barriers. The online-but-unable figure must come from
   `fct_conditional_national[internet_users_not_online_capable]`; do not type a
   static headline or subtract unrelated marginal totals. Explain that the
   indicator bars are not sequential and internet barriers are not UPI causes.
2. **Capability explorer:** demographic filters and weighted rates. Present
   state comparisons alphabetically with sample counts and review flags. No
   significance rankings without design-based uncertainty estimates.
3. **NPCI exploratory:** national total, classified and unclassified volumes.
   Scatter X = state capable/adult ratio from `fct_state`; Y = classified
   transactions per resident aged 15+. The delivered report shows all 36 points,
   source flags in tooltips, and no fitted line. If adding a fitted line, filter
   `included_in_fit = TRUE`; do not label it expected behaviour or an intervention target.
4. **Methods:** official reconciliation, unknown state coverage, source links,
   scope notes and the allocation-assumption table. Explain that invariance is
   constructed, and that capability/gap allocations are circular for this test.

## Breaking changes

- Remove `retention_from_prev` and `lost_here_crore` visuals/measures.
- Replace `predicted_txn_per_adult` with `fitted_classified_txn_per_adult`.
- Replace `performance` with neutral `comparison_label`.
- The `opportunity_sizing.csv` output now contains hypothetical population
  changes, not billions of transactions or an enablement ceiling.
- Third-category records are retained in the exports to reconcile totals.
- Source validation and national classified/unclassified totals have dedicated facts.

Delete old static claims about merchant-side constraints, the irrelevance of
unclassified volume, precise rankings, and intervention returns. Recheck
filters, labels and cached values in Desktop before publishing or sharing a
new screenshot. The current PBIX is a separate validated build; archived files
remain unchanged historical artifacts.
