# Standalone Watch — Claude Code Build Kit

Two parts: **Part 1** is setup you do once on your laptop. **Part 2** is the prompt you paste into Claude Code.

---

## Part 1 — Setup (about 30 minutes)

### 1. Install these
| What | Why | Where |
|---|---|---|
| **Python 3.11 or 3.12** | Runs the app | python.org/downloads (on Windows, tick "Add Python to PATH") |
| **Git** | Version control + needed on Windows for Claude Code's shell | git-scm.com/downloads |
| **VS Code** (optional but nice) | See and edit the files Claude writes | code.visualstudio.com |
| **Claude Code** | Builds the thing | See commands below |

**Claude Code install** (open Terminal on Mac, PowerShell on Windows):
- Mac: `curl -fsSL https://claude.ai/install.sh | bash`
- Windows PowerShell: `irm https://claude.ai/install.ps1 | iex`
- Then open a **new** terminal and run `claude --version` to check it worked.
- You need a paid Claude plan (Pro or Max) or an Anthropic Console account. It asks you to log in the first time.

### 2. Make accounts (free)
- **GitHub** (github.com): to store the code and show it on your resume
- **Streamlit Community Cloud** (share.streamlit.io): free hosting, gives you a public link

### 3. Optional, for later phases
- **Anthropic API key** (console.anthropic.com): only for Phases 4–6 (daily news summaries, investor takeaways, translating Bahasa announcements). Billed separately from your Claude subscription, but costs cents per transcript. Never paste the key into the code; Claude Code will set up a `.env` file for it.

### 4. Start the project
```bash
mkdir standalone-watch
cd standalone-watch
claude
```
Then paste Part 2. Claude Code installs the Python packages itself (streamlit, yfinance, pandas, plotly, etc.), so you don't need to.

**Tip:** Save Part 2 as `CLAUDE.md` in the project folder. Claude Code reads that file automatically every session, so it never forgets the plan.

---

## Part 2 — The prompt (paste everything below this line)

---

I'm a UCLA Economics + Data Science student building a portfolio project for investment banking (fintech focus) recruiting. I'm a beginner-to-intermediate coder, so explain what you're doing briefly as you go, keep code readable with comments, and don't over-engineer. **Start in plan mode: show me your plan for Phase 1 and wait for my OK before writing code.**

### Project: "Standalone Watch"
An interactive web app that simulates the impact of MSCI's proposed downgrade of Indonesia from Emerging Market to **Standalone Market** status.

**Context (verify dates with a quick search if you can):**
- On Oct 15, 2026, MSCI proposed reclassifying Indonesia from Emerging to Standalone, citing market dysfunction, alleged coordinated trading, and weak regulatory enforcement.
- On Oct 16, 2026, the Jakarta Composite Index (JCI) fell as much as ~11%, its worst day since Jan 1998, with a trading halt at open. Big banks (BBCA, BBRI, BMRI) fell ~15%. The rupiah hit ~18,070/USD.
- The consultation runs until **April 30, 2027**. MSCI's final decision comes by **end of June 2027**.
- Standalone markets are excluded from MSCI EM and Frontier indexes, so passive funds tracking MSCI EM would have to sell.
- Precedent: **Argentina** was reclassified to Standalone by MSCI in 2021.

### Tech stack
- **Python + Streamlit** (single app, multi-page is fine), **Plotly** for charts
- **yfinance** for prices (Indonesian tickers end in `.JK`; JCI is `^JKSE`; rupiah is `IDR=X`; Argentina Merval is `^MERV`; also try ETFs `EIDO` and `ARGT`)
- **pandas / numpy** for analysis
- Later phases: **feedparser** (news RSS), **pdfplumber**, **transformers** (FinBERT: `ProsusAI/finbert`), **scikit-learn**, **anthropic** SDK
- Use a virtual environment (`.venv`) and a `requirements.txt`. Cache data downloads with `st.cache_data` and save raw data to a `data/` folder so we don't re-download constantly.
- Set up git, a good `.gitignore` (exclude `.env`, `.venv`, large data), and a README.

### Stock universe (start here, make it easy to add more)
Banks: BBCA.JK, BBRI.JK, BMRI.JK, BBNI.JK
Large caps: TLKM.JK, ASII.JK
Fintech / digital (my niche, highlight these): GOTO.JK, ARTO.JK (Bank Jago), BBHI.JK (Allo Bank)
If any ticker fails in yfinance, tell me and suggest a replacement.

---

### Phase 1 — Clickable simulator (illustrative numbers OK)
Build the UI first, with a clear on-screen banner: **"Illustrative estimates — not investment advice."**
1. **Scenario toggle:** Stay EM / Frontier / Standalone. Everything updates when switched.
2. **Sliders (sidebar):**
   - Probability of downgrade (0–100%)
   - Passive AUM tracking MSCI EM ($bn, sensible default, editable)
   - Indonesia's weight in MSCI EM (%, editable)
   - % of passive holders that sell (0–100%)
   - Days to exit
   - Participation rate (% of daily volume sellers can trade without crushing price)
3. **Core math (put in a separate `model.py`, not in the UI file):**
   - Country outflow = passive AUM × Indonesia weight × % that sell × scenario factor
   - Per-stock outflow = country outflow × stock's share of Indonesia's index weight (approximate with free-float market cap if needed, and say so)
   - **Days of forced selling** = per-stock outflow ÷ (avg daily traded value × participation rate)
   - Expected outflow = outflow × probability
4. **Stock picker:** select a ticker to see its estimated outflow, days of forced selling, price change since Oct 15 2026, and a simple chart.
5. **Countdown hero banner** at the top of every page: a live days/hours countdown to **MSCI's official decision announcement**. MSCI has only said "by end of June 2027," so default the target to **June 30, 2027** and store it in one config value (`config.py`) so I can update it the moment MSCI publishes the exact date. Show a small secondary countdown to the **Apr 30, 2027** consultation close. Label the decision date as "expected" until confirmed.
6. Headline metrics row: total expected outflow ($), JCI change since announcement, IDR/USD change.

Run it locally (`streamlit run app.py`) and tell me how to view it.

### Phase 2 — Real data
- Pull real prices and volumes for the universe, JCI, and IDR.
- Compute 20-day average daily traded value (in USD) per stock.
- Replace illustrative weights with the best free approximation (free-float market cap, or EIDO ETF holdings if accessible). **Document every assumption in the app** in an "Assumptions & Methodology" expander.
- Add a **"forced seller vs. fundamentals"** table: rank stocks by days of forced selling vs. a basic fundamental (P/E or P/B from yfinance where available). Flag names that look mechanically oversold.

### Phase 3 — Argentina overlay
- Event study: align the Merval (and/or ARGT) around Argentina's 2021 standalone announcement date (verify the date) and the JCI around Oct 15 2026, both as "day 0."
- Slider to shift the window (e.g., −60 to +250 trading days). Plot normalized returns (day 0 = 100).
- Show a one-line takeaway: "JCI is X% below/above Argentina's path at the same point."
- Be careful about look-ahead bias and point it out if relevant.

### Phase 4 — Daily news tracker + timeline
A page that updates every day with what's happening in the downgrade story, so visitors can follow it like a live feed.

**Collecting news (free sources first):**
- Google News RSS search feeds via `feedparser` for queries like: "MSCI Indonesia," "Indonesia standalone market," "OJK reform," "IDX bursa efek," "JCI IHSG," "rupiah." Include both English and Bahasa queries.
- Optionally the GDELT API as a second free source. Tell me if any source is blocked or needs a paid key.
- Save to `data/news.csv` (date, headline, source, link, language, tags). **Deduplicate** by link and near-identical headlines.
- Store headline, source, and link only, plus a short summary in our own words. Don't copy full article text.

**Auto-updating daily:**
- Write a standalone script `update_news.py` that fetches, dedupes, tags, and appends new items.
- Schedule it with a **GitHub Actions workflow** that runs once a day (e.g., after the Jakarta market close, ~09:30 UTC), commits the updated CSV, and redeploys automatically. Explain why this works better than relying on Streamlit Cloud, which sleeps when idle.
- Also pull that day's **JCI close, IDR/USD, and EIDO** in the same job and save to `data/daily_market.csv`.

**Timeline page:**
- A vertical, day-by-day **timeline** (newest on top), each day showing: headlines with links, auto-tags (MSCI / Regulator (OJK, IDX) / Market move / Rupiah / Fintech), and that day's JCI % change and IDR/USD.
- **Pinned milestones** that stand out visually: Jan 2026 MSCI index freeze, Oct 15 2026 standalone proposal, Oct 16 2026 crash and trading halt, Apr 30 2027 consultation close, expected Jun 2027 decision. Keep these in an editable `milestones.csv`.
- Filters: date range, tag, language. Search box for keywords.
- A small chart of JCI since Oct 15 2026 with news-day markers you can hover over.
- Optional (Claude API): a 2–3 sentence **"Today in the downgrade"** daily summary written from the headlines, clearly labeled AI-generated.
- Show "Last updated: [timestamp]" at the top so visitors know it's live.

**Bonus:** feed new OJK/IDX regulator items straight into the Phase 6 "You be MSCI" voting queue.

### Phase 5 — Earnings call sentiment module
- Page where a user uploads an earnings call transcript (PDF or .txt).
- Extract text, split into **prepared remarks** vs. **Q&A** (best-effort heuristics; tell me the limits).
- Score sentiment with FinBERT per section and sentence; chart sentiment across the call.
- Highlight top 3 most positive, most negative, and most hedging sentences (hedge word list: "challenging," "uncertain," "headwinds," "cautious," etc.).
- Optional, using the Claude API with the key from `.env`: generate **investor takeaways** (3–5 bullets, guidance raised/held/cut, one-line bull and bear case, red flags).
- Let me save results per company/quarter so I can compare **pre- vs post-announcement tone** for Indonesian banks and fintechs.

### Phase 6 — "You be MSCI" + reform credibility score
- Load a list of OJK/IDX reform announcements (start with a CSV I fill in manually: date, source, text, link; scraping is a stretch goal).
- Translate Bahasa text to English with the Claude API if needed.
- Users vote each one **"real enforcement"** or **"just a promise."** Store votes (SQLite is fine locally; tell me what works on Streamlit Cloud).
- Build a simple NLP score for each announcement (concrete actions, numbers, penalties, dates = higher credibility). Show crowd score vs. model score side by side.
- Combine into a transparent **downgrade-probability gauge** with the formula shown to the user.

### Phase 7 — Deploy
- Push to GitHub and walk me through deploying on Streamlit Community Cloud step by step. Make sure secrets go in Streamlit's secrets manager and GitHub Actions secrets, not the repo. Confirm the daily news job runs successfully on GitHub.
- Write a README with: what it does, screenshots, methodology, assumptions, limitations, and how to run it.

---

### Rules throughout
- Build **one phase at a time**. After each phase, run the app, fix errors, summarize what you built in 3–5 bullets, and tell me what to test before moving on.
- Never hardcode API keys. Never present estimates as facts: label assumptions everywhere.
- If a data source is unavailable or paid, tell me and propose a free alternative instead of faking data silently.
- At the end of each phase, give me **one sentence I could say in an interview** about what that phase shows.

### Design (added by user)
Minimalist stock-terminal aesthetic. Colors: black, white, red only. Monospace numbers, thin rules, no clutter.
