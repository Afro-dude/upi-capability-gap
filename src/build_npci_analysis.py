"""
build_npci_analysis.py -- joins NPCI state-wise UPI volumes to the CMS-T
capability estimates and answers three questions in order.

  1. Does the 40% unattributed volume make state comparisons unusable?
  2. Does capability actually predict usage?
  3. What is the capability gap worth in transactions?

Question 1 comes first deliberately. If the answer had been yes, questions 2
and 3 would not be worth asking.
"""

import numpy as np
import pandas as pd
from scipy import stats

from cmst import load_person, rate_table, PROCESSED
from npci import load_npci, unclassified_share, quarter_totals, allocate

METHODS = ["excluded", "proportional", "by_adults", "by_capable"]


def capability_by_state():
    person = load_person()
    adults = person[person["age"] >= 15]
    return rate_table(adults, ["state"], "s7_upi_capable").rename(columns={
        "rate": "upi_capable_rate",
        "pop_weighted": "adult_pop",
        "count_weighted": "upi_capable_pop",
    })


def sensitivity(merged, unclassified_volume):
    """
    How much does the choice of allocation rule move the answer?

    Reported as the correlation between capability and per-adult usage under
    each rule, plus the Spearman rank correlation between each rule's state
    ordering and the ordering under 'excluded'.
    """
    base = allocate(merged, unclassified_volume, "excluded")
    base_order = base.set_index("state")["txn_per_adult"]

    rows = []
    for m in METHODS:
        d = allocate(merged, unclassified_volume, m)
        order = d.set_index("state")["txn_per_adult"].reindex(base_order.index)
        rows.append({
            "method": m,
            "pearson_r_vs_capability": np.corrcoef(
                d["upi_capable_rate"], d["txn_per_adult"])[0, 1],
            "spearman_vs_capability": stats.spearmanr(
                d["upi_capable_rate"], d["txn_per_adult"]).statistic,
            "rank_corr_vs_excluded": stats.spearmanr(order, base_order).statistic,
            "top_state": d.nlargest(1, "txn_per_adult")["state"].iloc[0],
        })
    return pd.DataFrame(rows)


def regression(d):
    """Fit usage on capability and return the frame with residuals attached."""
    fit = stats.linregress(d["upi_capable_rate"], d["txn_per_adult"])
    out = d.copy()
    out["predicted_txn_per_adult"] = fit.intercept + fit.slope * out["upi_capable_rate"]
    out["residual"] = out["txn_per_adult"] - out["predicted_txn_per_adult"]
    out["residual_z"] = out["residual"] / out["residual"].std()
    out["quadrant"] = np.where(
        out["residual"] > 0, "Converts above trend", "Capable but not converting")
    return out, fit


def sizing(d):
    """
    Transactions the capability gap represents, as a range.

    The benchmark is the observed national rate per capable adult. Newly
    enabled users would not transact at that rate -- they skew older, poorer
    and more rural -- so the estimate is reported at 40% and 60% of benchmark
    rather than as a point value.
    """
    per_capable_quarter = d["total_volume_mn"].sum() * 1e6 / d["upi_capable_pop"].sum()
    gap_pop = d["adult_pop"].sum() - d["upi_capable_pop"].sum()

    rows = []
    for h in (0.40, 0.60):
        q = gap_pop * per_capable_quarter * h
        rows.append({
            "haircut": h,
            "txns_per_quarter_bn": q / 1e9,
            "txns_per_month_bn": q / 3 / 1e9,
            "uplift_vs_classified_volume": q / (d["total_volume_mn"].sum() * 1e6),
        })
    return per_capable_quarter, gap_pop, pd.DataFrame(rows)


def main():
    cap = capability_by_state()
    npci = load_npci()

    # ---- 1. Is the residual fatal? ------------------------------------
    unc = unclassified_share(npci)
    unc.to_csv(PROCESSED / "npci_unclassified_share.csv", index=False)

    print("=" * 72)
    print("NPCI UNATTRIBUTED VOLUME")
    print("=" * 72)
    for _, r in unc.iterrows():
        print(f"  {r['month']} 2025 : {r['unclassified_share_volume']:.1%} of volume, "
              f"{r['unclassified_share_value']:.1%} of value")
    print()

    qt, unc_vol, unc_val = quarter_totals(npci)
    merged = qt.merge(
        cap[["state", "adult_pop", "upi_capable_rate", "upi_capable_pop",
             "n_unweighted"]],
        on="state", how="inner")
    print(f"  states matched: {len(merged)} of {len(qt)}")
    print()

    sens = sensitivity(merged, unc_vol)
    sens.to_csv(PROCESSED / "npci_allocation_sensitivity.csv", index=False)

    print("SENSITIVITY TO THE ALLOCATION RULE")
    print("  method          r vs capability   rank corr vs 'excluded'   top state")
    for _, r in sens.iterrows():
        print(f"  {r['method']:<14}  {r['pearson_r_vs_capability']:>13.3f}   "
              f"{r['rank_corr_vs_excluded']:>21.3f}   {r['top_state']}")
    print()
    print("  Excluding the residual, splitting it in proportion to observed")
    print("  volume, and splitting it by adult population all scale or shift")
    print("  every state identically, so none of them can change a ranking or")
    print("  a correlation. Only 'by_capable' moves the answer, and that rule")
    print("  is circular: it allocates by the very quantity under test.")
    print("  All results below therefore use 'excluded'.")
    print()

    # ---- 2. Does capability predict usage? ----------------------------
    d = allocate(merged, unc_vol, "excluded")
    d, fit = regression(d)
    d.to_csv(PROCESSED / "state_capability_vs_usage.csv", index=False)

    print("=" * 72)
    print("CAPABILITY vs USAGE")
    print("=" * 72)
    print(f"  R-squared : {fit.rvalue**2:.3f}")
    print(f"  p-value   : {fit.pvalue:.2e}")
    print(f"  slope     : {fit.slope:.1f} quarterly transactions per adult "
          f"per 100pp of capability")
    print()
    print("  Capability explains about 40% of the variation in per-adult usage.")
    print("  The other 60% is a second problem, and it has a geography.")
    print()

    print("CAPABLE BUT NOT CONVERTING (largest negative residuals)")
    for _, r in d.nsmallest(6, "residual").iterrows():
        print(f"  {r['state'][:20]:<20} capable {r['upi_capable_rate']:5.1%}   "
              f"actual {r['txn_per_adult']:6.1f}   expected "
              f"{r['predicted_txn_per_adult']:6.1f}   ({r['residual']:+.1f})")
    print()
    print("CONVERTING ABOVE TREND (largest positive residuals)")
    for _, r in d.nlargest(6, "residual").iterrows():
        print(f"  {r['state'][:20]:<20} capable {r['upi_capable_rate']:5.1%}   "
              f"actual {r['txn_per_adult']:6.1f}   expected "
              f"{r['predicted_txn_per_adult']:6.1f}   ({r['residual']:+.1f})")
    print()

    # ---- 3. What is the gap worth? ------------------------------------
    per_capable, gap_pop, sz = sizing(d)
    sz.to_csv(PROCESSED / "opportunity_sizing.csv", index=False)

    print("=" * 72)
    print("SIZING THE GAP")
    print("=" * 72)
    print(f"  benchmark: {per_capable:.1f} transactions per capable adult per quarter")
    print(f"  gap population: {gap_pop/1e7:.1f} crore adults")
    print()
    for _, r in sz.iterrows():
        print(f"  at {r['haircut']:.0%} of benchmark intensity: "
              f"{r['txns_per_month_bn']:.2f} bn transactions/month "
              f"({r['uplift_vs_classified_volume']:.0%} uplift on attributed volume)")
    print()
    print("  Reported as a range, not a point estimate. Newly enabled users skew")
    print("  older, poorer and more rural than the existing base and would not")
    print("  transact at the current average rate.")
    print()
    print(f"Tables written to {PROCESSED}/")


if __name__ == "__main__":
    main()
