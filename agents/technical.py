"""
Technical Agent
Fetches weekly price history via yfinance and computes:
  - 5 EMA, 20 EMA, 200 MA
  - Bollinger Bands (20-week, 2σ)
  - MACD (12/26/9) on weekly candles
  - ATR (14-week)
  - RSI (14-week)
  - Volume trend
Saves per-ticker candlestick chart PNG + technical.json
"""

import json
import os
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import yfinance as yf
from datetime import date, timedelta

warnings.filterwarnings("ignore")

CHART_WEEKS = 52


# ── Indicator calculations ──────────────────────────────────────────────────

def compute_ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def compute_sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window=window).mean()


def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def compute_macd(series: pd.Series):
    ema12 = compute_ema(series, 12)
    ema26 = compute_ema(series, 26)
    macd_line = ema12 - ema26
    signal_line = compute_ema(macd_line, 9)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def compute_bollinger(series: pd.Series, window: int = 20):
    mid = series.rolling(window).mean()
    std = series.rolling(window).std()
    upper = mid + 2 * std
    lower = mid - 2 * std
    return upper, mid, lower


def compute_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.rolling(period).mean()


# ── Chart generation ────────────────────────────────────────────────────────

def draw_chart(ticker: str, df: pd.DataFrame, output_dir: str) -> str:
    """Draw a weekly candlestick chart with indicators. Returns saved path."""
    df = df.tail(CHART_WEEKS).copy()
    dates = df.index

    fig, (ax1, ax2, ax3) = plt.subplots(
        3, 1, figsize=(14, 10),
        gridspec_kw={"height_ratios": [4, 1.2, 1.2]},
        sharex=True
    )
    fig.patch.set_facecolor("#0f0f0f")
    for ax in (ax1, ax2, ax3):
        ax.set_facecolor("#0f0f0f")
        ax.tick_params(colors="#cccccc", labelsize=8)
        ax.yaxis.label.set_color("#cccccc")
        for spine in ax.spines.values():
            spine.set_edgecolor("#333333")
        ax.grid(True, color="#1e1e1e", linewidth=0.5)

    # ── Candlesticks ──
    width = 4  # days (weekly candles)
    for i, (idx, row) in enumerate(df.iterrows()):
        o, h, l, c = row["Open"], row["High"], row["Low"], row["Close"]
        color = "#26a69a" if c >= o else "#ef5350"
        ax1.plot([idx, idx], [l, h], color=color, linewidth=0.8)
        rect = Rectangle(
            (mdates.date2num(idx) - width / 2, min(o, c)),
            width, abs(c - o),
            linewidth=0, facecolor=color
        )
        ax1.add_patch(rect)

    ax1.set_xlim(
        mdates.date2num(dates[0]) - 5,
        mdates.date2num(dates[-1]) + 5
    )

    # ── MAs & Bollinger ──
    ax1.plot(dates, df["EMA5"],   color="#f0e68c", linewidth=1.2, label="5 EMA")
    ax1.plot(dates, df["EMA20"],  color="#42a5f5", linewidth=1.4, label="20 EMA")
    ax1.plot(dates, df["MA200"],  color="#ff7043", linewidth=1.6, label="200 MA", linestyle="--")
    ax1.plot(dates, df["BB_upper"], color="#888888", linewidth=0.8, linestyle=":")
    ax1.plot(dates, df["BB_lower"], color="#888888", linewidth=0.8, linestyle=":")
    ax1.fill_between(dates, df["BB_upper"], df["BB_lower"], alpha=0.04, color="#888888")

    ax1.set_title(f"{ticker} — Weekly Chart ({CHART_WEEKS}w)", color="#eeeeee", fontsize=11, pad=8)
    ax1.legend(loc="upper left", fontsize=7, facecolor="#1a1a1a", labelcolor="#cccccc")
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:.0f}"))

    # ── MACD ──
    ax2.plot(dates, df["MACD"],   color="#42a5f5", linewidth=1.0, label="MACD")
    ax2.plot(dates, df["Signal"], color="#ff7043", linewidth=1.0, label="Signal")
    colors_hist = ["#26a69a" if v >= 0 else "#ef5350" for v in df["MACD_hist"]]
    ax2.bar(dates, df["MACD_hist"], color=colors_hist, width=4, alpha=0.7)
    ax2.axhline(0, color="#555555", linewidth=0.5)
    ax2.set_ylabel("MACD", fontsize=8)
    ax2.legend(loc="upper left", fontsize=7, facecolor="#1a1a1a", labelcolor="#cccccc")

    # ── Volume ──
    vol_colors = ["#26a69a" if df["Close"].iloc[i] >= df["Open"].iloc[i] else "#ef5350"
                  for i in range(len(df))]
    ax3.bar(dates, df["Volume"], color=vol_colors, width=4, alpha=0.8)
    ax3.set_ylabel("Volume", fontsize=8)
    ax3.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x/1e6:.0f}M"))

    ax3.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    ax3.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    plt.xticks(rotation=30, ha="right", color="#cccccc", fontsize=7)

    plt.tight_layout(h_pad=0.3)
    chart_path = f"{output_dir}/{ticker}_chart.png"
    plt.savefig(chart_path, dpi=130, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return chart_path


# ── Main fetch & compute ────────────────────────────────────────────────────

def fetch_technical(ticker: str, output_dir: str) -> dict:
    """Fetch weekly data, compute indicators, save chart. Returns summary dict."""
    try:
        end = date.today()
        start = end - timedelta(weeks=CHART_WEEKS + 50)  # extra for MA200 warmup

        df = yf.download(ticker, start=start, end=end, interval="1wk",
                         progress=False, auto_adjust=True)
        if df.empty or len(df) < 30:
            return {"ticker": ticker, "error": "Insufficient data"}

        # Flatten multi-level columns if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df.index = pd.to_datetime(df.index).date  # strip timezone

        close = df["Close"]

        df["EMA5"]    = compute_ema(close, 5)
        df["EMA20"]   = compute_ema(close, 20)
        df["MA200"]   = compute_sma(close, 200)
        df["RSI"]     = compute_rsi(close, 14)
        df["BB_upper"], df["BB_mid"], df["BB_lower"] = compute_bollinger(close, 20)
        df["MACD"], df["Signal"], df["MACD_hist"]    = compute_macd(close)
        df["ATR"]     = compute_atr(df["High"], df["Low"], close, 14)

        last = df.iloc[-1]
        prev = df.iloc[-2]
        price = float(last["Close"])

        def vs_ma(ma_val):
            if pd.isna(ma_val) or ma_val == 0:
                return None
            return round((price / float(ma_val) - 1) * 100, 1)

        # Volume trend: compare last 4 weeks avg vs prior 4 weeks avg
        vol_recent = df["Volume"].iloc[-4:].mean()
        vol_prior  = df["Volume"].iloc[-8:-4].mean()
        vol_trend  = "rising" if vol_recent > vol_prior * 1.1 else (
                     "falling" if vol_recent < vol_prior * 0.9 else "flat")

        # MACD crossover signal
        macd_signal = "bullish_cross" if (float(last["MACD"]) > float(last["Signal"]) and
                                           float(prev["MACD"]) <= float(prev["Signal"])) else (
                      "bearish_cross" if (float(last["MACD"]) < float(last["Signal"]) and
                                          float(prev["MACD"]) >= float(prev["Signal"])) else (
                      "above_signal" if float(last["MACD"]) > float(last["Signal"]) else "below_signal"))

        # Bollinger position
        bb_width = float(last["BB_upper"]) - float(last["BB_lower"])
        bb_pct = round((price - float(last["BB_lower"])) / bb_width * 100, 1) if bb_width > 0 else None

        # 52-week high/low
        recent = df.tail(52)
        w52_high = float(recent["High"].max())
        w52_low  = float(recent["Low"].min())
        pct_from_high = round((price / w52_high - 1) * 100, 1)
        pct_from_low  = round((price / w52_low  - 1) * 100, 1)

        chart_path = draw_chart(ticker, df, output_dir)

        return {
            "ticker": ticker,
            "price": round(price, 2),
            "ema5":  round(float(last["EMA5"]),  2) if not pd.isna(last["EMA5"])  else None,
            "ema20": round(float(last["EMA20"]), 2) if not pd.isna(last["EMA20"]) else None,
            "ma200": round(float(last["MA200"]), 2) if not pd.isna(last["MA200"]) else None,
            "vs_ema5_pct":  vs_ma(last["EMA5"]),
            "vs_ema20_pct": vs_ma(last["EMA20"]),
            "vs_ma200_pct": vs_ma(last["MA200"]),
            "rsi":   round(float(last["RSI"]), 1) if not pd.isna(last["RSI"]) else None,
            "atr":   round(float(last["ATR"]), 2) if not pd.isna(last["ATR"]) else None,
            "bb_upper": round(float(last["BB_upper"]), 2) if not pd.isna(last["BB_upper"]) else None,
            "bb_lower": round(float(last["BB_lower"]), 2) if not pd.isna(last["BB_lower"]) else None,
            "bb_position_pct": bb_pct,
            "macd_signal": macd_signal,
            "volume_trend": vol_trend,
            "week52_high": round(w52_high, 2),
            "week52_low":  round(w52_low, 2),
            "pct_from_52w_high": pct_from_high,
            "pct_from_52w_low":  pct_from_low,
            "chart_path": chart_path,
        }

    except Exception as e:
        return {"ticker": ticker, "error": str(e)}


def run(tickers: list, output_dir: str) -> dict:
    """Run technical analysis for all tickers and save JSON."""
    print(f"  [technical] Computing {len(tickers)} tickers...")
    results = {}
    for ticker in tickers:
        print(f"    {ticker}...", end=" ", flush=True)
        results[ticker] = fetch_technical(ticker, output_dir)
        print("done")

    out_path = f"{output_dir}/technical.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"  [technical] Saved → {out_path}")
    return results


if __name__ == "__main__":
    today = date.today().isoformat()
    out = f"data/{today}"
    os.makedirs(out, exist_ok=True)
    from config import ALL_TICKERS
    run(ALL_TICKERS, out)
