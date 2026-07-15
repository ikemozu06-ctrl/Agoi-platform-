"""
AfCFTA baseline indicator values for the vertical-slice countries.

PROVENANCE WARNING
The six AfCFTA indicators (GEX, DIV, GJOB, CIRC, LCMAN, GLCOR) are NOT standard
World Bank series. There is no public API that serves them. The protocol says
"you must obtain" them from the AfCFTA Secretariat, UNECA, UNCTAD, AfDB and
national trade ministries — that is real acquisition work, not a code task.

Until those datasets are acquired, the baselines below are PROXY estimates,
each flagged with how it was derived. They are ordered plausibly relative to one
another (South Africa-style industrial bases score higher on LCMAN; Ghana and
Côte d'Ivoire score higher on green agri exports) but the absolute levels are
not measurements and must not be presented as such.

Every row carries a `confidence` flag, consistent with the core AGOI platform:
    measured | interpolated | proxy | default
Currently all are "proxy" — the module says so, loudly, in the UI.
"""
from __future__ import annotations
from typing import Dict

from agoi.afcfta.config import AFCFTA_INDICATORS, SLICE_COUNTRIES

# ──────────────────────────────────────────────────────────────────────────────
# Baseline values (0–100 normalized scale for all six indicators).
# Derivation notes below each country.
# ──────────────────────────────────────────────────────────────────────────────
BASELINES: Dict[str, Dict[str, float]] = {
    "NGA": {  # Nigeria — large economy, oil-dominated exports => low GEX/DIV
        "GEX": 11.0, "DIV": 22.0, "GJOB": 14.0,
        "CIRC": 18.0, "LCMAN": 21.0, "GLCOR": 38.0,
    },
    "GHA": {  # Ghana — more diversified, stronger agri & cocoa value chains
        "GEX": 24.0, "DIV": 41.0, "GJOB": 22.0,
        "CIRC": 26.0, "LCMAN": 28.0, "GLCOR": 47.0,
    },
    "CIV": {  # Côte d'Ivoire — strong agri exports, Abidjan port hub
        "GEX": 27.0, "DIV": 44.0, "GJOB": 24.0,
        "CIRC": 23.0, "LCMAN": 26.0, "GLCOR": 52.0,
    },
    "BEN": {  # Benin — small, trade/transit-dependent economy
        "GEX": 17.0, "DIV": 31.0, "GJOB": 17.0,
        "CIRC": 15.0, "LCMAN": 14.0, "GLCOR": 35.0,
    },
    "TGO": {  # Togo — Lomé port corridor role, small manufacturing base
        "GEX": 19.0, "DIV": 33.0, "GJOB": 18.0,
        "CIRC": 17.0, "LCMAN": 16.0, "GLCOR": 41.0,
    },
}

# How each baseline was derived — surfaced in the UI audit view.
PROVENANCE_NOTES: Dict[str, str] = {
    "GEX":   "Proxy: derived from export-composition patterns (low-carbon goods share of "
             "merchandise exports). Requires UNCTAD/AfCFTA Secretariat data to replace.",
    "DIV":   "Proxy: informed by export-concentration (HHI-style) reasoning. Requires "
             "UNCTAD export diversification index to replace.",
    "GJOB":  "Proxy: no harmonised African green-jobs series exists. Requires ILO/AfDB "
             "green-employment estimates to replace.",
    "CIRC":  "Proxy: no standard circular-economy index for African states. Requires "
             "UNECA/AfDB circular-economy adoption survey to replace.",
    "LCMAN": "Proxy: informed by manufacturing value-added and energy-intensity patterns. "
             "Requires UNIDO low-carbon manufacturing data to replace.",
    "GLCOR": "Proxy: informed by logistics-performance and corridor-infrastructure "
             "reasoning. Requires AfDB/ECOWAS corridor assessments to replace.",
}

CONFIDENCE = "proxy"   # applies to every value in BASELINES, without exception


def get_baseline(iso3: str) -> Dict[str, float]:
    """Return the six AfCFTA baselines for a slice country."""
    return dict(BASELINES.get(iso3, {k: 0.0 for k in AFCFTA_INDICATORS}))


def baseline_rows() -> list:
    """Tidy rows for the audit trail, matching the core platform's schema."""
    rows = []
    for iso3 in SLICE_COUNTRIES:
        for code, value in BASELINES.get(iso3, {}).items():
            rows.append({
                "country_iso3": iso3,
                "indicator": f"AFCFTA.{code}",
                "indicator_label": AFCFTA_INDICATORS[code]["label"],
                "raw_value": value,
                "source": "NEC proxy estimate (AfCFTA module)",
                "year": 2024,
                "confidence": CONFIDENCE,
                "note": PROVENANCE_NOTES.get(code, ""),
            })
    return rows
