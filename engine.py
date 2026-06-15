"""
Scoring engine: pillar aggregation -> AGOI score -> bands, plus the audit table
and per-country data-coverage (confidence) score.

This is the heart of the auditable product. Every score is produced here and the
full audit table is emitted alongside it so any number can be traced to source.
"""
from __future__ import annotations
import datetime as dt
import uuid
import pandas as pd

from agoi import config
from agoi.registry import INDICATORS, AFRICAN_COUNTRIES, indicators_for_pillar
from agoi.scoring.normalization import normalize_long


def _coverage_for(confidences) -> float:
    """0-100 coverage score from confidence flags (1 - mean penalty)."""
    penalties = [config.CONF_PENALTY.get(c, 0.5) for c in confidences]
    if not penalties:
        return 0.0
    return round((1 - sum(penalties) / len(penalties)) * 100, 1)


def score(df_long: pd.DataFrame):
    """
    Input: tidy rows (country_iso3, indicator, raw_value, year, source,
           retrieval_date, confidence).
    Returns: (scores_df, audit_df) with a shared run_id.
    """
    run_id = uuid.uuid4().hex[:12]
    run_date = dt.date.today().isoformat()

    norm = normalize_long(df_long)
    norm["run_id"] = run_id

    # ── Audit table — one row per indicator-country value ──
    audit = norm[[
        "run_id", "country_iso3", "indicator", "raw_value", "direction",
        "normalized_score", "source", "year", "retrieval_date", "confidence",
    ]].copy()
    audit["pillar"] = audit["indicator"].map(lambda c: INDICATORS.get(c, {}).get("pillar"))
    audit["indicator_label"] = audit["indicator"].map(
        lambda c: INDICATORS.get(c, {}).get("label", c))

    # ── Pillar scores per country (mean of that pillar's normalized indicators) ──
    rows = []
    for iso3 in AFRICAN_COUNTRIES:
        country_rows = norm[norm["country_iso3"] == iso3]
        if country_rows.empty:
            continue
        pillar_scores = {}
        for pillar in config.PILLAR_WEIGHTS:
            codes = list(indicators_for_pillar(pillar).keys())
            vals = country_rows[country_rows["indicator"].isin(codes)]["normalized_score"]
            pillar_scores[pillar] = round(vals.mean(), 1) if len(vals) else 50.0

        agoi = sum(pillar_scores[p] * w for p, w in config.PILLAR_WEIGHTS.items())
        agoi = round(max(0, min(100, agoi)), 1)
        coverage = _coverage_for(country_rows["confidence"].tolist())

        row = {
            "run_id": run_id,
            "run_date": run_date,
            "country_iso3": iso3,
            "country": AFRICAN_COUNTRIES[iso3],
            "agoi_score": agoi,
            "band": config.classify_band(agoi),
            "data_coverage": coverage,
        }
        row.update({f"pillar_{p}": pillar_scores[p] for p in config.PILLAR_WEIGHTS})
        rows.append(row)

    scores_df = pd.DataFrame(rows).sort_values("agoi_score", ascending=False).reset_index(drop=True)
    scores_df["rank"] = scores_df.index + 1
    return scores_df, audit
