# Power BI build sheet

Everything needed to assemble the dashboard in Power BI Desktop. The data is
already shaped for it — run `python src/build_powerbi_export.py` and load the
ten CSVs in `data/powerbi/`.

The `.pbix` file itself has to be built in Desktop; it is a proprietary binary
that cannot be generated from a script.

---

## 1. Load

**Home → Get data → Text/CSV**, and load all ten files from `data/powerbi/`.
Or **Get data → Folder** and point at `data/powerbi` to bring them in together.

In Power Query, check that these are typed as **Decimal Number**, not Text —
Power BI occasionally guesses wrong on columns with large values:

`adults`, `capable_adults`, `excluded_adults`, `txn_volume_mn`,
`txn_per_adult`, `residual`, `households`

---

## 2. Model

Switch to **Model view** and create these relationships. All are
one-to-many, single direction, from the dimension to the fact.

| From | To | Cardinality |
|---|---|---|
| `dim_state[state]` | `fct_segment[state]` | 1 → * |
| `dim_state[state]` | `fct_state[state]` | 1 → * |
| `dim_sector[sector]` | `fct_segment[sector]` | 1 → * |
| `dim_sector[sector]` | `fct_barriers[sector]` | 1 → * |
| `dim_age_band[age_band]` | `fct_segment[age_band]` | 1 → * |
| `dim_sex[sex]` | `fct_segment[sex]` | 1 → * |

`fct_funnel`, `fct_sensitivity` and `fct_unclassified` stay disconnected. They
are national-level tables with no dimension to slice by, and wiring them into
the model would only create ambiguity.

**Sort columns.** Select `dim_age_band[age_band]` → **Column tools → Sort by
column → age_sort**. Repeat for `dim_sector[sector]` by `sector_sort`,
`dim_sex[sex]` by `sex_sort`, and `fct_funnel[stage]` by `stage_sort`.
Without this, every axis sorts alphabetically and the funnel reads in the
wrong order.

---

## 3. Measures

Create these in a new table (**Home → Enter data**, name it `_Measures`, load
an empty table, then add measures to it). Keeping measures in one place stops
them scattering across fact tables.

### Core

```dax
Adults = SUM ( fct_segment[adults] )

Capable Adults = SUM ( fct_segment[capable_adults] )

Excluded Adults = SUM ( fct_segment[excluded_adults] )

Capability Rate =
DIVIDE ( [Capable Adults], [Adults] )
```

**Why `Capability Rate` is a measure and not a stored column.** The export
deliberately omits rate columns. If a rate were stored per row and then
averaged, every state would count equally regardless of population — Lakshadweep
would pull the national figure as hard as Uttar Pradesh. Recomputing from the
summed numerator and denominator weights correctly at every level of
aggregation.

### Gap framing

```dax
Excluded (crore) = DIVIDE ( [Excluded Adults], 10000000 )

Adults (crore) = DIVIDE ( [Adults], 10000000 )

Share of National Gap =
DIVIDE (
    [Excluded Adults],
    CALCULATE ( [Excluded Adults], REMOVEFILTERS () )
)

Sample Size = SUM ( fct_segment[sample_n] )
```

### Gender gap

```dax
Female Capability =
CALCULATE ( [Capability Rate], dim_sex[sex] = "Female" )

Male Capability =
CALCULATE ( [Capability Rate], dim_sex[sex] = "Male" )

Gender Gap (pp) =
( [Male Capability] - [Female Capability] ) * 100
```

### Transactions (state level)

```dax
Txn Volume (mn) = SUM ( fct_state[txn_volume_mn] )

Txn per Adult =
DIVIDE ( [Txn Volume (mn)] * 1000000, SUM ( fct_state[adults] ) )

Residual = SUM ( fct_state[residual] )

Performance Note =
VAR r = [Residual]
RETURN
SWITCH (
    TRUE (),
    r < -10, "Transacts well below what its capability predicts — the "
           & "constraint is downstream, most plausibly merchant acceptance.",
    r > 10,  "Transacts above trend. Volume includes payments by visitors and "
           & "by businesses headquartered here, against a resident denominator.",
    "Close to the national trend line."
)
```

`Performance Note` drives a card visual that changes text as the user selects a
state — the same contextual explanation the Streamlit version gives.

### Ranking guard

```dax
Rate Rank Valid =
IF ( [Sample Size] >= 100, [Capability Rate], BLANK () )
```

Use this instead of `Capability Rate` on any visual that ranks *by* rate.
Blanking small cells keeps segments resting on thirty-odd respondents out of a
"lowest capability" ranking, where a 0% reading means "too few to detect"
rather than a finding.

---

## 4. Pages

Three pages, mirroring the argument rather than the data structure.

### Page 1 — What the data shows

No slicers. This page should read top to bottom for someone who never clicks.

| Visual | Type | Fields |
|---|---|---|
| Headline cards | Card ×3 | `Capability Rate`; `Excluded (crore)`; static text "19.5 crore online but cannot transact" |
| Adoption funnel | Bar chart, horizontal | Axis `fct_funnel[stage]`, Value `fct_funnel[share_of_adults]` |
| Barriers | Bar chart, horizontal | Axis `fct_barriers[barrier_group]`, Value `SUM(households)` |
| Capability by age and group | Line chart | Axis `dim_age_band[age_band]`, Values `Capability Rate`, Legend `sector` + `sex` |

On the funnel, set the "Able to transact online" data point to the accent
colour manually (**Format → Data colors → expand → select the point**). The
break at that stage is the finding; the other bars are context.

### Page 2 — Explore

| Visual | Type | Fields |
|---|---|---|
| Slicers | Slicer ×3 | `dim_sector[sector]`, `dim_age_band[age_band]`, `dim_sex[sex]` |
| Segment table | Table | sector, age_band, sex, `Adults (crore)`, `Capability Rate`, `Excluded (crore)`, `Sample Size` |
| State map | Filled map | Location `dim_state[state]`, Colour `Capability Rate` |
| Capability vs usage | Scatter | X `Capability Rate`, Y `Txn per Adult`, Legend `fct_state[performance]`, Details `state` |
| Context card | Card | `Performance Note` |

Set the map's Location data category: select `dim_state[state]` → **Column
tools → Data category → State or Province**. Without it Power BI cannot
geocode.

**Do not put `state` on the segment table.** With state included the data
splits into 565 cells, most of them small, and any ranking simply re-sorts
states by population — Uttar Pradesh takes nine of the top fifteen rows
whatever the slicers say. The state question belongs on the map and the
scatter, where transaction data is attached.

### Page 3 — How reliable is this?

| Visual | Type | Fields |
|---|---|---|
| Validation | Card ×2 | static: computed 99.46%, published ~99.5% |
| Unattributed volume | Column chart | Axis `fct_unclassified[month]`, Value `unclassified_share_volume` |
| Allocation sensitivity | Table | all columns of `fct_sensitivity` |
| Limitations | Text boxes | see `DATA_NOTES.md` §10 and §12 |

The sensitivity table is the strongest technical content in the project. Give
it room and add a text box explaining that three of the four rules return an
identical 0.637 because they scale or shift every state by the same constant,
and that the fourth is circular.

---

## 5. Formatting

Match the Streamlit app and the static figures so the three never diverge:

- Primary `#2C6E91`, accent `#C1440E`, text `#1A1A1A`, gridlines `#E2E0DC`
- Set once under **View → Themes → Customize current theme**
- Turn off visual borders and shadows; keep titles left-aligned
- Format `Capability Rate` as Percentage, 1 decimal
- Format `Excluded (crore)` as Decimal Number, 1 decimal

---

## 6. Publish

**Home → Publish** requires a Power BI account (the free tier works for
publishing to My Workspace). Sharing a link needs Pro, which most students do
not have.

Practical alternative: commit the `.pbix` to the repository and add a
screenshot of Page 1 to the README. Anyone with Desktop can open it, and the
screenshot is what a recruiter will actually look at.

Keep the file under GitHub's 100 MB limit — with these CSVs it will be well
under 5 MB.
