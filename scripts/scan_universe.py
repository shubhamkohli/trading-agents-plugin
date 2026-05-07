#!/usr/bin/env python3
"""
Scan exchange universes using Yahoo Finance via yfinance.

Examples:
  uv run python scripts/scan_universe.py --exchange TSX --top 25
  uv run python scripts/scan_universe.py --exchange NSE --top 50
  uv run python scripts/scan_universe.py --exchange ALL --top 100

Input files:
  data/universes/tsx.csv
  data/universes/tsxv.csv
  data/universes/neo.csv
  data/universes/cse.csv
  data/universes/nse.csv
  data/universes/bse.csv

CSV columns:
  symbol,name
  SHOP,Shopify Inc

Optional:
  yahoo_ticker
  SHOP.TO

Output:
  .out/universe_scans/<exchange>_<timestamp>.csv
  .out/universe_scans/<exchange>_<timestamp>.json
"""

import argparse
import csv
import json
import math
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yfinance as yf


ROOT = Path(__file__).resolve().parents[1]
EXCHANGE_CONFIG_PATH = ROOT / "data" / "universes" / "exchanges.json"
UNIVERSE_DIR = ROOT / "data" / "universes"
OUTPUT_DIR = ROOT / ".out" / "universe_scans"


@dataclass
class ExchangeConfig:
    code: str
    country: str
    currency: str
    yahoo_suffix: str
    min_market_cap: int
    description: str


def safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        value = float(value)
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    except Exception:
        return None


def safe_round(value: Any, digits: int = 2) -> float | None:
    value = safe_float(value)
    if value is None:
        return None
    return round(value, digits)


def load_exchange_configs() -> dict[str, ExchangeConfig]:
    if not EXCHANGE_CONFIG_PATH.exists():
        raise FileNotFoundError(f"Missing exchange config: {EXCHANGE_CONFIG_PATH}")

    raw = json.loads(EXCHANGE_CONFIG_PATH.read_text(encoding="utf-8"))
    configs: dict[str, ExchangeConfig] = {}

    for code, cfg in raw.items():
        configs[code.upper()] = ExchangeConfig(
            code=code.upper(),
            country=cfg["country"],
            currency=cfg["currency"],
            yahoo_suffix=cfg["yahoo_suffix"],
            min_market_cap=int(cfg["min_market_cap"]),
            description=cfg.get("description", ""),
        )

    return configs


def universe_file_for(exchange: str) -> Path:
    return UNIVERSE_DIR / f"{exchange.lower()}.csv"


def load_universe_rows(exchange: str, cfg: ExchangeConfig) -> list[dict[str, str]]:
    path = universe_file_for(exchange)

    if not path.exists():
        raise FileNotFoundError(
            f"Missing universe file for {exchange}: {path}. "
            f"Create CSV with columns: symbol,name"
        )

    rows: list[dict[str, str]] = []
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        required = {"symbol"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{path} missing required columns: {sorted(missing)}")

        for row in reader:
            symbol = (row.get("symbol") or "").strip()
            if not symbol:
                continue

            yahoo_ticker = (row.get("yahoo_ticker") or "").strip()
            if not yahoo_ticker:
                yahoo_ticker = symbol if "." in symbol else f"{symbol}{cfg.yahoo_suffix}"

            rows.append(
                {
                    "symbol": symbol,
                    "name": (row.get("name") or "").strip(),
                    "exchange": exchange,
                    "yahoo_ticker": yahoo_ticker,
                }
            )

    return rows


def pct_return(series: pd.Series, periods: int) -> float | None:
    if series is None or len(series) <= periods:
        return None

    current = safe_float(series.iloc[-1])
    previous = safe_float(series.iloc[-periods - 1])
    if current is None or previous in (None, 0):
        return None

    return round(((current / previous) - 1) * 100, 2)


def calc_rsi(close: pd.Series, window: int = 14) -> float | None:
    if close is None or len(close) < window + 2:
        return None

    delta = close.diff()
    gain = delta.clip(lower=0).rolling(window).mean()
    loss = (-delta.clip(upper=0)).rolling(window).mean()

    latest_loss = safe_float(loss.iloc[-1])
    latest_gain = safe_float(gain.iloc[-1])

    if latest_gain is None:
        return None
    if latest_loss in (None, 0):
        return 100.0

    rs = latest_gain / latest_loss
    return round(100 - (100 / (1 + rs)), 2)


def fetch_market_cap_and_info(yahoo_ticker: str) -> dict[str, Any]:
    tk = yf.Ticker(yahoo_ticker)

    info: dict[str, Any] = {}
    try:
        info = tk.info or {}
    except Exception:
        info = {}

    market_cap = info.get("marketCap")
    price = info.get("currentPrice") or info.get("regularMarketPrice")
    avg_volume = info.get("averageVolume") or info.get("averageVolume10days")
    sector = info.get("sector")
    industry = info.get("industry")
    short_name = info.get("shortName") or info.get("longName")

    return {
        "market_cap": safe_float(market_cap),
        "price": safe_float(price),
        "avg_volume": safe_float(avg_volume),
        "sector": sector,
        "industry": industry,
        "short_name": short_name,
    }


def fetch_history_metrics(yahoo_ticker: str) -> dict[str, Any]:
    try:
        hist = yf.Ticker(yahoo_ticker).history(period="1y", auto_adjust=True)
    except Exception:
        hist = pd.DataFrame()

    if hist.empty or "Close" not in hist.columns:
        return {
            "last_close": None,
            "return_20d_pct": None,
            "return_50d_pct": None,
            "sma50": None,
            "sma200": None,
            "rsi14": None,
            "avg_volume_20d": None,
            "above_sma50": None,
            "above_sma200": None,
        }

    close = hist["Close"].dropna()
    volume = hist["Volume"].dropna() if "Volume" in hist.columns else pd.Series(dtype=float)

    last_close = safe_float(close.iloc[-1]) if len(close) else None
    sma50 = safe_float(close.rolling(50).mean().iloc[-1]) if len(close) >= 50 else None
    sma200 = safe_float(close.rolling(200).mean().iloc[-1]) if len(close) >= 200 else None
    avg_volume_20d = safe_float(volume.tail(20).mean()) if len(volume) else None

    return {
        "last_close": safe_round(last_close),
        "return_20d_pct": pct_return(close, 20),
        "return_50d_pct": pct_return(close, 50),
        "sma50": safe_round(sma50),
        "sma200": safe_round(sma200),
        "rsi14": calc_rsi(close),
        "avg_volume_20d": safe_round(avg_volume_20d),
        "above_sma50": bool(last_close and sma50 and last_close > sma50),
        "above_sma200": bool(last_close and sma200 and last_close > sma200),
    }


def score_row(row: dict[str, Any]) -> float:
    score = 0.0

    return_20d = safe_float(row.get("return_20d_pct"))
    return_50d = safe_float(row.get("return_50d_pct"))
    rsi14 = safe_float(row.get("rsi14"))
    dollar_volume = safe_float(row.get("dollar_volume"))

    if row.get("above_sma50"):
        score += 15
    if row.get("above_sma200"):
        score += 15

    if return_20d is not None:
        score += max(min(return_20d, 25), -25) * 0.8

    if return_50d is not None:
        score += max(min(return_50d, 40), -40) * 0.6

    if rsi14 is not None:
        if 45 <= rsi14 <= 70:
            score += 10
        elif 70 < rsi14 <= 80:
            score += 3
        elif rsi14 > 80:
            score -= 5
        elif rsi14 < 35:
            score -= 5

    if dollar_volume is not None:
        if dollar_volume >= 10_000_000:
            score += 15
        elif dollar_volume >= 1_000_000:
            score += 8
        elif dollar_volume >= 250_000:
            score += 3
        else:
            score -= 5

    return round(score, 2)


def scan_exchange(exchange: str, cfg: ExchangeConfig, top: int, sleep_seconds: float) -> list[dict[str, Any]]:
    print(f"Scanning {exchange}: {cfg.description}")
    rows = load_universe_rows(exchange, cfg)
    print(f"Loaded {len(rows)} raw symbols for {exchange}")

    results: list[dict[str, Any]] = []

    for idx, base in enumerate(rows, start=1):
        yahoo_ticker = base["yahoo_ticker"]

        try:
            info = fetch_market_cap_and_info(yahoo_ticker)
            market_cap = info["market_cap"]

            if market_cap is None or market_cap < cfg.min_market_cap:
                print(f"[{idx}/{len(rows)}] SKIP {yahoo_ticker}: market_cap={market_cap}")
                continue

            hist_metrics = fetch_history_metrics(yahoo_ticker)

            price = info["price"] or hist_metrics["last_close"]
            avg_volume = hist_metrics["avg_volume_20d"] or info["avg_volume"]
            dollar_volume = None
            if price is not None and avg_volume is not None:
                dollar_volume = price * avg_volume

            result = {
                "exchange": exchange,
                "symbol": base["symbol"],
                "yahoo_ticker": yahoo_ticker,
                "name": base["name"] or info["short_name"],
                "currency": cfg.currency,
                "market_cap": round(market_cap),
                "min_market_cap": cfg.min_market_cap,
                "price": safe_round(price),
                "avg_volume": safe_round(avg_volume),
                "dollar_volume": safe_round(dollar_volume),
                "sector": info["sector"],
                "industry": info["industry"],
                **hist_metrics,
            }
            result["score"] = score_row(result)

            print(
                f"[{idx}/{len(rows)}] KEEP {yahoo_ticker}: "
                f"market_cap={result['market_cap']} score={result['score']}"
            )
            results.append(result)

        except Exception as e:
            print(f"[{idx}/{len(rows)}] ERROR {yahoo_ticker}: {e}")

        if sleep_seconds > 0:
            time.sleep(sleep_seconds)

    results.sort(key=lambda x: (x.get("score") or 0), reverse=True)
    return results[:top]


def write_outputs(exchange: str, rows: list[dict[str, Any]]) -> tuple[Path, Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    stem = f"{exchange.lower()}_{timestamp}"

    csv_path = OUTPUT_DIR / f"{stem}.csv"
    json_path = OUTPUT_DIR / f"{stem}.json"

    pd.DataFrame(rows).to_csv(csv_path, index=False)
    json_path.write_text(json.dumps(rows, indent=2, default=str), encoding="utf-8")

    return csv_path, json_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exchange", required=True, help="TSX, TSXV, NEO, CSE, NSE, BSE, or ALL")
    parser.add_argument("--top", type=int, default=50)
    parser.add_argument("--sleep", type=float, default=0.1, help="Seconds to sleep between tickers")
    args = parser.parse_args()

    configs = load_exchange_configs()
    requested = args.exchange.upper()

    if requested == "ALL":
        exchanges = list(configs.keys())
    else:
        if requested not in configs:
            raise ValueError(f"Unknown exchange {requested}. Available: {sorted(configs)}")
        exchanges = [requested]

    all_results: list[dict[str, Any]] = []

    for exchange in exchanges:
        results = scan_exchange(exchange, configs[exchange], args.top, args.sleep)
        csv_path, json_path = write_outputs(exchange, results)
        print(f"Wrote {csv_path}")
        print(f"Wrote {json_path}")
        all_results.extend(results)

    if requested == "ALL":
        all_results.sort(key=lambda x: (x.get("score") or 0), reverse=True)
        all_results = all_results[: args.top]
        csv_path, json_path = write_outputs("ALL", all_results)
        print(f"Wrote combined {csv_path}")
        print(f"Wrote combined {json_path}")

    print("\nTop results:")
    if all_results:
        display_cols = [
            "exchange",
            "yahoo_ticker",
            "name",
            "market_cap",
            "price",
            "return_20d_pct",
            "return_50d_pct",
            "dollar_volume",
            "score",
        ]
        print(pd.DataFrame(all_results)[display_cols].head(args.top).to_string(index=False))
    else:
        print("No symbols passed the filters.")


if __name__ == "__main__":
    main()