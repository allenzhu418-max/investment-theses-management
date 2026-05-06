"""
Fundamentals Agent
Fetches key financial metrics per ticker using yfinance (free, no API key).
Saves output to data/[date]/fundamentals.json
"""

import json
import yfinance as yf
from datetime import date


def safe(val, decimals=2):
    """Return rounded float or None cleanly."""
    try:
        if val is None:
            return None
        return round(float(val), decimals)
    except (TypeError, ValueError):
        return None


def pct(val):
    """Convert decimal ratio to percentage string."""
    if val is None:
        return None
    return round(float(val) * 100, 1)


def fetch_fundamentals(ticker: str) -> dict:
    """Fetch fundamental data for a single ticker."""
    try:
        t = yf.Ticker(ticker)
        info = t.info

        # Analyst price targets
        target_mean   = safe(info.get("targetMeanPrice"))
        target_high   = safe(info.get("targetHighPrice"))
        target_low    = safe(info.get("targetLowPrice"))
        current_price = safe(info.get("currentPrice") or info.get("regularMarketPrice"))
        upside = None
        if target_mean and current_price:
            upside = round((target_mean / current_price - 1) * 100, 1)

        return {
            "ticker": ticker,
            "name": info.get("longName") or info.get("shortName"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "current_price": current_price,
            "market_cap_b": safe((info.get("marketCap") or 0) / 1e9, 1),

            # Valuation
            "pe_trailing": safe(info.get("trailingPE")),
            "pe_forward": safe(info.get("forwardPE")),
            "ps_ratio": safe(info.get("priceToSalesTrailing12Months")),
            "pb_ratio": safe(info.get("priceToBook")),
            "peg_ratio": safe(info.get("pegRatio")),

            # Growth & earnings
            "eps_trailing": safe(info.get("trailingEps")),
            "eps_forward": safe(info.get("forwardEps")),
            "revenue_growth_yoy_pct": pct(info.get("revenueGrowth")),
            "earnings_growth_yoy_pct": pct(info.get("earningsGrowth")),

            # Margins
            "gross_margin_pct": pct(info.get("grossMargins")),
            "operating_margin_pct": pct(info.get("operatingMargins")),
            "profit_margin_pct": pct(info.get("profitMargins")),

            # Balance sheet
            "debt_to_equity": safe(info.get("debtToEquity")),
            "current_ratio": safe(info.get("currentRatio")),
            "return_on_equity_pct": pct(info.get("returnOnEquity")),
            "free_cashflow_b": safe((info.get("freeCashflow") or 0) / 1e9, 2),

            # Analyst targets
            "analyst_target_mean": target_mean,
            "analyst_target_high": target_high,
            "analyst_target_low": target_low,
            "analyst_upside_pct": upside,
            "analyst_recommendation": info.get("recommendationKey"),
            "analyst_count": info.get("numberOfAnalystOpinions"),

            # Dividend (relevant for MO, WMT)
            "dividend_yield_pct": pct(info.get("dividendYield")),
        }

    except Exception as e:
        return {"ticker": ticker, "error": str(e)}


def run(tickers: list, output_dir: str) -> dict:
    """Run fundamentals fetch for all tickers and save JSON."""
    print(f"  [fundamentals] Fetching {len(tickers)} tickers...")
    results = {}
    for ticker in tickers:
        print(f"    {ticker}...", end=" ", flush=True)
        results[ticker] = fetch_fundamentals(ticker)
        print("done")

    out_path = f"{output_dir}/fundamentals.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"  [fundamentals] Saved → {out_path}")
    return results


if __name__ == "__main__":
    import os
    today = date.today().isoformat()
    out = f"data/{today}"
    os.makedirs(out, exist_ok=True)
    from config import ALL_TICKERS
    run(ALL_TICKERS, out)
