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
# ---------------------------------------------------------------------------
UNIVERSE = [
    # Top 20 IDX stocks by total market cap (yfinance, 18 Oct 2026),
    # plus three digital-finance names as the fintech focus.
    # ticker,    name,                        sector,        fintech
    ("BBCA.JK", "Bank Central Asia",          "Bank",        False),
    ("DCII.JK", "DCI Indonesia",              "Data centres", False),
    ("BBRI.JK", "Bank Rakyat Indonesia",      "Bank",        False),
    ("BYAN.JK", "Bayan Resources",            "Coal",        False),
    ("BMRI.JK", "Bank Mandiri",               "Bank",        False),
    ("AMMN.JK", "Amman Mineral",              "Mining",      False),
    ("BREN.JK", "Barito Renewables",          "Energy",      False),
    ("TLKM.JK", "Telkom Indonesia",           "Telecom",     False),
    ("ASII.JK", "Astra International",        "Conglom.",    False),
    ("BRPT.JK", "Barito Pacific",             "Conglom.",    False),
    ("DSSA.JK", "Dian Swastatika Sentosa",    "Energy",      False),
    ("BBNI.JK", "Bank Negara Indonesia",      "Bank",        False),
    ("TPIA.JK", "Chandra Asri Pacific",       "Chemicals",   False),
    ("CASA.JK", "Capital Financial Indonesia", "Financials", False),
    ("UNTR.JK", "United Tractors",            "Industrial",  False),
    ("PANI.JK", "Pantai Indah Kapuk Dua",     "Property",    False),
    ("AADI.JK", "Adaro Andalan Indonesia",    "Coal",        False),
    ("ICBP.JK", "Indofood CBP",               "Consumer",    False),
    ("HMSP.JK", "HM Sampoerna",               "Consumer",    False),
    ("ADRO.JK", "Alamtri Resources",          "Mining",      False),
    # fintech / digital focus
    ("GOTO.JK", "GoTo Gojek Tokopedia",       "Fintech",     True),
    ("ARTO.JK", "Bank Jago",                  "Fintech",     True),
    ("BBHI.JK", "Allo Bank",                  "Fintech",     True),
]

# ASSUMPTION: our stocks make up roughly this share of the MSCI Indonesia
# index. Each stock's index weight = its share of our universe's free-float
# market cap x this number. (iShares blocks free download of EIDO holdings.)
UNIVERSE_COVERAGE = 0.85

# ASSUMPTION: a stock trading less than this per day (USD) is treated as
# outside the MSCI index (MSCI screens out very illiquid names), so index
# funds aren't forced to sell it. Its weight is set to 0.
MIN_ADV_USD = 100_000

# "Mechanically oversold" flag: more days of forced selling than the median
# stock in our universe AND a lower price-to-book than the median.

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
GREY = "#5E5E5E"   # muted white for labels
RULE = "#1A1A1A"   # hairline dividers
RED = "#E10600"
FONT = "'SF Mono', SFMono-Regular, ui-monospace, Menlo, monospace"

# ---------------------------------------------------------------------------
# News feed (Google News RSS, free, no key)
# ---------------------------------------------------------------------------
NEWS_QUERIES = [
    # query,                              language
    ("MSCI Indonesia",                     "en"),
    ("Indonesia standalone market MSCI",   "en"),
    ("OJK reform stock market",            "en"),
    ("Jakarta Composite Index",            "en"),
    ("rupiah",                             "en"),
    ("MSCI IHSG",                          "id"),
    ("OJK bursa efek reformasi",           "id"),
]
NEWS_START = "2026-10-01"  # ignore older articles
NEWS_TAGS = {  # tag: keywords (lowercase) that trigger it
    "MSCI": ["msci", "standalone", "frontier", "reclassif", "index provider"],
    "Regulator": ["ojk", "idx", "bursa efek", "regulator", " bei "],
    "Market": ["jci", "ihsg", "composite", "stocks", "saham", "halt", "plunge", "rally", "sell-off"],
    "Rupiah": ["rupiah", "bank indonesia", "currency"],
    "Fintech": ["goto", "gojek", "tokopedia", "bank jago", "allo bank", "fintech", "digital bank"],
}
