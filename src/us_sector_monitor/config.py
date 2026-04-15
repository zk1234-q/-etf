from __future__ import annotations

import json
from pathlib import Path

from .models import MonitorConfig, Sector


def load_config(
    config_path: Path,
    lookback_days: int,
    move_threshold_pct: float,
    volume_spike_threshold: float,
) -> MonitorConfig:
    with config_path.open("r", encoding="utf-8") as file:
        raw_sectors = json.load(file)

    sectors = [
        Sector(
            ticker=item["ticker"].upper(),
            name=item["name"],
            name_cn=item.get("name_cn", item["name"]),
            benchmark=bool(item.get("benchmark", False)),
        )
        for item in raw_sectors
    ]

    if not sectors:
        raise ValueError("No sectors were configured.")

    return MonitorConfig(
        sectors=sectors,
        lookback_days=lookback_days,
        move_threshold_pct=move_threshold_pct,
        volume_spike_threshold=volume_spike_threshold,
    )