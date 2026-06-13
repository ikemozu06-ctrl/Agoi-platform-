"""
World Bank data source.

Fetches indicators from the World Bank API, keyed on ISO alpha-3 (the fix).
Caches raw responses to data/cache/ so runs are reproducible and the source
can be re-inspected without re-hitting the API.

Returns tidy rows: country_iso3, indicator, raw_value, year, source, confidence.
"""
from __future__ import annotations
import json
import os
import time
import datetime as dt
from typing import Dict, List

import requests

from agoi import config
from agoi.registry import INDICATORS

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "cache")
WB_BASE = "https://api.worldbank.org/v2"


def _cache_path(indicator: str) -> str:
    os.makedirs(CACHE_DIR, exist_ok=True)
    today = dt.date.today().isoformat()
    return os.path.join(CACHE_DIR, f"wb_{indicator}_{today}.json")


def _fetch_indicator(indicator: str) -> List[dict]:
    """Fetch the most recent value per country for one indicator (all countries)."""
    cache = _cache_path(indicator)
    if os.path.exists(cache):
        with open(cache, "r", encoding="utf-8") as fh:
            return json.load(fh)

    # mrnev=1 -> most recent non-empty value per country
    url = f"{WB_BASE}/country/all/indicator/{indicator}"
    params = {"format": "json", "per_page": 20000, "mrnev": 1}

    last_err = None
    for attempt in range(config.WB_RETRIES + 1):
        try:
            resp = requests.get(url, params=params, timeout=config.WB_TIMEOUT)
            resp.raise_for_status()
            payload = resp.json()
            records = payload[1] if isinstance(payload, list) and len(payload) > 1 else []
            with open(cache, "w", encoding="utf-8") as fh:
                json.dump(records, fh)
            return records
        except Exception as exc:  # noqa: BLE001 - we degrade gracefully on purpose
            last_err = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"World Bank fetch failed for {indicator}: {last_err}")


def fetch_all(progress=None) -> List[dict]:
    """
    Fetch every indicator in the registry for all countries.
    Returns a list of tidy row dicts. Raises if the network is unavailable so
    the caller can decide to fall back to demo data.
    """
    rows: List[dict] = []
    retrieval = dt.date.today().isoformat()
    codes = list(INDICATORS.keys())

    for i, code in enumerate(codes):
        if progress:
            progress(i / len(codes), f"Fetching {code}…")
        records = _fetch_indicator(code)
        for rec in records:
            iso3 = rec.get("countryiso3code") or ""
            value = rec.get("value")
            year = rec.get("date")
            if not iso3 or value is None:
                continue
            rows.append({
                "country_iso3": iso3,
                "indicator": code,
                "raw_value": float(value),
                "year": int(year) if year else None,
                "source": INDICATORS[code]["source"],
                "retrieval_date": retrieval,
                "confidence": config.CONF_MEASURED,
            })
    if progress:
        progress(1.0, "World Bank fetch complete.")
    return rows
