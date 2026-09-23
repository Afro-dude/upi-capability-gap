# MERN implementation and scope

The application is implemented in `web/`; see [its run guide](../web/README.md).
MongoDB stores versioned aggregate snapshots and browser-private comparisons.
Express and Node expose GraphQL to React. Python remains an offline analytics
pipeline; no Python web server or REST analytics API is needed.

The six pages cover the national overview, demographic/state capability
exploration, classified NPCI activity, population what-ifs, methodology and
saved comparisons. Source hashes and CSV exports support inspection.

## Methodology carried into the application

- Rates are computed from summed weighted numerators and denominators.
- All recorded sex categories and all states remain in national estimates.
- Conditional indicators use respondent intersections, not subtraction.
- Cells below 30 respondents have their displayed rate withheld. This is not
  a confidence interval or a claim of precision above the threshold.
- Himachal Pradesh's online-banking check remains provisional, with a focused
  note when selected and details in Methods. It is not a national-page headline.
- NPCI unclassified volume is retained nationally and never redistributed into
  the observed state figures. There are no demographic transaction filters.
- The scatter displays observed state points without a fitted line. It cannot
  diagnose merchant acceptance, individual behaviour or programme effects.
- What-ifs multiply excluded population by a user-selected share. They do not
  need ML, and predict neither transactions nor causal effects. State scenarios
  remain disabled.

Imports validate aggregate consistency and preserve immutable versions. The
Python build owns raw source decoding and state-month duplicate checks. A local
admin command imports validated aggregates; there is no public upload endpoint.

Future account-based collaboration, fresh NPCI source verification, confidence
intervals and validated forecasting require additional work or source material.
They are not implied by adding a web interface.
