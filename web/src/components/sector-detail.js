/**
 * ETF 详情展开面板
 */
import { drawSparkline } from './sparkline.js';

let currentTicker = null;

function formatVal(value) {
  if (value === null || value === undefined || isNaN(value)) return '—';
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
}

/**
 * 显示指定 ETF 的详情。传 null 则隐藏面板。
 */
export function showDetail(etf, detailEl) {
  if (!detailEl) return;

  // etf 为 null → 隐藏
  if (!etf) {
    detailEl.style.display = 'none';
    currentTicker = null;
    return;
  }

  // 点击同一个 → 收起
  if (currentTicker === etf.ticker) {
    detailEl.style.display = 'none';
    currentTicker = null;
    return;
  }

  currentTicker = etf.ticker;

  const relHtml = etf.rel
    ? `
      <div class="wl-rel-grid">
        <div class="wl-rel-item"><span class="wl-rel-label">REL5</span><span class="wl-rel-value">${formatVal(etf.rel.rel_5)}</span></div>
        <div class="wl-rel-item"><span class="wl-rel-label">REL20</span><span class="wl-rel-value">${formatVal(etf.rel.rel_20)}</span></div>
        <div class="wl-rel-item"><span class="wl-rel-label">REL60</span><span class="wl-rel-value">${formatVal(etf.rel.rel_60)}</span></div>
        <div class="wl-rel-item"><span class="wl-rel-label">REL120</span><span class="wl-rel-value">${formatVal(etf.rel.rel_120)}</span></div>
      </div>
    `
    : '';

  // A 股映射区域
  const cnMappingHtml = etf.has_cn_mapping
    ? `
      <div class="wl-cn-mapping">
        <span class="wl-cn-badge-detail">有 A 股映射</span>
        <span class="wl-cn-hint">数据来源：隔夜雷达</span>
      </div>
    `
    : '';

  detailEl.innerHTML = `
    <div class="wl-detail-header">
      <h3 class="wl-detail-title">${etf.ticker} · ${etf.name}</h3>
      <button class="wl-detail-close" id="wl-detail-close">✕</button>
    </div>
    <div class="wl-detail-price">
      <span class="wl-detail-price-value">$${etf.price.toFixed(2)}</span>
      <span class="wl-detail-change">${formatVal(etf.change_pct)}</span>
      <span class="wl-detail-ytd">YTD: ${formatVal(etf.ytd)}</span>
    </div>
    <canvas id="sparkline-canvas" width="300" height="80"></canvas>
    ${relHtml}
    ${cnMappingHtml}
  `;

  detailEl.style.display = 'block';

  // 关闭按钮
  document.getElementById('wl-detail-close').addEventListener('click', () => {
    detailEl.style.display = 'none';
    currentTicker = null;
  });

  // 绘制走势图（MVP 用模拟数据，后续接入历史价格）
  const canvas = document.getElementById('sparkline-canvas');
  if (canvas && etf.price) {
    const mockData = generateMockHistory(etf);
    drawSparkline(canvas, mockData, { width: canvas.parentElement.clientWidth - 32 });
  }

  // 滚动到详情面板
  detailEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

/**
 * MVP 阶段：基于当日数据生成模拟走势。
 */
function generateMockHistory(etf) {
  const base = etf.price / (1 + etf.change_pct / 100);
  const points = 20;
  const data = [];
  for (let i = 0; i <= points; i++) {
    const noise = (Math.random() - 0.5) * base * 0.01;
    const trend = (etf.change_pct / 100) * base * (i / points);
    data.push(base + trend + noise);
  }
  return data;
}
