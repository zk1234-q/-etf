from __future__ import annotations

from pathlib import Path

import pandas as pd


REPORT_COLUMNS = [
    "ticker",
    "sector_cn",
    "close",
    "daily_pct",
    "relative_to_spy_pct",
    "volume_ratio_20d",
    "return_5d_pct",
    "return_20d_pct",
    "distance_to_ma20_pct",
    "signals",
]


def write_reports(analysis: pd.DataFrame, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    report_date = str(analysis["date"].max())
    csv_path = output_dir / f"sector_report_{report_date}.csv"
    markdown_path = output_dir / f"sector_report_{report_date}.md"

    analysis.to_csv(csv_path, index=False, encoding="utf-8-sig")
    markdown_path.write_text(render_markdown(analysis, report_date), encoding="utf-8-sig")
    return csv_path, markdown_path


def render_markdown(analysis: pd.DataFrame, report_date: str) -> str:
    sector_rows = analysis[analysis["is_benchmark"] == False].copy()  # noqa: E712
    benchmark_rows = analysis[analysis["is_benchmark"] == True].copy()  # noqa: E712
    strongest = sector_rows.nlargest(3, "daily_pct")
    weakest = sector_rows.nsmallest(3, "daily_pct")
    alerts = sector_rows[sector_rows["signals"] != "正常波动"].copy()

    lines = [
        f"# 美股板块每日行情报告 {report_date}",
        "",
        "## 今日概览",
        "",
    ]

    if not benchmark_rows.empty:
        benchmark = benchmark_rows.iloc[0]
        lines.append(
            f"- {benchmark['sector_cn']}({benchmark['ticker']}) 收盘 {benchmark['close']}, "
            f"日涨跌 {benchmark['daily_pct']}%。"
        )

    lines.extend(
        [
            f"- 最强板块: {_format_sector_list(strongest)}。",
            f"- 最弱板块: {_format_sector_list(weakest)}。",
            f"- 异动数量: {len(alerts)} 个板块触发监控信号。",
            "",
            "## 板块排行",
            "",
            _to_markdown_table(sector_rows[REPORT_COLUMNS]),
            "",
            "## 异动提示",
            "",
        ]
    )

    if alerts.empty:
        lines.append("- 暂无明显异动。")
    else:
        for _, row in alerts.iterrows():
            lines.append(
                f"- {row['sector_cn']}({row['ticker']}): 日涨跌 {row['daily_pct']}%, "
                f"相对 SPY {row['relative_to_spy_pct']}%, 信号: {row['signals']}。"
            )

    lines.extend(
        [
            "",
            "## 字段说明",
            "",
            "- `relative_to_spy_pct`: 当日涨跌幅减去 SPY 当日涨跌幅，衡量相对强弱。",
            "- `volume_ratio_20d`: 今日成交量 / 过去 20 个交易日平均成交量。",
            "- `distance_to_ma20_pct`: 收盘价相对 20 日均线的偏离百分比。",
            "",
        ]
    )
    return "\n".join(lines)


def _format_sector_list(rows: pd.DataFrame) -> str:
    return "、".join(f"{row['sector_cn']}({row['ticker']}, {row['daily_pct']}%)" for _, row in rows.iterrows())


def _to_markdown_table(frame: pd.DataFrame) -> str:
    renamed = frame.rename(
        columns={
            "ticker": "代码",
            "sector_cn": "板块",
            "close": "收盘",
            "daily_pct": "日涨跌%",
            "relative_to_spy_pct": "相对SPY%",
            "volume_ratio_20d": "量比20日",
            "return_5d_pct": "5日%",
            "return_20d_pct": "20日%",
            "distance_to_ma20_pct": "距20日线%",
            "signals": "信号",
        }
    )
    headers = [str(column) for column in renamed.columns]
    body = [[_format_cell(value) for value in row] for row in renamed.to_numpy()]
    widths = [len(header) for header in headers]
    for row in body:
        widths = [max(width, len(cell)) for width, cell in zip(widths, row)]

    header_line = "| " + " | ".join(header.ljust(width) for header, width in zip(headers, widths)) + " |"
    separator = "| " + " | ".join("-" * width for width in widths) + " |"
    body_lines = ["| " + " | ".join(cell.ljust(width) for cell, width in zip(row, widths)) + " |" for row in body]
    return "\n".join([header_line, separator, *body_lines])


def _format_cell(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value)