/**
 * 隔夜雷达视图 — 迁自原 main.js V1.1
 */
import { fetchRadarData } from '../data.js';
import { renderSectorCard } from '../components/radar-card.js';

function formatChange(value) {
  if (value === null || value === undefined) return '—';
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
}

/**
 * 渲染隔夜雷达视图。
 * @param {HTMLElement} container - #view-container
 * @param {HTMLElement} header - #app-header
 */
export async function renderRadarView(container, header) {
  const report = await fetchRadarData();

  if (!report) {
    container.innerHTML = '<p class="empty-state">暂无雷达数据</p>';
    header.innerHTML = `
      <h1 class="title">隔夜雷达</h1>
      <p class="slogan">昨夜美股异动，今日A股看点</p>
    `;
    return;
  }

  // Header
  const indexNames = { sp500: '标普', nasdaq: '纳指', dow: '道指' };
  let indicesHtml = '';
  for (const [key, name] of Object.entries(indexNames)) {
    if (report.market_indices && report.market_indices[key]) {
      const change = report.market_indices[key].change_pct;
      const cls = change >= 0 ? 'up' : 'down';
      indicesHtml += `<span class="index-item">${name}<span class="${cls}">${formatChange(change)}</span></span>`;
    }
  }

  header.innerHTML = `
    <h1 class="title">隔夜雷达</h1>
    <p class="slogan">昨夜美股异动，今日A股看点</p>
    <div class="market-indices">${indicesHtml}</div>
    <p class="date">${report.market_summary} · ${report.date} ${report.weekday}</p>
  `;

  // 免责声明 (顶部)
  const disclaimerHtml = `
    <div class="disclaimer wl-top-disclaimer">
      <p>仅供数据参考，不构成投资建议。数据来源：Yahoo Finance、AKShare、公开市场数据。</p>
    </div>
  `;

  // 卡片列表
  if (!report.sectors || report.sectors.length === 0) {
    container.innerHTML = disclaimerHtml + '<p class="empty-state">暂无板块数据</p>';
  } else {
    container.innerHTML = disclaimerHtml + report.sectors.map(renderSectorCard).join('');
  }
}
