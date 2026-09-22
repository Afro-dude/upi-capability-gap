# Data notes and interpretation boundaries

## 1. Sources and geography

CMS-T, NSS 80th Round, January–March 2025: 142,065 person records and 34,950
household records. The provided STATA files contain 106,631 persons aged 15+.
In this project, “adults” in legacy column names means **age 15+**, not age 18+.

The [official README](https://microdata.gov.in/NADA/index.php/catalog/239/download/4936)
specifies `Final Weight = MLT/100` and the first two digits of NSS-Region as the
State/UT code. The [layout](https://microdata.gov.in/NADA/index.php/catalog/239/download/4934)
supplies the state names. Code 25 is the merged D&N Haveli & Daman & Diu;
code 26 is not used. There are 36 state/UT codes in the supplied data. This
geography exists in the survey independently of NPCI.

FSU plus sample household number identifies a household. The frame excludes
some Andaman and Nicobar villages which are inaccessible throughout the year.
Sources retrieved for this review are logged in `docs/source_manifest.json`.

## 2. Capability and routing

Block 4 Q12: code 1 = UPI only; 2 = other online banking only; 3 = both;
4 = unable. UPI capability is codes 1 or 3; online-banking capability is 1–3.
The denominator is all persons aged 15+, including structural skips.

Block 4 eligibility includes device operation, but this is not the only gate.
Q9 follows eligible smartphone/tablet/computer use; Q12 also requires internet
capability (Q9 codes 1–3) and age 15+. In the supplied data, 17,113 device-capable
persons aged 15+ still have blank Q12. None of the internet-capable persons
aged 15+ have blank Q12. The earlier explanation attributing every skip solely
to inability to operate a device was incomplete.

The loader rejects missing/invalid Q12 for eligible internet-capable adults,
unknown nonblank Q12 codes, invalid weights and unmapped states. Structural
skips become false for the capability indicators; unexpected missing eligible
responses must not silently become false. See the [official schedule](https://microdata.gov.in/NADA/index.php/catalog/239/download/4939).

## 3. Weights and source reconciliation

Weighted rates are sums of weighted indicator values divided by sums of weights.
Aggregated rates must be recomputed from their numerators and denominators,
never averaged across states/cells. National totals include every recorded sex
category and every state, including provisional HP estimates; presentation
filters must not redefine national denominators silently.

`data/reference/official_online_capability.csv` transcribes Table 12, page A85,
age 15+, All/Person, from the [official report](https://mospi.gov.in/sites/default/files/publication_reports/CMST_report_m.pdf).
`official_state_validation.csv` compares unrounded computed online-banking rates
with the published one-decimal rates using a 0.05 percentage-point tolerance.
35/36 match. **Himachal Pradesh: 64.3917% computed versus 66.2% published**.
The cause remains unresolved. This is an online-banking check, not a claim
that the published value is a direct UPI-capability rate.

No survey records or weights are changed to force a match. HP is flagged in
state views and omitted from the descriptive NPCI fit. New discrepancies stop
the build. A resolved HP check will automatically remove that exclusion.
National online-banking capability reproduces 48.9%; UPI capability is 48.6%.
These checks do not independently validate weighted population totals.

## 4. Separate indicators and valid conditional rates

The seven displayed access/use/capability indicators are not nested. Among
respondents aged 15+, 1,655 report internet capability without smartphone use,
and 256 report online-banking capability without recent internet use.
Accordingly, `retention_from_prev` and `lost_here_crore` have been removed.
`funnel_national.csv` is retained as a legacy filename for prevalence indicators.

Conditional online-banking capability among internet users is:

    sum(weight × internet_used × online_capable) / sum(weight × internet_used)

The excluded-online population is the sum of weights for respondents who used
the internet but are not online capable. This gives about 19.5 crore people.
The conditional rate is 69.55%. `conditional_sector_gender.csv` applies the same
intersection within each group; the app and static chart share this table.
No claim about owning a smartphone follows from recent internet use.

## 5. Sampling uncertainty

**No design-based confidence intervals are published.** The official
[methodology](https://microdata.gov.in/NADA/index.php/catalog/239/download/4938),
sections 3.6 and 4.1, uses two-stage SRSWOR variance terms requiring stratum/frame
FSU counts N_st, sampled FSU counts n_st, listed household counts H_i,
subdivision factors D1_i and sampled household counts h_i. The supplied files
contain identifiers and final weights but not all the separate frame/listing
components. A product embedded in a final weight does not identify its factors.

The previous claim that identifiers alone made the full official formula
implementable was too strong. Exact estimation needs Schedule 0.0/listing or
equivalent frame metadata, plus explicit handling of singleton sampling strata.
Do not substitute an ordinary binomial interval or an undocumented bootstrap.

The display rule `n < 30` marks small cells. Its legacy field name `unreliable`
does not mean cells with `False` are statistically precise. State respondent,
household and FSU counts are provided as coverage diagnostics. Sorting point
estimates or checking sample size is not a test of significant differences.
Sex-specific comparisons also require appropriate domain variance estimates.

## 6. Barrier variables and causal limits

Household Q5 asks the main reason for no home internet; person Q16 applies to
internet-capable people who did not recently use it. These have different
denominators. Neither measures the causes of UPI non-capability directly.
Reported literacy barriers do not prove that coverage or affordability
interventions are exhausted, nor that onboarding has superior cost-effectiveness.

Age/sex/sector differences are descriptive. They do not establish mechanisms,
programme effectiveness, or which group should be prioritised. MPCE remains
unused in accordance with the survey's warning about auxiliary variables.

## 7. NPCI join and national reconciliation

The owner supplied Jan, Feb and Mar 2025 state-wise workbooks; their titles match
the intended quarter. The copies in `upi_data.zip` match the originals in
`Dataset files` cell-for-cell. An independent live NPCI download has not been
authenticated. Do not infer payer residence or geolocation collection details
beyond the metadata available in these files.

The loader requires exactly those three months, 36 unique mapped states/UTs
and one `UNCLASSIFIED#` row per month, and nonnegative volume/value. The join is
one-to-one after quarterly aggregation and fails if either source loses a state.

| Period | Total volume (million) | Unclassified volume (million) | Unclassified share |
|---|---:|---:|---:|
| Jan 2025 | 16,996.00 | 5,881.16 | 34.60% |
| Feb 2025 | 16,106.19 | 6,410.98 | 39.80% |
| Mar 2025 | 18,301.51 | 7,294.90 | 39.86% |
| Quarter | 51,403.70 | 19,587.04 | 38.10% |

The quarter percentage is the ratio of summed volumes, not an unweighted mean
of monthly percentages. Missing geography is not missing national volume.
Classified state volume totals 31,816.66 million; no unclassified transactions
are added to published observed state rows.

## 8. Allocation assumptions do not identify true rankings

Let O_s be classified volume, P_s population, U national unclassified volume.
Proportional allocation gives `(O_s/P_s) × (1 + U/sum(O))`.
Adult-population allocation gives `O_s/P_s + U/sum(P)`.
Their ranking/correlation invariance is an algebraic property of their assumed
allocations, not empirical evidence about the missing transactions.

Actual missing volume may vary across states. It is therefore incorrect to
claim all states are understated by about 40%, or that complete-volume rankings
are unaffected. Exclusion preserves observed data, but does not eliminate
selection bias or guarantee a conservative association.

Allocation by capable population builds capability into the outcome. Allocation
by excluded population demonstrates the opposite direction of the same problem.
Both are labelled hypothetical and circular for testing this relationship.
The assumption table retains all 36 states for comparability with the prior
table; it is not the source-validated 35-state regression sample.

## 9. Exploratory regression

The fit uses equal-weight state/UT observations with classified transactions per
resident aged 15+ as the outcome. Excluding unresolved HP gives 35 observations,
r = 0.6589 and R² = 0.4342 in the supplied snapshot. The original all-36-state
result r = 0.6366 remains reproducible in the assumption table.

This is a descriptive association, not a causal decomposition or validated
prediction. Residuals use neutral above/below-fit labels. The unexplained share
cannot be assigned to merchant acceptance or a separate behavioural problem.
Unknown state reporting coverage, survey uncertainty and a mismatch between
transaction location and resident population can affect both signs of residuals.
No respondent-level transaction inference follows from the ecological join.

## 10. Scenarios and national benchmarks

The supported scenario is `excluded population × explicitly assumed share
becoming capable`. It is a hypothetical population calculation, not a forecast.
No transaction intensity, treatment effect or cost assumption is inferred.
The baseline remains a survey point estimate with unresolved sampling uncertainty.

For transparency, `npci_national_summary.csv` reports total national volume
including unclassified volume. Dividing by the survey capable population gives
115.7 quarterly transactions per survey-capable person; using classified volume
only gives 71.6. Neither is an observed per-user frequency: the populations and
transaction roles are not linked. The previous 40–60% intensity assumption was
arbitrary, and its result was neither a forecast nor a strict upper bound.
Transaction projections and the “enablement ceiling” claim have been withdrawn.
