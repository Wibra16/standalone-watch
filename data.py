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
