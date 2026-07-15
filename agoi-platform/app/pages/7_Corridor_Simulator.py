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

from _shared import inject_css                   # noqa: E402
from agoi.afcfta import config as acfg           # noqa: E402
from agoi.afcfta import elasticity as el         # noqa: E402
from agoi.afcfta import engine                   # noqa: E402

st.set_page_config(page_title="Corridor simulator · AGOI™", page_icon="🛣️", layout="wide")
inject_css()

st.title("🛣️ Corridor Simulator — Lagos–Abidjan")
st.caption("ECOWAS coastal corridor · flood-risk → trade linkage via the Lagos City Lab")

if el.confidence_grade() == "PLACEHOLDER":
    st.error("🔬 **SCENARIO EXPLORER — NOT A FORECASTER.** Corridor coefficients are structural "
             "placeholders, not empirical estimates. All outputs are ranges; the range is the "
             "result. Do not cite these as findings.")

CORRIDOR_ID = "ECO-LGS-ABJ"
corridor = acfg.CORRIDORS[CORRIDOR_ID]

# Approximate node coordinates for the map
COORDS = {
    "ABJ": (5.32, -4.02), "ACC": (5.60, -0.19), "LOM": (6.13, 1.22),
    "COO": (6.37, 2.42),  "LOS": (6.45, 3.39),
}

# ── Levers ──
st.markdown("#### Policy levers")
lc = st.columns(6)
levers = {}
lever_order = ["A1", "A2", "A3", "A4", "A5"]
for i, code in enumerate(lever_order):
    with lc[i]:
        levers[code] = st.slider(code, 0.0, 1.0, 0.0, 0.1,
                                 help=f"{acfg.AFCFTA_LEVERS[code]['label']} — "
                                      f"{acfg.AFCFTA_LEVERS[code]['desc']}")
with lc[5]:
    res_lagos = st.slider("RES", 0.0, 1.0, 0.0, 0.1,
                          help=f"{acfg.LAGOS_RESILIENCE_LEVER['label']} — "
                               f"{acfg.LAGOS_RESILIENCE_LEVER['desc']}")

st.caption("A1 Green Standards · A2 Investment Incentives · A3 Corridor Upgrade · "
           "A4 CSA Protocols · A5 Circular Compliance · **RES** Lagos Flood Resilience")

sim = engine.simulate_corridor(CORRIDOR_ID, levers, res_lagos)
nodes = engine.node_risk(CORRIDOR_ID, res_lagos)

# ══════════════════════════════════════════════════════════
# Corridor map with node flood risk
# ══════════════════════════════════════════════════════════
left, right = st.columns([1.25, 1])

with left:
    st.markdown("#### Corridor nodes — flood risk")
    lats = [COORDS[n["node_id"]][0] for n in nodes]
    lons = [COORDS[n["node_id"]][1] for n in nodes]
    risk = [n["flood_risk_scenario"] for n in nodes]
    text = [f"{n['city']} ({n['country_iso3']})<br>"
            f"Flood risk: {n['flood_risk_baseline']:.0f} → <b>{n['flood_risk_scenario']:.0f}</b><br>"
            f"Logistics capacity: {n['logistics_capacity']}<br>"
            f"AfCFTA implementation: {n['afcfta_implementation']}"
            for n in nodes]

    fig = go.Figure()
    # corridor line
    fig.add_trace(go.Scattergeo(lat=lats, lon=lons, mode="lines",
                                line=dict(width=2, color="#0F766E"),
                                hoverinfo="skip", showlegend=False))
    # nodes coloured by scenario flood risk
    fig.add_trace(go.Scattergeo(
        lat=lats, lon=lons, mode="markers+text",
        text=[n["city"] for n in nodes], textposition="top center",
        textfont=dict(size=10, color="#0C2B2A"),
        marker=dict(size=[16 + r / 5 for r in risk], color=risk,
                    colorscale=[[0, "#1B6B35"], [0.5, "#FFC000"], [1, "#C62828"]],
                    cmin=0, cmax=100, showscale=True,
                    colorbar=dict(title="Flood<br>risk"), line=dict(width=1, color="white")),
        hovertext=text, hoverinfo="text", showlegend=False))
    fig.update_geos(scope="africa", lataxis_range=[3.5, 8.5], lonaxis_range=[-6, 5],
                    showcountries=True, countrycolor="#D5E3E0",
                    landcolor="#F5FAF9", showframe=False)
    fig.update_layout(height=380, margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(fig, use_container_width=True)

    if res_lagos > 0:
        lag = next(n for n in nodes if n["node_id"] == "LOS")
        st.success(f"🌊 Lagos flood risk **{lag['flood_risk_baseline']:.0f} → "
                   f"{lag['flood_risk_scenario']:.0f}** under RES={res_lagos:.1f}. "
                   "Neighbouring nodes benefit from corridor spillover.")

with right:
    st.markdown("#### Corridor metrics — scenario ranges")
    METRIC_LABELS = {
        "transit_time":   ("Transit time", "days"),
        "logistics_cost": ("Logistics cost", "USD/TEU"),
        "climate_risk":   ("Climate risk", "0–100"),
        "green_score":    ("Green logistics score", "0–100"),
        "trade_volume":   ("Trade volume", "index"),
    }
    rows = []
    for m, (label, unit) in METRIC_LABELS.items():
        v = sim[m]
        good = "↓ better" if v["direction"] == "lower" else "↑ better"
        rows.append({
            "Metric": label,
            "Baseline": f"{v['baseline']:,.1f}",
            "Scenario range": f"{min(v['low'], v['high']):,.1f} – {max(v['low'], v['high']):,.1f}",
            "Unit": unit,
            "Dir": good,
        })
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

    # Radar of the corridor's normalized position
    st.markdown("#### Corridor profile")
    def _norm(m):
        v = sim[m]
        # normalize each metric to 0–100 where higher = better
        if m == "transit_time":   return max(0, 100 - v["value"] / 8 * 100)
        if m == "logistics_cost": return max(0, 100 - v["value"] / 3500 * 100)
        if m == "climate_risk":   return max(0, 100 - v["value"])
        if m == "green_score":    return v["value"]
        if m == "trade_volume":   return min(100, v["value"] - 50)
        return 0

    cats = [METRIC_LABELS[m][0] for m in METRIC_LABELS]
    base_vals, scen_vals = [], []
    for m in METRIC_LABELS:
        v = sim[m]
        cur, v["value"] = v["value"], v["baseline"]
        base_vals.append(_norm(m)); v["value"] = cur
        scen_vals.append(_norm(m))

    radar = go.Figure()
    radar.add_trace(go.Scatterpolar(r=base_vals + [base_vals[0]], theta=cats + [cats[0]],
                                    name="Baseline", line_color="#B9CBC8", fill="toself", opacity=0.5))
    radar.add_trace(go.Scatterpolar(r=scen_vals + [scen_vals[0]], theta=cats + [cats[0]],
                                    name="Scenario", line_color="#0F766E", fill="toself", opacity=0.6))
    radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                        height=330, margin=dict(l=50, r=50, t=20, b=20),
                        legend=dict(orientation="h", y=-0.1))
    st.plotly_chart(radar, use_container_width=True)

# ══════════════════════════════════════════════════════════
# Lagos City Lab — flood → trade risk
# ══════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 🌊 Lagos City Lab — flood → trade-risk linkage")
st.caption("How Lagos flood-resilience investment (RES) propagates into corridor trade performance. "
           "This linkage is the analytically distinctive claim of the AfCFTA module.")

lagos = engine.simulate_lagos_trade_risk(res_lagos)
cols = st.columns(4)
for col, (code, v) in zip(cols, lagos.items()):
    with col:
        st.metric(v["label"], f"{v['baseline']:.1f} {v['unit']}",
                  delta=f"{v['delta']:+.1f}" if res_lagos > 0 else None,
                  delta_color="inverse")
        if res_lagos > 0:
            st.caption(f"Scenario: **{v['low']:.1f} – {v['high']:.1f}** {v['unit']}")

if res_lagos == 0:
    st.info("Raise the **RES** lever above to see the flood-resilience → trade-risk effect.")
else:
    st.caption("⚠️ Ranges reflect placeholder elasticity bounds. The width of each range is the "
               "honest measure of what is currently unknown.")
