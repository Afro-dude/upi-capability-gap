"""
build_analysis.py -- runs the full analysis and writes every processed table.

Order of operations:
  0. Validation gate: reproduce a published CMS-T figure.
  1. Adoption funnel, national and by sector.
  2. Segment gap table (state x sector x age x sex).
  3. Barrier diagnosis.
  4. State-level file, ready to join to NPCI transaction data.
"""

import numpy as np
import pandas as pd

from cmst import (
    load_person, load_household, wmean, wtotal, rate_table,
    PROCESSED, OUTPUTS, AGE_LABELS,
)

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
    """National funnel with absolute and conditional retention rates."""
    rows = []
    base = wtotal(adults)
    prev = base
    for col, label in FUNNEL:
        n = wtotal(adults, col)
        rows.append({
            "stage": label,
            "variable": col,
            "population_crore": n / 1e7,
            "pct_of_adults": n / base,
            "retention_from_prev": n / prev if prev else np.nan,
            "lost_here_crore": (prev - n) / 1e7,
        })
        prev = n
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

    # ---------------- 1. Funnel ----------------------------------------
    funnel = build_funnel(adults)
    funnel.to_csv(PROCESSED / "funnel_national.csv", index=False)
    print("NATIONAL ADOPTION FUNNEL (adults 15+)")
    for _, r in funnel.iterrows():
        print(f"  {r['stage']:<38} {r['pct_of_adults']:6.1%}"
              f"   (retains {r['retention_from_prev']:5.1%} of previous)")
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

    # Empty columns for the NPCI merge -- see docs/npci_join_template.csv
    st["npci_monthly_txn_volume"] = np.nan
    st["npci_monthly_txn_value_cr"] = np.nan

    st = st.sort_values("upi_capable_rate", ascending=False)
    st.to_csv(PROCESSED / "state_level.csv", index=False)

    print("UPI CAPABILITY BY STATE (top 8 and bottom 8, reliable cells only)")
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
