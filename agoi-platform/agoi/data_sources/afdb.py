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


# Module-level note explaining the last fetch outcome (surfaced in the UI).
LAST_STATUS = "not run"


def _get_api_key() -> Optional[str]:
    """
    The IATI Datastore is an Azure-APIM gated service and requires a free
    subscription key (header: Ocp-Apim-Subscription-Key). We read it from:
      1. Streamlit secrets  -> st.secrets["IATI_API_KEY"]
      2. environment        -> IATI_API_KEY
    Returns None if no key is configured.
    """
    # Environment first (works everywhere, incl. local + GitHub Actions).
    key = os.environ.get("IATI_API_KEY")
    if key:
        return key.strip()
    # Streamlit secrets (only available inside a Streamlit runtime).
    try:
        import streamlit as st  # local import; not a hard dependency of this module
        if "IATI_API_KEY" in st.secrets:
            return str(st.secrets["IATI_API_KEY"]).strip()
    except Exception:  # noqa: BLE001
        pass
    return None


def _fetch_raw() -> Optional[list]:
    """
    Query the IATI Datastore v3 for AfDB activities. Returns a list of activity
    dicts, or None if unavailable. Sets LAST_STATUS with the reason so the UI
    can explain *why* AfDB data is or isn't showing.
    Cached per day so repeated runs don't re-hit the API.
    """
    global LAST_STATUS

    cache = _cache_path()
    if os.path.exists(cache):
        with open(cache, "r", encoding="utf-8") as fh:
            LAST_STATUS = "loaded from today's cache"
            return json.load(fh)

    api_key = _get_api_key()
    if not api_key:
        LAST_STATUS = ("no IATI_API_KEY configured — add a free key from "
                       "developer.iatistandard.org to enable live AfDB data")
        return None

    # Datastore v3 query syntax: q is mandatory; fl selects fields; wt=json.
    params = {
        "q": f"reporting_org_ref:{AFDB_REPORTING_ORG}",
        "fl": "recipient_country_code,activity_status_code,transaction_value",
        "rows": 10000,
        "wt": "json",
    }
    headers = {"Ocp-Apim-Subscription-Key": api_key}
    try:
        resp = requests.get(IATI_DATASTORE, params=params, headers=headers,
                            timeout=config.WB_TIMEOUT)
        if resp.status_code in (401, 403):
            LAST_STATUS = f"IATI key rejected (HTTP {resp.status_code}) — check the key/subscription"
            return None
        resp.raise_for_status()
        payload = resp.json()
        docs = payload.get("response", {}).get("docs", [])
        if not docs:
            LAST_STATUS = "IATI returned no AfDB activities for this query"
            return None
        with open(cache, "w", encoding="utf-8") as fh:
            json.dump(docs, fh)
        LAST_STATUS = f"live: {len(docs)} AfDB activities fetched"
        return docs
    except Exception as exc:  # noqa: BLE001 — unreachable source must not break the platform
        LAST_STATUS = f"IATI request failed ({type(exc).__name__})"
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
