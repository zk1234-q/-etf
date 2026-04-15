from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Sector:
    ticker: str
    name: str
    name_cn: str
    benchmark: bool = False


@dataclass(frozen=True)
class MonitorConfig:
    sectors: list[Sector]
    lookback_days: int = 120
    move_threshold_pct: float = 1.5
    volume_spike_threshold: float = 1.8

    @property
    def tickers(self) -> list[str]:
        return [sector.ticker for sector in self.sectors]

    @property
    def benchmark_ticker(self) -> str | None:
        for sector in self.sectors:
            if sector.benchmark:
                return sector.ticker
        return None