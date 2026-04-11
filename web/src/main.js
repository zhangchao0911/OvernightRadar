/**
 * 美股涨了，A股呢？ — 前端逻辑
 */

const RESULTS_DIR = import.meta.env.BASE_URL + 'data/results/';

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

function renderReport(report) {
  document.getElementById('report-date').textContent =
    `${report.date} ${report.weekday}`;

  const container = document.getElementById('cards-container');
  if (report.cards.length === 0) {
    container.innerHTML = '<p class="empty-msg">今日美股无板块涨跌幅超过 2%</p>';
  } else {
    container.innerHTML = report.cards.map(renderCard).join('');
  }

  const quietSection = document.getElementById('quiet-section');
  if (report.quiet_sectors.length > 0) {
    quietSection.style.display = 'block';
    document.getElementById('quiet-list').innerHTML =
      report.quiet_sectors.map(renderQuietItem).join('');
  }
}

function renderCard(card) {
  const isUp = card.us_change_pct >= 0;
  const changeClass = isUp ? 'up' : 'down';
  const changeSign = isUp ? '+' : '';
  const changeStr = `${changeSign}${card.us_change_pct.toFixed(2)}%`;

  let probHtml = '';
  if (card.prob_high_open !== null && card.prob_high_open !== undefined) {
    const probPct = (card.prob_high_open * 100).toFixed(0);
    const impactSign = card.avg_impact >= 0 ? '+' : '';
    const impactStr = `${impactSign}${card.avg_impact.toFixed(2)}%`;
    probHtml = `
      <div class="card-prob">${probPct}% <span>概率高开</span></div>
      <div class="card-impact">平均幅度 ${impactStr}</div>
    `;
  } else {
    probHtml = '<div class="card-prob" style="font-size:14px;color:#aaa">样本不足</div>';
  }

  return `
    <div class="card">
      <div class="card-header">
        <span class="card-us">${card.us_etf} ${card.us_name}</span>
        <span class="card-change ${changeClass}">${changeStr}</span>
      </div>
      <div class="card-arrow">↓</div>
      <div class="card-cn">→ A股 ${card.cn_name}</div>
      ${probHtml}
      <span class="card-etf">${card.cn_etf_name}(${card.cn_etf_code})</span>
      ${card.sample_count > 0 ? `<div class="card-meta">(${card.window_days}日 · ${card.sample_count}次样本)</div>` : ''}
    </div>
  `;
}

function renderQuietItem(item) {
  const isUp = item.us_change_pct >= 0;
  const changeClass = isUp ? 'up' : 'down';
  const changeSign = isUp ? '+' : '';
  return `
    <div class="quiet-item">
      <span>${item.us_name} (${item.us_etf})</span>
      <span class="quiet-change ${changeClass}">${changeSign}${item.us_change_pct.toFixed(2)}%</span>
    </div>
  `;
}

main();
