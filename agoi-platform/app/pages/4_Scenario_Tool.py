import os
import sys

import pandas as pd
import plotly.express as px
import streamlit as st

_APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ROOT = os.path.dirname(_APP)
for _p in (_APP, _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)
from _shared import get_data, inject_css   # noqa: E402
from agoi import config                     # noqa: E402

st.set_page_config(page_title="Scenario tool · AGOI™", page_icon="🎛️", layout="wide")
inject_css()
st.title("🎛️ What-if scenario tool")
st.markdown("<span class='small-note'>Tier 1 — weight sensitivity. Adjust pillar weights and see how the "
            "ranking changes instantly. Pillar scores are already computed; only the weighting changes. "
            "This is an exploratory tool, not a forecast.</span>", unsafe_allow_html=True)

scores, audit, meta = get_data()
pillars = list(config.PILLAR_WEIGHTS.keys())

st.markdown("### Adjust pillar weights")
cols = st.columns(3)
weights = {}
for i, p in enumerate(pillars):
    with cols[i % 3]:
        weights[p] = st.slider(config.PILLAR_LABELS[p], 0, 50,
                               int(config.PILLAR_WEIGHTS[p] * 100), step=5,
                               key=f"w_{p}")

total = sum(weights.values())
if total == 0:
    st.error("Weights cannot all be zero.")
    st.stop()

norm_w = {p: w / total for p, w in weights.items()}
st.caption(f"Weights normalized to sum to 100% (you entered {total}%).")

# Recompute AGOI under the new weights (client-side re-aggregation).
df = scores.copy()
df["scenario_score"] = sum(df[f"pillar_{p}"] * norm_w[p] for p in pillars).round(1)
df["scenario_band"] = df["scenario_score"].apply(config.classify_band)
df["delta"] = (df["scenario_score"] - df["agoi_score"]).round(1)
df = df.sort_values("scenario_score", ascending=False).reset_index(drop=True)
df["new_rank"] = df.index + 1

st.markdown("### Scenario ranking")
movers = df[["new_rank", "country", "scenario_score", "scenario_band", "agoi_score", "delta"]].copy()
movers.columns = ["Rank", "Country", "Scenario score", "Scenario band", "Baseline", "Δ"]
st.dataframe(movers, use_container_width=True, hide_index=True,
             column_config={
                 "Scenario score": st.column_config.ProgressColumn(
                     "Scenario score", min_value=0, max_value=100, format="%.1f"),
                 "Δ": st.column_config.NumberColumn("Δ vs baseline", format="%+.1f"),
             })

st.markdown("### Biggest movers under this weighting")
top_up = df.nlargest(5, "delta")[["country", "delta"]]
top_dn = df.nsmallest(5, "delta")[["country", "delta"]]
c1, c2 = st.columns(2)
c1.markdown("**▲ Gainers**")
c1.dataframe(top_up.rename(columns={"country": "Country", "delta": "Δ"}),
             hide_index=True, use_container_width=True)
c2.markdown("**▼ Decliners**")
c2.dataframe(top_dn.rename(columns={"country": "Country", "delta": "Δ"}),
             hide_index=True, use_container_width=True)
