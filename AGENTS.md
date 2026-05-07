
# AGENTS.md

## Project

This repository.py` fetches market, news, fundamentals, and macro data using `yfinance`.This repository is `trading-agents-plugin`, a multi-agent trading analysis plugin originally designed for Claude Code slash commands.
- `commands/trading-analysis.md` contains the original Claude Code slash command prompt.
- `.claude/commands/trading-analysis.md` mirrors the Claude command.
- `skills/trading-analysis/` contains plugin skill content.
- The project uses Python 3.10+ and `uv`.

## OpenCode Migration Goals

1. Remove hardcoded author-specific paths.
2. Make command examples portable across Windows, macOS, and Linux.
3. Add OpenCode-compatible command documentation.
4. Keep Claude Code compatibility unless explicitly changing it.
5. Prefer small, reviewable changes.
6. Add tests before large refactors.
7. Keep market-data fetching deterministic where possible.
8. Make output structured and easy to validate.

## Development Rules

- Do not introduce paid LLM API dependencies for core market-data fetching.
- Do not remove the existing Claude command unless a replacement exists.
- Do not hardcode local machine paths.
- Use relative paths from the repository root whenever possible.
- Prefer `uv run python scripts/fetch_market_data.py ...` for examples.
- Keep Windows PowerShell compatibility in documentation.
- Keep Bash/macOS/Linux examples where useful.
- Avoid broad rewrites unless requested.
- When editing prompts, preserve the 7-agent pipeline:
  1. Technical Analyst
  2. News & Sentiment Analyst
  3. Fundamentals Analyst
  4. Macro Analyst
  5. Bull Analyst
  6. Bear Analyst
  7. Risk Analyst
  followed by Research Manager, Trader, and Portfolio Manager.

## Financial Safety

This project produces educational trading analysis, not personalized financial advice.

Every final user-facing trading output should include or imply:

- This is not financial advice.
- Users should verify data independently.
- Position sizing and risk controls are required.
- Market data can be delayed, incomplete, or inaccurate.

## Testing

Before claiming a change works, run:

```powershell
uv run python scripts\fetch_market_data.py --ticker NVDA --type technical
uv run python scripts\fetch_market_data.py --ticker NVDA --type news
uv run python scripts\fetch_market_data.py --ticker NVDA --type fundamentals
uv run python scripts\fetch_market_data.py --ticker MACRO --type macro

The goal of this adoption branch is to make the project work well with OpenCode and Zed while preserving compatibility with the existing Claude Code plugin structure.


## Current Architecture

- `scripts/fetch_market_data.py` fetches market, news, fundamentals, and macro data using `yfinance`.
- `commands/trading-analysis.md` contains the original Claude Code slash command prompt.
- `.claude/commands/trading-analysis.md` mirrors the Claude command.
- `skills/trading-analysis/` contains plugin skill content.
- The project uses Python 3.10+ and `uv`.
