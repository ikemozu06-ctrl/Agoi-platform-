import os
import sys
import io

import pandas as pd
import streamlit as st

_APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ROOT = os.path.dirname(_APP)
for _p in (_APP, _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)
from _shared import get_data, inject_css   # noqa: E402
from agoi import config                     # noqa: E402
from agoi.registry import INDICATORS        # noqa: E402

st.set_page_config(page_title="Export & methodology · AGOI™", page_icon="⬇️", layout="wide")
inject_css()
st.title("⬇️ Export centre & methodology")

scores, audit, meta = get_data()

st.markdown("### Downloads")
c1, c2, c3 = st.columns(3)
with c1:
    st.download_button("Scores (CSV)",
                       scores.to_csv(index=False).encode("utf-8"),
                       "agoi_scores.csv", "text/csv", use_container_width=True)
with c2:
    st.download_button("Full audit trail (CSV)",
                       audit.to_csv(index=False).encode("utf-8"),
                       "agoi_audit_trail.csv", "text/csv", use_container_width=True)
with c3:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        scores.to_excel(xw, sheet_name="Scores", index=False)
        audit.to_excel(xw, sheet_name="Audit trail", index=False)
    st.download_button("Excel workbook (.xlsx)", buf.getvalue(),
                       "agoi_platform.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       use_container_width=True)

st.markdown("---")
st.markdown("### Methodology")
st.markdown(f"""
**AGOI™** scores every African country 0–100 across six weighted pillars. Each indicator
flows through one consistent pipeline: **direction alignment → winsorization
({config.WINSOR_LOWER:.0%}/{config.WINSOR_UPPER:.0%}) → min-max scale to 0–100 → weighted
pillar aggregation → weighted AGOI score → opportunity band**.

Every value carries a **confidence flag** (measured / interpolated / proxy / default) and a
per-country **data-coverage score** so a score built on real data is always distinguishable
from one resting on fallbacks.
""")

st.markdown("#### Pillar weights")
wdf = pd.DataFrame({
    "Pillar": [config.PILLAR_LABELS[p] for p in config.PILLAR_WEIGHTS],
    "Weight": [f"{w:.0%}" for w in config.PILLAR_WEIGHTS.values()],
})
st.dataframe(wdf, hide_index=True, use_container_width=True)

st.markdown("#### Opportunity bands")
bdf = pd.DataFrame({
    "Band": [b[2] for b in config.BANDS],
    "Range": [f"{b[0]}–{b[1]-1}" for b in config.BANDS],
    "Reading": [config.BAND_READING[b[2]] for b in config.BANDS],
})
st.dataframe(bdf, hide_index=True, use_container_width=True)

st.markdown("#### Indicator registry")
idf = pd.DataFrame([
    {"Indicator": m["label"], "Code": c, "Pillar": config.PILLAR_LABELS[m["pillar"]],
     "Direction": m["direction"], "Source": m["source"]}
    for c, m in INDICATORS.items()
])
st.dataframe(idf, hide_index=True, use_container_width=True)

st.markdown("<br><span class='small-note'>Run "
            f"{meta['run_id']} · {meta['run_date']} · data mode: {meta['data_mode']}</span>",
            unsafe_allow_html=True)
