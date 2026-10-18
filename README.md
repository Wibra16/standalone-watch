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
- `config.py` — dates, tickers, defaults, colors
- `model.py` — outflow math (no UI)
- `data.py` — yfinance downloads + caching
- `components.py` — shared styling, disclaimer, live countdown
- `app.py` — the Streamlit page
