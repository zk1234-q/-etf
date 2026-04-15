from __future__ import annotations

import math

import pandas as pd

from .models import MonitorConfig


def analyze_sectors(prices: dict[str, pd.DataFrame], config: MonitorConfig) -> pd.DataFrame:
    rows = []
    benchmark_daily_pct = _benchmark_daily_pct(prices, config.benchmark_ticker)

    for sector in config.sectors:
        history = prices.get(sector.ticker)
        if history is None or len(history) < 2:
            continue

        latest = history.iloc[-1]
        previous = history.iloc[-2]
        price = float(latest["price"])
        previous_price = float(previous["price"])
        daily_pct = _pct_change(price, previous_price)
        gap_pct = _pct_change(float(latest["open"]), previous_price)
        intraday_pct = _pct_change(float(latest["close"]), float(latest["open"]))
        ma20 = _rolling_mean(history["price"], 20)
        ma50 = _rolling_mean(history["price"], 50)
        volume_ratio = _volume_ratio(history["volume"], 20)

        row = {
            "date": latest.name.date().isoformat(),
            "ticker": sector.ticker,
            "sector": sector.name,
            "sector_cn": sector.name_cn,
            "is_benchmark": sector.benchmark,
            "close": round(price, 2),
            "daily_pct": round(daily_pct, 2),
            "gap_pct": round(gap_pct, 2),
            "intraday_pct": round(intraday_pct, 2),
            "volume": int(latest["volume"]) if not math.isnan(float(latest["volume"])) else 0,
            "volume_ratio_20d": round(volume_ratio, 2) if volume_ratio is not None else None,
            "return_5d_pct": _period_return(history["price"], 5),
            "return_20d_pct": _period_return(history["price"], 20),
            "ma20": round(ma20, 2) if ma20 is not None else None,
            "ma50": round(ma50, 2) if ma50 is not None else None,
            "distance_to_ma20_pct": _distance_to_ma(price, ma20),
            "relative_to_spy_pct": round(daily_pct - benchmark_daily_pct, 2) if benchmark_daily_pct is not None else None,
        }
        row["signals"] = ", ".join(_signals(row, config))
        rows.append(row)

    if not rows:
        raise RuntimeError("Not enough price history to analyze sectors.")

    result = pd.DataFrame(rows)
    return result.sort_values(["is_benchmark", "daily_pct"], ascending=[True, False]).reset_index(drop=True)


def _benchmark_daily_pct(prices: dict[str, pd.DataFrame], benchmark_ticker: str | None) -> float | None:
    if not benchmark_ticker or benchmark_ticker not in prices or len(prices[benchmark_ticker]) < 2:
        return None

    history = prices[benchmark_ticker]
    return _pct_change(float(history.iloc[-1]["price"]), float(history.iloc[-2]["price"]))


def _pct_change(current: float, previous: float) -> float:
    if previous == 0 or math.isnan(previous) or math.isnan(current):
        return 0.0
    return (current / previous - 1) * 100


def _rolling_mean(series: pd.Series, window: int) -> float | None:
    if len(series.dropna()) < window:
        return None
    return float(series.rolling(window).mean().iloc[-1])


def _volume_ratio(series: pd.Series, window: int) -> float | None:
    clean = series.dropna()
    if len(clean) <= window:
        return None
    baseline = clean.iloc[-window - 1 : -1].mean()
    if baseline == 0:
        return None
    return float(clean.iloc[-1] / baseline)


def _period_return(series: pd.Series, days: int) -> float | None:
    clean = series.dropna()
    if len(clean) <= days:
        return None
    return round(_pct_change(float(clean.iloc[-1]), float(clean.iloc[-days - 1])), 2)


def _distance_to_ma(price: float, moving_average: float | None) -> float | None:
    if moving_average is None or moving_average == 0:
        return None
    return round(_pct_change(price, moving_average), 2)


def _signals(row: dict[str, object], config: MonitorConfig) -> list[str]:
    signals: list[str] = []
    daily_pct = float(row["daily_pct"])
    volume_ratio = row["volume_ratio_20d"]
    distance_to_ma20 = row["distance_to_ma20_pct"]

    if daily_pct >= config.move_threshold_pct:
        signals.append("强势上涨")
    elif daily_pct <= -config.move_threshold_pct:
        signals.append("明显下跌")

    if isinstance(volume_ratio, float) and volume_ratio >= config.volume_spike_threshold:
        signals.append("成交量放大")

    if isinstance(distance_to_ma20, float):
        if distance_to_ma20 >= 3:
            signals.append("站上20日线")
        elif distance_to_ma20 <= -3:
            signals.append("跌破20日线")

    return signals or ["正常波动"]