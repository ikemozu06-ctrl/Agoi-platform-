"""
AGOI™ ESG Platform — Streamlit MVP
Natural Eco Capital

Run locally:   streamlit run app/streamlit_app.py
"""
import os
import sys

import pandas as pd
import plotly.express as px
import streamlit as st

# Make the agoi package importable when run from the repo root or app/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agoi import config
from agoi.pipeline import run

# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AGOI™ ESG Platform — Natural Eco Capital",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

NAVY = "#1F3864"
BLUE = "#2E75B6"
GREEN = "#1B6B35"

st.markdown(f"""
<style>
.main .block-container {{padding-top: 2rem; max-width: 1200px;}}
h1, h2, h3 {{color: {NAVY};}}
.agoi-hero {{
  background: linear-gradient(110deg, {NAVY} 0%, {BLUE} 100%);
  padding: 1.6rem 2rem; border-radius: 14px; color: #fff; margin-bottom: 1.2rem;
}}
.agoi-hero h1 {{color:#fff; margin:0; font-size:2.0rem;}}
.agoi-hero p {{color:#dce6f5; margin:.3rem 0 0 0;}}
.metric-card {{background:#f5f8fc; border-radius:12px; padding:1rem 1.2rem; border:1px solid #e1e8f2;}}
.band-pill {{display:inline-block; padding:.18rem .7rem; border-radius:999px; color:#fff; font-weight:600; font-size:.82rem;}}
.small-note {{color:#666; font-size:.83rem;}}
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# Data loading (cached). The mode is chosen in the sidebar.
# ──────────────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False, ttl=60 * 60)
def load_data(mode: str):
    scores, audit, meta = run(mode=mode)
    return scores, audit, meta


def band_pill(label: str) -> str:
    return f'<span class="band-pill" style="background:{config.band_colour(label)}">{label}</span>'


def data_badge(meta: dict):
    mode = meta["data_mode"]
    if mode == "live":
        st.success(f"🟢 **Live World Bank data** · {meta['n_countries']} countries · "
                   f"{meta['n_indicators']} indicators · run {meta['run_id']} ({meta['run_date']})")
    elif mode == "mix":
        st.info(f"🔵 **Mixed data** (live World Bank + flagged demo fill) · "
                f"{meta['n_countries']} countries · run {meta['run_id']}. {meta['note']}")
    else:
        st.warning(f"🟡 **DEMO DATA — not real measurements.** {meta['note'] or 'Synthetic sample for demonstration.'} "
                   f"All values flagged low-confidence. Switch to Live/Mix in the sidebar for real World Bank data.")
    # AfDB diagnostic line — always visible so AfDB status is never a mystery.
    afdb_status = meta.get("afdb_status", "not run")
    st.caption(f"🏦 AfDB project data — {afdb_status}")


# ──────────────────────────────────────────────────────────────────────────────
# Sidebar — data mode control, shared across pages via session_state.
# ──────────────────────────────────────────────────────────────────────────────
st.sidebar.markdown("### ⚙️ Data source")
mode = st.sidebar.radio(
    "Mode",
    options=["mix", "live", "demo"],
    format_func=lambda m: {"mix": "Mixed (recommended)", "live": "Live World Bank only",
                           "demo": "Demo / offline"}[m],
    help="Mixed pulls live World Bank data and fills any gaps with clearly-flagged demo values.",
)
st.session_state["data_mode"] = mode

if st.sidebar.button("🔄 Refresh data (clear cache)"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown(
    "<span class='small-note'>AGOI™ — Africa Green Opportunity Index<br>"
    "Natural Eco Capital · MVP build</span>", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# Hero
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="agoi-hero">
  <h1>🌍 AGOI™ ESG Platform</h1>
  <p>Africa Green Opportunity Index — investment-readiness scoring across 54 African countries,
  with full data provenance and confidence flags.</p>
</div>
""", unsafe_allow_html=True)

with st.spinner("Loading scores…"):
    scores, audit, meta = load_data(mode)

data_badge(meta)

# ── Headline metrics ──
c1, c2, c3, c4 = st.columns(4)
top = scores.iloc[0]
core_green = (scores["band"] == "Core Green Zone").sum()
growth_green = (scores["band"] == "Growth Green Zone").sum()
avg_cov = scores["data_coverage"].mean()

with c1:
    st.markdown(f"<div class='metric-card'><b>Top-ranked</b><br><span style='font-size:1.3rem;color:{GREEN}'>"
                f"{top['country']}</span><br>{top['agoi_score']:.1f} / 100</div>", unsafe_allow_html=True)
with c2:
    st.markdown(f"<div class='metric-card'><b>Core Green Zone</b><br>"
                f"<span style='font-size:1.6rem;color:{GREEN}'>{core_green}</span> countries</div>",
                unsafe_allow_html=True)
with c3:
    st.markdown(f"<div class='metric-card'><b>Growth Green Zone</b><br>"
                f"<span style='font-size:1.6rem;color:{BLUE}'>{growth_green}</span> countries</div>",
                unsafe_allow_html=True)
with c4:
    st.markdown(f"<div class='metric-card'><b>Avg data coverage</b><br>"
                f"<span style='font-size:1.6rem;color:{NAVY}'>{avg_cov:.0f}%</span></div>",
                unsafe_allow_html=True)

st.markdown("### Continental ranking")

# ── Band filter ──
bands_present = [b[2] for b in config.BANDS if b[2] in scores["band"].unique()]
sel_bands = st.multiselect("Filter by opportunity band", bands_present, default=bands_present)
view = scores[scores["band"].isin(sel_bands)]

# ── Ranking bar chart ──
fig = px.bar(
    view.sort_values("agoi_score"),
    x="agoi_score", y="country", orientation="h",
    color="band",
    color_discrete_map={b[2]: b[3] for b in config.BANDS},
    labels={"agoi_score": "AGOI score", "country": ""},
    height=max(400, 18 * len(view)),
)
fig.update_layout(margin=dict(l=0, r=10, t=10, b=0), legend_title="Band",
                  plot_bgcolor="white", yaxis=dict(tickfont=dict(size=11)))
st.plotly_chart(fig, use_container_width=True)

# ── Ranking table ──
st.markdown("#### Score table")
show = view[["rank", "country", "agoi_score", "band", "data_coverage"]].copy()
show.columns = ["Rank", "Country", "AGOI score", "Band", "Coverage %"]
st.dataframe(show, use_container_width=True, hide_index=True,
             column_config={
                 "AGOI score": st.column_config.ProgressColumn(
                     "AGOI score", min_value=0, max_value=100, format="%.1f"),
                 "Coverage %": st.column_config.NumberColumn("Coverage %", format="%.0f%%"),
             })

st.markdown("<span class='small-note'>Use the pages in the sidebar for country profiles, "
            "the Africa map, pillar comparison, the scenario tool and the audit trail.</span>",
            unsafe_allow_html=True)
