"""
AGOI–AfCFTA Module — configuration.

Six country-level AfCFTA indicators, five policy levers, and the Lagos–Abidjan
corridor definition (the vertical slice).

Design principle carried from the core platform: nothing is asserted without
provenance. Every elasticity in elasticity.py carries a source and an
uncertainty range, and the simulator reports ranges rather than false-precision
point estimates.
"""

# ──────────────────────────────────────────────────────────────────────────────
# 1. AfCFTA country-level indicators
# ──────────────────────────────────────────────────────────────────────────────
AFCFTA_INDICATORS = {
    "GEX":   {"label": "Green Exports Share",              "unit": "% of merchandise exports",
              "direction": "higher"},
    "DIV":   {"label": "Export Diversification Index",     "unit": "0–100 (higher = more diversified)",
              "direction": "higher"},
    "GJOB":  {"label": "Green Jobs",                       "unit": "% of total employment",
              "direction": "higher"},
    "CIRC":  {"label": "Circular Economy Adoption",        "unit": "0–100 index",
              "direction": "higher"},
    "LCMAN": {"label": "Low-Carbon Manufacturing Share",   "unit": "% of manufacturing value added",
              "direction": "higher"},
    "GLCOR": {"label": "Green Logistics Corridor Score",   "unit": "0–100 index",
              "direction": "higher"},
}

# ──────────────────────────────────────────────────────────────────────────────
# 2. AfCFTA policy levers (simulation inputs). Each runs 0.0 → 1.0,
#    interpreted as "degree of policy adoption / implementation intensity".
# ──────────────────────────────────────────────────────────────────────────────
AFCFTA_LEVERS = {
    "A1": {"label": "Green Standards Adoption",
           "desc": "Harmonised green product & process standards across AfCFTA members."},
    "A2": {"label": "Green Investment Incentives",
           "desc": "Tax, tariff and concessional-finance incentives for green sectors."},
    "A3": {"label": "Logistics Corridor Upgrade",
           "desc": "Physical and digital upgrade of trade corridors (roads, ports, customs)."},
    "A4": {"label": "Climate-Smart Agriculture Protocols",
           "desc": "CSA standards embedded in agricultural trade protocols."},
    "A5": {"label": "Circular Economy Compliance",
           "desc": "Mandatory circularity / recyclability compliance for traded goods."},
}

# ──────────────────────────────────────────────────────────────────────────────
# 3. Vertical slice: the Lagos–Abidjan corridor (ECOWAS coastal corridor).
#    Node order runs west→east along the corridor.
# ──────────────────────────────────────────────────────────────────────────────
CORRIDOR_LAGOS_ABIDJAN = {
    "corridor_id": "ECO-LGS-ABJ",
    "name": "Lagos–Abidjan Corridor",
    "region": "ECOWAS",
    "nodes": [
        # node_id, city, country, type, flood_risk(0-100), logistics_capacity(0-100),
        # afcfta_implementation(0-100)
        {"node_id": "ABJ", "city": "Abidjan",  "country_iso3": "CIV", "node_type": "port",
         "flood_risk": 42, "logistics_capacity": 68, "afcfta_implementation": 55},
        {"node_id": "ACC", "city": "Accra",    "country_iso3": "GHA", "node_type": "port",
         "flood_risk": 38, "logistics_capacity": 64, "afcfta_implementation": 60},
        {"node_id": "LOM", "city": "Lomé",     "country_iso3": "TGO", "node_type": "port",
         "flood_risk": 45, "logistics_capacity": 58, "afcfta_implementation": 48},
        {"node_id": "COO", "city": "Cotonou",  "country_iso3": "BEN", "node_type": "port",
         "flood_risk": 52, "logistics_capacity": 51, "afcfta_implementation": 45},
        {"node_id": "LOS", "city": "Lagos",    "country_iso3": "NGA", "node_type": "port_hub",
         "flood_risk": 71, "logistics_capacity": 62, "afcfta_implementation": 52},
    ],
    # Baseline corridor-level metrics (see PROVENANCE note in elasticity.py)
    "baseline_metrics": {
        "transit_time":   4.8,    # days, Lagos→Abidjan freight
        "logistics_cost": 2450.0, # USD per TEU
        "climate_risk":   58.0,   # 0–100 composite
        "green_score":    41.0,   # GLCOR, 0–100
        "trade_volume":   100.0,  # index, baseline = 100
    },
}

CORRIDORS = {CORRIDOR_LAGOS_ABIDJAN["corridor_id"]: CORRIDOR_LAGOS_ABIDJAN}

# ──────────────────────────────────────────────────────────────────────────────
# 4. Lagos City Lab — trade-risk indicators (flood → trade linkage)
# ──────────────────────────────────────────────────────────────────────────────
LAGOS_TRADE_RISK = {
    "LAG_T1": {"label": "Port Flood Disruption Days",        "unit": "days/year",  "baseline": 17.0,
               "direction": "lower"},
    "LAG_T2": {"label": "Logistics Delay from Flooding",     "unit": "hours/event","baseline": 34.0,
               "direction": "lower"},
    "LAG_T3": {"label": "Flood Impact on Export Volumes",    "unit": "% reduction","baseline": 8.5,
               "direction": "lower"},
    "LAG_T4": {"label": "Flood Impact on Import Clearance",  "unit": "% delay",    "baseline": 12.0,
               "direction": "lower"},
}

# Lagos resilience lever (RES_lagos): 0–1, drainage/flood-defence investment level.
LAGOS_RESILIENCE_LEVER = {
    "key": "RES_LAGOS",
    "label": "Lagos Flood Resilience Investment",
    "desc": "Drainage upgrade, flood defence and port climate-proofing intensity.",
}

# The four ECOWAS slice countries scored in the vertical slice.
SLICE_COUNTRIES = ["NGA", "GHA", "CIV", "BEN", "TGO"]
