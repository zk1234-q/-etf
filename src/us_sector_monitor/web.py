from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd


WEB_COLUMNS = [
    "ticker",
    "sector_cn",
    "sector",
    "close",
    "daily_pct",
    "relative_to_spy_pct",
    "volume_ratio_20d",
    "return_5d_pct",
    "return_20d_pct",
    "distance_to_ma20_pct",
    "signals",
]


def write_web_data(analysis: pd.DataFrame, web_dir: Path) -> Path:
    data_dir = web_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    json_path = data_dir / "latest.json"
    payload = build_web_payload(analysis)
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return json_path


def build_web_payload(analysis: pd.DataFrame) -> dict[str, Any]:
    report_date = str(analysis["date"].max())
    sector_rows = analysis[analysis["is_benchmark"] == False].copy()  # noqa: E712
    benchmark_rows = analysis[analysis["is_benchmark"] == True].copy()  # noqa: E712
    alerts = sector_rows[sector_rows["signals"] != "正常波动"].copy()
    strongest = sector_rows.nlargest(3, "daily_pct")
    weakest = sector_rows.nsmallest(3, "daily_pct")

    benchmark = None
    if not benchmark_rows.empty:
        benchmark = _record_to_dict(benchmark_rows.iloc[0])

    return {
        "report_date": report_date,
        "generated_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "benchmark": benchmark,
        "summary": {
            "strongest": [_record_to_dict(row) for _, row in strongest.iterrows()],
            "weakest": [_record_to_dict(row) for _, row in weakest.iterrows()],
            "alert_count": int(len(alerts)),
            "sector_count": int(len(sector_rows)),
        },
        "sectors": [_record_to_dict(row) for _, row in sector_rows[WEB_COLUMNS].iterrows()],
        "alerts": [_record_to_dict(row) for _, row in alerts[WEB_COLUMNS].iterrows()],
    }


def _record_to_dict(row: pd.Series) -> dict[str, Any]:
    return {str(key): _json_value(value) for key, value in row.items()}


def _json_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value