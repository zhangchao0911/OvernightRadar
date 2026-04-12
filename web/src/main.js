/**
 * 隔夜雷达 — 前端逻辑 V1.1
 */

const RESULTS_DIR = import.meta.env.BASE_URL + 'data/results/';

const SENTIMENT_CONFIG = {
  4: { label: '🔴 强烈看多', cssClass: 'sentiment-label-4' },
  3: { label: '🔴 偏多', cssClass: 'sentiment-label-3' },
  2: { label: '⚪ 中性', cssClass: 'sentiment-label-2' },
  1: { label: '🟢 偏空', cssClass: 'sentiment-label-1' },
  0: { label: '🟢 强烈看空', cssClass: 'sentiment-label-0' },
};

async function main() {
  const app = document.getElementById('app');
  const loading = document.getElementById('loading');
  const errorEl = document.getElementById('error');

  try {
    const report = await fetchLatestReport();
    if (!report) {
      loading.style.display = 'none';
      errorEl.style.display = 'block';
      return;
    }

    renderReport(report);
    loading.style.display = 'none';
    app.style.display = 'block';
  } catch (e) {
    console.error('Failed to load report:', e);
    loading.style.display = 'none';
    errorEl.style.display = 'block';
  }
}

async function fetchLatestReport() {
  const dates = [];
  const now = new Date();
  for (let i = 0; i < 7; i++) {
    const d = new Date(now);
    d.setDate(d.getDate() - i);
    dates.push(formatDate(d));
  }

  for (const date of dates) {
    try {
      const resp = await fetch(`${RESULTS_DIR}${date}.json`);
      if (resp.ok) {
        return await resp.json();
      }
    } catch {
      // continue
    }
  }
  return null;
}

function formatDate(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

function formatChange(value) {
  if (value === null || value === undefined) return '—';
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(1)}%`;
}

function renderReport(report) {
  // ─── 市场指数 ─────────────────────────────
  const indicesEl = document.getElementById('market-indices');
  const indexNames = { sp500: '标普', nasdaq: '纳指', dow: '道指' };
  let indicesHtml = '';
  for (const [key, name] of Object.entries(indexNames)) {
    if (report.market_indices && report.market_indices[key]) {
      const change = report.market_indices[key].change_pct;
      const cls = change >= 0 ? 'up' : 'down';
      indicesHtml += `<span class="index-item">${name}<span class="${cls}">${formatChange(change)}</span></span>`;
    }
  }
  indicesEl.innerHTML = indicesHtml;

  // ─── 日期 + 总览 ──────────────────────────
  document.getElementById('report-date').textContent =
    `${report.market_summary} · ${report.date} ${report.weekday}`;

  // ─── 板块卡片 ─────────────────────────────
  const container = document.getElementById('cards-container');
  if (!report.sectors || report.sectors.length === 0) {
    container.innerHTML = '<p style="text-align:center;color:#888;padding:40px 0;">暂无板块数据</p>';
  } else {
    container.innerHTML = report.sectors.map(renderSectorCard).join('');
  }
}

function renderSectorCard(sector) {
  const changeClass = sector.us_change_pct >= 0 ? 'up' : 'down';
  const s = SENTIMENT_CONFIG[sector.sentiment_level] || SENTIMENT_CONFIG[2];

  // 相对强度文案
  const rsText = sector.relative_strength >= 0 ? '跑赢大盘' : '跑输大盘';
  const rsSign = sector.relative_strength >= 0 ? '+' : '';

  // 波动率文案
  const volText = sector.volatility.is_abnormal
    ? `异常波动 ${sector.volatility.vol_multiple}σ`
    : '正常波动';

  // 趋势文案
  let trendText = '平盘';
  if (sector.trend.direction === 'up' && sector.trend.consecutive_days > 0) {
    trendText = `连涨${sector.trend.consecutive_days}天+${sector.trend.cumulative_pct}%`;
  } else if (sector.trend.direction === 'down' && sector.trend.consecutive_days > 0) {
    trendText = `连跌${sector.trend.consecutive_days}天${sector.trend.cumulative_pct}%`;
  }

  // 产业链标的
  const stocksHtml = sector.supply_chain.map(stock => {
    const sc = stock.change_pct !== null && stock.change_pct !== undefined
      ? (stock.change_pct >= 0 ? 'up' : 'down')
      : 'na';
    return `<div class="stock-item">
      <span class="stock-name">${stock.name}(${stock.code})</span>
      <span class="stock-change ${sc}">${formatChange(stock.change_pct)}</span>
    </div>`;
  }).join('');

  // A股 ETF 标签（cn_etf_code 为空则不显示）
  let etfHtml = '';
  if (sector.cn_etf_code) {
    etfHtml = `<span class="card-cn-etf">${sector.cn_etf_name}(${sector.cn_etf_code})</span>`;
  }

  return `
    <div class="card sentiment-${sector.sentiment_level}">
      <div class="card-sentiment ${s.cssClass}">${s.label}</div>
      <div class="card-header">
        <span class="card-us">${sector.us_etf} ${sector.us_name}</span>
        <span class="card-change ${changeClass}">${formatChange(sector.us_change_pct)}</span>
      </div>
      <div class="card-detail">
        <span class="card-rs">${rsText}${rsSign}${sector.relative_strength.toFixed(1)}%</span>
      </div>
      <div class="card-detail">${volText} · ${trendText}</div>
      <div class="card-cn">→ A股${sector.cn_name} ${etfHtml}</div>
      <div class="card-stocks">${stocksHtml}</div>
    </div>
  `;
}

main();
