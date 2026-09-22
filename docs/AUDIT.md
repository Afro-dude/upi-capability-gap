# Methodology correction audit

## Inputs checked

- GitHub main at the checkout recorded in `source_manifest.json`.
- Owner-supplied `upi_data.zip`: both survey STATA files and Jan–Mar NPCI files.
- Original `Dataset files` folder and matching documentation ZIP.
- Official CMS-T README, layout, methodology and schedule downloaded from the
  catalogue. The README independently confirms weight and geography rules.
- Official report Table 12, page A85, as the online-banking reference.

## Reproduced checks

142,065 persons; 34,950 households; 106,631 respondents aged 15+; 36 state codes.
All three NPCI workbook copies match the owner-supplied originals cell-for-cell.
All 36 quarterly state joins reconcile. The baseline published observed state
volumes contain zero allocated unclassified volume. National quarterly volume
is 51,403.70 million, including 19,587.04 million unclassified (38.1043%).

UPI capability is 48.6316%; online-banking capability is 48.9018%. The official
state check matches 35/36 online-banking rates at one decimal. HP differs by
-1.8083 percentage points. This does not indicate that the other survey values
were derived from NPCI; the sources have separate measures and geography.

## Corrections

1. Removed claims of robustness to unknown state attribution and equal missing
   shares across states. Labelled all redistribution as assumption demonstrations.
2. Removed merchant-side diagnoses, causal interpretations of R², and asserted
   policy returns. Kept a descriptive fit with transparent sample exclusions.
3. Removed false funnel retention/loss columns. Conditional rates now use actual
   intersections and the app/static charts share the same computed tables.
4. Added source validation, eligible-response checks, state/month uniqueness,
   exact-quarter coverage, join coverage and national volume reconciliation.
5. Replaced arbitrary transaction projections with population what-ifs. Kept
   classified and total national ratios separately labelled in an audit table.
6. Preserved all recorded sex categories in aggregate Power BI exports. Added
   review/uncertainty metadata and migration guidance for the old report.
7. Rebuilt static figures and archived the superseded PBIX/screenshot. The
   proprietary Power BI report itself has not been rebuilt.

## Open items that must not be silently resolved

**Himachal Pradesh:** supplied-data calculations and the official reference
remain different. Weight scale and region encoding agree with the official
README; all other states match the displayed online-banking rates. No evidence
justifies replacing HP's survey estimate with 66.2% or changing its weights.
A documented revised data release/erratum or publisher clarification is needed.
The provisional survey totals remain included nationally; the fit excludes HP.

**Sampling uncertainty:** the exact official two-stage variance formula needs
frame/listing components unavailable in the supplied extracts. Identifiers and
the final multiplier alone are insufficient. No fabricated confidence interval,
effective-sample-size shortcut or naive binomial interval is substituted.

**NPCI provenance and coverage:** local source copies reconcile, but a fresh
authoritative download and state-level attribution-coverage information have
not been obtained. Country-wide unclassified share cannot establish each
state's reporting coverage or payer residence.

**Power BI:** corrected source tables and measures are supplied; the archived
binary and image remain historical artifacts, not verified current outputs.

## Verification

Run `python -m pytest` for synthetic methodological checks, committed-output
reconciliation and Streamlit interaction smoke checks. Raw-data reproduction
tests additionally run when the ignored `data/raw/` inputs are present. Run the
four build scripts in README order to reproduce tables and static figures.
