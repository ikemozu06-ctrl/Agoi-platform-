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
from _shared import get_data, band_pill, inject_css   # noqa: E402
from agoi import config                                # noqa: E402

st.set_page_config(page_title="Country profile · AGOI™", page_icon="🌍", layout="wide")
inject_css()
st.title("📋 Country profile")

scores, audit, meta = get_data()

country = st.selectbox("Select a country", scores["country"].tolist())
row = scores[scores["country"] == country].iloc[0]
iso3 = row["country_iso3"]

c1, c2, c3 = st.columns([1.4, 1, 1])
with c1:
    st.metric("AGOI score", f"{row['agoi_score']:.1f} / 100")
    st.markdown(band_pill(row["band"]), unsafe_allow_html=True)
    st.markdown(f"<br><span class='small-note'>{config.BAND_READING[row['band']]}</span>",
                unsafe_allow_html=True)
with c2:
    st.metric("Continental rank", f"#{int(row['rank'])} of {len(scores)}")
with c3:
    st.metric("Data coverage", f"{row['data_coverage']:.0f}%",
              help="Share of indicators based on measured vs imputed data.")

# ── Pillar radar ──
st.markdown("### Pillar breakdown")
pillars = list(config.PILLAR_WEIGHTS.keys())
labels = [config.PILLAR_LABELS[p] for p in pillars]
values = [row[f"pillar_{p}"] for p in pillars]

radar = go.Figure()
radar.add_trace(go.Scatterpolar(
    r=values + [values[0]], theta=labels + [labels[0]],
    fill="toself", line_color="#2E75B6", name=country))
radar.update_layout(
    polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
    showlegend=False, height=430, margin=dict(l=60, r=60, t=30, b=30))
st.plotly_chart(radar, use_container_width=True)

cols = st.columns(len(pillars))
for col, p in zip(cols, pillars):
    col.metric(config.PILLAR_LABELS[p].split(" ")[0], f"{row[f'pillar_{p}']:.0f}",
               help=f"{config.PILLAR_LABELS[p]} · weight {config.PILLAR_WEIGHTS[p]:.0%}")

# ── Audit trail ──
st.markdown("### Audit trail — why this score?")
st.markdown("<span class='small-note'>Every indicator behind this country's score, with its "
            "source, year and confidence flag.</span>", unsafe_allow_html=True)

ca = audit[audit["country_iso3"] == iso3].copy()
ca = ca[["pillar", "indicator_label", "raw_value", "normalized_score",
         "source", "year", "confidence"]]
ca.columns = ["Pillar", "Indicator", "Raw value", "Normalized (0-100)", "Source", "Year", "Confidence"]
ca = ca.sort_values("Pillar")
st.dataframe(ca, use_container_width=True, hide_index=True,
             column_config={
                 "Normalized (0-100)": st.column_config.ProgressColumn(
                     "Normalized (0-100)", min_value=0, max_value=100, format="%.0f"),
             })

st.download_button(
    "⬇️ Download this country's audit trail (CSV)",
    ca.to_csv(index=False).encode("utf-8"),
    file_name=f"agoi_audit_{iso3}.csv", mime="text/csv")
