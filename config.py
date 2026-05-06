"""
Portfolio configuration — single source of truth.
Edit this file to update holdings, watchlist, or sector labels.
"""

# Holdings with sector context
HOLDINGS = {
    "NVDA": {"sector": "AI value chain", "notes": "Core AI/GPU position"},
    "MU":   {"sector": "AI value chain", "notes": "Memory, HBM for AI"},
    "SOXL": {"sector": "AI value chain", "notes": "3x leveraged semis ETF — high volatility, short-hold instrument"},
    "MRVL": {"sector": "AI value chain", "notes": "Custom silicon, networking"},
    "APH":  {"sector": "AI value chain", "notes": "Connectors/interconnects for AI infra"},
    "VST":  {"sector": "AI value chain", "notes": "Power/energy for data centres"},
    "MO":   {"sector": "Defensive", "notes": "Tobacco, dividend yield"},
    "WMT":  {"sector": "Defensive", "notes": "Retail, consumer staples"},
    "PDD":  {"sector": "Defensive", "notes": "China e-commerce — geopolitical risk flag"},
    "DAL":  {"sector": "Defensive", "notes": "Airlines — macro/fuel sensitive"},
}

# Watchlist — same full analysis as holdings
WATCHLIST = {
    "SNDK": {"sector": "AI value chain", "notes": "Flash storage, WD spinoff"},
    "AMAT": {"sector": "AI value chain", "notes": "Semiconductor equipment"},
    "LITE": {"sector": "AI value chain", "notes": "Optical components for AI networking"},
    "COHR": {"sector": "AI value chain", "notes": "Optical/laser components"},
    "AAOI": {"sector": "AI value chain", "notes": "Optical transceivers, high beta"},
}

# All tickers combined for full run
ALL_TICKERS = list(HOLDINGS.keys()) + list(WATCHLIST.keys())

# Macro benchmark tickers fetched automatically
MACRO_TICKERS = {
    "^VIX":     "Market fear / volatility index",
    "SPY":      "S&P 500 — broad market trend",
    "SMH":      "VanEck Semiconductor ETF (25 stocks, NVDA-heavy ~25%) — semis sector health",
    "SOXX":     "iShares Semiconductor ETF (30 stocks, capped 8% per name) — broader semis read; divergence from SMH signals NVDA-specific vs sector-wide moves",
    "XLK":      "Tech sector ETF — broad tech trend",
    "^TNX":     "US 10-year Treasury yield — rate environment",
    "DX-Y.NYB": "US Dollar index — affects multinationals (PDD, WMT)",
}

# Correlation cluster warning — these move together in a semis selloff
CORRELATION_CLUSTER = ["NVDA", "MU", "SOXL", "MRVL", "AMAT", "SNDK"]

# News lookback window in hours
NEWS_LOOKBACK_HOURS = 48

# Chart output settings
CHART_WEEKS = 52  # weeks of history shown on technical chart
