"""
News Agent
Fetches latest headlines for each ticker from free RSS feeds.
Sources: Yahoo Finance RSS, Google News RSS
No API key required.
Saves output to data/[date]/news.json
"""

import json
import feedparser
import requests
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from dateutil import parser as dateparser


NEWS_LOOKBACK_HOURS = 48
MAX_HEADLINES_PER_TICKER = 6

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; investment-research-bot/1.0)"
}


def parse_pub_date(entry) -> datetime | None:
    """Parse publication date from a feed entry, return UTC-aware datetime or None."""
    for field in ("published", "updated", "pubDate"):
        raw = entry.get(field)
        if raw:
            try:
                return parsedate_to_datetime(raw)
            except Exception:
                pass
            try:
                dt = dateparser.parse(raw)
                if dt and dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except Exception:
                pass
    return None


def is_recent(pub_date: datetime | None, hours: int = NEWS_LOOKBACK_HOURS) -> bool:
    if pub_date is None:
        return True  # include if date unknown
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    return pub_date >= cutoff


def fetch_rss(url: str) -> list:
    """Fetch and parse an RSS feed, return list of entries."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        feed = feedparser.parse(resp.content)
        return feed.entries
    except Exception:
        try:
            feed = feedparser.parse(url)
            return feed.entries
        except Exception:
            return []


def get_headlines_for_ticker(ticker: str) -> list[dict]:
    """Fetch headlines from Yahoo Finance + Google News RSS for a ticker."""
    headlines = []
    seen_titles = set()

    sources = [
        # Yahoo Finance RSS for this ticker
        f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US",
        # Google News RSS search
        f"https://news.google.com/rss/search?q={ticker}+stock&hl=en-US&gl=US&ceid=US:en",
    ]

    for url in sources:
        entries = fetch_rss(url)
        for entry in entries:
            title = entry.get("title", "").strip()
            if not title or title in seen_titles:
                continue
            pub_date = parse_pub_date(entry)
            if not is_recent(pub_date):
                continue
            seen_titles.add(title)
            headlines.append({
                "title": title,
                "source": entry.get("source", {}).get("title") if isinstance(entry.get("source"), dict) else entry.get("source", ""),
                "url": entry.get("link", ""),
                "published": pub_date.isoformat() if pub_date else None,
            })

    # Sort by date descending, newest first
    headlines.sort(key=lambda x: x["published"] or "", reverse=True)
    return headlines[:MAX_HEADLINES_PER_TICKER]


def run(tickers: list, output_dir: str) -> dict:
    """Fetch news for all tickers and save JSON."""
    print(f"  [news] Fetching headlines for {len(tickers)} tickers (last {NEWS_LOOKBACK_HOURS}h)...")
    results = {}
    for ticker in tickers:
        print(f"    {ticker}...", end=" ", flush=True)
        headlines = get_headlines_for_ticker(ticker)
        results[ticker] = {
            "ticker": ticker,
            "headlines": headlines,
            "count": len(headlines),
        }
        print(f"{len(headlines)} headlines")

    out_path = f"{output_dir}/news.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"  [news] Saved → {out_path}")
    return results


if __name__ == "__main__":
    import os
    from datetime import date
    today = date.today().isoformat()
    out = f"data/{today}"
    os.makedirs(out, exist_ok=True)
    from config import ALL_TICKERS
    run(ALL_TICKERS, out)
