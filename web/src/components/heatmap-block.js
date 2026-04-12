/**
 * 热力图方块组件 — 单个 ETF 方块渲染
 */

/**
 * 根据指标值返回颜色。美股惯例：绿涨红跌。
 */
export function getColor(value) {
  if (value === null || value === undefined || isNaN(value)) return '#e8e8e8';

  if (value >= 5) return '#1b7a1b';
  if (value >= 2) return '#3ba53b';
  if (value >= 0.5) return '#81c784';
  if (value > 0) return '#c8e6c9';
  if (value === 0) return '#e8e8e8';
  if (value > -0.5) return '#ffcdd2';
  if (value > -2) return '#e57373';
  if (value > -5) return '#d32f2f';
  return '#b71c1c';
}

export function getIndicatorValue(etf, indicatorKey) {
  if (indicatorKey === 'change_pct') {
    return etf.change_pct;
  }
  if (etf.rel && indicatorKey in etf.rel) {
    return etf.rel[indicatorKey];
  }
  return null;
}

function formatValue(value) {
  if (value === null || value === undefined || isNaN(value)) return '—';
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
}

/**
 * 渲染单个 ETF 方块 HTML。
 */
export function renderBlock(etf, indicatorKey) {
  const value = getIndicatorValue(etf, indicatorKey);
  const bgColor = getColor(value);
  const displayValue = formatValue(value);
  const cnBadge = etf.has_cn_mapping
    ? '<span class="wl-cn-badge" title="有A股映射">A</span>'
    : '';

  return `
    <div class="wl-block" data-ticker="${etf.ticker}" style="background-color: ${bgColor}">
      <span class="wl-block-ticker">${etf.ticker}</span>
      <span class="wl-block-name">${etf.name || ''}</span>
      <span class="wl-block-value">${displayValue}</span>
      ${cnBadge}
    </div>
  `;
}

/**
 * 在所有 groups 中查找指定 ticker 的 ETF 数据。
 */
export function findEtf(groups, ticker) {
  for (const group of Object.values(groups)) {
    if (!group.etfs) continue;
    const found = group.etfs.find(e => e.ticker === ticker);
    if (found) return found;
  }
  return null;
}
