from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd
import yfinance as yf


MIN_HISTORY_ROWS = 2


def fetch_daily_prices(tickers: list[str], lookback_days: int) -> dict[str, pd.DataFrame]:
    if not tickers:
        raise ValueError("At least one ticker is required.")

    raw = _download(tickers, lookback_days, threads=True)
    prices = _split_download(raw, tickers)

    retry_tickers = [ticker for ticker in tickers if not _has_enough_history(prices.get(ticker))]
    for ticker in retry_tickers:
        single_raw = _download([ticker], lookback_days, threads=False)
        single_prices = _split_download(single_raw, [ticker])
        if _has_enough_history(single_prices.get(ticker)):
            prices[ticker] = single_prices[ticker]

    missing = sorted(ticker for ticker in tickers if not _has_enough_history(prices.get(ticker)))
    if missing:
        raise RuntimeError(f"Missing usable data for tickers: {', '.join(missing)}")

    return prices


def _download(tickers: list[str], lookback_days: int, threads: bool) -> pd.DataFrame:
    raw = yf.download(
        tickers=tickers,
        period=f"{lookback_days}d",
        interval="1d",
        auto_adjust=False,
        group_by="ticker",
        progress=False,
        threads=threads,
    )

    if raw.empty:
        return pd.DataFrame()
    return raw


def _split_download(raw: pd.DataFrame, tickers: list[str]) -> dict[str, pd.DataFrame]:
    prices: dict[str, pd.DataFrame] = {}
    if raw.empty:
        return prices

    if isinstance(raw.columns, pd.MultiIndex):
        first_level = set(raw.columns.get_level_values(0))
        second_level = set(raw.columns.get_level_values(1))
        for ticker in tickers:
            if ticker in first_level:
                prices[ticker] = _clean_price_frame(raw[ticker])
            elif ticker in second_level:
                prices[ticker] = _clean_price_frame(raw.xs(ticker, axis=1, level=1))
    else:
        prices[tickers[0]] = _clean_price_frame(raw)

    return prices


def _clean_price_frame(frame: pd.DataFrame) -> pd.DataFrame:
    normalized = frame.rename(columns={column: column.lower().replace(" ", "_") for column in frame.columns})
    expected_columns = {"open", "high", "low", "close", "volume"}
    missing = expected_columns - set(normalized.columns)
    if missing:
        raise RuntimeError(f"Price data is missing columns: {', '.join(sorted(missing))}")

    if "adj_close" in normalized.columns:
        normalized["price"] = normalized["adj_close"]
    else:
        normalized["price"] = normalized["close"]

    normalized = normalized.dropna(subset=["price"]).copy()
    normalized.index = pd.to_datetime(normalized.index)
    normalized["fetched_at_utc"] = datetime.now(UTC).isoformat(timespec="seconds")
    return normalized


def _has_enough_history(frame: pd.DataFrame | None) -> bool:
    return frame is not None and len(frame) >= MIN_HISTORY_ROWS