import json
from datetime import date
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from scripts.fetch_market_data import (
    _safe,
    fetch_fundamentals,
    fetch_macro,
    fetch_news,
    fetch_technical,
    main,
)

def test_safe():
    assert _safe(10.555) == 10.56
    assert _safe("10.555") == 10.56
    assert _safe(float("nan")) is None
    assert _safe(float("inf")) is None
    assert _safe("not a number") is None
    assert _safe(None) is None

@patch("yfinance.Ticker")
def test_fetch_technical_empty(mock_ticker):
    mock_instance = MagicMock()
    mock_instance.history.return_value = pd.DataFrame()
    mock_ticker.return_value = mock_instance

    result = fetch_technical("AAPL", date(2023, 1, 1))
    assert "error" in result
    assert "No price data for AAPL" in result["error"]

@patch("yfinance.Ticker")
def test_fetch_technical_success(mock_ticker):
    mock_instance = MagicMock()
    # Need enough data for indicators
    # SMA200 needs 200, 52w high/low needs 252. We'll provide 300.
    dates = pd.date_range(start="2022-01-01", periods=300)
    df = pd.DataFrame(
        {
            "Close": [100.0 + i for i in range(300)],
            "Volume": [1000] * 300,
            "High": [105.0 + i for i in range(300)],
            "Low": [95.0 + i for i in range(300)],
        },
        index=dates,
    )
    mock_instance.history.return_value = df
    mock_ticker.return_value = mock_instance

    as_of = date(2023, 1, 1)
    result = fetch_technical("AAPL", as_of)

    assert result["ticker"] == "AAPL"
    assert result["as_of"] == as_of.isoformat()
    assert "price" in result
    assert "indicators" in result
    assert result["price"]["current"] == 399.0  # 100 + 299
    assert result["price"]["52w_high"] is not None
    assert result["indicators"]["sma50"] is not None

@patch("yfinance.Ticker")
def test_fetch_news(mock_ticker):
    mock_instance = MagicMock()
    mock_instance.news = [
        {
            "content": {
                "title": "News Title",
                "summary": "News Summary",
                "provider": {"displayName": "Publisher"},
            }
        }
    ]
    mock_ticker.return_value = mock_instance

    result = fetch_news("AAPL", date(2023, 1, 1))
    assert result["ticker"] == "AAPL"
    assert result["news_count"] == 1
    assert result["items"][0]["title"] == "News Title"
    assert result["items"][0]["publisher"] == "Publisher"

@patch("yfinance.Ticker")
def test_fetch_macro(mock_ticker):
    mock_instance = MagicMock()
    mock_instance.news = [
        {"content": {"title": "Macro News", "summary": "Summary", "provider": {"displayName": "Source"}}}
    ]
    mock_ticker.return_value = mock_instance

    result = fetch_macro(date(2023, 1, 1))
    assert result["as_of"] == "2023-01-01"
    assert result["macro_news_count"] > 0
    assert len(result["items"]) > 0
    assert result["items"][0]["title"] == "Macro News"

@patch("yfinance.Ticker")
def test_fetch_fundamentals(mock_ticker):
    mock_instance = MagicMock()
    mock_instance.info = {"marketCap": 1000000.0, "sector": "Technology"}
    # Mocking quarterly statements which are DataFrames
    income_stmt = pd.DataFrame({pd.Timestamp("2022-12-31"): [100.0]}, index=["Total Revenue"])
    mock_instance.quarterly_income_stmt = income_stmt
    mock_instance.quarterly_balance_sheet = pd.DataFrame()
    mock_instance.quarterly_cashflow = pd.DataFrame()
    mock_ticker.return_value = mock_instance

    result = fetch_fundamentals("AAPL", date(2023, 1, 1))
    assert result["ticker"] == "AAPL"
    assert result["marketCap"] == 1000000.0
    assert "quarterly_income_stmt" in result
    assert "2022-12-31" in result["quarterly_income_stmt"]
    assert result["quarterly_income_stmt"]["2022-12-31"]["Total Revenue"] == 100.0

@patch("scripts.fetch_market_data.fetch_technical")
@patch("sys.argv", ["fetch_market_data.py", "--ticker", "AAPL", "--type", "technical", "--date", "2023-01-01"])
def test_main(mock_fetch):
    mock_fetch.return_value = {"success": True}
    with patch("builtins.print") as mock_print:
        main()
        mock_print.assert_called_once()
        args, _ = mock_print.call_args
        printed_json = json.loads(args[0])
        assert printed_json["success"] is True

@patch("scripts.fetch_market_data.fetch_technical")
@patch("sys.argv", ["fetch_market_data.py", "--ticker", "AAPL", "--type", "technical", "--date", "2023-01-01"])
def test_main_error(mock_fetch):
    mock_fetch.side_effect = Exception("Test Error")
    with patch("builtins.print") as mock_print:
        main()
        mock_print.assert_called_once()
        args, _ = mock_print.call_args
        printed_json = json.loads(args[0])
        assert "error" in printed_json
        assert printed_json["error"] == "Test Error"
