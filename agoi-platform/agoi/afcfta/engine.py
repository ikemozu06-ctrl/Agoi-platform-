"""
AfCFTA simulation engine.

Implements the equations from the AGOI–AfCFTA Development Protocol:

  Country indicator update:   I'ᵢ = Iᵢ + Σₖ βᵢ,ₖ · Aₖ
  Corridor transit time:      TIME' = TIME − (α₁A₃ + α₂A₁ + α₃A₂)
  Corridor logistics cost:    COST' = COST − (δ₁A₃ + δ₂A₂)
  Corridor climate risk:      RISK' = RISK − (ρ₁A₃ + ρ₂·RES_lagos)
  Corridor green score:       GLCOR'= GLCOR + (γ₁A₁ + γ₂A₅ + γ₃A₃)
  Corridor trade volume:      TRVOL'= TRVOL + (θ₁A₃ + θ₂A₂ + θ₃A₁)
  Lagos trade-risk:           LAG_Tᵢ' = LAG_Tᵢ − (λᵢ · RES_lagos)

CRITICAL DESIGN DECISION — UNCERTAINTY PROPAGATION
Every β carries (low, value, high). This engine propagates all three, so every
output is a RANGE, not a point estimate. This is deliberate: the protocol's
equations produce confident-looking numbers, but the coefficients behind them are
currently placeholders. Reporting "green exports rise 4–11%" is defensible;
reporting "8.4%" is not. The UI must never display the central value alone.
"""
from __future__ import annotations
from typing import Dict

from agoi.afcfta import config as acfg
from agoi.afcfta import elasticity as el


def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


# ──────────────────────────────────────────────────────────────────────────────
# Country simulation
# ──────────────────────────────────────────────────────────────────────────────
def simulate_country(baseline: Dict[str, float], levers: Dict[str, float]) -> Dict[str, Dict]:
    """
    baseline: {indicator_code: value}  e.g. {"GEX": 12.0, ...}
    levers:   {lever_code: 0.0–1.0}    e.g. {"A1": 0.5, ...}

    Returns {indicator: {baseline, low, value, high, delta_low, delta, delta_high}}
    Each bound is computed by applying the corresponding β bound across all levers.
    """
    out: Dict[str, Dict] = {}
    for ind in acfg.AFCFTA_INDICATORS:
        base = float(baseline.get(ind, 0.0))
        row = el.COUNTRY_ELASTICITY.get(ind, {})

        d_lo = d_mid = d_hi = 0.0
        for lever, a in levers.items():
            b = row.get(lever)
            if not b or a <= 0:
                continue
            d_lo  += b["low"]   * a
            d_mid += b["value"] * a
            d_hi  += b["high"]  * a

        out[ind] = {
            "baseline":   round(base, 2),
            "low":        round(_clamp(base + d_lo), 2),
            "value":      round(_clamp(base + d_mid), 2),
            "high":       round(_clamp(base + d_hi), 2),
            "delta_low":  round(d_lo, 2),
            "delta":      round(d_mid, 2),
            "delta_high": round(d_hi, 2),
        }
    return out


# ──────────────────────────────────────────────────────────────────────────────
# Corridor simulation
# ──────────────────────────────────────────────────────────────────────────────
def _corridor_delta(metric: str, levers: Dict[str, float], res_lagos: float):
    """Sum β·A across the coefficients defined for this metric. Returns (lo, mid, hi)."""
    coeffs = el.CORRIDOR_COEFFS.get(metric, {})
    lo = mid = hi = 0.0
    for key, b in coeffs.items():
        a = res_lagos if key == "RES_LAGOS" else levers.get(key, 0.0)
        if a <= 0:
            continue
        lo  += b["low"]   * a
        mid += b["value"] * a
        hi  += b["high"]  * a
    return lo, mid, hi


def simulate_corridor(corridor_id: str, levers: Dict[str, float],
                      res_lagos: float = 0.0) -> Dict[str, Dict]:
    """
    Apply the protocol's five corridor equations with uncertainty propagation.
    Metrics where LOWER is better (transit_time, logistics_cost, climate_risk) are
    SUBTRACTED; metrics where HIGHER is better are ADDED.
    """
    corridor = acfg.CORRIDORS[corridor_id]
    base = corridor["baseline_metrics"]

    # (metric, direction) — "lower" means the lever reduces it (good)
    spec = [
        ("transit_time",   "lower"),
        ("logistics_cost", "lower"),
        ("climate_risk",   "lower"),
        ("green_score",    "higher"),
        ("trade_volume",   "higher"),
    ]

    results: Dict[str, Dict] = {}
    for metric, direction in spec:
        b0 = float(base[metric])
        lo, mid, hi = _corridor_delta(metric, levers, res_lagos)

        if direction == "lower":
            # bigger delta = bigger reduction = better. The HIGH β gives the LOW value.
            v_best  = max(0.0, b0 - hi)
            v_mid   = max(0.0, b0 - mid)
            v_worst = max(0.0, b0 - lo)
            results[metric] = {
                "baseline": round(b0, 1), "direction": "lower",
                "low": round(v_best, 1), "value": round(v_mid, 1), "high": round(v_worst, 1),
                "delta": round(-mid, 1), "delta_low": round(-hi, 1), "delta_high": round(-lo, 1),
            }
        else:
            cap = 100.0 if metric == "green_score" else None
            def _c(x):
                return round(min(x, cap), 1) if cap else round(x, 1)
            results[metric] = {
                "baseline": round(b0, 1), "direction": "higher",
                "low": _c(b0 + lo), "value": _c(b0 + mid), "high": _c(b0 + hi),
                "delta": round(mid, 1), "delta_low": round(lo, 1), "delta_high": round(hi, 1),
            }
    return results


# ──────────────────────────────────────────────────────────────────────────────
# Lagos flood → trade-risk simulation (the City Lab linkage)
# ──────────────────────────────────────────────────────────────────────────────
def simulate_lagos_trade_risk(res_lagos: float) -> Dict[str, Dict]:
    """
    All four Lagos trade-risk indicators are 'lower is better'. The resilience
    lever reduces each. Returns ranges.
    """
    out: Dict[str, Dict] = {}
    for code, meta in acfg.LAGOS_TRADE_RISK.items():
        b0 = float(meta["baseline"])
        b = el.LAGOS_COEFFS[code]
        red_lo, red_mid, red_hi = b["low"] * res_lagos, b["value"] * res_lagos, b["high"] * res_lagos
        out[code] = {
            "label": meta["label"], "unit": meta["unit"],
            "baseline": round(b0, 1),
            "low":   round(max(0.0, b0 - red_hi), 1),   # best case
            "value": round(max(0.0, b0 - red_mid), 1),
            "high":  round(max(0.0, b0 - red_lo), 1),   # worst case
            "delta": round(-red_mid, 1),
        }
    return out


def node_risk(corridor_id: str, res_lagos: float) -> list:
    """
    Corridor node risk, with the Lagos flood linkage applied.
    Lagos resilience investment reduces Lagos node flood risk directly, and
    (at a lower weight) neighbouring nodes via corridor spillover.
    """
    corridor = acfg.CORRIDORS[corridor_id]
    nodes = []
    for n in corridor["nodes"]:
        fr = float(n["flood_risk"])
        if n["node_id"] == "LOS":
            fr_new = max(0.0, fr - 30.0 * res_lagos)        # direct effect
        else:
            fr_new = max(0.0, fr - 6.0 * res_lagos)         # corridor spillover
        nodes.append({**n,
                      "flood_risk_baseline": fr,
                      "flood_risk_scenario": round(fr_new, 1)})
    return nodes


# ──────────────────────────────────────────────────────────────────────────────
# AGOI integration: AfCFTA readiness score feeding the core index
# ──────────────────────────────────────────────────────────────────────────────
def afcfta_readiness(indicator_values: Dict[str, float]) -> float:
    """
    Composite 0–100 AfCFTA readiness from the six indicators (equal weight for
    now — weighting is a governance decision, not a code decision).
    Assumes each indicator is already normalized 0–100.
    """
    vals = [float(indicator_values.get(k, 0.0)) for k in acfg.AFCFTA_INDICATORS]
    return round(sum(vals) / len(vals), 1) if vals else 0.0
