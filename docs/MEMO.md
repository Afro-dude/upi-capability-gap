# India's UPI capability gap is a skills problem, not an access problem

**Analysis of NSS 80th Round, Comprehensive Modular Survey: Telecom (Jan–Mar 2025)**
1,42,065 individuals · 34,950 households · weighted to 91.4 crore adults

---

## Situation

UPI's headline numbers describe a saturated market: over 24,000 crore
transactions in FY 2025-26, near-universal adoption among young urban adults.
That framing is built on transaction data, which by construction can only
describe the people already transacting.

Turning to survey microdata inverts the picture. **Slightly under half of
Indian adults — 48.6% — are able to transact via UPI. 46.9 crore adults are
not.** The interesting question is not how large that number is, but *where in
the adoption chain those people are stuck*, because the answer determines who
can fix it and at what cost.

---

## Finding 1 — The chain breaks after connectivity, not before it

Adults do not fall out of the funnel where the conventional story says they do.

| Stage | Share of adults 15+ | Retains |
|---|---|---|
| Can operate a phone or computer | 87.6% | — |
| Had access to a mobile phone (3m) | 87.0% | 99.2% |
| Used a smartphone (3m) | 70.8% | 81.4% |
| Able to use the internet | 70.5% | 99.6% |
| Used the internet (3m) | 70.0% | 99.2% |
| **Able to transact online** | **48.9%** | **69.9%** |
| Able to transact via UPI | 48.6% | 99.4% |

Two stages lose meaningful numbers of people. Getting a smartphone loses 19%.
But the largest single break is the last one: **among adults who already use
the internet, 30% cannot transact online.** That is 19.5 crore people who own
the device, have the connection, browse the web — and stop at the payment.

The final step, from online transaction to UPI specifically, loses almost
nobody (99.4% retention). Only 0.3% of adults can bank online by some means
*other* than UPI. In India, digital payment capability and UPI capability have
become effectively the same thing.

**Implication:** the marginal rupee spent on towers and handsets buys much less
UPI adoption than the marginal rupee spent on the last mile. 19.5 crore people
are already paid for by the connectivity investment and are not converting.

---

## Finding 2 — Households say the barrier is skill; cost and coverage barely register

Of the 4.2 crore households without internet at home, the stated main reason
falls out as:

| Reason | Share |
|---|---|
| **Digital literacy** (don't know how to use it / what it is) | **47.6%** |
| No perceived need | 34.0% |
| Cost (equipment + service) | 10.5% |
| Availability / supply | 3.0% |
| Other | 4.9% |

"Not available in the area" is **2.8%**. "Service cost too high" is **2.6%**.
The infrastructure build-out and the tariff war have largely done their work;
what remains is a capability constraint that neither addresses.

This holds in cities too. Urban households cite "don't know how to use it" at
36.2% — barely below the rural 40.1%. This is not a rural connectivity story
wearing a different hat.

---

## Finding 3 — The gap is majority female, and it survives connectivity

**60.6% of the entire capability gap is female.** Women's UPI capability is
36.8% against men's 60.2% — a 23-point gap.

The instinct is to attribute this to unequal device or internet access. The data
does not support that. Restricting to adults *who already use the internet*:

| | Male | Female |
|---|---|---|
| Rural | 74.9% | 55.4% |
| Urban | 84.5% | 63.6% |

A 20-point gap persists among men and women who are equally online. **8.3 crore
rural women use the internet and cannot transact on it.** Whatever is stopping
them sits downstream of access — plausibly account ownership, household control
of finances, confidence, or trust, none of which this survey measures directly.

The state-level variation is the clue that this is not immutable. The
within-state gender gap ranges from **5 points in Mizoram to 46 points in Dadra
& Nagar Haveli and Daman & Diu**, at similar overall capability levels. States
with comparable infrastructure produce very different outcomes for women, which
means something policy-shaped is driving it.

---

## Finding 4 — Age is the sharpest single cut

| Age band | UPI-capable | Gap |
|---|---|---|
| 15–24 | 67.6% | 6.8 crore |
| 25–34 | 67.5% | 6.6 crore |
| 35–44 | 51.0% | 8.5 crore |
| 45–59 | 31.3% | 13.4 crore |
| 60+ | 12.4% | 11.7 crore |

Capability halves between 25–34 and 45–59. **The 45+ population alone accounts
for 25.1 crore of the 46.9 crore gap** — more than half, from a group that is
not aging into capability and will not be reached by any strategy aimed at first
smartphone purchase.

---

## Recommendation

**Target two segments, in this order.**

**1. The already-connected non-transactors (19.5 crore).** These people have
cleared every expensive prerequisite. They need assisted onboarding at the point
of trust — banking correspondents, kirana merchants, self-help groups — not
another app feature. The unit economics are unusually favourable because the
device and data costs are already sunk. Rural women who are online but cannot
transact (8.3 crore) are the largest coherent sub-segment and should be the
pilot population.

**2. The 45+ cohort (25.1 crore).** Distinct problem, distinct fix. This group
skews toward feature phones and low confidence, and is the natural population
for UPI Lite, UPI 123PAY and voice- or PIN-simplified flows. Success here is
measured in first-transaction conversion, not app installs.

**Deprioritise** pure coverage expansion as an adoption lever. At 2.8% stated
as an availability barrier, it is close to exhausted as an explanation.

---

## What would make this conclusive

This analysis establishes where capability is missing and what people say is
stopping them. Three things it cannot do, and how to close each:

- **Capability is not usage.** Q12 measures ability, not behaviour. Merging
  NPCI's state-wise transaction volumes onto the state capability file
  (`state_level.csv`, columns already reserved) would show whether high-capability
  states actually transact more, and identify states that are capable but not
  converting — a different problem again. Note that a large share of NPCI's
  state-wise volume is unclassified and must be handled explicitly.
- **No causal claim.** The gender gap's persistence among internet users is
  suggestive, not identified. Testing it needs account-ownership data — Global
  Findex would serve.
- **One quarter, no trend.** Jan–Mar 2025 only.

---

*Full methodology, routing logic and every caveat: `DATA_NOTES.md`.
All figures are weighted using the official multiplier (MLT/100); denominators
are all adults aged 15+ unless stated. Cells with fewer than 30 sample
observations are excluded from quoted figures.*
