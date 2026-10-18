"""
data.py — download prices from Yahoo Finance (yfinance), cache them, and
save a copy to data/ so we don't re-download on every click.
"""
from pathlib import Path

import pandas as pd
import streamlit as st
import yfinance as yf

import config

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)


@st.cache_data(ttl=60 * 60, show_spinner=False)  # refresh at most hourly
def load_prices(ticker, start="2026-01-01"):
    """Daily OHLCV for one ticker. Falls back to the saved CSV if Yahoo fails.
    Returns an empty DataFrame if nothing is available (never fake data)."""
    path = DATA_DIR / f"{ticker.replace('^', '').replace('=', '_')}.csv"
    try:
        df = yf.download(ticker, start=start, progress=False, auto_adjust=False)
        if isinstance(df.columns, pd.MultiIndex):  # yfinance returns 2-level columns
            df.columns = df.columns.get_level_values(0)
        if not df.empty:
            df.to_csv(path)
            return df
    except Exception:
        pass
    if path.exists():
        return pd.read_csv(path, index_col=0, parse_dates=True)
    return pd.DataFrame()


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


@st.cache_data(ttl=24 * 60 * 60, show_spinner=False)  # fundamentals change slowly
def load_info(ticker):
    """Float shares, P/E and P/B from yfinance. Missing values come back as None."""
    keys = ["sharesOutstanding", "impliedSharesOutstanding", "heldPercentInsiders",
            "trailingEps", "bookValue", "financialCurrency"]
    try:
        info = yf.Ticker(ticker).info
        return {k: info.get(k) for k in keys}
    except Exception:
        return {k: None for k in keys}


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
