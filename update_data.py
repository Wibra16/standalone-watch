"""
update_data.py — refresh data/fundamentals.csv (share counts, EPS, book value)
for every stock in the simulator, so the live site loads them instantly.
Run it whenever you like (the daily GitHub Action can run it too):
    python update_data.py
"""
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

import config
from data import FUND_CSV, fetch_info

tickers = [t[0] for t in config.UNIVERSE]
with ThreadPoolExecutor(max_workers=8) as pool:
    rows = dict(zip(tickers, pool.map(fetch_info, tickers)))
pd.DataFrame.from_dict(rows, orient="index").to_csv(FUND_CSV)
print(f"Saved fundamentals for {len(rows)} stocks to {FUND_CSV}")
