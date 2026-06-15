"""
Top-level pipeline: choose a data source, run the scoring engine, return results.

Modes:
  "live"  — World Bank only (raise/empty -> caller handles)
  "demo"  — synthetic data only, clearly flagged
  "mix"   — try World Bank; fill any missing country/indicator pairs with demo
            values flagged confidence="default" (the honest hybrid)
"""
from __future__ import annotations
import pandas as pd

from agoi import config
from agoi.registry import INDICATORS, AFRICAN_COUNTRIES
from agoi.data_sources import worldbank, demo, afdb
from agoi.scoring.engine import score


def _demo_frame() -> pd.DataFrame:
    return pd.DataFrame(demo.fetch_all())


def _live_frame(progress=None) -> pd.DataFrame:
    """World Bank rows + AfDB project rows (AfDB omitted silently if unreachable)."""
    wb_rows = worldbank.fetch_all(progress=progress)
    afdb_rows = []
    try:
        if progress:
            progress(0.95, "Fetching AfDB project data…")
        afdb_rows = afdb.fetch_all()
    except Exception:  # noqa: BLE001 — never let AfDB break the World Bank pull
        afdb_rows = []
    return pd.DataFrame(wb_rows + afdb_rows)


def _fill_missing(live: pd.DataFrame) -> pd.DataFrame:
    """Add demo rows for any country/indicator pair missing from the live pull."""
    have = set(zip(live["country_iso3"], live["indicator"]))
    demo_rows = demo.fetch_all()
    fill = [r for r in demo_rows
            if (r["country_iso3"], r["indicator"]) not in have
            and r["country_iso3"] in AFRICAN_COUNTRIES]
    if not fill:
        return live
    return pd.concat([live, pd.DataFrame(fill)], ignore_index=True)


def run(mode: str = "mix", progress=None):
    """
    Returns (scores_df, audit_df, meta).
    meta carries data_mode actually used and any fallback note for the UI.
    """
    note = ""
    if mode == "demo":
        df = _demo_frame()
        used = "demo"
    else:
        try:
            live = _live_frame(progress=progress)
            # keep only African countries we track
            live = live[live["country_iso3"].isin(AFRICAN_COUNTRIES)]
            if live.empty:
                raise RuntimeError("World Bank returned no usable rows.")
            if mode == "mix":
                df = _fill_missing(live)
                used = "mix"
                n_demo = (df["confidence"] == config.CONF_DEFAULT).sum()
                if n_demo:
                    note = f"{n_demo} indicator values filled with demo data (flagged)."
            else:  # live
                df = live
                used = "live"
        except Exception as exc:  # noqa: BLE001
            df = _demo_frame()
            used = "demo"
            note = f"Live data unavailable ({exc}). Showing demo data."

    scores_df, audit_df = score(df)
    meta = {
        "data_mode": used,
        "note": note,
        "n_countries": len(scores_df),
        "n_indicators": df["indicator"].nunique(),
        "run_id": scores_df["run_id"].iloc[0] if len(scores_df) else None,
        "run_date": scores_df["run_date"].iloc[0] if len(scores_df) else None,
    }
    return scores_df, audit_df, meta
