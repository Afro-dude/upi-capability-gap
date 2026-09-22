"""
build_analysis.py -- runs the full analysis and writes every processed table.

Order of operations:
  0. Validation gate: reproduce a published CMS-T figure.
  1. Separate prevalence indicators and respondent-level conditional rates.
  2. Segment gap table (state x sector x age x sex).
  3. Reported internet barriers (not UPI-specific causal evidence).
  4. State-level file, ready to join to NPCI transaction data.
"""

import numpy as np
import pandas as pd

from cmst import (
    load_person, load_household, wmean, wtotal, rate_table,
    PROCESSED, OUTPUTS, AGE_LABELS,
)
from validation import official_state_check

FUNNEL = [
    ("s1_can_use_device",   "Can operate a phone or computer"),
    ("s2_had_phone",        "Had access to a mobile phone (3m)"),
    ("s3_used_smartphone",  "Used a smartphone (3m)"),
    ("s4_can_use_internet", "Able to use the internet"),
    ("s5_used_internet",    "Used the internet (3m)"),
    ("s6_can_bank_online",  "Able to transact online"),
    ("s7_upi_capable",      "Able to transact via UPI"),
]


def validation_gate(adults):
    """
    Reproduce the published figure: among persons who can transact online,
    the share able to do so via UPI. The CMS-T report puts this at ~99.5%
    for ages 15-29.
    """
    young = adults[adults["age"].between(15, 29)]
    online = young[young["s6_can_bank_online"]]
    got = wmean(online, "s7_upi_capable")

    print("=" * 68)
    print("VALIDATION GATE")
    print("=" * 68)
    print(f"  UPI share among 15-29 online transactors : {got:.4%}")
    print(f"  Published figure                          : ~99.5%")
    passed = abs(got - 0.995) < 0.005
    print(f"  RESULT: {'PASS' if passed else 'FAIL'}")
    print()
    return passed


def build_funnel(adults):
    """Independent prevalence indicators; the legacy filename is retained."""
    rows = []
    base = wtotal(adults)
    for col, label in FUNNEL:
        n = wtotal(adults, col)
        rows.append({
            "stage": label,
            "variable": col,
            "population_crore": n / 1e7,
            "pct_of_adults": n / base,
        })
    return pd.DataFrame(rows)


def conditional_table(adults, by=None):
    """Actual intersections among recent internet users, not ratios of marginals."""
    groups = [((), adults)] if not by else adults.groupby(by, observed=True)
    rows = []
    for key, d in groups:
        key = key if isinstance(key, tuple) else (key,)
        online = d[d['s5_used_internet']]
        denom = wtotal(online)
        capable = wtotal(online, 's6_can_bank_online')
        row = dict(zip(by or [], key))
        row.update(internet_users=denom, online_capable_internet_users=capable,
                   internet_users_not_online_capable=denom-capable,
                   conditional_rate=capable/denom if denom else np.nan,
                   n_internet_users=len(online))
        rows.append(row)
    return pd.DataFrame(rows)


def transition_checks(adults):
    rows = []
    for (prev, prev_label), (current, current_label) in zip(FUNNEL, FUNNEL[1:]):
        both = adults[prev] & adults[current]
        outside = ~adults[prev] & adults[current]
        rows.append({'previous': prev_label, 'current': current_label,
                     'current_outside_previous_n': int(outside.sum()),
                     'current_outside_previous_population': wtotal(adults, outside),
                     'conditional_rate': wtotal(adults, both)/wtotal(adults, prev)})
    return pd.DataFrame(rows)


def funnel_by(adults, by):
    """Same funnel, split by one or more columns, in wide form."""
    frames = []
    for col, label in FUNNEL:
        t = rate_table(adults, by, col)[by + ["rate"]]
        t["stage"] = label
        frames.append(t)
    long = pd.concat(frames)
    return long.pivot_table(index=by, columns="stage", values="rate")


def main():
    PROCESSED.mkdir(parents=True, exist_ok=True)
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    person = load_person()
    hh = load_household()
    adults = person[person["age"] >= 15].copy()

    print(f"persons loaded   : {len(person):,}")
    print(f"households loaded: {len(hh):,}")
    print(f"adults (15+)     : {len(adults):,}")
    print(f"weighted adults  : {wtotal(adults)/1e7:,.1f} crore")
    print()

    if not validation_gate(adults):
        raise SystemExit("Validation gate failed -- stopping.")
    official = official_state_check(adults)
    official.to_csv(PROCESSED / 'official_state_validation.csv', index=False)
    print(official.loc[~official.matches_published_precision].to_string(index=False))
    conditional_table(adults).to_csv(PROCESSED / 'conditional_national.csv', index=False)
    conditional_table(adults, ['sector_name', 'gender_name']).to_csv(
        PROCESSED / 'conditional_sector_gender.csv', index=False)
    transition_checks(adults).to_csv(PROCESSED / 'indicator_overlap_checks.csv', index=False)
    pd.DataFrame([{'adult_pop': wtotal(adults),
                   'upi_capable_pop': wtotal(adults, 's7_upi_capable'),
                   'upi_capable_rate': wmean(adults, 's7_upi_capable'),
                   'gap_pop': wtotal(adults, ~adults.s7_upi_capable),
                   'n_unweighted': len(adults)}]).to_csv(PROCESSED / 'national_summary.csv', index=False)

    # ---------------- 1. Funnel ----------------------------------------
    funnel = build_funnel(adults)
    funnel.to_csv(PROCESSED / "funnel_national.csv", index=False)
    print("NATIONAL INDICATORS (persons aged 15+; not sequential stages)")
    for _, r in funnel.iterrows():
        print(f"  {r['stage']:<38} {r['pct_of_adults']:6.1%}")
    print()

    funnel_by(adults, ["sector_name"]).to_csv(PROCESSED / "funnel_by_sector.csv")
    funnel_by(adults, ["sector_name", "gender_name"]).to_csv(
        PROCESSED / "funnel_by_sector_gender.csv")
    funnel_by(adults, ["age_band"]).to_csv(PROCESSED / "funnel_by_age.csv")

    # ---------------- 2. Segment gap table -----------------------------
    seg_cols = ["state", "state_code", "sector_name", "age_band", "gender_name"]
    seg = rate_table(adults, seg_cols, "s7_upi_capable")
    seg = seg.rename(columns={
        "rate": "upi_capable_rate",
        "count_weighted": "upi_capable_pop",
        "pop_weighted": "adult_pop",
    })
    seg["gap_pop"] = seg["adult_pop"] - seg["upi_capable_pop"]
    seg = seg.sort_values("gap_pop", ascending=False)
    seg.to_csv(PROCESSED / "segment_gap_table.csv", index=False)
    national_seg = rate_table(adults, ['sector_name', 'age_band', 'gender_name'], 's7_upi_capable')
    national_seg['gap_pop'] = national_seg.pop_weighted - national_seg.count_weighted
    national_seg.to_csv(PROCESSED / 'national_segments.csv', index=False)

    print("TEN LARGEST CAPABILITY GAPS BY SEGMENT")
    print("(segment = state x sector x age band x sex)")
    top = seg[~seg["unreliable"]].head(10)
    for _, r in top.iterrows():
        print(f"  {r['state'][:18]:<18} {r['sector_name']:<6} "
              f"{str(r['age_band']):<6} {r['gender_name']:<7} "
              f"rate {r['upi_capable_rate']:5.1%}   "
              f"gap {r['gap_pop']/1e6:5.2f}m people")
    print()

    # Coarser segment view, national
    for by in (["sector_name"], ["gender_name"], ["age_band"],
               ["sector_name", "gender_name"]):
        t = rate_table(adults, by, "s7_upi_capable")
        name = "_".join(c.replace("_name", "") for c in by)
        t.to_csv(PROCESSED / f"upi_rate_by_{name}.csv", index=False)

    # ---------------- 3. Barriers --------------------------------------
    # Person-level Q16 is asked only of people able to use the internet who
    # did not use it in 3 months -- a narrow group. The household-level
    # Block 5 Q5 covers every household without home internet, so it is the
    # more useful barrier variable. Both are written out.
    pb = person[person["reason_no_internet"].notna()]
    pbt = rate_table(pb, ["sector_name", "reason_no_internet"], "s1_can_use_device")
    pbt["share_within_sector"] = pbt.groupby("sector_name")["pop_weighted"].transform(
        lambda s: s / s.sum())
    pbt.to_csv(PROCESSED / "barriers_person.csv", index=False)

    hb = hh[hh["reason_no_internet_hh"].notna()].copy()
    hbt = (hb.groupby(["sector_name", "reason_no_internet_hh"], observed=True)
             .agg(n_unweighted=("weight", "size"),
                  households=("weight", "sum"))
             .reset_index())
    hbt["share_within_sector"] = hbt.groupby("sector_name")["households"].transform(
        lambda s: s / s.sum())
    hbt = hbt.sort_values(["sector_name", "households"], ascending=[True, False])
    hbt.to_csv(PROCESSED / "barriers_household.csv", index=False)

    print("WHY HOUSEHOLDS HAVE NO INTERNET AT HOME (top 5 per sector)")
    for sec in ["Rural", "Urban"]:
        print(f"  {sec}:")
        for _, r in hbt[hbt["sector_name"] == sec].head(5).iterrows():
            print(f"    {r['reason_no_internet_hh']:<36} "
                  f"{r['share_within_sector']:5.1%}  "
                  f"({r['households']/1e6:.1f}m hhlds)")
    print()

    # ---------------- 4. State file for the NPCI join ------------------
    st = rate_table(adults, ["state", "state_code"], "s7_upi_capable")
    st = st.rename(columns={
        "rate": "upi_capable_rate",
        "pop_weighted": "adult_pop",
        "count_weighted": "upi_capable_pop",
    })
    st["gap_pop"] = st["adult_pop"] - st["upi_capable_pop"]

    # Rural share of adults, a likely explanatory covariate
    rural = rate_table(adults, ["state_code"], adults["sector_name"] == "Rural")
    st = st.merge(rural[["state_code", "rate"]].rename(
        columns={"rate": "rural_share_of_adults"}), on="state_code", how="left")

    # Female capability rate, and the within-state gender gap
    fem = adults[adults["gender_name"] == "Female"]
    male = adults[adults["gender_name"] == "Male"]
    fr = rate_table(fem, ["state_code"], "s7_upi_capable")[["state_code", "rate"]]
    mr = rate_table(male, ["state_code"], "s7_upi_capable")[["state_code", "rate"]]
    st = st.merge(fr.rename(columns={"rate": "female_rate"}), on="state_code", how="left")
    st = st.merge(mr.rename(columns={"rate": "male_rate"}), on="state_code", how="left")
    st["gender_gap_pp"] = (st["male_rate"] - st["female_rate"]) * 100
    st = st.merge(official[['state_code', 'review_status', 'matches_published_precision']],
                  on='state_code', validate='one_to_one')
    coverage = adults.groupby('state_code').agg(n_fsu=('fsu', 'nunique'),
                                                n_households=('hhid', 'nunique')).reset_index()
    st = st.merge(coverage, on='state_code', validate='one_to_one')
    st = st.sort_values('state')
    st.to_csv(PROCESSED / "state_level.csv", index=False)

    print("UPI CAPABILITY BY STATE (alphabetical excerpts, n >= 30; precision unverified)")
    rel = st[~st["unreliable"]]
    for _, r in rel.head(8).iterrows():
        print(f"  {r['state'][:24]:<24} {r['upi_capable_rate']:6.1%}   "
              f"gender gap {r['gender_gap_pp']:5.1f}pp")
    print("  ...")
    for _, r in rel.tail(8).iterrows():
        print(f"  {r['state'][:24]:<24} {r['upi_capable_rate']:6.1%}   "
              f"gender gap {r['gender_gap_pp']:5.1f}pp")
    print()

    print(f"All tables written to {PROCESSED}/")


if __name__ == "__main__":
    main()
