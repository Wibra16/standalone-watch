"""
news.py — pull headlines about the downgrade from Google News RSS,
deduplicate, tag, and save to data/news.csv.

We keep only headline, source, link and date (never full article text).
Run on its own to refresh:  python news.py
"""
import re
import urllib.parse
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path

import feedparser
import pandas as pd

import config

NEWS_CSV = Path(__file__).parent / "data" / "news.csv"


def _feed_url(query, lang):
    q = urllib.parse.quote(query)
    if lang == "id":
        return f"https://news.google.com/rss/search?q={q}&hl=id&gl=ID&ceid=ID:id"
    return f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"


def _clean_title(title, source):
    """Google appends ' - Source' to every headline; strip it."""
    suffix = f" - {source}"
    return title[: -len(suffix)] if source and title.endswith(suffix) else title


def _tags(text):
    text = text.lower()
    return ",".join(tag for tag, words in config.NEWS_TAGS.items() if any(w in text for w in words))


def _norm(title):
    return re.sub(r"[^a-z0-9 ]", "", title.lower())


def fetch():
    """Download all queries and return a deduplicated DataFrame."""
    rows = []
    for query, lang in config.NEWS_QUERIES:
        feed = feedparser.parse(_feed_url(query, lang))
        for e in feed.entries:
            source = e.get("source", {}).get("title", "")
            title = _clean_title(e.get("title", ""), source)
            published = datetime(*e.published_parsed[:6], tzinfo=timezone.utc) if e.get("published_parsed") else None
            if not published or published.strftime("%Y-%m-%d") < config.NEWS_START:
                continue
            rows.append({"published": published, "headline": title, "source": source,
                         "link": e.get("link", ""), "language": lang, "tags": _tags(title)})
    df = pd.DataFrame(rows)
    if df.empty:
        return df

    # Deduplicate: same link, then near-identical headlines (>85% similar)
    df = df.sort_values("published", ascending=False).drop_duplicates("link")
    kept = []
    for _, r in df.iterrows():
        if all(SequenceMatcher(None, _norm(r.headline), _norm(k.headline)).ratio() < 0.85 for k in kept):
            kept.append(r)
    df = pd.DataFrame(kept)
    # Keep stories that hit at least one tag (filters out unrelated rupiah noise, etc.)
    return df[df["tags"] != ""].reset_index(drop=True)


def update():
    """Fetch new items, merge with the saved CSV, save, return everything."""
    new = fetch()
    old = load_saved()
    df = pd.concat([new, old]).drop_duplicates("link") if not old.empty else new
    if not df.empty:
        df = df.sort_values("published", ascending=False)
        df.to_csv(NEWS_CSV, index=False)
    return df


def load_saved():
    if NEWS_CSV.exists():
        return pd.read_csv(NEWS_CSV, parse_dates=["published"])
    return pd.DataFrame()


if __name__ == "__main__":
    out = update()
    print(f"{len(out)} stories saved to {NEWS_CSV}")
