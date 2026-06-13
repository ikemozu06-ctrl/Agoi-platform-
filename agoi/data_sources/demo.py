"""
Demo data source.

Generates realistic, deterministic sample values for every indicator and country
when live World Bank data is unavailable (offline, rate-limited, or user-selected
demo mode). Values are seeded so they are stable across runs, and every row is
flagged confidence="default" so the platform is always honest that these are not
measured values.

The values are not random noise: they are anchored to rough real-world regional
patterns so the demo is plausible for a board demo, but they must never be
presented as real data.
"""
from __future__ import annotations
import datetime as dt
import hashlib
from typing import List

from agoi import config
from agoi.registry import INDICATORS, AFRICAN_COUNTRIES

# Rough regional anchors (0-1 scale) used to make demo data plausible rather
# than uniform. Higher = stronger on green-investment fundamentals overall.
_REGIONAL_ANCHOR = {
    "MUS": 0.78, "SYC": 0.74, "ZAF": 0.70, "MAR": 0.68, "CPV": 0.66,
    "NAM": 0.64, "BWA": 0.63, "TUN": 0.62, "GHA": 0.60, "KEN": 0.60,
    "RWA": 0.62, "SEN": 0.58, "EGY": 0.57, "CIV": 0.55, "NGA": 0.52,
    "TZA": 0.52, "UGA": 0.50, "ZMB": 0.49, "ETH": 0.48, "BEN": 0.47,
    "DZA": 0.55, "GAB": 0.54, "AGO": 0.45, "MOZ": 0.44, "CMR": 0.45,
    "MWI": 0.42, "MLI": 0.40, "BFA": 0.40, "NER": 0.36, "TCD": 0.32,
    "COD": 0.34, "CAF": 0.30, "SSD": 0.26, "SOM": 0.25, "ERI": 0.30,
}
_DEFAULT_ANCHOR = 0.45


def _det_unit(iso3: str, code: str) -> float:
    """Deterministic pseudo-value in [0,1] from a hash of (country, indicator)."""
    h = hashlib.sha256(f"{iso3}:{code}".encode()).hexdigest()
    return int(h[:8], 16) / 0xFFFFFFFF


def _scaled_value(iso3: str, code: str) -> float:
    """Produce a plausible raw value for the indicator's natural range."""
    anchor = _REGIONAL_ANCHOR.get(iso3, _DEFAULT_ANCHOR)
    jitter = (_det_unit(iso3, code) - 0.5) * 0.4   # +/- 0.2
    base = max(0.02, min(0.98, anchor + jitter))   # blended 0-1 signal

    direction = INDICATORS[code]["direction"]
    # For "lower is better" indicators, invert so a strong country gets a low raw value.
    signal = base if direction == "higher" else (1.0 - base)

    # Map the 0-1 signal onto a believable real-world range per indicator family.
    ranges = {
        "EG.ELC.RNEW.ZS": (0, 95),     "EG.FEC.RNEW.ZS": (2, 90),
        "RL.EST": (-2.0, 1.2),         "RQ.EST": (-2.0, 1.2),
        "FS.AST.PRVT.GD.ZS": (5, 120), "FX.OWN.TOTL.ZS": (10, 90),
        "BX.KLT.DINV.WD.GD.ZS": (0, 12),
        "AG.LND.FRST.ZS": (1, 70),     "ER.H2O.INTR.PC": (50, 12000),
        "SL.UEM.1524.ZS": (3, 55),     "SL.TLF.CACT.FE.ZS": (20, 85),
    }
    lo, hi = ranges.get(code, (0, 100))
    # signal already encodes direction; for "lower" indicators map strong signal
    # (high) back to a *low* raw value.
    if INDICATORS[code]["direction"] == "lower":
        return round(hi - signal * (hi - lo), 2)
    return round(lo + signal * (hi - lo), 2)


def fetch_all() -> List[dict]:
    rows: List[dict] = []
    retrieval = dt.date.today().isoformat()
    for iso3 in AFRICAN_COUNTRIES:
        for code in INDICATORS:
            rows.append({
                "country_iso3": iso3,
                "indicator": code,
                "raw_value": _scaled_value(iso3, code),
                "year": 2024,
                "source": "DEMO (synthetic)",
                "retrieval_date": retrieval,
                "confidence": config.CONF_DEFAULT,
            })
    return rows
