"""
app.py -- India's Digital Payments Capability Gap

Reads only from data/processed/, which is committed to the repository. The
raw microdata is not, so the app cannot rerun the pipeline -- it presents what
build_analysis.py and build_npci_analysis.py already computed.

Run locally:  streamlit run app.py
"""

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

BASE = Path(__file__).resolve().parent
PROCESSED = BASE / "data" / "processed"

st.set_page_config(
    page_title="India's Digital Payments Capability Gap",
    page_icon="◐",
    layout="wide",
)

# Palette follows the static figures so the two never diverge, but the
# supporting greys have to shift with the theme -- a mid grey that reads well
# on paper-white disappears against near-black. Both variants clear WCAG AA
# for body text against their own background.
try:
    DARK = st.context.theme.type == "dark"
except Exception:          # older Streamlit, or theme not resolved yet
    DARK = False

if DARK:
    INK = "#ececec"        # primary text
    BODY = "#d4d4d4"       # lede
    NOTE = "#a8a8a8"       # captions
    COOL = "#5aa9d0"       # lightened for contrast on dark
    ACCENT = "#e87a4a"
    MUTED = "#7e7e7e"
    RULE = "#3a3a3a"
else:
    INK = "#1a1a1a"
    BODY = "#2c2c2c"
    NOTE = "#5a5a5a"       # was #6a6a6a; darkened to clear AA on white
    COOL = "#2c6e91"
    ACCENT = "#c1440e"
    MUTED = "#8a8a8a"
    RULE = "#e2e0dc"

st.markdown(f"""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Serif:wght@500;600&display=swap" rel="stylesheet">
<style>
  html, body, [class*="css"], .stMarkdown, p, li {{ font-family: 'IBM Plex Sans', sans-serif; }}
  h1, h2, h3 {{ font-family: 'IBM Plex Serif', serif; letter-spacing: -0.01em; }}
  h1 {{ font-size: 2.1rem; font-weight: 600; line-height: 1.15; }}
  h2 {{ font-size: 1.35rem; font-weight: 600; margin-top: 2.2rem; }}
  h3 {{ font-size: 1.05rem; font-weight: 600; }}
  .stDataFrame, .stMetric {{ font-family: 'IBM Plex Mono', monospace; }}
  [data-testid="stMetricValue"] {{ font-family: 'IBM Plex Mono', monospace; font-size: 1.9rem; }}
  [data-testid="stMetricLabel"] {{ font-size: .8rem; color: {NOTE}; letter-spacing: .02em; }}
  .lede {{ font-size: 1.12rem; line-height: 1.6; max-width: 46rem; color: {BODY}; }}
  .note {{ font-size: .87rem; color: {NOTE}; line-height: 1.55; max-width: 46rem; }}
  .note a {{ color: {COOL}; }}
  .stTabs [data-baseweb="tab"] {{ font-family: 'IBM Plex Sans', sans-serif; font-weight: 500; }}
  hr {{ border-color: {RULE}; }}
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load(name):
    return pd.read_csv(PROCESSED / name)


def layout(fig, height=380, showlegend=False):
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=8, t=8, b=8),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="IBM Plex Sans, sans-serif", size=12, color=INK),
        showlegend=showlegend,
        legend=dict(orientation="h", y=1.12, x=0),
        xaxis=dict(gridcolor=RULE, zeroline=False),
        yaxis=dict(gridcolor=RULE, zeroline=False),
        hoverlabel=dict(font_family="IBM Plex Mono, monospace"),
    )
    return fig


BARRIER_GROUPS = {
    "Digital literacy": ["Don't know how to use it", "Don't know what internet is"],
    "No perceived need": ["Do not need it", "Available but doesn't meet needs",
                          "Have internet access elsewhere", "Lack of local content"],
    "Cost": ["Equipment cost too high", "Service cost too high"],
    "Availability / supply": ["Not available in area", "No electricity"],
    "Other": ["Others", "Privacy/security concerns",
              "Cultural reasons / harmful content"],
}


# ---------------------------------------------------------------- header ----
st.markdown("# India's digital payments capability gap")
st.markdown(
    '<p class="lede">Nearly half of Indian adults cannot make a UPI payment. '
    'This looks at who they are and where in the adoption chain they get '
    'stuck &mdash; using the government\'s own survey microdata rather than '
    'transaction totals, because transaction data can only describe the people '
    'already transacting.</p>',
    unsafe_allow_html=True)
st.markdown(
    '<p class="note">NSS 80th Round, Comprehensive Modular Survey: Telecom '
    '(Jan&ndash;Mar 2025) &middot; 1,42,065 individuals &middot; 34,950 '
    'households &middot; joined to NPCI state-wise UPI statistics for the same '
    'quarter.</p>',
    unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["What the data shows", "Explore", "How reliable is this?"])


# ============================================================== TAB 1 =======
with tab1:
    funnel = load("funnel_national.csv")
    gap_crore = 46.9

    c1, c2, c3 = st.columns(3)
    c1.metric("Adults able to use UPI", "48.6%")
    c2.metric("Adults who cannot", f"{gap_crore} crore")
    c3.metric("Online, but cannot transact", "19.5 crore")

    st.markdown("## The chain breaks at the last step, not the first")
    st.markdown(
        '<p class="lede">Seven in ten adults use the internet. Fewer than five '
        'in ten can transact on it. The largest single drop is not getting '
        'online &mdash; it is the step from being online to being able to pay.</p>',
        unsafe_allow_html=True)

    f = funnel.copy()
    colors = [ACCENT if s == "Able to transact online" else COOL for s in f["stage"]]
    fig = go.Figure(go.Bar(
        y=f["stage"], x=f["pct_of_adults"], orientation="h",
        marker_color=colors,
        text=[f"{v:.0%}" for v in f["pct_of_adults"]],
        textposition="outside",
        customdata=f[["population_crore", "retention_from_prev"]],
        hovertemplate="<b>%{y}</b><br>%{customdata[0]:.1f} crore adults"
                      "<br>keeps %{customdata[1]:.0%} of the previous step"
                      "<extra></extra>",
    ))
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(tickformat=".0%", range=[0, 1.08])
    st.plotly_chart(layout(fig, 400), use_container_width=True)
    st.markdown(
        '<p class="note">Of adults who already use the internet, 30% cannot '
        'make an online payment. The final step &mdash; from online payments in '
        'general to UPI specifically &mdash; loses almost nobody, because in '
        'India the two have become the same thing.</p>',
        unsafe_allow_html=True)

    # ---- barriers
    st.markdown("## Households say the problem is skill, not cost or coverage")

    hb = load("barriers_household.csv")
    tot = hb.groupby("reason_no_internet_hh")["households"].sum()
    share = tot / tot.sum()
    mapped = {r for items in BARRIER_GROUPS.values() for r in items}
    missing = set(share.index) - mapped
    if missing:   # a label was renamed upstream; better to know than to lose it
        st.error(f"Unmapped barrier categories, excluded from the chart: "
                 f"{sorted(missing)}")
    agg = {g: share.reindex(items).fillna(0).sum()
           for g, items in BARRIER_GROUPS.items()}
    agg = pd.Series(agg).sort_values()

    fig = go.Figure(go.Bar(
        y=agg.index, x=agg.values, orientation="h",
        marker_color=[ACCENT if g == "Digital literacy" else MUTED for g in agg.index],
        text=[f"{v:.0%}" for v in agg.values], textposition="outside",
        hovertemplate="<b>%{y}</b><br>%{x:.1%} of households<extra></extra>",
    ))
    fig.update_xaxes(tickformat=".0%", range=[0, max(agg.values) * 1.2])
    st.plotly_chart(layout(fig, 300), use_container_width=True)
    st.markdown(
        '<p class="note">4.2 crore households without internet at home, by '
        'their stated main reason. &ldquo;Not available in the area&rdquo; is '
        '2.8%; &ldquo;service cost too high&rdquo; is 2.6%. The build-out and '
        'the price war have largely done their work. What is left is a skills '
        'constraint that neither addresses &mdash; and urban households cite it '
        'at 36%, barely below the rural 40%.</p>',
        unsafe_allow_html=True)

    # ---- gender
    st.markdown("## The gender gap survives connectivity")

    fsg = load("funnel_by_sector_gender.csv")
    fsg["conversion"] = fsg["Able to transact online"] / fsg["Used the internet (3m)"]
    piv = fsg.pivot(index="sector_name", columns="gender_name", values="conversion")
    piv = piv.reindex(["Rural", "Urban"])
    # The survey records a third category, but its cells rest on too few
    # respondents to estimate reliably, so this chart shows two.

    fig = go.Figure()
    for g, col in [("Male", COOL), ("Female", ACCENT)]:
        fig.add_bar(x=piv.index, y=piv[g], name=g, marker_color=col,
                    text=[f"{v:.0%}" for v in piv[g]], textposition="outside",
                    hovertemplate="<b>%{x} &middot; " + g +
                                  "</b><br>%{y:.1%} can transact<extra></extra>")
    fig.update_yaxes(tickformat=".0%", range=[0, 1])
    st.plotly_chart(layout(fig, 340, showlegend=True), use_container_width=True)
    st.markdown(
        '<p class="note">Share able to transact online, among adults who '
        '<em>already use the internet</em>. A 20-point gap persists between men '
        'and women who are equally connected, so access is not the explanation. '
        '8.3 crore rural women use the internet and cannot pay with it. Women '
        'are 60.6% of the total capability gap.</p>',
        unsafe_allow_html=True)

    # ---- age
    st.markdown("## Age is the sharpest single cut")
    age = load("upi_rate_by_age_band.csv")
    age["gap_crore"] = (age["pop_weighted"] - age["count_weighted"]) / 1e7
    fig = go.Figure(go.Bar(
        x=age["age_band"], y=age["rate"], marker_color=COOL,
        text=[f"{v:.0%}" for v in age["rate"]], textposition="outside",
        customdata=age[["gap_crore"]],
        hovertemplate="<b>%{x}</b><br>%{y:.1%} able to use UPI"
                      "<br>%{customdata[0]:.1f} crore cannot<extra></extra>",
    ))
    fig.update_yaxes(tickformat=".0%", range=[0, 0.8])
    st.plotly_chart(layout(fig, 300), use_container_width=True)
    st.markdown(
        '<p class="note">Capability halves between 25&ndash;34 and 45&ndash;59. '
        'Adults over 45 account for 25.1 crore of the 46.9 crore gap &mdash; a '
        'group that will not be reached by anything aimed at first-time '
        'smartphone buyers.</p>',
        unsafe_allow_html=True)

    # ---- so what
    st.markdown("## What follows")
    a, b = st.columns(2)
    with a:
        st.markdown("**Two segments, in this order**")
        st.markdown(
            "**The already-connected who cannot pay** &mdash; 19.5 crore people "
            "who have cleared every expensive prerequisite. The device and the "
            "data are sunk costs; what is missing is assisted onboarding at a "
            "point of trust. Rural women who are online but cannot transact "
            "(8.3 crore) are the largest coherent group and the natural pilot.")
        st.markdown(
            "**The 45+ cohort** &mdash; 25.1 crore, skewing to feature phones "
            "and low confidence. A different fix: UPI Lite, 123PAY, voice and "
            "simplified PIN flows. Measured in first transactions, not installs.")
    with b:
        st.markdown("**What to stop doing**")
        st.markdown(
            "Coverage expansion has largely stopped being the constraint. At "
            "2.8% of households citing availability, it is close to exhausted "
            "as an explanation for exclusion.")
        st.markdown(
            "And several states need no enablement programme at all &mdash; see "
            "the state view under **Explore**, where capability is high and "
            "usage is not.")


# ============================================================== TAB 2 =======
with tab2:
    st.markdown("## Explore the gap")
    st.markdown(
        '<p class="note">Every figure is a weighted estimate for adults aged 15 '
        'and over. Cells resting on fewer than 30 sample respondents are '
        'excluded.</p>',
        unsafe_allow_html=True)

    view = st.radio("View", ["By segment", "By state"],
                    horizontal=True, label_visibility="collapsed")

    if view == "By segment":
        # State is deliberately absent here. Adding it splits the data into 565
        # cells, most of them small, which forces sample-size thresholds and
        # lets the largest states crowd out every ranking. Aggregating it away
        # leaves twenty cells, the smallest resting on 3,188 respondents, and
        # the state question is answered properly under "By state" -- where the
        # transaction data is also attached.
        seg = load("segment_gap_table.csv")
        seg = seg[seg["gender_name"] != "Transgender"]
        g = (seg.groupby(["sector_name", "age_band", "gender_name"], as_index=False)
                .agg(sample=("n_unweighted", "sum"),
                     adults=("adult_pop", "sum"),
                     capable=("upi_capable_pop", "sum")))
        g["rate"] = g["capable"] / g["adults"]
        g["gap"] = g["adults"] - g["capable"]
        g["group"] = g["sector_name"] + " " + g["gender_name"].str.lower()

        measure = st.radio("Show", ["Capability rate", "Adults excluded"],
                           horizontal=True)

        st.markdown(
            '<p class="note">Capability runs from 88% among urban men aged '
            '25&ndash;34 to 4% among rural women over 60 &mdash; more than a '
            'twentyfold '
            'spread across the same country in the same quarter. Sector and sex '
            'each shift the level; age changes the shape.</p>',
            unsafe_allow_html=True)

        ORDER = ["15-24", "25-34", "35-44", "45-59", "60+"]
        SERIES = [("Urban Male", COOL, "solid"), ("Rural Male", COOL, "dash"),
                  ("Urban Female", ACCENT, "solid"), ("Rural Female", ACCENT, "dash")]

        fig = go.Figure()
        for name, colr, dash in SERIES:
            sec, gen = name.split()
            d = (g[(g["sector_name"] == sec) & (g["gender_name"] == gen)]
                 .set_index("age_band").reindex(ORDER).reset_index())
            if measure == "Capability rate":
                yv, tmpl = d["rate"], ("<b>" + name + " · %{x}</b><br>"
                                       "%{y:.1%} able to use UPI"
                                       "<br>%{customdata[0]:.2f} crore excluded"
                                       "<extra></extra>")
                cd = d[["gap"]] / 1e7
            else:
                yv, tmpl = d["gap"] / 1e7, ("<b>" + name + " · %{x}</b><br>"
                                            "%{y:.2f} crore excluded"
                                            "<br>%{customdata[0]:.1%} able to use UPI"
                                            "<extra></extra>")
                cd = d[["rate"]]
            fig.add_scatter(x=d["age_band"], y=yv, name=name, mode="lines+markers",
                            line=dict(color=colr, dash=dash, width=2.2),
                            marker=dict(size=8), customdata=cd.values,
                            hovertemplate=tmpl)

        if measure == "Capability rate":
            fig.update_yaxes(tickformat=".0%", range=[0, 1],
                             title="Share able to use UPI")
        else:
            fig.update_yaxes(title="Adults who cannot use UPI (crore)")
        fig.update_xaxes(title="Age band")
        st.plotly_chart(layout(fig, 440, showlegend=True), use_container_width=True)

        if measure == "Capability rate":
            st.markdown(
                '<p class="note">Rural women sit lowest at every age &mdash; the '
                'sector gap and the sex gap compound rather than substitute. The '
                'one crossing is telling: rural men lead urban women until 60, '
                'then fall behind them. Among the oldest cohort, living in a '
                'city matters more than being a man.</p>',
                unsafe_allow_html=True)
        else:
            st.markdown(
                '<p class="note">Rate and headcount point in different '
                'directions. Rural women over 60 are the least capable group but '
                'not the largest, because the cohort itself is smaller. The '
                'biggest single block of excluded adults is rural women aged '
                '45&ndash;59.</p>',
                unsafe_allow_html=True)

        st.markdown("**Every segment**")
        tbl = g.sort_values("gap", ascending=False)[
            ["sector_name", "age_band", "gender_name", "adults", "rate",
             "gap", "sample"]].rename(columns={
                 "sector_name": "Sector", "age_band": "Age", "gender_name": "Sex",
                 "adults": "Adults", "rate": "Able to use UPI",
                 "gap": "Cannot use UPI", "sample": "Sample n"})
        st.dataframe(
            tbl.style.format({"Adults": "{:,.0f}", "Able to use UPI": "{:.1%}",
                              "Cannot use UPI": "{:,.0f}", "Sample n": "{:,.0f}"}),
            use_container_width=True, hide_index=True, height=420)
        st.markdown(
            '<p class="note">The survey also records a third sex category. Its '
            'cells rest on 143 respondents in total across the whole sample, too '
            'few to estimate at this level of detail, so they are excluded from '
            'this view rather than shown as though they were comparable.</p>',
            unsafe_allow_html=True)

    else:
        cvu = load("state_capability_vs_usage.csv")
        lvl = load("state_level.csv")
        s = cvu.merge(lvl[["state", "female_rate", "male_rate", "gender_gap_pp",
                           "rural_share_of_adults"]], on="state", how="left")

        pick = st.selectbox("State or union territory",
                            sorted(s["state"]), index=sorted(s["state"]).index("Manipur"))
        row = s[s["state"] == pick].iloc[0]

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Able to use UPI", f"{row['upi_capable_rate']:.1%}")
        m2.metric("Transactions per adult", f"{row['txn_per_adult']:.0f}",
                  help="UPI transactions per adult, Q1 2025")
        m3.metric("Expected at this capability", f"{row['predicted_txn_per_adult']:.0f}")
        m4.metric("Difference", f"{row['residual']:+.0f}",
                  delta=f"{row['residual']:+.0f}",
                  help="How far the state sits from the national trend line")

        if row["residual"] < -10:
            st.warning(
                f"**{pick} transacts well below what its capability predicts.** "
                "Enabling more people is not the binding constraint here — the "
                "obstacle sits downstream, most plausibly on the merchant side: "
                "QR acceptance, connectivity at the point of sale, or entrenched "
                "cash preference in local commerce.")
        elif row["residual"] > 10:
            st.info(
                f"**{pick} transacts well above the trend.** Read this with "
                "care: volume includes payments made by visitors and by "
                "businesses headquartered in the state, while the denominator "
                "counts residents only. Tourism and commercial concentration "
                "inflate the figure mechanically.")

        st.markdown("**Where the state sits nationally**")
        below = s[s["residual"] < 0]
        above = s[s["residual"] >= 0]
        fig = go.Figure()
        for grp, col, nm in [(above, COOL, "Converts above trend"),
                             (below, ACCENT, "Capable but not converting")]:
            fig.add_scatter(
                x=grp["upi_capable_rate"], y=grp["txn_per_adult"],
                mode="markers", name=nm,
                marker=dict(size=9, color=col, opacity=.55),
                text=grp["state"],
                hovertemplate="<b>%{text}</b><br>%{x:.1%} capable"
                              "<br>%{y:.0f} transactions per adult<extra></extra>")
        fig.add_scatter(
            x=s["upi_capable_rate"], y=s["predicted_txn_per_adult"],
            mode="lines", line=dict(color=MUTED, dash="dash", width=1),
            name="Trend", hoverinfo="skip")
        fig.add_scatter(
            x=[row["upi_capable_rate"]], y=[row["txn_per_adult"]],
            mode="markers+text", name=pick, text=[pick],
            textposition="top center",
            textfont=dict(family="IBM Plex Sans", size=12),
            marker=dict(size=15, color=INK, line=dict(color="white", width=2)),
            hovertemplate="<b>%{text}</b><extra></extra>")
        fig.update_xaxes(tickformat=".0%", title="Adults able to use UPI")
        fig.update_yaxes(title="UPI transactions per adult, Q1 2025")
        st.plotly_chart(layout(fig, 460, showlegend=True), use_container_width=True)

        g1, g2 = st.columns(2)
        with g1:
            st.markdown("**Capability by sex**")
            fig = go.Figure(go.Bar(
                x=["Female", "Male"], y=[row["female_rate"], row["male_rate"]],
                marker_color=[ACCENT, COOL],
                text=[f"{row['female_rate']:.0%}", f"{row['male_rate']:.0%}"],
                textposition="outside", hovertemplate="<b>%{x}</b><br>%{y:.1%}<extra></extra>"))
            fig.update_yaxes(tickformat=".0%", range=[0, 1])
            st.plotly_chart(layout(fig, 260), use_container_width=True)
            st.markdown(
                f'<p class="note">A {row["gender_gap_pp"]:.0f} point gap. '
                'Nationally this ranges from 5 points in Mizoram to 46 in '
                'Dadra &amp; Nagar Haveli and Daman &amp; Diu, at similar '
                'overall capability &mdash; so it is not a function of '
                'development level.</p>',
                unsafe_allow_html=True)
        with g2:
            st.markdown("**Segments within this state**")
            seg = load("segment_gap_table.csv")
            sub = seg[(seg["state"] == pick) & (~seg["unreliable"])]
            if sub.empty:
                st.markdown(
                    '<p class="note">Every segment in this state rests on fewer '
                    'than 30 sample respondents, so none are shown. Smaller '
                    'union territories often fall below that threshold.</p>',
                    unsafe_allow_html=True)
            else:
                sub = sub.nlargest(8, "gap_pop").copy()
                sub["label"] = (sub["sector_name"] + " · " + sub["age_band"]
                                + " · " + sub["gender_name"])
                fig = go.Figure(go.Bar(
                    y=sub["label"][::-1], x=sub["upi_capable_rate"][::-1],
                    orientation="h", marker_color=COOL,
                    text=[f"{v:.0%}" for v in sub["upi_capable_rate"][::-1]],
                    textposition="outside",
                    customdata=sub[["gap_pop"]][::-1] / 1e6,
                    hovertemplate="<b>%{y}</b><br>%{x:.1%} able to use UPI"
                                  "<br>%{customdata[0]:.2f} million excluded<extra></extra>"))
                fig.update_xaxes(tickformat=".0%", range=[0, 1.12])
                st.plotly_chart(layout(fig, 260), use_container_width=True)


# ============================================================== TAB 3 =======
with tab3:
    st.markdown("## Does the pipeline read the data correctly?")
    st.markdown(
        '<p class="lede">Before computing anything, the pipeline reproduces a '
        'figure already published by the National Statistical Office. If it '
        'cannot, it stops.</p>',
        unsafe_allow_html=True)
    a, b = st.columns(2)
    a.metric("Computed", "99.46%",
             help="Share of adults 15–29 able to transact online who can do so via UPI")
    b.metric("Published", "~99.5%")
    st.markdown(
        '<p class="note">Weighted totals also land at 30.7 crore households, '
        'consistent with independent estimates of India\'s household count. '
        'One decision does most of the work here: the survey skips its payment '
        'questions for anyone who cannot operate a phone or computer at all, '
        'and those blanks are counted as <em>not capable</em> rather than '
        'dropped. Treating them as missing would inflate every rate in this '
        'dashboard by roughly 40%.</p>',
        unsafe_allow_html=True)

    st.markdown("## The 40% of transactions NPCI cannot place")
    unc = load("npci_unclassified_share.csv")
    st.markdown(
        '<p class="lede">NPCI buckets a transaction as &ldquo;unclassified&rdquo; '
        'whenever the app did not send location data. In the quarter analysed '
        'here that was between a third and two fifths of all volume &mdash; and '
        'it moved by 5 points inside three months.</p>',
        unsafe_allow_html=True)

    fig = go.Figure(go.Bar(
        x=unc["month"], y=unc["unclassified_share_volume"], marker_color=ACCENT,
        text=[f"{v:.1%}" for v in unc["unclassified_share_volume"]],
        textposition="outside",
        hovertemplate="<b>%{x} 2025</b><br>%{y:.1%} of volume unattributed<extra></extra>"))
    fig.update_yaxes(tickformat=".0%", range=[0, 0.5])
    st.plotly_chart(layout(fig, 280), use_container_width=True)

    st.markdown("### Why it does not invalidate the state comparison")
    st.markdown(
        '<p class="lede">A residual that large looks disqualifying. Testing it '
        'directly shows otherwise. Four rules for distributing the unattributed '
        'volume were compared:</p>',
        unsafe_allow_html=True)

    sens = load("npci_allocation_sensitivity.csv")
    show = sens.rename(columns={
        "method": "Rule",
        "pearson_r_vs_capability": "Correlation with capability",
        "rank_corr_vs_excluded": "Rank agreement with 'excluded'",
        "top_state": "Highest per-adult usage"})
    st.dataframe(
        show[["Rule", "Correlation with capability",
              "Rank agreement with 'excluded'", "Highest per-adult usage"]]
        .style.format({"Correlation with capability": "{:.3f}",
                       "Rank agreement with 'excluded'": "{:.3f}"}),
        use_container_width=True, hide_index=True)

    st.markdown(
        "Excluding the residual, splitting it in proportion to observed volume, "
        "and splitting it by adult population all **scale or shift every state "
        "by the same constant**. Neither operation can change a ranking or a "
        "correlation, so all three return an identical 0.637 — as they must.")
    st.markdown(
        "Only the fourth rule moves the answer, and it moves it for the wrong "
        "reason: allocating unattributed volume in proportion to *capable* "
        "population and then correlating the result against capability builds "
        "the relationship into the data. It is retained in the code as a "
        "demonstration of the trap, and every result here uses the most "
        "conservative rule.")
    st.markdown(
        '<p class="note">So the residual limits what can be said about '
        '<em>absolute</em> per-capita levels &mdash; every state figure is '
        'understated by roughly 40% &mdash; while leaving the <em>relative</em> '
        'comparison intact. That is the comparison the analysis rests on.</p>',
        unsafe_allow_html=True)

    st.markdown("## What this analysis cannot do")
    lim = [
        ("Capability is not usage",
         "The survey asks whether a person is *able* to transact via UPI, not "
         "whether they do, how often, or for how much. Every survey-side figure "
         "is an enablement gap."),
        ("One quarter, no trend",
         "January to March 2025 only. Nothing here shows a gap widening or "
         "closing, and no causal claim is made."),
        ("No confidence intervals",
         "The methodology document gives the variance formula for the two-stage "
         "sample design; it is not yet implemented. Large states are barely "
         "affected, but small union territories rest on a few hundred "
         "respondents and their rankings should not be read closely."),
        ("State-level, not person-level, on the transaction side",
         "Capability is measured per person; NPCI volume is per state. The join "
         "supports statements about states, never about individuals within "
         "them. No segment is ever assigned a transaction count."),
        ("Usage counts residents, volume does not",
         "Transactions attributed to a state include payments by visitors and "
         "by businesses headquartered there, against a denominator of resident "
         "adults. This inflates Goa and Delhi in particular."),
        ("The sizing is a ceiling",
         "4.5–6.7 billion transactions a month applies an observed intensity "
         "benchmark, at a 40–60% haircut, to a population that does not yet "
         "transact. It answers how large the opportunity is, not what any "
         "intervention would deliver."),
    ]
    for title, body in lim:
        with st.expander(title):
            st.markdown(body)

    st.markdown("---")
    st.markdown(
        '<p class="note">Source code, full methodology and the underlying '
        'tables: <a href="https://github.com/Afro-dude">github.com/Afro-dude</a>'
        '</p>',
        unsafe_allow_html=True)