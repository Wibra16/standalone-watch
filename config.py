"""
config.py — every number or date you might want to change lives here.
Edit this file (not the app code) when MSCI publishes the exact decision date
or when you want to tweak defaults.
"""
from datetime import datetime, timezone, timedelta

# ---------------------------------------------------------------------------
# Key dates
# ---------------------------------------------------------------------------
WIB = timezone(timedelta(hours=7))  # Jakarta time (UTC+7)

ANNOUNCEMENT_DATE = "2026-10-15"  # MSCI proposes Standalone reclassification
CRASH_DATE = "2026-10-16"         # JCI's worst day since 1998

# MSCI only said "by end of June 2027". Update this the moment MSCI publishes
# the exact date, and flip DECISION_CONFIRMED to True.
DECISION_DATE = datetime(2027, 6, 30, 23, 59, tzinfo=WIB)
DECISION_CONFIRMED = False

CONSULTATION_CLOSE = datetime(2027, 4, 30, 23, 59, tzinfo=WIB)

# ---------------------------------------------------------------------------
# Stock universe. Add a row to add a stock.
# weight = ILLUSTRATIVE share of Indonesia's MSCI index weight (Phase 1 only).
#          Rough guesses, NOT official MSCI weights. Phase 2 replaces them.
# ---------------------------------------------------------------------------
UNIVERSE = [
    # ticker,    name,                   sector,      fintech, weight
    ("BBCA.JK", "Bank Central Asia",     "Bank",      False,   0.22),
    ("BBRI.JK", "Bank Rakyat Indonesia", "Bank",      False,   0.15),
    ("BMRI.JK", "Bank Mandiri",          "Bank",      False,   0.11),
    ("BBNI.JK", "Bank Negara Indonesia", "Bank",      False,   0.04),
    ("TLKM.JK", "Telkom Indonesia",      "Telecom",   False,   0.07),
    ("ASII.JK", "Astra International",   "Conglom.",  False,   0.06),
    ("GOTO.JK", "GoTo Gojek Tokopedia",  "Fintech",   True,    0.03),
    ("ARTO.JK", "Bank Jago",             "Fintech",   True,    0.01),
    ("BBHI.JK", "Allo Bank",             "Fintech",   True,    0.005),
]

INDEX_TICKER = "^JKSE"   # Jakarta Composite Index
FX_TICKER = "IDR=X"      # rupiah per 1 USD
ETF_TICKER = "EIDO"      # iShares MSCI Indonesia ETF

# ---------------------------------------------------------------------------
# Scenarios: what fraction of the passive "sell" happens in each outcome.
# ASSUMPTIONS — Frontier is < 1 because some Frontier-index trackers would buy.
# ---------------------------------------------------------------------------
SCENARIOS = {
    "Stay EM": 0.0,
    "Frontier": 0.85,
    "Standalone": 1.0,
}

# ---------------------------------------------------------------------------
# Slider defaults (all illustrative, all editable in the sidebar)
# ---------------------------------------------------------------------------
DEFAULTS = {
    "probability": 50,          # % chance MSCI confirms the downgrade
    "passive_aum_bn": 500,      # $bn passively tracking MSCI EM (rough estimate)
    "indonesia_weight": 1.5,    # % of MSCI EM that is Indonesia (rough)
    "pct_sell": 100,            # % of passive holders that actually sell
    "days_to_exit": 20,         # trading days sellers spread the exit over
    "participation": 20,        # % of daily volume sellers can be without crushing price
}
ADV_WINDOW = 20  # days used for average daily traded value

# ---------------------------------------------------------------------------
# Design tokens: black / white / red only
# ---------------------------------------------------------------------------
BLACK = "#000000"
WHITE = "#F5F5F5"
GREY = "#6B6B6B"   # muted white for labels and rules
RED = "#E10600"
