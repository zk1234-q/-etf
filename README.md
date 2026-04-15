# 美股板块每日行情监控

这是一个轻量级 Python 项目，用 SPDR 行业 ETF 代理美股主要板块。每次运行会拉取最近日线行情，计算板块强弱、量能和趋势信号，并输出 CSV、Markdown 日报和手机可看的网页数据。

## 网页效果

项目已经内置 GitHub Pages 静态网页：

- `docs/index.html`: 手机和电脑都能打开的行情仪表盘
- `docs/styles.css`: 页面样式
- `docs/app.js`: 读取数据并渲染排行、概览和异动提示
- `docs/data/latest.json`: 每日最新行情数据

本地生成数据后，可以直接打开：

```powershell
start .\docs\index.html
```

如果浏览器因为本地文件限制无法读取 JSON，可以启动一个本地静态服务：

```powershell
python -m http.server 8000 -d docs
```

然后访问：

```text
http://localhost:8000
```

## 覆盖板块

默认配置在 `config/sectors.json`，包含：

- `SPY`: 标普 500 基准
- `XLK`: 科技
- `XLF`: 金融
- `XLV`: 医疗保健
- `XLY`: 可选消费
- `XLP`: 必需消费
- `XLI`: 工业
- `XLE`: 能源
- `XLB`: 材料
- `XLU`: 公用事业
- `XLRE`: 房地产
- `XLC`: 通信服务

## 快速开始

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:PYTHONPATH = "$PWD\src"
python -m us_sector_monitor.cli
```

报告会生成在 `reports` 目录，网页数据会生成在 `docs/data/latest.json`。

## 常用参数

```powershell
python -m us_sector_monitor.cli --lookback-days 180 --move-threshold 2 --volume-threshold 2
```

- `--lookback-days`: 拉取历史天数，默认 120
- `--move-threshold`: 日涨跌幅异动阈值，默认 1.5%
- `--volume-threshold`: 20 日量比阈值，默认 1.8
- `--skip-web`: 只生成 CSV 和 Markdown，不更新网页 JSON
- `--web-dir`: 指定网页目录，默认 `docs`

## 部署到 GitHub Pages

最省心的方式是让 GitHub Actions 自动更新和发布网页。

1. 在 GitHub 新建一个仓库，例如 `us-sector-monitor`。
2. 在本地项目目录执行：

```powershell
git init
git add .
git commit -m "Initial US sector dashboard"
git branch -M main
git remote add origin https://github.com/你的用户名/us-sector-monitor.git
git push -u origin main
```

3. 打开 GitHub 仓库的 `Settings` -> `Pages`。
4. 在 `Build and deployment` 里把 `Source` 选成 `GitHub Actions`。
5. 打开 `Actions`，运行 `Update US Sector Dashboard`。
6. 运行成功后，手机访问：

```text
https://你的用户名.github.io/us-sector-monitor/
```

内置 workflow 文件在 `.github/workflows/update-sector-dashboard.yml`。它会在 UTC 工作日 22:30 自动运行，大约是北京时间次日 06:30，适合美股收盘后更新。

## 监控指标

- `daily_pct`: 当日涨跌幅
- `relative_to_spy_pct`: 相对 SPY 的当日强弱
- `volume_ratio_20d`: 今日成交量与过去 20 个交易日均量的比值
- `return_5d_pct`: 近 5 个交易日收益率
- `return_20d_pct`: 近 20 个交易日收益率
- `distance_to_ma20_pct`: 收盘价相对 20 日均线偏离
- `signals`: 根据阈值生成的中文信号

## 数据说明

本项目使用 `yfinance` 拉取 Yahoo Finance 行情数据。它适合个人研究和监控，不建议直接作为实盘交易系统的唯一数据源。