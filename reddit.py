"""
reddit.py — "internet sentiment": the most-upvoted Reddit posts about
Indonesia's markets in the last day, each with a tone score.

Uses Reddit's official API (free for non-commercial use). Needs two values,
kept OUT of the code:
  REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET
locally in a .env file (git-ignored), and as GitHub Actions secrets for the
daily job. Without them, fetch() returns None and the site shows a note.

Tone uses VADER, a standard rule-based sentiment model for short social text:
compound score from -1 (very negative) to +1 (very positive).
"""
import os
import calendar
import re
import time
from pathlib import Path

import feedparser
import requests
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

USER_AGENT = "python:standalone-watch:1.0 (educational project by Shakti Widjonarko)"
QUERIES = ["MSCI Indonesia", "Indonesia stock market", "IHSG", "Jakarta Composite", "Indonesia stocks", "rupiah"]
# A post must mention at least one of these to count as on-topic
TOPIC = re.compile(r"indonesia|\bidx\b|\bjci\b|ihsg|jakarta|rupiah|\bmsci\b|\beido\b|\bojk\b", re.I)
_vader = SentimentIntensityAnalyzer()


def _load_env():
    """Read KEY=value lines from .env (no extra dependency needed)."""
    env = Path(__file__).parent / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def _token():
    _load_env()
    cid, secret = os.environ.get("REDDIT_CLIENT_ID"), os.environ.get("REDDIT_CLIENT_SECRET")
    if not cid or not secret:
        return None
    r = requests.post("https://www.reddit.com/api/v1/access_token", auth=(cid, secret),
                      data={"grant_type": "client_credentials"}, headers={"User-Agent": USER_AGENT}, timeout=15)
    r.raise_for_status()
    return r.json()["access_token"]


def tone(text):
    s = _vader.polarity_scores(text)["compound"]
    return round(s, 3), ("positive" if s >= 0.15 else "negative" if s <= -0.15 else "neutral")


def _search(token, window):
    headers = {"Authorization": f"bearer {token}", "User-Agent": USER_AGENT}
    posts = {}
    for q in QUERIES:
        r = requests.get("https://oauth.reddit.com/search", headers=headers, timeout=15,
                         params={"q": q, "sort": "top", "t": window, "limit": 25, "type": "link"})
        if r.status_code != 200:
            continue
        for child in r.json().get("data", {}).get("children", []):
            p = child["data"]
            text = f'{p.get("title", "")} {p.get("selftext", "")[:400]}'
            if p.get("over_18") or not TOPIC.search(text):
                continue
            score, label = tone(text)
            posts[p["id"]] = {
                "title": p["title"], "sub": p["subreddit"], "score": p["score"], "comments": p["num_comments"],
                "url": "https://www.reddit.com" + p["permalink"], "created": int(p["created_utc"]),
                "tone": score, "label": label,
            }
        time.sleep(1)   # stay well under Reddit's rate limit
    return sorted(posts.values(), key=lambda p: p["score"], reverse=True)


def _search_rss(window):
    """Keyless fallback: Reddit's public RSS search (sorted by top, no vote counts)."""
    posts, rank, seen = {}, 0, set()
    for q in QUERIES:
        for attempt in range(3):
            r = requests.get("https://www.reddit.com/search.rss", headers={"User-Agent": USER_AGENT}, timeout=15,
                             params={"q": q, "sort": "top", "t": window, "limit": 25})
            if r.status_code != 429:
                break
            time.sleep(10 * (attempt + 1))
        if r.status_code == 200:
            for e in feedparser.parse(r.text).entries:
                # Title must be on-topic: a passing mention deep in the body (e.g. an S&P 500
                # thread) isn't a post "about Indonesia's markets".
                if e.link in posts or "/comments/" not in e.link or not TOPIC.search(e.title):
                    continue
                sub = e.link.split("/r/")[1].split("/")[0]
                key = re.sub(r"^\[[^\]]*\]\s*-\s*|\W+", "", e.title.lower())   # "[World] - X" == "X"
                if re.search(r"auto$|^autonewspaper$", sub, re.I) or key in seen:  # news-bot reposts, duplicates
                    continue
                seen.add(key)
                score, label = tone(e.title)
                posts[e.link] = {
                    "title": e.title, "sub": sub, "score": None, "comments": None, "url": e.link,
                    "created": calendar.timegm(stamp) if (stamp := e.get("published_parsed") or e.get("updated_parsed")) else None,
                    "tone": score, "label": label, "rank": rank,
                }
                rank += 1
        time.sleep(3)
    # Reddit's "t=day" is loose, so enforce the window ourselves
    cutoff = time.time() - {"day": 86400, "week": 7 * 86400}[window]
    fresh = [p for p in posts.values() if p["created"] and p["created"] >= cutoff]
    return sorted(fresh, key=lambda p: p["rank"])


def fetch(top=5):
    """Top posts of the last day (falls back to the last week if the day is quiet).
    Uses the API when keys exist, otherwise the public RSS feed."""
    token = _token()
    search = (lambda w: _search(token, w)) if token else _search_rss
    window, posts = "day", search("day")
    if len(posts) < 3:            # fewer than 3 fresh posts: widen to the week
        window, posts = "week", search("week")
    picked = posts[:top]
    every = posts[:25]
    mood = round(sum(p["tone"] for p in every) / len(every), 3) if every else None
    return {"window": window, "posts": picked, "mood": mood, "sample": len(every),
            "split": {k: sum(p["label"] == k for p in every) for k in ("positive", "neutral", "negative")}}


if __name__ == "__main__":
    out = fetch()
    if out is None:
        print("No REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET found (add them to .env).")
    else:
        print(f"{len(out['posts'])} posts ({out['window']}), mood {out['mood']}, split {out['split']}")
        for p in out["posts"]:
            print(f"  {p['score'] or '':>6} ↑  r/{p['sub']:<16} {p['label']:<8} {p['title'][:70]}")
