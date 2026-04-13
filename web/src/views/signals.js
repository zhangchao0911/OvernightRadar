/**
 * 交易信号视图 — 显示板块突破、趋势反转、异常波动等信号
 */

// 组件导入（Phase 4 创建）
import { renderSignalCard } from '../components/signal-card.js';
import { renderStatsPanel } from '../components/stats-panel.js';

// 数据导入（需要在 data.js 中添加）
import { fetchSignals, fetchSignalHistory } from '../data.js';

/**
 * 渲染信号统计面板
 * @param {Array} signals - 信号列表
 * @returns {string} HTML string
 */
function renderStatsOverview(signals) {
  if (!signals || signals.length === 0) {
    return '<div class="stats-overview-empty">暂无信号数据</div>';
  }

  const stats = {
    total: signals.length,
    bullish: signals.filter(s => s.direction === 'bullish').length,
    bearish: signals.filter(s => s.direction === 'bearish').length,
    highConfidence: signals.filter(s => s.confidence === 'high').length,
  };

  return `
    <div class="stats-overview">
      <div class="stat-item">
        <span class="stat-label">总信号</span>
        <span class="stat-value">${stats.total}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">看涨</span>
        <span class="stat-value stat-bullish">${stats.bullish}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">看跌</span>
        <span class="stat-value stat-bearish">${stats.bearish}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">高置信度</span>
        <span class="stat-value stat-high">${stats.highConfidence}</span>
      </div>
    </div>
  `;
}

/**
 * 渲染信号列表容器
 * @param {Array} signals - 信号列表
 * @returns {string} HTML string
 */
function renderSignalsList(signals) {
  if (!signals || signals.length === 0) {
    return `
      <div class="signals-empty">
        <p class="empty-state">暂无交易信号</p>
        <p class="empty-state" style="font-size: 12px; margin-top: 8px;">
          当市场出现板块突破、趋势反转或异常波动时，系统会自动生成信号
        </p>
      </div>
    `;
  }

  return `
    <div class="signals-list">
      ${signals.map(signal => renderSignalCard(signal)).join('')}
    </div>
  `;
}

/**
 * 渲染信号过滤器和排序选项
 * @returns {string} HTML string
 */
function renderSignalFilters() {
  return `
    <div class="signal-filters">
      <div class="filter-group">
        <label>方向：</label>
        <select id="signal-direction-filter">
          <option value="all">全部</option>
          <option value="bullish">看涨</option>
          <option value="bearish">看跌</option>
        </select>
      </div>
      <div class="filter-group">
        <label>置信度：</label>
        <select id="signal-confidence-filter">
          <option value="all">全部</option>
          <option value="high">高</option>
          <option value="medium">中</option>
          <option value="low">低</option>
        </select>
      </div>
      <div class="filter-group">
        <label>信号类型：</label>
        <select id="signal-type-filter">
          <option value="all">全部</option>
          <option value="breakout">突破</option>
          <option value="reversal">反转</option>
          <option value="anomaly">异常波动</option>
        </select>
      </div>
    </div>
  `;
}

/**
 * 渲染完整信号视图
 * @param {HTMLElement} container - 容器元素
 * @param {Object} options - 配置选项
 */
export async function renderSignalsView(container, options = {}) {
  const { filters = {} } = options;

  try {
    // 获取信号数据
    const signals = await fetchSignals(filters);
    const history = await fetchSignalHistory();

    // 渲染视图
    container.innerHTML = `
      <div class="signals-view">
        <div class="signals-header">
          <h2 class="signals-title">交易信号</h2>
          <p class="signals-subtitle">基于板块异动和市场趋势自动生成</p>
        </div>
        ${renderStatsOverview(signals)}
        ${renderSignalFilters()}
        ${renderSignalsList(signals)}
      </div>
    `;

    // 绑定过滤器事件
    bindFilterEvents();

  } catch (error) {
    console.error('Failed to render signals view:', error);
    container.innerHTML = `
      <div class="signals-error">
        <p class="error-state">加载信号数据失败</p>
        <p class="error-detail">${error.message}</p>
      </div>
    `;
  }
}

/**
 * 绑定过滤器事件
 */
function bindFilterEvents() {
  const directionFilter = document.getElementById('signal-direction-filter');
  const confidenceFilter = document.getElementById('signal-confidence-filter');
  const typeFilter = document.getElementById('signal-type-filter');

  const applyFilters = () => {
    const filters = {
      direction: directionFilter.value,
      confidence: confidenceFilter.value,
      type: typeFilter.value,
    };
    // 重新渲染视图
    const container = document.querySelector('.signals-view');
    if (container) {
      renderSignalsView(container.parentElement, { filters });
    }
  };

  directionFilter?.addEventListener('change', applyFilters);
  confidenceFilter?.addEventListener('change', applyFilters);
  typeFilter?.addEventListener('change', applyFilters);
}
