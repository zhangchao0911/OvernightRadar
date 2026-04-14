/**
 * 热力图方块组件 — 单个 ETF 方块渲染
 */

/**
 * 根据指标值返回颜色。
 * 统一使用中国习惯：红涨绿跌
 */
export function getColor(value, isCN = false) {
  if (value === null || value === undefined || isNaN(value)) return '#334155';

  // 统一红涨绿跌
  if (value >= 5) return '#d32f2f';
  if (value >= 2) return '#e57373';
  if (value >= 0.5) return '#ffcdd2';
  if (value > 0) return '#ef9a9a';
  if (value === 0) return '#334155';
  if (value > -0.5) return '#c8e6c9';
  if (value > -2) return '#81c784';
  if (value > -5) return '#3ba53b';
  return '#1b7a1b';
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
 * 渲染单个 ETF/板块 方块 HTML。
 * isCN=true 时使用 A股颜色方案和 code 字段。
 */
export function renderBlock(etf, indicatorKey, isCN = false) {
  const value = getIndicatorValue(etf, indicatorKey);
  const bgColor = getColor(value, isCN);
  const displayValue = formatValue(value);

  // A股用 code，美股用 ticker
  const code = etf.code || etf.ticker;
  const name = etf.name || '';
  const cnBadge = !isCN && etf.has_cn_mapping
    ? '<span class="wl-cn-badge" title="有A股映射">A</span>'
    : '';

  const cnClass = isCN ? ' cn' : '';
  return `
    <div class="wl-block${cnClass}" data-code="${code}" style="background-color: ${bgColor}">
      <span class="wl-block-ticker">${code}</span>
      <span class="wl-block-name">${name}</span>
      <span class="wl-block-value">${displayValue}</span>
      ${cnBadge}
    </div>
  `;
}

/**
 * 在所有 groups 中查找指定 ticker/code 的 ETF 或板块数据。
 * 美股查找 group.etfs (by ticker)，A股查找 group.sectors (by code)。
 */
export function findEtf(groups, tickerOrCode) {
  for (const group of Object.values(groups)) {
    // 美股用 etfs 数组
    if (group.etfs) {
      const found = group.etfs.find(e => e.ticker === tickerOrCode);
      if (found) return found;
    }
    // A股用 sectors 数组
    if (group.sectors) {
      const found = group.sectors.find(e => e.code === tickerOrCode);
      if (found) return found;
    }
  }
  return null;
}
