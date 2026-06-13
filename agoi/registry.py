"""
Country and indicator registry.

The single most important fix from the prototype: every country is keyed on its
ISO 3166-1 alpha-3 code. The World Bank API returns `countryiso3code` on every
record, so keying on alpha-3 means live data joins correctly instead of silently
falling back to defaults (see Technical Manual v1.0, Section 3.2.1).
"""

# ──────────────────────────────────────────────────────────────────────────────
# 54 African countries, keyed by ISO alpha-3.
# ──────────────────────────────────────────────────────────────────────────────
AFRICAN_COUNTRIES = {
    "DZA": "Algeria",          "AGO": "Angola",         "BEN": "Benin",
    "BWA": "Botswana",         "BFA": "Burkina Faso",   "BDI": "Burundi",
    "CPV": "Cabo Verde",       "CMR": "Cameroon",       "CAF": "Central African Republic",
    "TCD": "Chad",             "COM": "Comoros",        "COG": "Congo, Rep.",
    "COD": "Congo, Dem. Rep.", "CIV": "Côte d'Ivoire",  "DJI": "Djibouti",
    "EGY": "Egypt",            "GNQ": "Equatorial Guinea", "ERI": "Eritrea",
    "SWZ": "Eswatini",         "ETH": "Ethiopia",       "GAB": "Gabon",
    "GMB": "Gambia",           "GHA": "Ghana",          "GIN": "Guinea",
    "GNB": "Guinea-Bissau",    "KEN": "Kenya",          "LSO": "Lesotho",
    "LBR": "Liberia",          "LBY": "Libya",          "MDG": "Madagascar",
    "MWI": "Malawi",           "MLI": "Mali",           "MRT": "Mauritania",
    "MUS": "Mauritius",        "MAR": "Morocco",        "MOZ": "Mozambique",
    "NAM": "Namibia",          "NER": "Niger",          "NGA": "Nigeria",
    "RWA": "Rwanda",           "STP": "São Tomé and Príncipe", "SEN": "Senegal",
    "SYC": "Seychelles",       "SLE": "Sierra Leone",   "SOM": "Somalia",
    "ZAF": "South Africa",     "SSD": "South Sudan",    "SDN": "Sudan",
    "TZA": "Tanzania",         "TGO": "Togo",           "TUN": "Tunisia",
    "UGA": "Uganda",           "ZMB": "Zambia",         "ZWE": "Zimbabwe",
}

# ──────────────────────────────────────────────────────────────────────────────
# Indicator registry. Each entry:
#   code      — World Bank indicator code
#   pillar    — which pillar it feeds
#   direction — "higher" (higher is better) or "lower" (lower is better)
#   source    — human-readable source label
# Codes marked verify in the manual are the governance ones; we use the
# documented WB codes here and fall back gracefully if a series is empty.
# ──────────────────────────────────────────────────────────────────────────────
INDICATORS = {
    # Sectoral Green Opportunity
    "EG.ELC.RNEW.ZS": {"pillar": "sectoral", "direction": "higher",
                       "source": "World Bank WDI", "label": "Renewable electricity output (% of total)"},
    "EG.FEC.RNEW.ZS": {"pillar": "sectoral", "direction": "higher",
                       "source": "World Bank WDI", "label": "Renewable energy consumption (% of final energy)"},

    # Policy & Institutional Readiness
    "RL.EST":          {"pillar": "policy", "direction": "higher",
                        "source": "World Bank WGI", "label": "Rule of law estimate"},
    "RQ.EST":          {"pillar": "policy", "direction": "higher",
                        "source": "World Bank WGI", "label": "Regulatory quality estimate"},

    # Green Finance Ecosystem
    "FS.AST.PRVT.GD.ZS": {"pillar": "finance", "direction": "higher",
                          "source": "World Bank WDI", "label": "Domestic credit to private sector (% GDP)"},
    "FX.OWN.TOTL.ZS":    {"pillar": "finance", "direction": "higher",
                          "source": "World Bank Global Findex", "label": "Account ownership (% age 15+)"},

    # Market-Tested Bankability
    "BX.KLT.DINV.WD.GD.ZS": {"pillar": "bankability", "direction": "higher",
                             "source": "World Bank WDI", "label": "FDI net inflows (% GDP)"},

    # Resilience & Natural Capital
    "AG.LND.FRST.ZS": {"pillar": "resilience", "direction": "higher",
                       "source": "World Bank WDI", "label": "Forest area (% of land area)"},
    "ER.H2O.INTR.PC": {"pillar": "resilience", "direction": "higher",
                       "source": "World Bank WDI", "label": "Renewable internal freshwater per capita"},

    # Inclusive & Just Transition
    "SL.UEM.1524.ZS":      {"pillar": "inclusive", "direction": "lower",
                            "source": "World Bank WDI", "label": "Youth unemployment (% ages 15-24)"},
    "SL.TLF.CACT.FE.ZS":   {"pillar": "inclusive", "direction": "higher",
                            "source": "World Bank WDI", "label": "Female labour force participation (%)"},
}


def indicators_for_pillar(pillar: str):
    return {code: meta for code, meta in INDICATORS.items() if meta["pillar"] == pillar}
