import json
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)

# Standard Yahoo Finance suffixes based on the user's provided requirements
EXCHANGES: Dict[str, dict] = {
    "TSX": {
        "country": "Canada",
        "currency": "CAD",
        "yahoo_suffix": ".TO",
        "min_market_cap": 50000000,
        "description": "Toronto Stock Exchange (>= $50M CAD)"
    },
    "TSXV": {
        "country": "Canada",
        "currency": "CAD",
        "yahoo_suffix": ".V",
        "min_market_cap": 50000000,
        "description": "TSX Venture Exchange (>= $50M CAD)"
    },
    "NEO": {
        "country": "Canada",
        "currency": "CAD",
        "yahoo_suffix": ".NE",
        "min_market_cap": 50000000,
        "description": "Cboe Canada / NEO (>= $50M CAD)"
    },
    "CSE": {
        "country": "Canada",
        "currency": "CAD",
        "yahoo_suffix": ".CN",
        "min_market_cap": 50000000,
        "description": "Canadian Securities Exchange (>= $50M CAD)"
    },
    "NSE": {
        "country": "India",
        "currency": "INR",
        "yahoo_suffix": ".NS",
        "min_market_cap": 1000000000,
        "description": "National Stock Exchange of India (>= ₹100 crore)"
    },
    "BSE": {
        "country": "India",
        "currency": "INR",
        "yahoo_suffix": ".BO",
        "min_market_cap": 1000000000,
        "description": "Bombay Stock Exchange (>= ₹100 crore)"
    }
}

def format_ticker_for_yahoo(ticker: str) -> str:
    """
    Parses an exchange-prefixed ticker (e.g., TSX:SHOP) and appends the correct
    Yahoo Finance suffix (e.g., SHOP.TO). If no known exchange prefix is found,
    returns the original ticker.
    """
    if ":" in ticker:
        parts = ticker.split(":", 1)
        exchange = parts[0].upper()
        symbol = parts[1].upper()

        if exchange in EXCHANGES:
            suffix = EXCHANGES[exchange]["yahoo_suffix"]
            formatted_ticker = f"{symbol}{suffix}"
            logger.debug(f"Formatted {ticker} -> {formatted_ticker} for Yahoo Finance")
            return formatted_ticker

    return ticker.upper()

def get_exchange_info(exchange_code: str) -> Optional[dict]:
    """Returns metadata for the given exchange code."""
    return EXCHANGES.get(exchange_code.upper())
