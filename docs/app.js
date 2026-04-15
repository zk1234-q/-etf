const state = {
  maxAbsMove: 1,
};

const formatter = new Intl.NumberFormat("zh-CN", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

async function loadDashboard() {
  try {
    const response = await fetch(`data/latest.json?v=${Date.now()}`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const data = await response.json();
    renderDashboard(data);
  } catch (error) {
    renderError(error);
  }
}

function renderDashboard(data) {
  state.maxAbsMove = Math.max(...data.sectors.map((sector) => Math.abs(Number(sector.daily_pct) || 0)), 1);
  renderBenchmark(data.benchmark, data.report_date);
  renderSummary(data);
  renderRanking(data.sectors);
  renderAlerts(data.alerts);
  renderTable(data.sectors);

  document.getElementById("footerDate").textContent = `行情日期 ${data.report_date}，UTC ${formatGeneratedAt(data.generated_at_utc)} 更新`;
}

function renderBenchmark(benchmark, reportDate) {
  const card = document.getElementById("benchmarkCard");
  if (!benchmark) {
    card.innerHTML = `<span class="label">基准</span><strong>无数据</strong><small>${reportDate}</small>`;
    return;
  }

  const direction = Number(benchmark.daily_pct) >= 0 ? "up" : "down";
  card.innerHTML = `
    <span class="label">${benchmark.sector_cn || "基准"} · ${benchmark.ticker}</span>
    <strong class="${direction}">${formatPct(benchmark.daily_pct)}</strong>
    <small>收盘 ${formatNumber(benchmark.close)} · 行情日期 ${reportDate}</small>
  `;
}

function renderSummary(data) {
  const strongest = data.summary.strongest?.[0];
  const weakest = data.summary.weakest?.[0];
  const cards = [
    ["领涨板块", strongest ? `${strongest.sector_cn} ${formatPct(strongest.daily_pct)}` : "暂无"],
    ["领跌板块", weakest ? `${weakest.sector_cn} ${formatPct(weakest.daily_pct)}` : "暂无"],
    ["异动数量", `${data.summary.alert_count} 个`],
    ["覆盖板块", `${data.summary.sector_count} 个`],
  ];

  document.getElementById("summaryCards").innerHTML = cards
    .map(([label, value]) => `<article class="summary-card"><span>${label}</span><strong>${value}</strong></article>`)
    .join("");
}

function renderRanking(sectors) {
  const rows = [...sectors].sort((a, b) => Number(b.daily_pct) - Number(a.daily_pct));
  document.getElementById("rankingList").innerHTML = rows
    .map((sector) => {
      const change = Number(sector.daily_pct) || 0;
      const polarity = change >= 0 ? "positive" : "negative";
      const width = Math.max(6, Math.round((Math.abs(change) / state.maxAbsMove) * 100));
      return `
        <article class="rank-row ${polarity}">
          <div class="rank-fill" style="width: ${width}%"></div>
          <div class="rank-content">
            <span class="ticker">${escapeHtml(sector.ticker)}</span>
            <span class="name">${escapeHtml(sector.sector_cn)} · ${escapeHtml(sector.sector)}</span>
            <span class="change">${formatPct(sector.daily_pct)}</span>
          </div>
        </article>
      `;
    })
    .join("");
}

function renderAlerts(alerts) {
  const target = document.getElementById("alertsList");
  if (!alerts.length) {
    target.innerHTML = `<div class="alert-item"><strong>暂无明显异动</strong><span>所有板块都在阈值范围内波动。</span></div>`;
    return;
  }

  target.innerHTML = alerts
    .map(
      (alert) => `
        <div class="alert-item">
          <strong>${escapeHtml(alert.sector_cn)} · ${escapeHtml(alert.ticker)} ${formatPct(alert.daily_pct)}</strong>
          <span>相对 SPY ${formatPct(alert.relative_to_spy_pct)}，${escapeHtml(alert.signals)}</span>
        </div>
      `,
    )
    .join("");
}

function renderTable(sectors) {
  const rows = [...sectors].sort((a, b) => Number(b.daily_pct) - Number(a.daily_pct));
  document.getElementById("sectorTable").innerHTML = rows
    .map((sector) => {
      const direction = Number(sector.daily_pct) >= 0 ? "up" : "down";
      return `
        <tr>
          <td>${escapeHtml(sector.ticker)}</td>
          <td>${escapeHtml(sector.sector_cn)}</td>
          <td>${formatNumber(sector.close)}</td>
          <td class="${direction}">${formatPct(sector.daily_pct)}</td>
          <td>${formatPct(sector.relative_to_spy_pct)}</td>
          <td>${formatNumber(sector.volume_ratio_20d)}</td>
          <td>${formatPct(sector.return_5d_pct)}</td>
          <td>${formatPct(sector.return_20d_pct)}</td>
          <td><span class="signal-pill">${escapeHtml(sector.signals)}</span></td>
        </tr>
      `;
    })
    .join("");
}

function renderError(error) {
  const message = `数据读取失败：${escapeHtml(error.message)}。请先运行 Python 命令生成 docs/data/latest.json。`;
  document.getElementById("summaryCards").innerHTML = `<div class="error-box">${message}</div>`;
  document.getElementById("rankingList").innerHTML = "";
  document.getElementById("alertsList").innerHTML = "";
}

function formatPct(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "-";
  }
  const number = Number(value);
  return `${number > 0 ? "+" : ""}${formatter.format(number)}%`;
}

function formatNumber(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "-";
  }
  return formatter.format(Number(value));
}

function formatGeneratedAt(value) {
  if (!value) {
    return "未知时间";
  }
  return value.replace("T", " ").replace("+00:00", "");
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

loadDashboard();