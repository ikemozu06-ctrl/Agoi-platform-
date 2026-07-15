import os
import sys

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

_APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ROOT = os.path.dirname(_APP)
for _p in (_APP, _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from _shared import inject_css                       # noqa: E402
from agoi.afcfta import config as acfg               # noqa: E402
from agoi.afcfta import elasticity as el             # noqa: E402
from agoi.afcfta import engine, data                 # noqa: E402

st.set_page_config(page_title="AfCFTA · AGOI™", page_icon="🌍", layout="wide")
inject_css()

st.title("🌍 AfCFTA Readiness & Scenario Explorer")
st.caption("ECOWAS vertical slice — Nigeria, Ghana, Côte d'Ivoire, Benin, Togo")

# ── The credibility banner. Non-negotiable. ──
grade = el.confidence_grade()
counts = el.matrix_provenance_summary()
if grade == "PLACEHOLDER":
    st.error(
        "🔬 **SCENARIO EXPLORER — NOT A FORECASTER.** "
        f"All {counts['assumed']} elasticity coefficients are **structural placeholders**, not "
        "empirical estimates. Outputs show the *shape* of a policy response, never its true "
        "magnitude. Results are reported as **ranges**, and the ranges are wide because the "
        "uncertainty is real. Do not cite these numbers as findings. "
        "See the *Elasticity governance* tab for the research plan that replaces them."
    )
elif grade == "MIXED":
    st.warning(f"⚠️ Elasticity matrix partially grounded — {counts['assumed']} coefficients "
               "remain placeholders. Treat affected outputs as scenarios, not forecasts.")

tab1, tab2, tab3 = st.tabs(["📊 Country readiness", "🎛️ Policy scenario", "🔬 Elasticity governance"])

# ══════════════════════════════════════════════════════════
# TAB 1 — Readiness
# ══════════════════════════════════════════════════════════
with tab1:
    rows = []
    for iso3 in acfg.SLICE_COUNTRIES:
        b = data.get_baseline(iso3)
        rows.append({
            "Country": iso3,
            "AfCFTA readiness": engine.afcfta_readiness(b),
            **{acfg.AFCFTA_INDICATORS[k]["label"]: v for k, v in b.items()},
        })
    df = pd.DataFrame(rows).sort_values("AfCFTA readiness", ascending=False)

    st.markdown("#### AfCFTA readiness — the six indicators")
    st.caption("⚠️ All baseline values are **proxy estimates**. The six AfCFTA indicators are not "
               "standard World Bank series and must be acquired from the AfCFTA Secretariat, "
               "UNCTAD, UNECA and AfDB. See provenance notes below.")
    st.dataframe(df, hide_index=True, use_container_width=True,
                 column_config={"AfCFTA readiness": st.column_config.ProgressColumn(
                     "AfCFTA readiness", min_value=0, max_value=100, format="%.1f")})

    # Grouped bar of the six indicators
    fig = go.Figure()
    for code, meta in acfg.AFCFTA_INDICATORS.items():
        fig.add_trace(go.Bar(
            name=code, x=acfg.SLICE_COUNTRIES,
            y=[data.get_baseline(c)[code] for c in acfg.SLICE_COUNTRIES],
            hovertemplate=f"<b>{meta['label']}</b><br>%{{x}}: %{{y}}<extra></extra>"))
    fig.update_layout(barmode="group", height=420, plot_bgcolor="white",
                      margin=dict(l=0, r=0, t=20, b=0),
                      yaxis_title="Index (0–100, proxy)", legend_title="Indicator")
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("📋 Indicator provenance — how each baseline was derived"):
        for code, note in data.PROVENANCE_NOTES.items():
            st.markdown(f"**{code} — {acfg.AFCFTA_INDICATORS[code]['label']}**  \n{note}")

# ══════════════════════════════════════════════════════════
# TAB 2 — Policy scenario
# ══════════════════════════════════════════════════════════
with tab2:
    c1, c2 = st.columns([1, 2])

    with c1:
        st.markdown("#### Policy levers")
        country = st.selectbox("Country", acfg.SLICE_COUNTRIES, index=0)
        levers = {}
        for code, meta in acfg.AFCFTA_LEVERS.items():
            levers[code] = st.slider(f"{code} — {meta['label']}", 0.0, 1.0, 0.0, 0.1,
                                     help=meta["desc"])

    with c2:
        base = data.get_baseline(country)
        res = engine.simulate_country(base, levers)

        st.markdown(f"#### Scenario outcome — {country}")
        if not any(levers.values()):
            st.info("Move a lever to run a scenario.")
        else:
            st.caption("Bars show the **uncertainty range** from the elasticity bounds. "
                       "The range — not the midpoint — is the result.")

        fig = go.Figure()
        codes = list(acfg.AFCFTA_INDICATORS.keys())
        fig.add_trace(go.Bar(
            name="Baseline", y=codes, x=[res[k]["baseline"] for k in codes],
            orientation="h", marker_color="#B9CBC8"))
        fig.add_trace(go.Bar(
            name="Scenario range", y=codes,
            x=[res[k]["high"] - res[k]["low"] for k in codes],
            base=[res[k]["low"] for k in codes],
            orientation="h", marker_color="#14B8A6", opacity=0.75,
            hovertemplate="%{y}: %{base:.1f} – %{x:.1f}<extra></extra>"))
        fig.update_layout(barmode="overlay", height=380, plot_bgcolor="white",
                          xaxis_title="Index (0–100)", margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)

        tbl = pd.DataFrame([{
            "Indicator": acfg.AFCFTA_INDICATORS[k]["label"],
            "Baseline": res[k]["baseline"],
            "Scenario range": f"{res[k]['low']:.1f} – {res[k]['high']:.1f}",
            "Δ range": f"{res[k]['delta_low']:+.1f} … {res[k]['delta_high']:+.1f}",
        } for k in codes])
        st.dataframe(tbl, hide_index=True, use_container_width=True)

# ══════════════════════════════════════════════════════════
# TAB 3 — Elasticity governance
# ══════════════════════════════════════════════════════════
with tab3:
    st.markdown("#### Why this matters")
    st.markdown(
        "The AfCFTA protocol specifies a 6-indicator × 5-lever elasticity matrix but does **not** "
        "say where the β coefficients come from. That gap is the single biggest credibility risk in "
        "the module: a simulator populated with invented coefficients produces confident, "
        "precise-looking policy numbers with no empirical basis — and unlike a wrong score, a wrong "
        "elasticity carries an implied **causal** claim a ministry or DFI might act on."
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Estimated", counts["estimated"], help="Fitted from panel data — highest confidence")
    c2.metric("Literature", counts["literature"], help="From cited published studies")
    c3.metric("Elicited", counts["elicited"], help="Structured expert elicitation")
    c4.metric("Placeholder", counts["assumed"], help="NOT evidence — must be replaced")

    st.markdown("#### The matrix (β — country indicators)")
    st.caption("Each cell: central value with [low – high] bounds. All currently placeholders.")
    mat = []
    for ind, row in el.COUNTRY_ELASTICITY.items():
        r = {"Indicator": ind}
        for lever in acfg.AFCFTA_LEVERS:
            b = row.get(lever)
            r[lever] = f"{b['value']:.1f}  [{b['low']:.1f}–{b['high']:.1f}]" if b else "—"
        mat.append(r)
    st.dataframe(pd.DataFrame(mat), hide_index=True, use_container_width=True)

    st.markdown("#### Research plan — replacing the placeholders")
    for title, desc in el.ELASTICITY_ROADMAP:
        st.markdown(f"**{title}**  \n{desc}")

    st.info("**Rule enforced in code:** every β must carry a provenance flag and an uncertainty "
            "range. The simulator propagates the range and reports bands, never point estimates. "
            "This is what lets AGOI–AfCFTA be cited by an institution rather than dismissed by it.")
