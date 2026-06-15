"""
Normalization pipeline (Technical Manual v2.0, Section 4.2):

    raw_value -> direction alignment -> winsorization -> min-max scale (0-100)

One consistent method across all indicators so a 70 in one pillar is
methodologically comparable to a 70 in another.
"""
from __future__ import annotations
import pandas as pd

from agoi import config
from agoi.registry import INDICATORS


def normalize_indicator(series: pd.Series, direction: str) -> pd.Series:
    """
    series: index = country_iso3, values = raw_value for ONE indicator.
    Returns a 0-100 normalized score series (higher always = better).
    """
    s = series.astype(float).copy()

    # 1. Direction alignment — invert "lower is better" so higher always wins.
    if direction == "lower":
        s = -s

    # 2. Winsorization — clip extremes so one outlier doesn't compress everyone.
    lo = s.quantile(config.WINSOR_LOWER)
    hi = s.quantile(config.WINSOR_UPPER)
    s = s.clip(lower=lo, upper=hi)

    # 3. Min-max scale to 0-100.
    smin, smax = s.min(), s.max()
    if smax == smin:
        return pd.Series(50.0, index=s.index)  # no spread -> neutral
    return (s - smin) / (smax - smin) * 100.0


def normalize_long(df: pd.DataFrame) -> pd.DataFrame:
    """
    df (long/tidy): country_iso3, indicator, raw_value, ... , confidence
    Adds a `normalized_score` column computed per indicator across countries.
    """
    out = []
    for code, group in df.groupby("indicator"):
        direction = INDICATORS.get(code, {}).get("direction", "higher")
        wide = group.set_index("country_iso3")["raw_value"]
        norm = normalize_indicator(wide, direction)
        g = group.copy()
        g["normalized_score"] = g["country_iso3"].map(norm)
        g["direction"] = direction
        out.append(g)
    return pd.concat(out, ignore_index=True)
