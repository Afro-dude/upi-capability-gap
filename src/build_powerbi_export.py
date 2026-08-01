"""
build_powerbi_export.py -- reshapes the processed tables into a star schema
for Power BI.

The Streamlit app reads the analysis tables directly because Python can join
whatever it likes at runtime. Power BI wants the opposite: narrow fact tables,
separate dimension tables, and relationships defined once in the model. Feeding
it wide denormalised CSVs works but produces a mess -- duplicated attributes,
no shared slicers, and measures that cannot be reused across visuals.

Output goes to data/powerbi/ as one folder of CSVs to load as a single source.

    Dimensions          Facts
    ----------          -----
    dim_state           fct_segment       (state x sector x age x sex)
    dim_sector          fct_state         (state, incl. NPCI transactions)
    dim_age_band        fct_funnel        (national adoption stages)
    dim_sex             fct_barriers      (household reasons, by sector)
                        fct_sensitivity   (allocation-rule comparison)
"""

from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent.parent
PROCESSED = BASE / "data" / "processed"
OUT = BASE / "data" / "powerbi"

AGE_ORDER = ["15-24", "25-34", "35-44", "45-59", "60+"]


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    seg = pd.read_csv(PROCESSED / "segment_gap_table.csv")
    seg = seg[seg["gender_name"] != "Transgender"].copy()
    state = pd.read_csv(PROCESSED / "state_level.csv")
    cvu = pd.read_csv(PROCESSED / "state_capability_vs_usage.csv")
    funnel = pd.read_csv(PROCESSED / "funnel_national.csv")
    barriers = pd.read_csv(PROCESSED / "barriers_household.csv")
    sens = pd.read_csv(PROCESSED / "npci_allocation_sensitivity.csv")
    unc = pd.read_csv(PROCESSED / "npci_unclassified_share.csv")

    # ---------------- dimensions ---------------------------------------
    dim_state = state[["state", "state_code", "rural_share_of_adults"]].copy()
    dim_state["state_code"] = dim_state["state_code"].astype(str).str.zfill(2)
    # A region attribute makes the Northeast finding a one-click slicer
    NORTHEAST = {"Arunachal Pradesh", "Assam", "Manipur", "Meghalaya", "Mizoram",
                 "Nagaland", "Sikkim", "Tripura"}
    HILL = {"Himachal Pradesh", "Jammu & Kashmir", "Ladakh", "Uttarakhand"}
    UT_SMALL = {"Chandigarh", "Puducherry", "Lakshadweep", "Andaman & N. Islands",
                "D&N Haveli & Daman & Diu", "Delhi", "Goa"}

    def region(s):
        if s in NORTHEAST:
            return "Northeast"
        if s in HILL:
            return "Hill states"
        if s in UT_SMALL:
            return "Small state / UT"
        return "Other"

    dim_state["region"] = dim_state["state"].map(region)
    dim_state.to_csv(OUT / "dim_state.csv", index=False)

    pd.DataFrame({"sector": ["Rural", "Urban"], "sector_sort": [1, 2]}) \
        .to_csv(OUT / "dim_sector.csv", index=False)

    pd.DataFrame({"age_band": AGE_ORDER,
                  "age_sort": range(1, len(AGE_ORDER) + 1),
                  "age_group_broad": ["Under 35", "Under 35", "35-59",
                                      "35-59", "60+"]}) \
        .to_csv(OUT / "dim_age_band.csv", index=False)

    pd.DataFrame({"sex": ["Female", "Male"], "sex_sort": [1, 2]}) \
        .to_csv(OUT / "dim_sex.csv", index=False)

    # ---------------- facts --------------------------------------------
    # Additive columns only. Rates are deliberately NOT stored -- Power BI must
    # compute them as measures, or averaging a rate across states silently
    # weights every state equally regardless of population.
    fct_segment = seg.rename(columns={
        "sector_name": "sector", "gender_name": "sex",
        "adult_pop": "adults", "upi_capable_pop": "capable_adults",
        "gap_pop": "excluded_adults", "n_unweighted": "sample_n",
    })[["state", "sector", "age_band", "sex",
        "adults", "capable_adults", "excluded_adults", "sample_n"]]
    fct_segment.to_csv(OUT / "fct_segment.csv", index=False)

    fct_state = (state[["state", "adult_pop", "upi_capable_pop", "gap_pop",
                        "n_unweighted", "female_rate", "male_rate",
                        "gender_gap_pp"]]
                 .merge(cvu[["state", "total_volume_mn", "value_cr",
                             "txn_per_adult", "txn_per_capable_adult",
                             "predicted_txn_per_adult", "residual"]],
                        on="state", how="left")
                 .rename(columns={"adult_pop": "adults",
                                  "upi_capable_pop": "capable_adults",
                                  "gap_pop": "excluded_adults",
                                  "n_unweighted": "sample_n",
                                  "total_volume_mn": "txn_volume_mn",
                                  "value_cr": "txn_value_cr"}))
    fct_state["performance"] = fct_state["residual"].apply(
        lambda r: "Converts above trend" if r >= 0 else "Capable but not converting")
    fct_state.to_csv(OUT / "fct_state.csv", index=False)

    funnel = funnel.copy()
    funnel["stage_sort"] = range(1, len(funnel) + 1)
    funnel.rename(columns={"pct_of_adults": "share_of_adults"}) \
          .to_csv(OUT / "fct_funnel.csv", index=False)

    BARRIER_GROUP = {
        "Don't know how to use it": "Digital literacy",
        "Don't know what internet is": "Digital literacy",
        "Do not need it": "No perceived need",
        "Available but doesn't meet needs": "No perceived need",
        "Have internet access elsewhere": "No perceived need",
        "Lack of local content": "No perceived need",
        "Equipment cost too high": "Cost",
        "Service cost too high": "Cost",
        "Not available in area": "Availability / supply",
        "No electricity": "Availability / supply",
        "Others": "Other",
        "Privacy/security concerns": "Other",
        "Cultural reasons / harmful content": "Other",
    }
    b = barriers.rename(columns={"sector_name": "sector",
                                 "reason_no_internet_hh": "reason",
                                 "n_unweighted": "sample_n"}).copy()
    b["barrier_group"] = b["reason"].map(BARRIER_GROUP)
    unmapped = b.loc[b["barrier_group"].isna(), "reason"].unique()
    if len(unmapped):
        raise ValueError(f"Unmapped barrier reasons: {list(unmapped)}")
    b[["sector", "reason", "barrier_group", "households", "sample_n"]] \
        .to_csv(OUT / "fct_barriers.csv", index=False)

    sens.rename(columns={
        "method": "allocation_rule",
        "pearson_r_vs_capability": "correlation_with_capability",
        "rank_corr_vs_excluded": "rank_agreement_with_excluded",
        "top_state": "highest_usage_state",
    }).to_csv(OUT / "fct_sensitivity.csv", index=False)

    unc.to_csv(OUT / "fct_unclassified.csv", index=False)

    print(f"Power BI star schema written to {OUT}/")
    for f in sorted(OUT.glob("*.csv")):
        d = pd.read_csv(f)
        print(f"  {f.name:<26} {len(d):>4} rows  {len(d.columns)} cols")

    # Integrity: every fact key must exist in its dimension
    states = set(dim_state["state"])
    assert set(fct_segment["state"]) <= states, "segment has unknown states"
    assert set(fct_state["state"]) <= states, "state fact has unknown states"
    assert set(fct_segment["age_band"]) <= set(AGE_ORDER), "unknown age band"
    print("\n  referential integrity: OK")


if __name__ == "__main__":
    main()
