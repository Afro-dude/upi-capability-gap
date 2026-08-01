"""
cmst.py -- loading and variable construction for NSS 80th Round
Comprehensive Modular Survey: Telecom (Jan-Mar 2025).

All code definitions are taken from the official schedule (Volume_II_CMST.pdf,
Block 3 / Block 4 / Block 5) and the data layout (Data_Layout_CMST_2025.xlsx).

Key facts encoded here, each traceable to a source document:
  * Final weight = mlt / 100                     (README_CMST_2025.docx)
  * State code  = first 2 digits of nss_reg      (README_CMST_2025.docx)
  * Household key = fsu + ssu                    (README_CMST_2025.docx)
  * Block 4 is asked only of persons aged >= 3 who can use a mobile phone
    OR a computer (Block 3, cols 5/6). Q11/Q12 are further restricted to
    age >= 15.                                   (Volume_II_CMST.pdf, Block 4)
"""

from pathlib import Path
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent.parent
RAW = BASE / "data" / "raw"
PROCESSED = BASE / "data" / "processed"
OUTPUTS = BASE / "outputs"

# --------------------------------------------------------------------------
# State codes -- Data_Layout_CMST_2025.xlsx, sheet "State code"
# --------------------------------------------------------------------------
STATE_NAMES = {
    "01": "Jammu & Kashmir", "02": "Himachal Pradesh", "03": "Punjab",
    "04": "Chandigarh", "05": "Uttarakhand", "06": "Haryana", "07": "Delhi",
    "08": "Rajasthan", "09": "Uttar Pradesh", "10": "Bihar", "11": "Sikkim",
    "12": "Arunachal Pradesh", "13": "Nagaland", "14": "Manipur",
    "15": "Mizoram", "16": "Tripura", "17": "Meghalaya", "18": "Assam",
    "19": "West Bengal", "20": "Jharkhand", "21": "Odisha",
    "22": "Chhattisgarh", "23": "Madhya Pradesh", "24": "Gujarat",
    "25": "D&N Haveli & Daman & Diu", "27": "Maharashtra",
    "28": "Andhra Pradesh", "29": "Karnataka", "30": "Goa",
    "31": "Lakshadweep", "32": "Kerala", "33": "Tamil Nadu",
    "34": "Puducherry", "35": "Andaman & N. Islands", "36": "Telangana",
    "37": "Ladakh",
}

SECTOR = {1: "Rural", 2: "Urban"}
GENDER = {1: "Male", 2: "Female", 3: "Transgender"}

# Block 4 Q16 -- reason for NOT using internet (person level)
REASON_PERSON = {
    1: "Not available in area", 2: "Available but doesn't meet needs",
    3: "Don't know how to use it", 4: "Don't know what internet is",
    5: "Do not need it", 6: "Not allowed to use it",
    7: "Equipment cost too high", 8: "Service cost too high",
    9: "Lack of local content", 10: "Privacy/security concerns", 99: "Others",
}

# Block 5 Q5 -- reason household has no internet at home
REASON_HH = {
    1: "Not available in area", 2: "Available but doesn't meet needs",
    3: "Don't know how to use it", 4: "Don't know what internet is",
    5: "Do not need it", 6: "Cultural reasons / harmful content",
    7: "Equipment cost too high", 8: "Service cost too high",
    9: "Lack of local content", 10: "Privacy/security concerns",
    11: "No electricity", 12: "Have internet access elsewhere", 99: "Others",
}

AGE_BANDS = [(15, 24), (25, 34), (35, 44), (45, 59), (60, 200)]
AGE_LABELS = ["15-24", "25-34", "35-44", "45-59", "60+"]


def _clean(df):
    """Strip whitespace from string columns; blanks become NaN."""
    for c in df.columns:
        if df[c].dtype == object:
            df[c] = df[c].astype(str).str.strip().replace({"": np.nan, "nan": np.nan})
    return df


def _num(s):
    return pd.to_numeric(s, errors="coerce")


def load_person():
    df = _clean(pd.read_stata(RAW / "CMST80PER.dta", convert_categoricals=False))

    df["age"] = _num(df["age"])
    df["weight"] = _num(df["mlt"]) / 100.0          # README: Final Weight = MLT/100
    df["state_code"] = df["nss_reg"].str[:2]         # README: first 2 digits
    df["state"] = df["state_code"].map(STATE_NAMES)
    df["hhid"] = df["fsu"].astype(str) + "-" + df["ssu"].astype(str)
    df["sector_name"] = _num(df["sector"]).map(SECTOR)
    df["gender_name"] = _num(df["gender"]).map(GENDER)

    df["age_band"] = pd.cut(
        df["age"],
        bins=[b[0] for b in AGE_BANDS] + [201],
        labels=AGE_LABELS,
        right=False,
    )

    # ---------------- Funnel stages -------------------------------------
    # Every stage is defined so that "not routed to the question" resolves
    # to False. This is correct: a person who cannot use a mobile phone or a
    # computer at all is definitionally not capable of a UPI transaction, and
    # the schedule simply does not ask them the downstream questions.

    q3, q4, q8 = _num(df["b4q3"]), _num(df["b4q4"]), _num(df["b4q8"])
    q9, q10, q12 = _num(df["b4q9"]), _num(df["b4q10"]), _num(df["b4q12"])

    # Stage 1: can operate a mobile phone or a computer (Block 3, col 5/6)
    df["s1_can_use_device"] = (_num(df["use_mobile"]) == 1) | (_num(df["use_comp"]) == 1)

    # Stage 2: had access to any mobile phone in last 3 months (Q3 codes 1,2,3)
    df["s2_had_phone"] = q3.isin([1, 2, 3])

    # Stage 3: used a smartphone in last 3 months (Q4 == 1)
    df["s3_used_smartphone"] = q4 == 1

    # Stage 4: able to use the internet (Q9 codes 1,2,3)
    df["s4_can_use_internet"] = q9.isin([1, 2, 3])

    # Stage 5: actually used internet in last 3 months (Q10 == 1)
    df["s5_used_internet"] = q10 == 1

    # Stage 6: able to transact online by any means (Q12 codes 1,2,3)
    df["s6_can_bank_online"] = q12.isin([1, 2, 3])

    # Stage 7: able to transact via UPI (Q12 codes 1 or 3)
    df["s7_upi_capable"] = q12.isin([1, 3])

    # Net-banking only, i.e. online-capable but NOT via UPI (Q12 == 2)
    df["non_upi_only"] = q12 == 2

    df["reason_no_internet"] = _num(df["b4q16"]).map(REASON_PERSON)
    df["used_computer_3m"] = q8 == 1

    return df


def load_household():
    df = _clean(pd.read_stata(RAW / "CMST80HH.dta", convert_categoricals=False))

    df["weight"] = _num(df["mlt"]) / 100.0
    df["state_code"] = df["nss_reg"].str[:2]
    df["state"] = df["state_code"].map(STATE_NAMES)
    df["hhid"] = df["fsu"].astype(str) + "-" + df["ssu"].astype(str)
    df["sector_name"] = _num(df["sector"]).map(SECTOR)

    df["hh_size"] = _num(df["b3q2"])
    df["mpce"] = _num(df["b3q5"])            # auxiliary variable -- see DATA_NOTES
    df["online_purchase"] = _num(df["b3q6"]).isin([1, 2, 3])
    df["has_internet_home"] = _num(df["b5q2"]) == 1
    df["has_landline"] = _num(df["b5q1"]) == 1
    df["reason_no_internet_hh"] = _num(df["b5q5"]).map(REASON_HH)

    return df


# --------------------------------------------------------------------------
# Weighted estimation helpers
# --------------------------------------------------------------------------

def wmean(df, flag, weight="weight"):
    """Weighted proportion of `flag` (a boolean column or Series)."""
    f = df[flag] if isinstance(flag, str) else flag
    w = df[weight]
    denom = w.sum()
    return np.nan if denom == 0 else float((w * f).sum() / denom)


def wtotal(df, flag=None, weight="weight"):
    """Weighted population total, optionally restricted to `flag`."""
    if flag is None:
        return float(df[weight].sum())
    f = df[flag] if isinstance(flag, str) else flag
    return float((df[weight] * f).sum())


def rate_table(df, by, flag, min_n=30):
    """
    Weighted rate of `flag` within each cell of `by`, with unweighted sample
    counts and a small-cell suppression flag.

    Small cells are NOT dropped -- they are flagged, so the caller decides.
    """
    g = df.groupby(by, observed=True)
    out = g.apply(
        lambda d: pd.Series({
            "n_unweighted": len(d),
            "pop_weighted": d["weight"].sum(),
            "rate": wmean(d, flag),
            "count_weighted": wtotal(d, flag),
        }),
        include_groups=False,
    ).reset_index()
    out["unreliable"] = out["n_unweighted"] < min_n
    return out
