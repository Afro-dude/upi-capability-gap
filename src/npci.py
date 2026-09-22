"""
npci.py -- NPCI state-wise UPI statistics, joined to the CMS-T capability file.

Source: NPCI Ecosystem Statistics -> UPI Statewise Statistics, monthly XLSX.
Months used: Jan, Feb, Mar 2025 -- chosen to match the CMS-T field period
exactly, so capability and transaction volume describe the same quarter.

The supplied workbooks leave a large share of transaction volume without a
state attribution, labelled 'UNCLASSIFIED#': 34.6% to 39.9% each month.
The workbooks do not establish the collection mechanism or payer residence.
Observed per-capita comparisons use classified volume only. Allocations of
unclassified volume are explicitly hypothetical, not recovered observations.
"""

import re
from pathlib import Path

import numpy as np
import pandas as pd

from cmst import RAW, STATE_NAMES

NPCI_DIR = RAW / "npci"

# NPCI writes state names differently from the NSS code list. Only the
# genuinely ambiguous ones need mapping; the rest match on uppercase.
NPCI_TO_NSS = {
    "JAMMU AND KASHMIR": "Jammu & Kashmir",
    "DADRA & NAGAR HAVELI & DAMAN & DIU": "D&N Haveli & Daman & Diu",
    "ANDAMAN & NICOBAR": "Andaman & N. Islands",
}
_UPPER_TO_NSS = {v.upper(): v for v in STATE_NAMES.values()}

UNCLASSIFIED = "UNCLASSIFIED#"


def _read_month(path):
    """One monthly XLSX. Row 0 is a title; the real header is row 1."""
    df = pd.read_excel(path, header=1)
    df = df[df["State / Union Territory"].notna()].copy()

    for col in ["Volume (in Mn)", "Value (in Cr.)"]:
        df[col] = (df[col].astype(str)
                          .str.replace(",", "", regex=False)
                          .astype(float))

    df["state_npci"] = df["State / Union Territory"].str.strip().str.upper()
    df["month"] = re.search(r"2025-(\w+)", path.name).group(1)
    return df.rename(columns={"Volume (in Mn)": "volume_mn",
                              "Value (in Cr.)": "value_cr"})[
        ["month", "state_npci", "volume_mn", "value_cr"]]


def load_npci():
    """Exactly Q1 2025, long form, with NSS state names attached."""
    paths = sorted(NPCI_DIR.glob("upi_statewise_2025-*.xlsx"))
    if not paths:
        raise FileNotFoundError(
            f"No NPCI files in {NPCI_DIR}. Download 'UPI Statewise Statistics' "
            "from npci.org.in and save as upi_statewise_2025-<Mon>.xlsx"
        )
    expected = {f'upi_statewise_2025-{m}.xlsx' for m in ('Jan', 'Feb', 'Mar')}
    if {p.name for p in paths} != expected:
        raise ValueError('Expected exactly Jan, Feb and Mar 2025 NPCI workbooks')
    df = pd.concat([_read_month(p) for p in paths], ignore_index=True)

    def to_nss(name):
        if name == UNCLASSIFIED:
            return None
        return NPCI_TO_NSS.get(name) or _UPPER_TO_NSS.get(name)

    df["state"] = df["state_npci"].map(to_nss)

    unmatched = set(df.loc[df["state"].isna(), "state_npci"]) - {UNCLASSIFIED}
    if unmatched:
        raise ValueError(f"Unmapped NPCI state names: {sorted(unmatched)}")
    for month, group in df.groupby('month'):
        if group.state_npci.duplicated().any() or len(group) != 37:
            raise ValueError(f'{month}: expected 36 unique states plus one unclassified row')
        if set(group.state.dropna()) != set(STATE_NAMES.values()):
            raise ValueError(f'{month}: incomplete state coverage')
        if group[['volume_mn', 'value_cr']].isna().any().any() or (group[['volume_mn', 'value_cr']] < 0).any().any():
            raise ValueError(f'{month}: invalid volume or value')

    return df


def unclassified_share(npci):
    """Share of volume and value NPCI cannot attribute, by month."""
    rows = []
    for m, g in npci.groupby("month"):
        unc = g[g["state_npci"] == UNCLASSIFIED]
        rows.append({
            "month": m,
            "total_volume_mn": g["volume_mn"].sum(),
            "unclassified_volume_mn": unc["volume_mn"].sum(),
            "unclassified_share_volume": unc["volume_mn"].sum() / g["volume_mn"].sum(),
            "unclassified_share_value": unc["value_cr"].sum() / g["value_cr"].sum(),
        })
    order = {"Jan": 1, "Feb": 2, "Mar": 3}
    return pd.DataFrame(rows).sort_values("month", key=lambda s: s.map(order))


def quarter_totals(npci):
    """Sum the three months into one Q1 2025 figure per state."""
    known = npci[npci["state"].notna()]
    out = (known.groupby("state", as_index=False)
                .agg(volume_mn=("volume_mn", "sum"),
                     value_cr=("value_cr", "sum")))
    unc = npci[npci["state_npci"] == UNCLASSIFIED]
    return out, float(unc["volume_mn"].sum()), float(unc["value_cr"].sum())


def allocate(state_df, unclassified_volume, method):
    """
    Distribute the unattributed volume across states under one assumption.

    excluded     -- classified volume only; missing state shares are unknown.
    proportional -- split in proportion to each state's observed volume.
    by_adults    -- split in proportion to adult population.
    by_capable   -- split in proportion to UPI-capable adult population.
    by_gap       -- hypothetical allocation by excluded population (also circular).

    'proportional' is a useful control: because it scales every state by the
    same constant, it cannot change per-capita *rankings* at all. Any ranking
    invariance is a property of that assumption, not validation of true ranks.
    """
    d = state_df.copy()
    if unclassified_volume < 0 or not np.isfinite(unclassified_volume):
        raise ValueError('Unclassified volume must be finite and nonnegative')
    if (d[['adult_pop', 'upi_capable_pop']] <= 0).any().any():
        raise ValueError('Population denominators must be positive')
    if method == "excluded":
        d["allocated_mn"] = 0.0
    elif method == "proportional":
        d["allocated_mn"] = unclassified_volume * d["volume_mn"] / d["volume_mn"].sum()
    elif method == "by_adults":
        d["allocated_mn"] = unclassified_volume * d["adult_pop"] / d["adult_pop"].sum()
    elif method == "by_capable":
        d["allocated_mn"] = unclassified_volume * d["upi_capable_pop"] / d["upi_capable_pop"].sum()
    elif method == 'by_gap':
        gap = d.adult_pop - d.upi_capable_pop
        if (gap < 0).any() or gap.sum() <= 0:
            raise ValueError('Gap allocation requires a positive excluded population')
        d['allocated_mn'] = unclassified_volume * gap / gap.sum()
    else:
        raise ValueError(method)

    d["total_volume_mn"] = d["volume_mn"] + d["allocated_mn"]
    d["txn_per_adult"] = d["total_volume_mn"] * 1e6 / d["adult_pop"]
    d["txn_per_capable_adult"] = d["total_volume_mn"] * 1e6 / d["upi_capable_pop"]
    d["method"] = method
    return d
