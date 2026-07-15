"""
AfCFTA elasticity matrix — WITH MANDATORY PROVENANCE.

═══════════════════════════════════════════════════════════════════════════════
READ THIS BEFORE USING ANY OUTPUT OF THIS MODULE
═══════════════════════════════════════════════════════════════════════════════
The AfCFTA Development Protocol specifies a 6-indicator × 5-lever elasticity
matrix (β) but does NOT specify where the β values come from. That gap is the
single biggest credibility risk in the whole module: a simulator populated with
invented coefficients produces confident, precise-looking policy numbers with no
empirical basis — and unlike a wrong score, a wrong elasticity carries an implied
CAUSAL claim that a ministry or DFI might act on.

This module therefore refuses to store a bare number. Every β carries:

    value        the central estimate
    low, high    an uncertainty range (NOT decoration — the simulator propagates it)
    provenance   how we know it:
                   "estimated"  — fitted from panel data (highest confidence)
                   "literature" — taken from a cited published study
                   "elicited"   — structured expert elicitation, range recorded
                   "assumed"    — PLACEHOLDER. Not evidence. Must be replaced.
    source       a citable string; for "assumed" it says so plainly

CURRENT STATE: every β below is provenance="assumed". They are STRUCTURAL
PLACEHOLDERS that make the engine runnable end-to-end — they are NOT findings.
The UI labels them as such and the simulator reports RANGES, never point
estimates. Replacing these with estimated/literature/elicited values is the
first substantive research task of the AfCFTA module (see ELASTICITY_ROADMAP).

Directionality of the placeholders is defensible (a logistics upgrade plausibly
raises green-logistics score more than it raises green jobs); the MAGNITUDES are
not. Treat every number as "shape, not size".
═══════════════════════════════════════════════════════════════════════════════
"""
from __future__ import annotations
from typing import Dict

# Provenance levels, ordered by strength.
PROV_ESTIMATED  = "estimated"
PROV_LITERATURE = "literature"
PROV_ELICITED   = "elicited"
PROV_ASSUMED    = "assumed"

PROV_RANK = {PROV_ESTIMATED: 3, PROV_LITERATURE: 2, PROV_ELICITED: 1, PROV_ASSUMED: 0}

PROV_LABEL = {
    PROV_ESTIMATED:  "Estimated from panel data",
    PROV_LITERATURE: "Derived from published literature",
    PROV_ELICITED:   "Structured expert elicitation",
    PROV_ASSUMED:    "PLACEHOLDER — not evidence",
}


def beta(value: float, low: float, high: float,
         provenance: str = PROV_ASSUMED, source: str = "") -> Dict:
    """Construct an elasticity entry. Provenance and range are mandatory."""
    if provenance == PROV_ASSUMED and not source:
        source = "Structural placeholder. No empirical basis. Must be replaced."
    return {"value": value, "low": low, "high": high,
            "provenance": provenance, "source": source}


# ──────────────────────────────────────────────────────────────────────────────
# COUNTRY ELASTICITY MATRIX  β[indicator][lever]
# Interpretation: a lever at full adoption (A=1.0) shifts the indicator by β
# points on its own scale. Ranges are deliberately WIDE — that width is honest.
# ──────────────────────────────────────────────────────────────────────────────
COUNTRY_ELASTICITY: Dict[str, Dict[str, Dict]] = {
    "GEX": {   # Green Exports Share
        "A1": beta(6.0,  2.0, 11.0),   # green standards open premium markets
        "A2": beta(5.0,  1.5,  9.5),   # investment incentives build green capacity
        "A3": beta(3.5,  1.0,  7.0),   # corridors lower export friction
        "A4": beta(2.5,  0.5,  5.5),   # CSA lifts green agri exports
        "A5": beta(2.0,  0.5,  4.5),   # circularity as a market-access condition
    },
    "DIV": {   # Export Diversification
        "A1": beta(2.5,  0.5,  5.5),
        "A2": beta(5.5,  2.0, 10.0),   # incentives seed new sectors
        "A3": beta(4.5,  1.5,  9.0),   # corridors widen viable export set
        "A4": beta(3.0,  0.5,  6.5),
        "A5": beta(1.5,  0.0,  4.0),
    },
    "GJOB": {  # Green Jobs
        "A1": beta(3.0,  1.0,  6.5),
        "A2": beta(6.5,  2.5, 12.0),   # incentives are the main jobs channel
        "A3": beta(3.0,  1.0,  6.5),
        "A4": beta(5.0,  1.5, 10.0),   # CSA is labour-intensive
        "A5": beta(4.0,  1.0,  8.5),   # circular economy is job-rich
    },
    "CIRC": {  # Circular Economy Adoption
        "A1": beta(4.0,  1.0,  8.0),
        "A2": beta(3.5,  1.0,  7.5),
        "A3": beta(1.5,  0.0,  4.0),
        "A4": beta(2.0,  0.0,  5.0),
        "A5": beta(9.0,  4.0, 15.0),   # the lever is the mechanism
    },
    "LCMAN": { # Low-Carbon Manufacturing Share
        "A1": beta(5.0,  1.5, 10.0),
        "A2": beta(6.0,  2.0, 11.5),
        "A3": beta(2.5,  0.5,  5.5),
        "A4": beta(1.0,  0.0,  3.0),
        "A5": beta(4.5,  1.5,  9.0),
    },
    "GLCOR": { # Green Logistics Corridor Score
        "A1": beta(4.0,  1.0,  8.5),
        "A2": beta(3.0,  0.5,  6.5),
        "A3": beta(9.5,  5.0, 15.0),   # the lever is the mechanism
        "A4": beta(1.0,  0.0,  3.0),
        "A5": beta(3.5,  1.0,  7.0),
    },
}

# ──────────────────────────────────────────────────────────────────────────────
# CORRIDOR EQUATION COEFFICIENTS
# Per the protocol's corridor equations. Same provenance discipline applies.
#   TIME' = TIME - (a1·A3 + a2·A1 + a3·A2)
#   COST' = COST - (d1·A3 + d2·A2)
#   RISK' = RISK - (r1·A3 + r2·RES_lagos)
#   GLCOR'= GLCOR + (g1·A1 + g2·A5 + g3·A3)
#   TRVOL'= TRVOL + (t1·A3 + t2·A2 + t3·A1)
# ──────────────────────────────────────────────────────────────────────────────
CORRIDOR_COEFFS = {
    "transit_time": {   # days reduced at full lever adoption
        "A3": beta(1.10, 0.50, 1.80),
        "A1": beta(0.25, 0.05, 0.60),
        "A2": beta(0.20, 0.00, 0.50),
    },
    "logistics_cost": { # USD/TEU reduced
        "A3": beta(420.0, 180.0, 700.0),
        "A2": beta(150.0,  40.0, 300.0),
    },
    "climate_risk": {   # index points reduced
        "A3": beta(8.0,  3.0, 14.0),
        "RES_LAGOS": beta(15.0, 7.0, 24.0),  # Lagos resilience is the big lever
    },
    "green_score": {    # GLCOR index points gained
        "A1": beta(7.0,  3.0, 12.0),
        "A5": beta(5.5,  2.0, 10.0),
        "A3": beta(9.0,  4.0, 15.0),
    },
    "trade_volume": {   # index points gained (baseline 100)
        "A3": beta(9.0,  3.5, 16.0),
        "A2": beta(5.0,  1.5, 10.0),
        "A1": beta(3.5,  1.0,  7.5),
    },
}

# ──────────────────────────────────────────────────────────────────────────────
# LAGOS FLOOD → TRADE-RISK COEFFICIENTS
# How the Lagos resilience lever (RES_LAGOS) improves each trade-risk indicator.
# All four indicators are "lower is better", so the lever REDUCES them.
# ──────────────────────────────────────────────────────────────────────────────
LAGOS_COEFFS = {
    "LAG_T1": beta(11.0, 5.0, 16.0),   # port flood disruption days avoided
    "LAG_T2": beta(20.0, 9.0, 30.0),   # logistics delay hours avoided
    "LAG_T3": beta(5.5,  2.0,  9.0),   # export volume loss avoided (pp)
    "LAG_T4": beta(7.5,  3.0, 12.0),   # import clearance delay avoided (pp)
}


# ──────────────────────────────────────────────────────────────────────────────
# Governance helpers
# ──────────────────────────────────────────────────────────────────────────────
def matrix_provenance_summary() -> Dict[str, int]:
    """Count β entries by provenance across the whole module."""
    counts = {PROV_ESTIMATED: 0, PROV_LITERATURE: 0, PROV_ELICITED: 0, PROV_ASSUMED: 0}

    def _walk(d):
        for v in d.values():
            if isinstance(v, dict) and "provenance" in v:
                counts[v["provenance"]] = counts.get(v["provenance"], 0) + 1
            elif isinstance(v, dict):
                _walk(v)

    _walk(COUNTRY_ELASTICITY)
    _walk(CORRIDOR_COEFFS)
    _walk(LAGOS_COEFFS)
    return counts


def confidence_grade() -> str:
    """
    Overall grade for the elasticity matrix. Drives the warning banner in the UI.
    Any 'assumed' coefficients at all => the module is a SCENARIO EXPLORER, not a
    forecaster, and must say so.
    """
    c = matrix_provenance_summary()
    total = sum(c.values())
    if total == 0:
        return "EMPTY"
    if c[PROV_ASSUMED] == total:
        return "PLACEHOLDER"          # nothing is evidence-based yet
    if c[PROV_ASSUMED] > 0:
        return "MIXED"                # partially grounded
    if c[PROV_ESTIMATED] >= total / 2:
        return "ESTIMATED"            # majority empirically fitted
    return "GROUNDED"                 # literature/elicited, no placeholders


# The research task that replaces the placeholders. Surfaced in the UI.
ELASTICITY_ROADMAP = [
    ("1. Econometric estimation",
     "Fit β from historical panel data (trade flows vs. policy adoption) wherever "
     "a usable panel exists. Highest confidence. Sets provenance='estimated'."),
    ("2. Literature-derived priors",
     "For indicators without a panel, take elasticities from published trade/climate "
     "economics studies and cite each one. Sets provenance='literature'."),
    ("3. Structured expert elicitation",
     "Convene AfCFTA Secretariat / UNECA / AfDB experts. Elicit RANGES, not point "
     "estimates; record attribution. Sets provenance='elicited'."),
    ("4. Calibration & review cycle",
     "Back-test scenarios against observed outcomes; schedule expert re-review. "
     "Publish the matrix and its provenance alongside the methodology."),
]
