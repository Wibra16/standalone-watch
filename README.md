# Standalone Watch

Interactive simulator of MSCI's proposed reclassification of Indonesia from Emerging to **Standalone** market status (proposed 15 Oct 2026).

> Illustrative estimates — not investment advice.

## Run locally
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Structure
- `app.py` — sets up the four top tabs
- `views/home.py` — full-screen countdown to MSCI's decision
- `views/updates.py` — daily news feed (Google News RSS)
- `views/simulator.py` — forced-selling model for Indonesia
- `views/argentina.py` — case study of Argentina's 2021 move to Standalone
- `config.py` — dates, tickers, defaults, colors
- `model.py` — outflow math (no UI)
- `data.py` — yfinance downloads, caching, weights, valuation, event windows
- `news.py` — fetch, dedupe and tag headlines (`python news.py` to refresh)
- `update_data.py` — refresh the fundamentals snapshot `data/fundamentals.csv` (`python update_data.py`)
- `components.py` — shared styling and UI building blocks
- `companies.py` — short profiles shown when a home-page ticker is clicked

## Disclaimer
Independent educational project. Not investment advice. Figures are illustrative estimates based on stated
assumptions and free public data (Yahoo Finance, Google News). Not affiliated with MSCI Inc., IDX or OJK;
all trademarks belong to their owners. Provided "as is" without warranty.

## Author
Created by Shakti Widjonarko · shakti.widjo@gmail.com

© 2026 Shakti Widjonarko. All rights reserved.
