"""
data.py — download prices from Yahoo Finance (yfinance), cache them, and
save a copy to data/ so we don't re-download on every click.
"""
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import streamlit as st
import yfinance as yf

import config

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# yfinance is not thread-safe: two pages downloading at once can get each
# other's data mixed in. One download at a time avoids that.
_YF_LOCK = threading.Lock()


@st.cache_data(ttl=60 * 60, show_spinner=False)  # refresh at most hourly
def load_prices(ticker, start="2026-01-01"):
    """Daily OHLCV for one ticker. Falls back to the saved CSV if Yahoo fails.
    Returns an empty DataFrame if nothing is available (never fake data)."""
    path = DATA_DIR / f"{ticker.replace('^', '').replace('=', '_')}.csv"
    try:
        with _YF_LOCK:
            df = yf.download(ticker, start=start, progress=False, auto_adjust=False, threads=False)
        if isinstance(df.columns, pd.MultiIndex):  # (field, ticker) columns: keep only ours
            if ticker in df.columns.get_level_values(1):
                df = df.xs(ticker, axis=1, level=1)
            else:
                df.columns = df.columns.get_level_values(0)
        df = df.loc[:, ~df.columns.duplicated()]
        if not df.empty and "Close" in df:
            df.to_csv(path)
            return df
    except Exception:
        pass
    if path.exists():
        return pd.read_csv(path, index_col=0, parse_dates=True)
    return pd.DataFrame()


@st.cache_data(ttl=60 * 60, show_spinner=False)
def load_many(tickers, start="2026-01-01"):
    """Daily OHLCV for many tickers in ONE request (much faster than one each).
    Returns {ticker: DataFrame}; a ticker Yahoo didn't return falls back to
    load_prices (saved CSV), and is empty if nothing is available."""
    tickers = list(tickers)
    out = {}
    try:
        with _YF_LOCK:
            raw = yf.download(tickers, start=start, progress=False, auto_adjust=False,
                              group_by="ticker", threads=True)
        for t in tickers:
            if isinstance(raw.columns, pd.MultiIndex) and t in raw.columns.get_level_values(0):
                df = raw[t].dropna(how="all")
                if not df.empty and "Close" in df:
                    df.to_csv(DATA_DIR / f"{t.replace('^', '').replace('=', '_')}.csv")
                    out[t] = df
    except Exception:
        pass
    for t in tickers:          # anything missing: single download / saved copy
        if t not in out:
            out[t] = load_prices(t, start)
    return out


def change_since(df, date=config.ANNOUNCEMENT_DATE):
    """% change from the close on `date` (or the last close before it) to today."""
    if df.empty:
        return None
    before = df.loc[:date, "Close"]
    if before.empty:
        return None
    return (df["Close"].iloc[-1] / before.iloc[-1] - 1) * 100


def avg_daily_traded_value_usd(df, fx_df, window=config.ADV_WINDOW):
    """Average of (close x volume) over the last `window` days, converted
    from rupiah to US dollars at the latest IDR/USD rate."""
    if df.empty or fx_df.empty:
        return None
    traded_idr = (df["Close"] * df["Volume"]).tail(window).mean()
    return traded_idr / fx_df["Close"].iloc[-1]


FUND_KEYS = ["sharesOutstanding", "impliedSharesOutstanding", "heldPercentInsiders",
             "trailingEps", "bookValue", "financialCurrency"]
FUND_CSV = DATA_DIR / "fundamentals.csv"


def fetch_info(ticker):
    """Live fundamentals for one ticker from yfinance (slow: ~0.3s each)."""
    try:
        info = yf.Ticker(ticker).info
        return {k: info.get(k) for k in FUND_KEYS}
    except Exception:
        return {k: None for k in FUND_KEYS}


@st.cache_data(ttl=24 * 60 * 60, show_spinner=False)  # fundamentals change slowly
def load_fundamentals(tickers):
    """Share counts, EPS and book value for many tickers.
    Reads the snapshot in data/fundamentals.csv (instant; refreshed by
    update_data.py), and fetches only missing tickers live, in parallel."""
    snap = {}
    if FUND_CSV.exists():
        df = pd.read_csv(FUND_CSV, index_col=0)
        snap = {t: {k: (None if pd.isna(v) else v) for k, v in row.items()} for t, row in df.iterrows()}
    missing = [t for t in tickers if t not in snap]
    if missing:
        with ThreadPoolExecutor(max_workers=8) as pool:
            for t, info in zip(missing, pool.map(fetch_info, missing)):
                snap[t] = info
    return {t: snap[t] for t in tickers}


def load_info(ticker):
    """Fundamentals for one ticker (served from the shared snapshot above)."""
    universe = tuple(t[0] for t in config.UNIVERSE)
    if ticker in universe:
        return load_fundamentals(universe)[ticker]
    return load_fundamentals((ticker,))[ticker]


def valuation(info, price_idr, usd_idr):
    """P/E and P/B computed ourselves. For companies that report in USD
    (BREN, AMMN, BYAN...), yfinance gives book value in USD but price in
    rupiah, so its own P/B comes out in the hundreds of thousands.
    (EPS is already in rupiah, so only book value needs converting.)"""
    fx = usd_idr if info.get("financialCurrency") == "USD" else 1
    eps, book = info.get("trailingEps"), info.get("bookValue")
    pe = price_idr / eps if eps and eps > 0 else None   # no P/E when loss-making
    pb = price_idr / (book * fx) if book and book > 0 else None
    return pe, pb


def free_float_weights(universe, prices, coverage, eligible=None):
    """Approximate each stock's weight in MSCI Indonesia.

    free-float market cap = shares x (1 - % held by insiders) x latest price
    (We take the larger of yfinance's two share counts: one of them is
    occasionally wrong by ~100x, e.g. BBNI.)
    weight = stock's share of the universe's free-float cap x coverage
    Stocks not in `eligible` (failed the liquidity screen) get weight 0.
    Returns {ticker: weight}, or None for stocks we can't price.
    """
    caps = {}
    for ticker, *_ in universe:
        if eligible is not None and ticker not in eligible:
            caps[ticker] = 0
            continue
        info = load_info(ticker)
        df = prices[ticker]
        shares = max(info["sharesOutstanding"] or 0, info["impliedSharesOutstanding"] or 0)
        free_float = 1 - (info["heldPercentInsiders"] or 0)
        caps[ticker] = shares * free_float * df["Close"].iloc[-1] if shares and not df.empty else None
    total = sum(c for c in caps.values() if c)
    return {t: (c / total * coverage if c is not None else None) for t, c in caps.items()}


def event_window(close, day0, before=60, after=250):
    """Line a price series up around an event: index = trading days from
    `day0` (0 = last close on or before the event), values rebased so day 0 = 100.
    Only uses data that exists, so for a recent event the line simply stops today."""
    close = close.dropna()
    pos = close.index.searchsorted(pd.Timestamp(day0), side="right") - 1
    if pos < 0:
        return pd.Series(dtype=float)
    window = close.iloc[max(0, pos - before): pos + after + 1]
    out = window / close.iloc[pos] * 100
    out.index = range(max(0, pos - before) - pos, max(0, pos - before) - pos + len(out))
    return out


class _Incomplete(Exception):
    """Raised so st.cache_data does not keep a partial download."""
    def __init__(self, rows):
        self.rows = rows


def last_closes(codes):
    """Latest close and day % change for a list of IDX codes.
    Returns [(code, close, pct_change), ...] in the order given; skips failures.
    A partial result (e.g. Yahoo rate-limiting) is shown but not cached, so the
    next visit tries again instead of keeping gaps for six hours."""
    try:
        return _last_closes_cached(codes)
    except _Incomplete as e:
        return e.rows


@st.cache_data(ttl=6 * 60 * 60, show_spinner=False)  # closing prices only change once a day
def _last_closes_cached(codes):
    tickers = [c + ".JK" for c in codes]
    try:
        # One request for all 75 (threaded inside yfinance). The lock stops two
        # pages downloading at once, which is what used to mix up / hang data;
        # the timeout keeps a slow Yahoo from freezing the home page.
        with _YF_LOCK:
            df = yf.download(tickers, period="10d", progress=False, auto_adjust=False,
                             threads=True, timeout=10)["Close"]
    except Exception:
        raise _Incomplete([])
    out = []
    for code, t in zip(codes, tickers):
        s = df[t].dropna() if t in df else pd.Series(dtype=float)
        if len(s) >= 2:
            out.append((code, float(s.iloc[-1]), float(s.iloc[-1] / s.iloc[-2] * 100 - 100)))
    if len(out) < 0.9 * len(codes):
        raise _Incomplete(out)
    return out
