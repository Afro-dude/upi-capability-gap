# Data notes

Every non-obvious decision made in this analysis, with the source document that
justifies it. This file exists so that each number can be defended.

---

## 1. Source

NSS 80th Round, **Comprehensive Modular Survey: Telecom (CMS-T)**, fielded
January–March 2025 by the National Statistical Office. Unit-level data obtained
from `microdata.gov.in` (catalogue 239).

| File | Records |
|---|---|
| `CMST80HH.dta` | 34,950 households |
| `CMST80PER.dta` | 142,065 persons |

Both counts match `README_CMST_2025.docx` exactly, confirming a complete read.

The STATA distribution was used rather than the fixed-width text files. The
`.dta` files carry the same records; using them removes an entire class of
byte-offset parsing error.

---

## 2. Weights

`README_CMST_2025.docx` states plainly: **Final Weight = MLT / 100**. The raw
`mlt` field is the stratum-level multiplier `(N_st / n_st) * D1 * (H_sti /
h_sti)` defined in section 4.1 of the methodology document.

Applying it gives:

- **30.7 crore households** — consistent with independent estimates of India's
  household count.
- **91.4 crore adults aged 15+**.

All households within an FSU carry the same multiplier, as the README specifies.

**Not done:** standard errors. The methodology document gives the full variance
formula (section 3.6), which requires stratum and sub-stratum identifiers in a
two-stage SRSWOR design. The identifiers are present in the data, so this is
implementable, but every estimate reported here is a point estimate without a
confidence interval. State-level and fine segment cells are the ones most
affected.

---

## 3. The UPI variable

This is the single most important definition in the project, and it is easy to
get wrong.

The data layout describes `b4q12` only as *"Whether able to perform online
banking transactions via devices like computers, or mobile"*, which reads like a
yes/no item. It is not. The **schedule** (`Volume_II_CMST.pdf`, Block 4 Q12)
gives the actual codes:

| Code | Meaning |
|---|---|
| 1 | Yes, through UPI only |
| 2 | Yes, through net banking or other means (except UPI) only |
| 3 | Yes, both |
| 4 | No |

So:

- **UPI-capable** = codes 1 or 3
- **Online-transaction-capable** = codes 1, 2 or 3
- Code 2 alone is only **0.3%** of adults — negligible, which is itself a
  finding about how UPI has crowded out other retail digital payment methods.

Anyone reading only the layout file would have concluded that UPI is not
measured in the microdata and fallen back on a proxy. Read the schedule.

---

## 4. Question routing, and why blanks are zeros

`b4q12` is blank for 65,492 of 142,065 person records. Those blanks are not
missing data; they are structural non-response driven by the schedule's skip
logic:

1. **Block 4** is administered only to persons aged 3+ who have code 1 in
   Block 3 col. 5 **or** col. 6 — that is, who can operate a mobile phone or a
   computer.
2. **Q12 additionally requires age ≥ 15.**

Verified empirically: `b4q12` is non-blank for 0.0% of under-15s and 71.8% of
15+, exactly matching the stated routing.

**Decision: for adults 15+, a blank `b4q12` is treated as not UPI-capable.**

This is substantively correct rather than merely convenient. A person who
cannot operate a phone or a computer at all cannot execute a UPI transaction.
The schedule does not ask them because the answer is already determined.

The consequence is that **the denominator throughout is all adults aged 15+**,
not "adults who were asked the question". Using the latter would inflate every
capability rate by roughly 40% and produce a badly flattering picture.

---

## 5. Funnel construction

| Stage | Definition | Source |
|---|---|---|
| Can operate a phone or computer | Block 3 col. 5 = 1 or col. 6 = 1 | Block 3 |
| Had a mobile phone (3m) | `b4q3` ∈ {1,2,3} | Q3 |
| Used a smartphone (3m) | `b4q4` = 1 | Q4 |
| Able to use the internet | `b4q9` ∈ {1,2,3} | Q9 |
| Used the internet (3m) | `b4q10` = 1 | Q10 |
| Able to transact online | `b4q12` ∈ {1,2,3} | Q12 |
| Able to transact via UPI | `b4q12` ∈ {1,3} | Q12 |

Note that Q4 is itself conditional on Q3 ∈ {1,3}, and Q9 on Q4/Q6/Q8 = 1. The
funnel is therefore genuinely nested: each stage is a subset of the one above
it, which is what makes the conditional retention rates interpretable.

---

## 6. Geography

There is no state column. `README_CMST_2025.docx`: the **first two digits of
`nss_reg`** give the State/UT code. Names are mapped from the "State code" sheet
of `Data_Layout_CMST_2025.xlsx`.

Note the code list skips 26 and includes 25 as the merged
"D&N Haveli & Daman & Diu" UT.

**Coverage caveat:** villages in the Andaman & Nicobar Islands that are hard to
access year-round were excluded from the survey frame by design.

---

## 7. Barrier variables — two of them, with different scopes

There are two "reason" questions and they are **not** interchangeable.

**Person-level (Block 4 Q16)** is asked only of people who are *able* to use the
internet but did **not** use it in the last three months. That is a narrow and
unusual group — people with the capability who chose not to exercise it. It is
not a general measure of why people are offline.

**Household-level (Block 5 Q5)** is asked of every household without internet at
home, covering 4.2 crore households. This is the broader and more useful
variable, and it is the one used for the headline barrier finding.

Both are written out (`barriers_person.csv`, `barriers_household.csv`), but the
argument rests on the household version. Conflating them would be a real error.

---

## 8. Variables deliberately not used

**MPCE (`b3q5`).** `Note_for_data_user - CMS-Telecom.docx` warns that household
characteristics including consumption expenditure were collected *for
consistency checking*, and advises against generating estimates resting solely
on these auxiliary variables. CMS-T is not a consumption survey and its MPCE
item is a single abbreviated question, not a full consumption schedule.

It is loaded and available in `cmst.py` but **no finding in this project uses
it**. An income-gradient analysis would need the Household Consumption
Expenditure Survey or Global Findex instead.

Cross-tabulating the survey's *own* indicators by age, sex and sector is a
different matter and is exactly what the official report does; those axes are
used freely.

---

## 9. Small cells

The full segment table has state × sector × age band × sex cells, some of which
rest on very few sample persons. Cells with fewer than 30 unweighted
observations are **flagged** (`unreliable = True`) rather than dropped, so the
analyst decides. All headline figures quoted in the memo exclude flagged cells.

This matters most for small UTs — Lakshadweep, Ladakh, Andaman & Nicobar — where
even state-level estimates are thin.

---

## 10. What this data cannot do

Stated plainly, because these are the questions an interviewer should ask:

1. **Capability is not usage.** Q12 asks whether a person is *able* to transact
   via UPI, not whether they do, how often, or for how much. Every gap figure
   here is an enablement gap, not a transaction forecast.

2. **One point in time.** Jan–Mar 2025 only. No trend, no before/after, no
   causal claim. Comparison to earlier NSS rounds would require checking that
   the questions and routing are genuinely comparable, which they may not be —
   CMS-T is a new short-duration survey format.

3. **No transaction values.** Nothing in the survey records amounts. Linking
   capability to volume requires external NPCI data at state level, and that
   link is ecological: it supports statements about states, not about
   individuals within them.

---

## 11. Open items

- **NPCI state-wise volumes not yet merged.** `data/processed/state_level.csv`
  contains empty `npci_monthly_txn_volume` and `npci_monthly_txn_value_cr`
  columns ready to be filled. NPCI began publishing state-wise UPI data in
  June 2025; a substantial share of national volume is reported as
  "unclassified" and cannot be attributed to any state, so any per-capita
  figure must state whether that residual was excluded or distributed.
- Standard errors, per section 2 above.

---

## 12. NPCI state-wise transaction data

**Source.** NPCI Ecosystem Statistics → *UPI Statewise Statistics*, monthly
XLSX. Jan, Feb and Mar 2025 are used, chosen to match the CMS-T field period
exactly so that capability and volume describe the same quarter. Using a later
month would compare Jan–Mar 2025 capability against a period over which UPI grew
substantially.

**File shape.** Row 0 is a merged title cell; the real header is row 1. Volume
and value arrive as strings with Indian-style comma grouping and must be
de-comma'd before conversion. 36 states/UTs plus one `UNCLASSIFIED#` row.

**Name mapping.** Three NPCI names differ from the NSS code list and are mapped
explicitly: `JAMMU AND KASHMIR`, `DADRA & NAGAR HAVELI & DAMAN & DIU`,
`ANDAMAN & NICOBAR`. The remaining 33 match on uppercase. The loader raises if
any name fails to map rather than silently dropping a state — all 36 match.

### 12.1 The unattributed volume, and why it turns out not to matter

NPCI's disclaimer states that where location data was not received, the
transaction is categorised as unclassified. In Q1 2025:

| Month | Unclassified, volume | Unclassified, value |
|---|---|---|
| Jan 2025 | 34.6% | 32.6% |
| Feb 2025 | 39.8% | 37.5% |
| Mar 2025 | 39.9% | 37.4% |

A 5.3pp swing inside a single quarter, so the share is not stable either.

This looks disqualifying for state comparison, and the instinct to abandon the
merge is reasonable. It is also wrong, for a mechanical reason.

Four allocation rules were tested (`npci.allocate`):

| Rule | Effect on each state's transactions-per-adult |
|---|---|
| `excluded` | baseline |
| `proportional` | multiplies every state by the same constant |
| `by_adults` | adds the same constant to every state |
| `by_capable` | adds a term proportional to that state's capability rate |

Multiplying every observation by a constant, or adding a constant to every
observation, changes neither a rank ordering nor a Pearson correlation. So the
first three rules are mathematically guaranteed to give identical answers — and
they do, at r = 0.637 with rank correlation 1.000 against each other.

`by_capable` gives r = 0.731, and that difference is an artefact, not a finding.
Allocating unattributed volume in proportion to capable population and then
correlating the result against capability rate builds the relationship into the
data. **It must not be used to test the capability–usage relationship**, and it
is retained in the code only as a demonstration of the trap.

**Conclusion:** the unclassified bucket limits the interpretation of *absolute*
per-capita levels — every state's figure is understated by roughly 40% — but is
provably irrelevant to *relative* comparison, which is what the analysis rests
on. All published results use `excluded`, the most conservative rule.

### 12.2 Ecological inference

Capability comes from person-level survey records; volume comes from
state-level administrative aggregates. The merge therefore supports claims about
states and not about individuals within them.

Concretely: it is supported to say "states with lower capability transact less
per adult." It is **not** supported to say "rural women aged 45+ generate X
transactions" — their transactions are never observed. The segment breakdowns in
this project are breakdowns of the *capability gap*; the volume estimate is a
state-level projection applied to that gap, and is labelled as such.

### 12.3 Per-capita usage is resident-denominated

Transaction volume attributed to a state includes payments made by visitors and
by businesses headquartered there, while the denominator is resident adults.
Goa (+66.6 residual) and Delhi (+37.0) are the clearest cases — tourism and
commercial concentration respectively. Their positive residuals should not be
read as residents transacting unusually often.

This is a genuine limitation on the residual analysis and cannot be fixed with
the available data. It matters less for the negative residuals, which is where
the argument in Finding 6 sits.

### 12.4 The sizing calculation

```
unrealised transactions = gap population
                        × transactions per capable adult
                        × haircut
```

- **Benchmark:** 71.6 transactions per capable adult per quarter, computed as
  attributed Q1 volume divided by weighted capable adult population.
- **Gap population:** 46.9 crore adults aged 15+ who are not UPI-capable.
- **Haircut:** 40% and 60% of benchmark, reported as a range.

The haircut exists because newly enabled users are not drawn from the same
distribution as existing ones — they skew older, poorer, more rural and more
female, all of which predict lower transaction frequency. No haircut at all
would assume the marginal user behaves like the average user, which is
implausible on the face of it. The 40–60% band is a judgement, not an estimate
from data, and is stated as such.

The result — 4.5 to 6.7 billion transactions per month, a 42–63% uplift on
attributed volume — is an **enablement ceiling**. It answers how large the
opportunity is if capability were closed, not what would happen under any
particular intervention.
