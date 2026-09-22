# Revised MERN scope

The web application will use MongoDB, Express, React and Node.js. To honour
the request to avoid REST as well as FastAPI, use GraphQL through Express.
The Python analysis remains an offline reproducible data-production pipeline;
no Python web server is needed. Implementation of the MERN app is a separate
step from this methodology correction.

## First version

- A React capability explorer for age, sex and sector with permitted state
  views, coverage information and explicit source discrepancy warnings.
- Saved comparisons and notes tied to a dataset version in MongoDB.
- An assumption-based population calculator: estimated excluded population
  multiplied by a user-selected share becoming capable. No ML or transaction
  forecast. State scenarios remain disabled while source/uncertainty issues
  are unresolved; national scenarios retain the baseline caveats.
- An optional, separate NPCI exploratory page using classified volumes with
  national unclassified share shown prominently. No automatic intervention
  ranking, merchant diagnosis or demographic transaction estimates.
- Admin imports of validated aggregate datasets and their source manifest,
  validation results, reporting period and uncertainty status.

## Import and query rules

Store numerators and denominators as well as rates, and recompute aggregate
rates from summed components. Do not average percentages. Preserve state codes
as strings, raw-data exclusions, all sex categories in totals, the distinction
between structural skips and missing eligible answers, and source version IDs.

Import must reject duplicate state-months, incomplete quarter coverage, unknown
state mappings, inconsistent totals and unrecognised validation failures.
HP remains flagged until a documented reconciliation; excluding it from a
descriptive fit must not silently exclude it from national population totals.
Do not call a sample-size threshold a confidence interval or precision score.

Future transaction forecasting needs compatible outcome data and independent
validation. Programme-effect prediction additionally needs an appropriate
causal evaluation design. Choosing MERN or adding ML does not supply either.
