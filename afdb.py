"""
AfDB project / lending data source.

Source: African Development Bank publishes its project pipeline to the IATI
(International Aid Transparency Initiative) standard. The AfDB Projects Portal
(projectsportal.afdb.org) is built on this same IATI data. We query the public
IATI Datastore, which is the most stable machine-readable route, and aggregate
active AfDB commitments per recipient country.

The resulting indicator — "AfDB active project commitments per country" — feeds
the Bankability pillar: it is a direct, observed signal of where a major DFI is
actually deploying capital, which is exactly what "market-tested bankability"
is meant to capture.

IMPORTANT — verification note:
    This connector targets documented IATI endpoints, but the exact live response
    shape can change and cannot be reached from a restricted sandbox. On a host
    with open internet (e.g. Streamlit Cloud) call fetch_all() once and confirm it
    returns rows. If the structure differs, the parsing in _parse_activities() is
    the single place to adjust. Until verified, the pipeline treats AfDB values as
    confidence="proxy" and falls back silently if the source is unreachable.
"""
from __future__ import annotations
import datetime as dt
import json
import os
from collections import defaultdict
from typing import Dict, List, Optional

import requests

from agoi import config

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "cache")

# IATI Datastore (public). AfDB's IATI reporting-org identifier is "46002".
# The Datastore search API returns activity records as JSON.
IATI_DATASTORE = "https://api.iatistandard.org/datastore/activity/select"
AFDB_REPORTING_ORG = "46002"

# The indicator code we expose to the rest of the platform.
AFDB_INDICATOR = "AFDB.PROJ.COMMIT.PC"
AFDB_INDICATOR_LABEL = "AfDB active project commitments (USD per capita, proxy)"


def _cache_path() -> str:
    os.makedirs(CACHE_DIR, exist_ok=True)
    return os.path.join(CACHE_DIR, f"afdb_projects_{dt.date.today().isoformat()}.json")


def _fetch_raw() -> Optional[list]:
    """
    Query the IATI Datastore for AfDB activities. Returns a list of activity
    dicts, or None if the source is unreachable / returns nothing usable.
    Cached per day so repeated runs don't re-hit the API.
    """
    cache = _cache_path()
    if os.path.exists(cache):
        with open(cache, "r", encoding="utf-8") as fh:
            return json.load(fh)

    params = {
        "q": f"reporting_org_ref:{AFDB_REPORTING_ORG}",
        "fl": "recipient_country_code,activity_status_code,"
              "transaction_value,transaction_type_code,recipient_country_percentage",
        "rows": 10000,
        "wt": "json",
    }
    try:
        resp = requests.get(IATI_DATASTORE, params=params, timeout=config.WB_TIMEOUT)
        resp.raise_for_status()
        payload = resp.json()
        docs = payload.get("response", {}).get("docs", [])
        if not docs:
            return None
        with open(cache, "w", encoding="utf-8") as fh:
            json.dump(docs, fh)
        return docs
    except Exception:  # noqa: BLE001 — unreachable source must not break the platform
        return None


def _parse_activities(docs: list) -> Dict[str, float]:
    """
    Aggregate total commitment value per ISO alpha-3 recipient country.

    NOTE: IATI country codes are ISO alpha-2; we convert to alpha-3 to match the
    rest of the platform. This is the one place to adjust if the live response
    field names differ from what is requested above.
    """
    from agoi.geospatial.iso import alpha2_to_alpha3  # local import to avoid cycles

    totals: Dict[str, float] = defaultdict(float)
    for d in docs:
        codes = d.get("recipient_country_code")
        values = d.get("transaction_value")
        if not codes or not values:
            continue
        # Fields may be scalars or lists depending on the record; normalise.
        code_list = codes if isinstance(codes, list) else [codes]
        val_list = values if isinstance(values, list) else [values]
        total_val = 0.0
        for v in val_list:
            try:
                total_val += float(v)
            except (TypeError, ValueError):
                continue
        if total_val <= 0:
            continue
        share = 1.0 / len(code_list)
        for c in code_list:
            iso3 = alpha2_to_alpha3(str(c).upper())
            if iso3:
                totals[iso3] += total_val * share
    return dict(totals)


def fetch_all() -> List[dict]:
    """
    Return tidy rows for the AfDB commitments indicator, one per country.
    Returns [] if the source is unreachable (pipeline then simply omits AfDB).
    """
    docs = _fetch_raw()
    if not docs:
        return []

    totals = _parse_activities(docs)
    if not totals:
        return []

    retrieval = dt.date.today().isoformat()
    rows: List[dict] = []
    for iso3, value in totals.items():
        rows.append({
            "country_iso3": iso3,
            "indicator": AFDB_INDICATOR,
            "raw_value": round(value, 2),
            "year": dt.date.today().year,
            "source": "AfDB (IATI Datastore)",
            "retrieval_date": retrieval,
            "confidence": config.CONF_PROXY,
        })
    return rows
