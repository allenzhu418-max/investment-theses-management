"""
Investment Research — Data Collection Runner
=============================================
Fetches all raw data for today's analysis session and saves to data/[date]/.

Usage:
    python run_analysis.py

What it does:
    1. Creates data/[date]/ directory
    2. Runs all four data agents (fundamentals, technical, news, risk)
    3. Saves JSON data files + chart PNGs
    4. Prints a summary of what was collected

After this runs, bring the output to Claude Code for report generation.
"""

import os
import sys
import json
import time
from datetime import date

# ── Setup ───────────────────────────────────────────────────────────────────

TODAY = date.today().isoformat()
DATA_DIR = os.path.join("data", TODAY)
os.makedirs(DATA_DIR, exist_ok=True)

from config import ALL_TICKERS, HOLDINGS, WATCHLIST


def print_header():
    print("\n" + "═" * 60)
    print(f"  Investment Research — Data Collection")
    print(f"  Date: {TODAY}")
    print(f"  Tickers: {len(ALL_TICKERS)} ({len(HOLDINGS)} holdings + {len(WATCHLIST)} watchlist)")
    print("═" * 60 + "\n")


def print_section(name: str):
    print(f"\n{'─' * 40}")
    print(f"  {name}")
    print(f"{'─' * 40}")


def save_run_manifest(results: dict):
    """Save a manifest of what was collected this run."""
    manifest = {
        "date": TODAY,
        "tickers": ALL_TICKERS,
        "agents_run": list(results.keys()),
        "data_dir": DATA_DIR,
        "errors": {},
    }
    for agent, data in results.items():
        if isinstance(data, dict):
            errs = [t for t, v in data.items() if isinstance(v, dict) and "error" in v]
            if errs:
                manifest["errors"][agent] = errs

    path = os.path.join(DATA_DIR, "manifest.json")
    with open(path, "w") as f:
        json.dump(manifest, f, indent=2)
    return manifest


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    print_header()
    results = {}
    start_time = time.time()

    # 1. Fundamentals
    print_section("Fundamentals Agent")
    from agents import fundamentals
    results["fundamentals"] = fundamentals.run(ALL_TICKERS, DATA_DIR)

    # 2. Technical (also generates charts)
    print_section("Technical Agent")
    from agents import technical
    results["technical"] = technical.run(ALL_TICKERS, DATA_DIR)

    # 3. News
    print_section("News Agent")
    from agents import news
    results["news"] = news.run(ALL_TICKERS, DATA_DIR)

    # 4. Risk
    print_section("Risk Agent")
    from agents import risk
    results["risk"] = risk.run(ALL_TICKERS, DATA_DIR)

    # ── Summary ──
    manifest = save_run_manifest(results)
    elapsed = round(time.time() - start_time, 1)

    print("\n" + "═" * 60)
    print(f"  Data collection complete ({elapsed}s)")
    print(f"  Output directory: {DATA_DIR}/")
    print(f"  Files generated:")
    for f in sorted(os.listdir(DATA_DIR)):
        size = os.path.getsize(os.path.join(DATA_DIR, f))
        print(f"    {f:<40} {size/1024:.1f} KB")

    if manifest["errors"]:
        print(f"\n  ⚠ Errors encountered:")
        for agent, tickers in manifest["errors"].items():
            print(f"    [{agent}] Failed tickers: {', '.join(tickers)}")

    print("\n  Next step: open Claude Code and say")
    print(f'  "Generate today\'s research report from data/{TODAY}/"')
    print("═" * 60 + "\n")


if __name__ == "__main__":
    main()
