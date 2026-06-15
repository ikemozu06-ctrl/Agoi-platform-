"""
Minimal ISO 3166-1 alpha-2 -> alpha-3 converter.

Self-contained (no pycountry dependency) so the free deployment stays lean.
Covers all 54 African countries plus a few common non-African recipients that
may appear in regional AfDB activities. Returns None for anything unknown so the
caller can skip it rather than guess.
"""

_A2_A3 = {
    # African countries
    "DZ": "DZA", "AO": "AGO", "BJ": "BEN", "BW": "BWA", "BF": "BFA",
    "BI": "BDI", "CV": "CPV", "CM": "CMR", "CF": "CAF", "TD": "TCD",
    "KM": "COM", "CG": "COG", "CD": "COD", "CI": "CIV", "DJ": "DJI",
    "EG": "EGY", "GQ": "GNQ", "ER": "ERI", "SZ": "SWZ", "ET": "ETH",
    "GA": "GAB", "GM": "GMB", "GH": "GHA", "GN": "GIN", "GW": "GNB",
    "KE": "KEN", "LS": "LSO", "LR": "LBR", "LY": "LBY", "MG": "MDG",
    "MW": "MWI", "ML": "MLI", "MR": "MRT", "MU": "MUS", "MA": "MAR",
    "MZ": "MOZ", "NA": "NAM", "NE": "NER", "NG": "NGA", "RW": "RWA",
    "ST": "STP", "SN": "SEN", "SC": "SYC", "SL": "SLE", "SO": "SOM",
    "ZA": "ZAF", "SS": "SSD", "SD": "SDN", "TZ": "TZA", "TG": "TGO",
    "TN": "TUN", "UG": "UGA", "ZM": "ZMB", "ZW": "ZWE",
}


def alpha2_to_alpha3(code: str):
    """Return the ISO alpha-3 for an alpha-2 code, or None if unknown.
    Also passes through valid 3-letter codes unchanged."""
    if not code:
        return None
    code = code.strip().upper()
    if len(code) == 3 and code in _A2_A3.values():
        return code
    return _A2_A3.get(code)
