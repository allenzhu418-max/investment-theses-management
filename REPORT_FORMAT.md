# Report Format — Daily Research Brief

This file defines the exact structure Claude uses when generating the daily research report.
It ensures every session produces a consistent, comparable output.

---

## How to Trigger a Report

1. Paste today's coach screenshot into Claude Code
2. Say: "Generate today's research report"

Claude will:
- Extract and save the coach's Chinese text to `data/[date]/coach.txt`
- Run `python run_analysis.py` to fetch all data
- Read all JSON outputs from `data/[date]/`
- Write the report to `reports/research_[date].md`
- Commit and push to GitHub

---

## Report Structure

### File: `reports/research_[YYYY-MM-DD].md`

---

```
---
date: YYYY-MM-DD
tickers_covered: [list]
coach_guidance: yes/no
data_sources: [yfinance, rss]
generated_by: claude-sonnet-4-6
---

# Daily Research Brief — [Date]

## Session Summary

### Macro Environment
[3-4 sentences on macro context drawn from VIX, SPY, SMH, SOXX, XLK, TNX, DXY data]
- VIX: [level] ([risk label]) · WoW: [%]
- SPY: [trend vs 20EMA/200MA]
- SMH / SOXX: [semis sector health, note if they diverge]
- TNX: [yield level and direction — rising/falling]

### Coach Guidance Summary
[2-3 sentences summarising the coach's overall market view for today]
> 「[most relevant Chinese quote]」

Tickers mentioned by coach: [list]
Sectors flagged: [list]

---

## Holdings

[One section per holding, in this order: NVDA, MU, SOXL, MRVL, APH, VST, MO, WMT, PDD, DAL]

---

### [TICKER] — [Full Company Name]
**[Sector]** | [One-line description from config]

#### Coach Signal
[If coach mentioned this ticker or its sector:]
> 「[exact Chinese quote]」
**Signal: [Constructive / Cautious / Neutral / Not mentioned]**
[1-2 sentences on how coach's view applies to this specific stock]

[If not mentioned:]
*Coach guidance today does not specifically address [TICKER] or its sector.*

#### Macro Relevance
[1 sentence: how today's macro environment (VIX, rates, sector trend) affects this stock specifically]

#### Fundamentals
[Compact 2-3 line summary — NOT a table dump. Lead with what matters most.]
P/E [x] · Fwd P/E [x] · Rev growth [%] YoY · [Gross/Op] margin [%]
Analyst target: $[mean] ([+/-%] upside) · [N] analysts · Rec: [Buy/Hold/Sell]
[One sentence on balance sheet health or notable metric if relevant]

#### Technical
![TICKER chart](../data/[date]/[TICKER]_chart.png)

Price $[x] · 5EMA $[x] · 20EMA $[x] · 200MA $[x]
RSI [x] ([overbought >70 / oversold <30 / neutral]) · MACD: [signal]
BB position: [x]% ([compressed / mid / extended]) · ATR $[x]
[1-2 sentences interpreting the technical picture — trend direction, key level to watch]

#### Key Levels
Resistance: $[x] · $[x] · $[x]    ← nearest levels above price (swing highs, BB upper, 52w high)
Support:    $[x] · $[x] · $[x]    ← nearest levels below price (swing lows, EMAs, BB lower, 52w low)
[1 sentence: what the nearest resistance and support mean in plain English — e.g. "The $216 level
is the prior swing high and 52-week high; a clean break above it puts the stock in new high territory.
The first support is the 20 EMA at $187 — a pullback there would be healthy without breaking the trend."]

#### News (last 48h)
[List up to 5 headlines. If no relevant news: "No significant news in the past 48 hours."]
- [Headline] — [Source], [time ago]

#### Risk Flags
[List only real flags — don't pad with low-signal items]
[Use ⚠ for active flags, ℹ for standing notes]
⚠ Earnings in [N] days ([date])          [if < 30 days]
⚠ [Drawdown flag if > 15% from recent high]
⚠ [Correlation cluster note if relevant]
ℹ Beta [x] · Short interest [x]%
ℹ [SOXL leveraged ETF note — always shown for SOXL]
ℹ [PDD geopolitical note — always shown for PDD]

#### Thesis Check
[Read thesis/[TICKER].md before writing this section]

**Status: [✓ Intact / ⚠ Monitor / ✗ Challenged]**

[2-4 sentences evaluating whether today's data — fundamentals, technical, news, risk — supports
or contradicts the stored thesis. Be specific: reference the proof metrics and exit criteria
written in the thesis file. Do not restate the whole thesis — just evaluate it against today's data.]

[If thesis status is ⚠ Monitor or ✗ Challenged, add:]
**What changed:** [The specific data point or event that triggered the flag]
**What to watch next:** [The next data point or event that will clarify whether this is noise or a trend]

#### Overall Picture
[3-5 sentences of neutral synthesis. What does the totality of data say?
No buy/sell language. Describe what the data shows, what the key tension is,
what would change the picture. This is the section I write with most care.]

---

[Repeat for each holding]

---

## Watchlist

[Same format as holdings, including Thesis Check. Order: SNDK, AMAT, LITE, COHR, AAOI]
[For watchlist, replace Overall Picture ending with:]
**Entry consideration:** [Reference the entry conditions in thesis/[TICKER].md.
Are any of those conditions closer to being met today? What would need to happen?]

---

## Appendix: Raw Data Reference
- Fundamentals: `data/[date]/fundamentals.json`
- Technical: `data/[date]/technical.json`
- News: `data/[date]/news.json`
- Risk: `data/[date]/risk.json`
- Coach guidance: `data/[date]/coach.txt`
```

---

## Tone and Style Guidelines

- **English** for all analysis, data interpretation, and synthesis
- **Chinese** preserved verbatim for coach quotes — never translate, never paraphrase
- **No buy/sell recommendations** — describe what the data shows, not what to do
- **Concise over comprehensive** — 3 precise sentences beat 8 vague ones
- **Lead with signal, not noise** — if there's nothing meaningful to say about news, say so in one line
- **Specific over general** — "$196, sitting at 68% of Bollinger Band width" not "price looks elevated"
- **Risk flags are real flags** — don't list beta as a risk flag for a low-beta stock just to fill the section

## Consistency Rules

- Always use the same section order every day — this makes week-over-week comparison easy
- Chart images use relative paths so reports render correctly in Obsidian
- Every report has the YAML frontmatter block — this enables future scripted analysis
- Coach quotes are always in `「」` brackets to distinguish from English text

---

## On Historical Accuracy

Every report is **immutable once committed to git**.
If data was wrong on a given day (e.g. yfinance returned a stale price), note it inline but do not retroactively edit the file.
The git history is the audit trail — it proves what was said and when.
