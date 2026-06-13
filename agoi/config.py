"""
AGOI configuration — single source of truth for weights, bands and thresholds.

Everything tunable lives here so that re-weighting or re-banding is a config
change, not a code change (see Technical Manual v2.0, Section 4.1).
"""

# ──────────────────────────────────────────────────────────────────────────────
# Six-pillar weights. Must sum to 1.0.
# ──────────────────────────────────────────────────────────────────────────────
PILLAR_WEIGHTS = {
    "sectoral":   0.25,   # Sectoral Green Opportunity
    "policy":     0.20,   # Policy & Institutional Readiness
    "finance":    0.20,   # Green Finance Ecosystem
    "bankability":0.15,   # Market-Tested Bankability
    "resilience": 0.10,   # Resilience & Natural Capital
    "inclusive":  0.10,   # Inclusive & Just Transition
}

PILLAR_LABELS = {
    "sectoral":    "Sectoral Green Opportunity",
    "policy":      "Policy & Institutional Readiness",
    "finance":     "Green Finance Ecosystem",
    "bankability": "Market-Tested Bankability",
    "resilience":  "Resilience & Natural Capital",
    "inclusive":   "Inclusive & Just Transition",
}

# ──────────────────────────────────────────────────────────────────────────────
# Opportunity bands. (lower_inclusive, upper_exclusive, label, hex colour)
# ──────────────────────────────────────────────────────────────────────────────
BANDS = [
    (80, 101, "Core Green Zone",     "#1B6B35"),
    (60,  80, "Growth Green Zone",   "#4CAF72"),
    (40,  60, "Emerging Green Zone", "#FFC000"),
    (20,  40, "High-Friction Zone",  "#E58A00"),
    (0,   20, "Red Zone",            "#C62828"),
]

BAND_READING = {
    "Core Green Zone":     "Bankable; ready for scaled deployment.",
    "Growth Green Zone":   "Strong fundamentals; near-term selective opportunity.",
    "Emerging Green Zone": "Real potential; needs structuring or de-risking.",
    "High-Friction Zone":  "High friction; concessional or blended capital required.",
    "Red Zone":            "Severe constraints; not currently investable at scale.",
}


def classify_band(score: float) -> str:
    for lo, hi, label, _ in BANDS:
        if lo <= score < hi:
            return label
    return "Red Zone"


def band_colour(label: str) -> str:
    for _, _, lbl, colour in BANDS:
        if lbl == label:
            return colour
    return "#999999"


# ──────────────────────────────────────────────────────────────────────────────
# Monitoring thresholds (Technical Manual v2.0, Section 6.4)
# ──────────────────────────────────────────────────────────────────────────────
ALERT_SCORE_DELTA_MEDIUM = 5.0     # points
ALERT_COVERAGE_DROP_MEDIUM = 10.0  # percentage points
ALERT_SCORE_DELTA_LOW = 2.0        # points

# ──────────────────────────────────────────────────────────────────────────────
# Winsorization percentiles for normalization
# ──────────────────────────────────────────────────────────────────────────────
WINSOR_LOWER = 0.05
WINSOR_UPPER = 0.95

# ──────────────────────────────────────────────────────────────────────────────
# Network behaviour
# ──────────────────────────────────────────────────────────────────────────────
WB_TIMEOUT = 20          # seconds per World Bank request
WB_RETRIES = 2

# ──────────────────────────────────────────────────────────────────────────────
# Confidence flags
# ──────────────────────────────────────────────────────────────────────────────
CONF_MEASURED     = "measured"
CONF_INTERPOLATED = "interpolated"
CONF_PROXY        = "proxy"
CONF_DEFAULT      = "default"

CONF_PENALTY = {
    CONF_MEASURED:     0.0,
    CONF_INTERPOLATED: 0.10,
    CONF_PROXY:        0.25,
    CONF_DEFAULT:      0.50,
}
