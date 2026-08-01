"""
build_charts.py -- the four figures that carry the argument.

  fig1  the funnel, showing where adults are lost
  fig2  barrier composition: skill vs cost vs availability
  fig3  the conversion gap -- who is online but cannot transact
  fig4  state ranking with the within-state gender gap
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from cmst import load_person, load_household, wmean, wtotal, rate_table, OUTPUTS
from build_analysis import build_funnel, FUNNEL

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "grid.linestyle": "-",
    "figure.dpi": 130,
})

INK = "#1a1a1a"
ACCENT = "#c1440e"
MUTED = "#8a8a8a"
COOL = "#2c6e91"


def fig1_funnel(adults):
    f = build_funnel(adults)
    fig, ax = plt.subplots(figsize=(9, 5))

    y = np.arange(len(f))[::-1]
    pct = f["pct_of_adults"].values
    colors = [ACCENT if s == "Able to transact online" else COOL for s in f["stage"]]

    ax.barh(y, pct, color=colors, height=0.62)
    for yi, p, ret in zip(y, pct, f["retention_from_prev"]):
        ax.text(p + 0.012, yi, f"{p:.0%}", va="center", fontsize=10, color=INK)
        if ret < 0.95:
            ax.text(p / 2, yi, f"loses {1-ret:.0%}", va="center", ha="center",
                    fontsize=9, color="white", weight="bold")

    ax.set_yticks(y)
    ax.set_yticklabels(f["stage"])
    ax.set_xlim(0, 1.06)
    ax.set_xticks(np.arange(0, 1.01, 0.2))
    ax.xaxis.set_major_formatter(lambda x, _: f"{x:.0%}")
    ax.set_xlabel("Share of adults aged 15+")
    ax.set_title("The bottleneck is not connectivity\n"
                 "Digital payment adoption funnel, India, Jan–Mar 2025",
                 loc="left", fontsize=13, weight="bold", color=INK, pad=14)
    fig.tight_layout()
    fig.savefig(OUTPUTS / "fig1_funnel.png", bbox_inches="tight")
    plt.close(fig)


def fig2_barriers(hh):
    hb = hh[hh["reason_no_internet_hh"].notna()]
    t = (hb.groupby("reason_no_internet_hh")["weight"].sum()
           .sort_values(ascending=False))
    share = t / t.sum()

    groups = {
        "Digital literacy": ["Don't know how to use it", "Don't know what internet is"],
        "No perceived need": ["Do not need it", "Available but doesn't meet needs",
                              "Have internet access elsewhere", "Lack of local content"],
        "Cost": ["Equipment cost too high", "Service cost too high"],
        "Availability / supply": ["Not available in area", "No electricity"],
        "Other": ["Others", "Privacy/security concerns",
                  "Cultural reasons / harmful content"],
    }
    agg = {g: share.reindex(items).fillna(0).sum() for g, items in groups.items()}
    agg = pd.Series(agg).sort_values(ascending=True)

    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    colors = [ACCENT if g == "Digital literacy" else MUTED for g in agg.index]
    ax.barh(agg.index, agg.values, color=colors, height=0.6)
    for i, v in enumerate(agg.values):
        ax.text(v + 0.008, i, f"{v:.0%}", va="center", fontsize=10, color=INK)

    ax.set_xlim(0, max(agg.values) * 1.18)
    ax.xaxis.set_major_formatter(lambda x, _: f"{x:.0%}")
    ax.set_xlabel("Share of households without home internet")
    ax.set_title("Skill, not supply, keeps households offline\n"
                 "Stated main reason for no internet at home, 4.2 crore households",
                 loc="left", fontsize=13, weight="bold", color=INK, pad=14)
    fig.tight_layout()
    fig.savefig(OUTPUTS / "fig2_barriers.png", bbox_inches="tight")
    plt.close(fig)


def fig3_conversion(adults):
    """Among people already using the internet, who can transact?"""
    online = adults[adults["s5_used_internet"]]
    cells = []
    for sec in ["Rural", "Urban"]:
        for g in ["Male", "Female"]:
            d = online[(online["sector_name"] == sec) & (online["gender_name"] == g)]
            cells.append({"sector": sec, "gender": g,
                          "conv": wmean(d, "s6_can_bank_online"),
                          "pop": wtotal(d)})
    c = pd.DataFrame(cells)

    fig, ax = plt.subplots(figsize=(7.5, 4.4))
    x = np.arange(2)
    w = 0.36
    male = c[c["gender"] == "Male"].set_index("sector").loc[["Rural", "Urban"], "conv"]
    fem = c[c["gender"] == "Female"].set_index("sector").loc[["Rural", "Urban"], "conv"]

    ax.bar(x - w / 2, male.values, w, label="Male", color=COOL)
    ax.bar(x + w / 2, fem.values, w, label="Female", color=ACCENT)
    for xi, v in zip(x - w / 2, male.values):
        ax.text(xi, v + 0.015, f"{v:.0%}", ha="center", fontsize=10)
    for xi, v in zip(x + w / 2, fem.values):
        ax.text(xi, v + 0.015, f"{v:.0%}", ha="center", fontsize=10)

    ax.set_xticks(x)
    ax.set_xticklabels(["Rural", "Urban"])
    ax.set_ylim(0, 1)
    ax.yaxis.set_major_formatter(lambda y, _: f"{y:.0%}")
    ax.set_ylabel("Able to transact online")
    ax.legend(frameon=False, loc="upper left")
    ax.set_title("The gap survives connectivity\n"
                 "Share able to transact online, among adults who already use the internet",
                 loc="left", fontsize=13, weight="bold", color=INK, pad=14)
    fig.tight_layout()
    fig.savefig(OUTPUTS / "fig3_conversion.png", bbox_inches="tight")
    plt.close(fig)


def fig4_states(adults):
    st = rate_table(adults, ["state"], "s7_upi_capable")
    fem = rate_table(adults[adults["gender_name"] == "Female"], ["state"], "s7_upi_capable")
    male = rate_table(adults[adults["gender_name"] == "Male"], ["state"], "s7_upi_capable")
    st = (st.merge(fem[["state", "rate"]].rename(columns={"rate": "f"}), on="state")
            .merge(male[["state", "rate"]].rename(columns={"rate": "m"}), on="state"))
    st = st[~st["unreliable"]].sort_values("rate")

    fig, ax = plt.subplots(figsize=(8.5, 10))
    y = np.arange(len(st))
    ax.hlines(y, st["f"], st["m"], color="#d5d5d5", lw=2.4, zorder=1)
    ax.scatter(st["f"], y, s=38, color=ACCENT, zorder=3, label="Female")
    ax.scatter(st["m"], y, s=38, color=COOL, zorder=3, label="Male")

    ax.set_yticks(y)
    ax.set_yticklabels(st["state"], fontsize=9)
    ax.set_xlim(0, 1)
    ax.xaxis.set_major_formatter(lambda x, _: f"{x:.0%}")
    ax.set_xlabel("Share of adults 15+ able to transact via UPI")
    ax.legend(frameon=False, loc="lower right")
    ax.set_title("Two different problems, depending on the state\n"
                 "UPI capability by state and sex; bar length is the gender gap",
                 loc="left", fontsize=13, weight="bold", color=INK, pad=14)
    fig.tight_layout()
    fig.savefig(OUTPUTS / "fig4_states.png", bbox_inches="tight")
    plt.close(fig)


def fig5_capability_vs_usage():
    """The merge chart: does capability predict usage, and who deviates?"""
    from scipy import stats as _st
    from cmst import load_person as _lp
    from npci import load_npci, quarter_totals, allocate
    from build_npci_analysis import capability_by_state

    cap = capability_by_state()
    npci = load_npci()
    qt, unc_vol, _ = quarter_totals(npci)
    d = qt.merge(cap[["state", "adult_pop", "upi_capable_rate",
                      "upi_capable_pop"]], on="state")
    d = allocate(d, unc_vol, "excluded")

    fit = _st.linregress(d["upi_capable_rate"], d["txn_per_adult"])
    d["resid"] = d["txn_per_adult"] - (fit.intercept + fit.slope * d["upi_capable_rate"])

    fig, ax = plt.subplots(figsize=(9.5, 6.5))

    xs = np.linspace(d["upi_capable_rate"].min() - 0.03,
                     d["upi_capable_rate"].max() + 0.03, 50)
    ax.plot(xs, fit.intercept + fit.slope * xs, color=MUTED, lw=1.2,
            ls="--", zorder=1)

    below = d[d["resid"] < 0]
    above = d[d["resid"] >= 0]
    ax.scatter(above["upi_capable_rate"], above["txn_per_adult"],
               s=46, color=COOL, zorder=3, label="Converts above trend")
    ax.scatter(below["upi_capable_rate"], below["txn_per_adult"],
               s=46, color=ACCENT, zorder=3, label="Capable but not converting")

    # Label only the states that carry the argument: the clear over- and
    # under-performers, plus Tripura at the extreme low end. States sitting on
    # the trend line are left unlabelled -- they illustrate the fit rather than
    # deviate from it, and naming them only adds clutter.
    #
    # Chhattisgarh and West Bengal nearly coincide, as do Mizoram and Sikkim.
    # Each pair is split across opposite sides of its markers, and the vertical
    # offset follows the dot's actual position -- the lower dot gets the lower
    # label. Same-side placement leaves it ambiguous which label belongs to
    # which point, and an inverted offset is worse than none.
    labels = {
        "Goa":              (9, -1, "left"),
        "Delhi":            (9, -1, "left"),
        "Telangana":        (9, -1, "left"),
        "Chandigarh":       (-9, -1, "right"),
        "Maharashtra":      (9, -1, "left"),
        "Manipur":          (9, -1, "left"),
        "Himachal Pradesh": (9, -1, "left"),
        "Meghalaya":        (9, -1, "left"),
        "Tripura":          (9, -1, "left"),
        "Bihar":            (9, -1, "left"),
        "Mizoram":          (9, -7, "left"),    # rightmost, lower
        "Sikkim":           (-9, 9, "right"),   # leftmost, higher
        "Chhattisgarh":     (-9, 8, "right"),   # higher of the pair
        "West Bengal":      (9, -8, "left"),    # lower of the pair
    }
    for name, (dx, dy, ha) in labels.items():
        row = d[d["state"] == name]
        if not row.shape[0]:
            continue
        ax.annotate(name,
                    (row["upi_capable_rate"].iloc[0],
                     row["txn_per_adult"].iloc[0]),
                    textcoords="offset points", xytext=(dx, dy),
                    ha=ha, va="center", fontsize=8.5, color=INK)

    ax.xaxis.set_major_formatter(lambda x, _: f"{x:.0%}")
    ax.set_xlabel("Share of adults able to transact via UPI")
    ax.set_ylabel("UPI transactions per adult, Q1 2025")
    ax.legend(frameon=False, loc="upper left")
    ax.set_title(f"Capability explains about 40% of the story\n"
                 f"State UPI usage against capability  (R² = {fit.rvalue**2:.2f})",
                 loc="left", fontsize=13, weight="bold", color=INK, pad=14)
    fig.tight_layout()
    fig.savefig(OUTPUTS / "fig5_capability_vs_usage.png", bbox_inches="tight")
    plt.close(fig)


def main():
    person = load_person()
    hh = load_household()
    adults = person[person["age"] >= 15].copy()

    fig1_funnel(adults)
    fig2_barriers(hh)
    fig3_conversion(adults)
    fig4_states(adults)

    try:
        fig5_capability_vs_usage()
        n = 5
    except FileNotFoundError as e:
        print(f"skipping fig5 (NPCI data not present): {e}")
        n = 4
    print(f"{n} figures written to {OUTPUTS}/")


if __name__ == "__main__":
    main()
