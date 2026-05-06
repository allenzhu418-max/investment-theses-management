"""
Risk Agent
Flags position-level and portfolio-level risks.

Position-level (per ticker):
  - Drawdown from recent high
  - Short interest % of float
  - Beta vs SPY
  - Days to next earnings
  - Insider transactions (last 90 days)
  - SOXL-specific leveraged ETF warning

Portfolio-level:
  - Sector concentration %
  - Correlation cluster warning (semis)

Macro context (auto-fetched):
  - VIX level + trend
  - SPY trend (vs 20EMA / 200MA)
  - SMH trend (semis sector)
  - XLK trend (tech sector)
  - TNX (10yr yield)
  - DXY (USD strength)

Saves output to data/[date]/risk.json
"""

import json
import warnings
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import date, timedelta

warnings.filterwarnings("ignore")


def safe(val, decimals=2):
    try:
        if val is None or (isinstance(val, float) and np.isnan(val)):
            return None
        return round(float(val), decimals)
    except Exception:
        return None


# ── Per-ticker risk ─────────────────────────────────────────────────────────

def fetch_ticker_risk(ticker: str, config_entry: dict) -> dict:
    """Compute risk metrics for a single ticker."""
    try:
        t = yf.Ticker(ticker)
        info = t.info

        # ── Drawdown from recent high ──
        hist = t.history(period="6mo", interval="1d", auto_adjust=True)
        if hist.empty:
            drawdown_pct = None
            recent_high = None
        else:
            price = float(hist["Close"].iloc[-1])
            recent_high = float(hist["High"].max())
            drawdown_pct = round((price / recent_high - 1) * 100, 1)

        # ── Short interest ──
        short_pct = safe(info.get("shortPercentOfFloat"))
        if short_pct is not None:
            short_pct = round(short_pct * 100, 1)

        # ── Beta ──
        beta = safe(info.get("beta"))

        # ── Earnings date ──
        days_to_earnings = None
        earnings_date_str = None
        try:
            cal = t.calendar
            if cal is not None and not cal.empty:
                # calendar is a DataFrame with dates as column index
                if "Earnings Date" in cal.index:
                    ed = cal.loc["Earnings Date"].values[0]
                elif hasattr(cal, "columns") and len(cal.columns) > 0:
                    ed = cal.iloc[0, 0]
                else:
                    ed = None
                if ed is not None:
                    ed = pd.Timestamp(ed).date()
                    earnings_date_str = ed.isoformat()
                    days_to_earnings = (ed - date.today()).days
        except Exception:
            pass

        # ── Insider transactions ──
        insider_flag = None
        try:
            insider = t.insider_transactions
            if insider is not None and not insider.empty:
                # Look at last 90 days
                cutoff = pd.Timestamp(date.today() - timedelta(days=90))
                if "Start Date" in insider.columns:
                    recent = insider[pd.to_datetime(insider["Start Date"]) >= cutoff]
                else:
                    recent = insider.head(10)

                if not recent.empty and "Transaction" in recent.columns:
                    sells = recent["Transaction"].str.contains("Sale|Sell", case=False, na=False).sum()
                    buys  = recent["Transaction"].str.contains("Buy|Purchase", case=False, na=False).sum()
                    if sells >= 3:
                        insider_flag = f"Cluster selling: {sells} insider sales in last 90 days"
                    elif buys >= 2:
                        insider_flag = f"Insider buying: {buys} purchases in last 90 days"
        except Exception:
            pass

        # ── SOXL leveraged ETF warning ──
        leveraged_warning = None
        if ticker == "SOXL":
            leveraged_warning = (
                "SOXL is a 3x leveraged ETF tracking the SOX index. "
                "Daily rebalancing causes volatility decay — unsuitable as a long-term hold in choppy/ranging markets. "
                "Best used for short-term directional bets when semis sector has clear momentum."
            )

        # ── PDD geopolitical flag ──
        geo_flag = None
        if ticker == "PDD":
            geo_flag = "China-listed ADR — exposed to US-China regulatory risk, delisting risk, and yuan/macro factors."

        return {
            "ticker": ticker,
            "sector": config_entry.get("sector"),
            "notes": config_entry.get("notes"),
            "drawdown_from_6mo_high_pct": drawdown_pct,
            "recent_6mo_high": safe(recent_high),
            "short_interest_pct": short_pct,
            "beta": beta,
            "earnings_date": earnings_date_str,
            "days_to_earnings": days_to_earnings,
            "insider_flag": insider_flag,
            "leveraged_etf_warning": leveraged_warning,
            "geopolitical_flag": geo_flag,
        }

    except Exception as e:
        return {"ticker": ticker, "error": str(e)}


# ── Macro context ───────────────────────────────────────────────────────────

def fetch_macro(macro_tickers: dict) -> dict:
    """Fetch macro benchmark tickers and compute simple trend signals."""
    macro = {}
    for symbol, description in macro_tickers.items():
        try:
            t = yf.Ticker(symbol)
            hist = t.history(period="3mo", interval="1d", auto_adjust=True)
            if hist.empty:
                macro[symbol] = {"description": description, "error": "No data"}
                continue

            close = hist["Close"]
            price = float(close.iloc[-1])
            ema20 = float(close.ewm(span=20, adjust=False).mean().iloc[-1])
            ma50  = float(close.rolling(50).mean().iloc[-1]) if len(close) >= 50 else None

            # Week-over-week change
            wow_pct = round((price / float(close.iloc[-5]) - 1) * 100, 1) if len(close) >= 5 else None
            # Month-over-month change
            mom_pct = round((price / float(close.iloc[-21]) - 1) * 100, 1) if len(close) >= 21 else None

            trend = "above_ema20" if price > ema20 else "below_ema20"

            macro[symbol] = {
                "description": description,
                "price": round(price, 2),
                "ema20": round(ema20, 2),
                "ma50": round(ma50, 2) if ma50 else None,
                "vs_ema20_pct": round((price / ema20 - 1) * 100, 1),
                "wow_pct": wow_pct,
                "mom_pct": mom_pct,
                "trend": trend,
            }

            # VIX-specific risk level label
            if symbol == "^VIX":
                macro[symbol]["risk_level"] = (
                    "extreme_fear" if price > 40 else
                    "high_fear"    if price > 30 else
                    "elevated"     if price > 20 else
                    "low"
                )

        except Exception as e:
            macro[symbol] = {"description": description, "error": str(e)}

    return macro


# ── Portfolio-level risk ────────────────────────────────────────────────────

def portfolio_risk(holdings: dict, watchlist: dict, correlation_cluster: list) -> dict:
    """Compute sector concentration and correlation cluster exposure."""
    all_positions = {**holdings, **watchlist}
    total = len(all_positions)

    sector_counts = {}
    for ticker, meta in all_positions.items():
        s = meta.get("sector", "Unknown")
        sector_counts[s] = sector_counts.get(s, 0) + 1

    sector_pct = {s: round(c / total * 100, 1) for s, c in sector_counts.items()}

    # Which holdings are in the correlation cluster
    cluster_holdings = [t for t in holdings if t in correlation_cluster]
    cluster_watchlist = [t for t in watchlist if t in correlation_cluster]

    return {
        "total_positions": total,
        "sector_concentration": sector_pct,
        "correlation_cluster": {
            "tickers": correlation_cluster,
            "holdings_in_cluster": cluster_holdings,
            "watchlist_in_cluster": cluster_watchlist,
            "warning": (
                f"{len(cluster_holdings)} holdings ({', '.join(cluster_holdings)}) are in the semis correlation cluster. "
                "In a broad semiconductor selloff, these tend to fall together regardless of individual fundamentals."
            ) if cluster_holdings else None,
        },
    }


# ── Main run ────────────────────────────────────────────────────────────────

def run(tickers: list, output_dir: str) -> dict:
    """Run full risk analysis and save JSON."""
    from config import HOLDINGS, WATCHLIST, MACRO_TICKERS, CORRELATION_CLUSTER

    all_config = {**HOLDINGS, **WATCHLIST}

    print(f"  [risk] Fetching risk data for {len(tickers)} tickers...")
    ticker_risks = {}
    for ticker in tickers:
        print(f"    {ticker}...", end=" ", flush=True)
        ticker_risks[ticker] = fetch_ticker_risk(ticker, all_config.get(ticker, {}))
        print("done")

    print("  [risk] Fetching macro benchmarks...")
    macro = fetch_macro(MACRO_TICKERS)

    print("  [risk] Computing portfolio-level risk...")
    port_risk = portfolio_risk(HOLDINGS, WATCHLIST, CORRELATION_CLUSTER)

    results = {
        "tickers": ticker_risks,
        "macro": macro,
        "portfolio": port_risk,
    }

    out_path = f"{output_dir}/risk.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"  [risk] Saved → {out_path}")
    return results


if __name__ == "__main__":
    import os
    today = date.today().isoformat()
    out = f"data/{today}"
    os.makedirs(out, exist_ok=True)
    from config import ALL_TICKERS
    run(ALL_TICKERS, out)
