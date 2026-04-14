/**
 * 雷达卡片组件 — 渲染单个板块的情绪卡片
 */

const SENTIMENT_CONFIG = {
  4: { label: '强烈看多', cssClass: 'sentiment-label-4' },
  3: { label: '偏多', cssClass: 'sentiment-label-3' },
  2: { label: '中性', cssClass: 'sentiment-label-2' },
  1: { label: '偏空', cssClass: 'sentiment-label-1' },
  0: { label: '强烈看空', cssClass: 'sentiment-label-0' },
};

function formatChange(value) {
  if (value === null || value === undefined) return '—';
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
}

/**
 * 渲染单个板块卡片 HTML。
 */
export function renderSectorCard(sector) {
  const changeClass = sector.us_change_pct >= 0 ? 'up' : 'down';
  const s = SENTIMENT_CONFIG[sector.sentiment_level] || SENTIMENT_CONFIG[2];

  // 相对强度
  const rsText = sector.relative_strength >= 0 ? '跑赢大盘' : '跑输大盘';
  const rsClass = sector.relative_strength >= 0 ? 'up' : 'down';

  // 波动率文案
  const volText = sector.volatility.is_abnormal
    ? `异常波动 ${sector.volatility.vol_multiple}x`
    : '正常波动';

  // 趋势文案
  let trendText = '平盘';
  if (sector.trend.direction === 'up' && sector.trend.consecutive_days > 0) {
    trendText = `连涨${sector.trend.consecutive_days}天 +${sector.trend.cumulative_pct}%`;
  } else if (sector.trend.direction === 'down' && sector.trend.consecutive_days > 0) {
    trendText = `连跌${sector.trend.consecutive_days}天 ${sector.trend.cumulative_pct}%`;
  }

  // 产业链标的
  const stocksHtml = sector.supply_chain.map(stock => {
    const sc = stock.change_pct !== null && stock.change_pct !== undefined
      ? (stock.change_pct >= 0 ? 'up' : 'down')
      : 'na';
    return `<div class="stock-item">
      <span class="stock-name">${stock.name}</span>
      <span class="stock-change ${sc}">${formatChange(stock.change_pct)}</span>
    </div>`;
  }).join('');

  // A股 ETF 标签
  let etfHtml = '';
  if (sector.cn_etf_code) {
    etfHtml = `<span class="card-cn-etf">${sector.cn_etf_name}(${sector.cn_etf_code})</span>`;
  }

  return `
    <div class="card sentiment-${sector.sentiment_level}">
      <div class="card-sentiment ${s.cssClass}">${s.label}</div>
      <div class="card-header">
        <span class="card-us">${sector.us_name} <span style="color:var(--color-muted);font-weight:400">${sector.us_etf}</span></span>
        <span class="card-change ${changeClass}">${formatChange(sector.us_change_pct)}</span>
      </div>
      <div class="card-detail">
        <span class="card-rs ${rsClass}">${rsText} ${sector.relative_strength >= 0 ? '+' : ''}${sector.relative_strength.toFixed(1)}%</span>
      </div>
      <div class="card-detail">${volText} / ${trendText}</div>
      <div class="card-cn">A 股映射: ${sector.cn_name} ${etfHtml}</div>
      <div class="card-stocks">${stocksHtml}</div>
    </div>
  `;
}
