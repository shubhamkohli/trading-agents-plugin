import asyncio
import json
import logging
import os
import argparse
from datetime import date

from dotenv import load_dotenv
from litellm import acompletion

from scripts.fetch_market_data import (
    fetch_technical,
    fetch_news,
    fetch_fundamentals,
    fetch_macro
)

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# Default model, can be overridden via litellm mechanics or env vars
MODEL = os.getenv("MODEL", "gpt-4o")

def get_today_str() -> str:
    return date.today().isoformat()

async def run_agent(system_prompt: str, user_prompt: str = "") -> str:
    """Wrapper to run a simple LLM completion via LiteLLM."""
    messages = [{"role": "system", "content": system_prompt}]
    if user_prompt:
        messages.append({"role": "user", "content": user_prompt})

    response = await acompletion(
        model=MODEL,
        messages=messages,
    )
    return response.choices[0].message.content.strip()

async def run_technical_analyst(ticker: str, as_of: str) -> str:
    logging.info(f"Running Technical Analyst for {ticker}...")
    data = fetch_technical(ticker, date.fromisoformat(as_of))
    data_str = json.dumps(data, indent=2, default=str)
    prompt = f"""You are a technical analyst for {ticker} as of {as_of}.

Data:
{data_str}

Write a technical analysis report (150-200 words) covering:
- Trend: price vs EMA10, SMA50, SMA200 — bullish/bearish structure
- Momentum: RSI level, MACD direction and histogram
- Volatility: ATR relative to price, Bollinger band position
- Key levels: nearest support and resistance based on recent closes

End with exactly: TECHNICAL SIGNAL: BULLISH, BEARISH, or NEUTRAL"""
    return await run_agent(prompt)

async def run_news_analyst(ticker: str, as_of: str) -> str:
    logging.info(f"Running News Analyst for {ticker}...")
    data = fetch_news(ticker, date.fromisoformat(as_of))
    data_str = json.dumps(data, indent=2, default=str)
    prompt = f"""You are a news and sentiment analyst for {ticker} as of {as_of}.

Data:
{data_str}

Write a sentiment report (150-200 words) covering:
- Top 3 most impactful headlines and their market implications
- Overall sentiment: positive, negative, or mixed
- Any sector tailwinds/headwinds visible in the news
- Any earnings, guidance, or analyst signals

End with exactly: SENTIMENT SIGNAL: POSITIVE, NEGATIVE, or NEUTRAL"""
    return await run_agent(prompt)

async def run_fundamentals_analyst(ticker: str, as_of: str) -> str:
    logging.info(f"Running Fundamentals Analyst for {ticker}...")
    data = fetch_fundamentals(ticker, date.fromisoformat(as_of))
    data_str = json.dumps(data, indent=2, default=str)
    prompt = f"""You are a fundamentals analyst for {ticker} as of {as_of}.

Data:
{data_str}

Write a fundamentals report (200-250 words) covering:
- Valuation: trailing P/E, forward P/E, PEG ratio (forward PE / earnings growth), P/B vs sector norms
- Growth: revenue growth, earnings growth trajectory
- Quality: gross/operating margins, ROE, free cash flow
- Balance sheet: total debt, total cash, D/E ratio (totalDebt / (totalDebt + stockholders equity)), current ratio
- Risk metrics: beta, short ratio
- Quarterly financials: cite 1-2 key line items from quarterly_income_stmt and quarterly_balance_sheet (e.g. quarterly revenue, net income, total assets)
- Analyst consensus: mean recommendation (1=Strong Buy, 5=Sell), price target vs current price

End with exactly: FUNDAMENTAL SIGNAL: STRONG, FAIR, or WEAK"""
    return await run_agent(prompt)

async def run_macro_analyst(as_of: str) -> str:
    logging.info(f"Running Macro Analyst as of {as_of}...")
    data = fetch_macro(date.fromisoformat(as_of))
    data_str = json.dumps(data, indent=2, default=str)
    prompt = f"""You are a macro analyst providing global market context as of {as_of}.

Data:
{data_str}

Write a macro context report (100-150 words) covering:
- Key macro themes visible in S&P 500, Treasury yield, oil, and gold news
- Any geopolitical, monetary policy, or economic signals that could affect equities
- Overall macro environment: risk-on, risk-off, or neutral

End with exactly: MACRO SIGNAL: RISK-ON, RISK-OFF, or NEUTRAL"""
    return await run_agent(prompt)

async def run_bull_analyst(ticker: str, tech: str, news: str, fund: str, macro: str) -> str:
    logging.info("Running Bull Analyst...")
    prompt = f"""You are a Bull Analyst advocating for investing in {ticker}. Your task is to build
a strong, evidence-based case emphasizing growth potential, competitive advantages,
and positive market indicators.

Key points to focus on:
- Growth Potential: Highlight market opportunities, revenue projections, and scalability.
- Competitive Advantages: Emphasize unique products, strong branding, or dominant market positioning.
- Positive Indicators: Use financial health, industry trends, and recent positive news as evidence.
- Engagement: Present your argument conversationally. Be direct and confident.

Resources available:

TECHNICAL REPORT:
{tech}

NEWS REPORT:
{news}

MACRO REPORT:
{macro}

FUNDAMENTALS REPORT:
{fund}

Write 150-200 words. Use specific data points from the reports above.

End with exactly: BULL CONVICTION: HIGH, MEDIUM, or LOW"""
    return await run_agent(prompt)

async def run_bear_analyst(ticker: str, tech: str, news: str, fund: str, macro: str, bull: str) -> str:
    logging.info("Running Bear Analyst...")
    prompt = f"""You are a Bear Analyst making the case against investing in {ticker}. Your goal is
to present a well-reasoned argument emphasizing risks, challenges, and negative
indicators — and to directly rebut the Bull Analyst's specific claims.

Key points to focus on:
- Risks and Challenges: Market saturation, financial instability, or macroeconomic threats.
- Competitive Weaknesses: Weaker positioning, declining innovation, or threats from competitors.
- Negative Indicators: Use financial data, market trends, or adverse news.
- Macro Risks: Use the macro report to identify broader market headwinds.
- Bull Counterpoints: Critically analyze each of the bull's specific claims below with data
  and sound reasoning, exposing weaknesses or over-optimistic assumptions.
- Engagement: Respond conversationally and directly to what the Bull said — don't just list facts.

Resources available:

TECHNICAL REPORT:
{tech}

NEWS REPORT:
{news}

MACRO REPORT:
{macro}

FUNDAMENTALS REPORT:
{fund}

BULL ANALYST'S ARGUMENT (respond to this directly):
{bull}

Write 150-200 words. Rebut the bull's specific arguments using data from the reports.

End with exactly: BEAR CONVICTION: HIGH, MEDIUM, or LOW"""
    return await run_agent(prompt)

async def run_risk_analyst(fund: str, macro: str, bull: str, bear: str) -> str:
    logging.info("Running Risk Analyst...")
    prompt = f"""You are a conservative Risk Analyst. Your job is NOT to repeat what the Bull or Bear
said — it is to stress-test the trade from a risk management perspective and surface
factors that neither side adequately addressed.

Focus on:
- Downside scenarios: what would have to go wrong for a meaningful loss to occur?
- Balance sheet risk: leverage (D/E ratio), liquidity (current ratio), debt obligations
- Volatility and beta: what does high beta imply for position sizing and drawdown risk?
- Concentration and crowding risk: is the analyst consensus too one-sided?
- Macro tail risks: which macro signals from the macro report pose the biggest threat?
- Any risk the Bull and Bear both glossed over

Resources available:

FUNDAMENTALS REPORT:
{fund}

MACRO REPORT:
{macro}

BULL ARGUMENT:
{bull}

BEAR ARGUMENT:
{bear}

Write 150-200 words. Be specific — cite numbers (beta, D/E, short ratio, yield levels).
Do not simply side with the bear. Raise risks that neither analyst addressed.

End with exactly: RISK LEVEL: HIGH, MEDIUM, or LOW"""
    return await run_agent(prompt)

async def run_research_manager(bull: str, bear: str, risk: str) -> str:
    logging.info("Running Research Manager...")
    prompt = f"""You are now the Research Manager and debate facilitator. Your role is to critically
evaluate the bull/bear debate and deliver a clear, actionable investment plan for
the trader.

**Rating Scale** (use exactly one):
- **Buy**: Strong conviction in the bull thesis; recommend taking or growing the position
- **Overweight**: Constructive view; recommend gradually increasing exposure
- **Hold**: Balanced view; recommend maintaining the current position
- **Underweight**: Cautious view; recommend trimming exposure
- **Sell**: Strong conviction in the bear thesis; recommend exiting or avoiding the position

Commit to a clear stance whenever the debate's strongest arguments warrant one;
reserve Hold for situations where the evidence on both sides is genuinely balanced.

**Debate to evaluate:**

BULL ANALYST:
{bull}

BEAR ANALYST:
{bear}

RISK ANALYST:
{risk}

Output your investment plan in this format:
RECOMMENDATION: [Buy / Overweight / Hold / Underweight / Sell]

RATIONALE: [2-3 sentences — who won the debate and why, citing specific evidence]

STRATEGIC ACTIONS: [2-3 sentences — what the trader should specifically do: entry approach, sizing, conditions to watch]"""
    return await run_agent(prompt)

async def run_trader(plan: str, tech: str) -> str:
    logging.info("Running Trader...")
    prompt = f"""You are a Trader converting the Research Manager's plan into a concrete transaction proposal.
Anchor your reasoning in the analyst reports and the investment plan. Be specific on price levels.

INVESTMENT PLAN FROM RESEARCH MANAGER:
{plan}

TECHNICAL REPORT (for price levels):
{tech}

Output your transaction proposal in this format:
ACTION: [Buy / Hold / Sell]

REASONING: [2-3 sentences anchored in the reports — why this action, why now]

ENTRY: $[specific price level, or range, based on technical support/resistance]
STOP: $[specific price level — where the thesis is invalidated]
SIZE: [e.g. "3-5% of portfolio, add in 2 tranches" or "maintain current position"]"""
    return await run_agent(prompt)

async def run_portfolio_manager(ticker: str, as_of: str, plan: str, trader: str, bull: str, bear: str, risk: str) -> str:
    logging.info("Running Portfolio Manager...")
    prompt = f"""You are now the Portfolio Manager. Synthesize all inputs and deliver the final decision.

RESEARCH MANAGER'S PLAN:
{plan}

TRADER'S PROPOSAL:
{trader}

BULL ARGUMENT:
{bull}

BEAR ARGUMENT:
{bear}

RISK ANALYST:
{risk}

Output the final decision in this EXACT format:

TICKER: {ticker}
DATE: {as_of}
SIGNAL: [BUY / SELL / HOLD]
RATING: [Overweight / Equal Weight / Underweight]
ENTRY: $[price from Trader]
STOP: $[price from Trader]
SIZE: [sizing from Trader]

BULL: [one sentence — the single strongest bull argument]
BEAR: [one sentence — the single strongest bear argument]
VERDICT: [2-3 sentences — why the bull or bear case won and what specifically to do]"""
    return await run_agent(prompt)

async def main():
    parser = argparse.ArgumentParser(description="Multi-Agent Trading Analysis Pipeline")
    parser.add_argument("ticker", type=str, help="The stock ticker to analyze (e.g., NVDA, TSX:SHOP)")
    parser.add_argument("--date", type=str, default=get_today_str(), help="Date in YYYY-MM-DD format")
    args = parser.parse_args()

    ticker = args.ticker
    as_of = args.date

    logging.info(f"Starting analysis for {ticker} as of {as_of}")

    # Phase 1: Parallel Data Analysis
    tech_task = asyncio.create_task(run_technical_analyst(ticker, as_of))
    news_task = asyncio.create_task(run_news_analyst(ticker, as_of))
    fund_task = asyncio.create_task(run_fundamentals_analyst(ticker, as_of))
    macro_task = asyncio.create_task(run_macro_analyst(as_of))

    tech_report, news_report, fund_report, macro_report = await asyncio.gather(
        tech_task, news_task, fund_task, macro_task
    )

    # Phase 2: Adversarial Bull/Bear Debate + Risk
    bull_report = await run_bull_analyst(ticker, tech_report, news_report, fund_report, macro_report)
    bear_report = await run_bear_analyst(ticker, tech_report, news_report, fund_report, macro_report, bull_report)
    risk_report = await run_risk_analyst(fund_report, macro_report, bull_report, bear_report)

    # Phase 3: Research Manager
    research_plan = await run_research_manager(bull_report, bear_report, risk_report)

    # Phase 4: Trader
    trader_proposal = await run_trader(research_plan, tech_report)

    # Phase 5: Portfolio Manager
    pm_decision = await run_portfolio_manager(
        ticker, as_of, research_plan, trader_proposal, bull_report, bear_report, risk_report
    )

    print("\n" + "="*50)
    print("FINAL PORTFOLIO MANAGER DECISION")
    print("="*50)
    print(pm_decision)
    print("="*50)

if __name__ == "__main__":
    asyncio.run(main())
