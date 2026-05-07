# AGENTS.md

## Project

Multi-agent trading analysis plugin for Claude Code & OpenCode. 9 LLM subagents in a 5-phase pipeline → BUY/SELL/HOLD decision. Market data via `yfinance` (free, no API key).

## Setup

```bash
uv sync
```
Python >= 3.10. No linter, formatter, typechecker, or test suite configured.

## Key Commands

```
uv run python scripts/fetch_market_data.py --ticker NVDA --type technical
uv run python scripts/fetch_market_data.py --ticker NVDA --type news
uv run python scripts/fetch_market_data.py --ticker NVDA --type fundamentals
uv run python scripts/fetch_market_data.py --ticker MACRO --type macro

uv run python scripts/scan_universe.py --exchange TSX --top 25
uv run python scripts/scan_universe.py --exchange ALL --top 100
```

Verify changes by running the data fetcher manually.

## Architecture

9 agents in 5 phases — preserved order matters when editing prompts:

| Phase | Agents | Execution |
|-------|--------|-----------|
| 1 | Technical, News, Fundamentals, Macro | Parallel |
| 2 | Bull → Bear (rebuts Bull) → Risk | Sequential |
| 3 | Research Manager | — |
| 4 | Trader (entry/stop/sizing) | — |
| 5 | Portfolio Manager (BUY/SELL/HOLD) | — |

Three copies of the pipeline prompt exist (currently near-identical):
- `commands/trading-analysis.md` — Claude Code slash command
- `.claude/commands/trading-analysis.md` — Claude Code internal copy
- `.opencode/commands/trading-analysis.md` — **canonical OpenCode version** (uses relative paths, no hardcoded routes)
- `skills/trading-analysis/SKILL.md` — skill definition

## Gotchas

- **No tests, no CI, no pre-commit.** Manual verification only.
- **`.opencode/package.json`** is gitignored — local shim for `@opencode-ai/plugin`.