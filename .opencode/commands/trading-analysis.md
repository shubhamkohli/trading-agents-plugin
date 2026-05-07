
---
name: trading-analysis
description: Multi-agent trading analysis for a stock ticker (OpenCode compatible).
---

You are running inside OpenCode.

Extract the ticker symbol from $ARGUMENTS (e.g. "NVDA").
If no ticker is provided, ask the user for one before proceeding.

Set TODAY to the current date in YYYY-MM-DD format.

You have access to:
- The local repository
- Python via `uv`
- No hardcoded absolute paths

All data fetches MUST use relative paths from the repo root.

---

## Phase 1 — Data Collection (Deterministic)

Run the following commands:

### Technical
```bash
uv run python scripts/fetch_market_data.py --ticker $TICKER --type technical --date $TODAY
```

### News
```bash
uv run python scripts/fetch_market_data.py --ticker $TICKER --type news --date $TODAY
```

### Fundamentals
```bash
uv run python scripts/fetch_market_data.py --ticker $TICKER --type fundamentals --date $TODAY
```

### Macro
```bash
uv run python scripts/fetch_market_data.py --ticker $TICKER --type macro --date $TODAY
```
