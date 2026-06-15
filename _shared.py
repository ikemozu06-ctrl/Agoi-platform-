"""Shared helpers for AGOI Streamlit pages."""
import os
import sys

import streamlit as st

_APP = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_APP)
for _p in (_APP, _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from agoi import config            # noqa: E402
from agoi.pipeline import run      # noqa: E402


@st.cache_data(show_spinner=False, ttl=60 * 60)
def load_data(mode: str):
    return run(mode=mode)


def get_data():
    """Load data using the mode chosen on the main page (defaults to mix)."""
    mode = st.session_state.get("data_mode", "mix")
    return load_data(mode)


def band_pill(label: str) -> str:
    return (f'<span style="display:inline-block;padding:.18rem .7rem;border-radius:999px;'
            f'color:#fff;font-weight:600;font-size:.82rem;background:{config.band_colour(label)}">'
            f'{label}</span>')


def inject_css():
    st.markdown("""
    <style>
    .main .block-container {padding-top: 2rem; max-width: 1200px;}
    h1, h2, h3 {color:#1F3864;}
    .small-note {color:#666; font-size:.83rem;}
    </style>
    """, unsafe_allow_html=True)
