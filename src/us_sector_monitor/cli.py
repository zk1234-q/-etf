from __future__ import annotations

import argparse
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a daily US sector market report.")
    parser.add_argument("--config", type=Path, default=Path("config/sectors.json"), help="Path to sector config JSON.")
    parser.add_argument("--output-dir", type=Path, default=Path("reports"), help="Directory for generated reports.")
    parser.add_argument("--web-dir", type=Path, default=Path("docs"), help="Directory for the GitHub Pages dashboard.")
    parser.add_argument("--skip-web", action="store_true", help="Only generate CSV and Markdown reports.")
    parser.add_argument("--lookback-days", type=int, default=120, help="Number of calendar days to fetch.")
    parser.add_argument("--move-threshold", type=float, default=1.5, help="Daily percent move threshold for alerts.")
    parser.add_argument("--volume-threshold", type=float, default=1.8, help="20-day volume ratio threshold for alerts.")
    return parser


def main() -> None:
    args = build_parser().parse_args()

    from .analyzer import analyze_sectors
    from .config import load_config
    from .data import fetch_daily_prices
    from .reporter import write_reports
    from .web import write_web_data

    config = load_config(
        config_path=args.config,
        lookback_days=args.lookback_days,
        move_threshold_pct=args.move_threshold,
        volume_spike_threshold=args.volume_threshold,
    )
    prices = fetch_daily_prices(config.tickers, config.lookback_days)
    analysis = analyze_sectors(prices, config)
    csv_path, markdown_path = write_reports(analysis, args.output_dir)

    print("US sector report generated.")
    print(f"CSV: {csv_path}")
    print(f"Markdown: {markdown_path}")

    if not args.skip_web:
        web_json_path = write_web_data(analysis, args.web_dir)
        print(f"Web data: {web_json_path}")


if __name__ == "__main__":
    main()