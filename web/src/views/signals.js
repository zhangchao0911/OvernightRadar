/**
 * 交易信号视图 — 显示板块突破、趋势反转、异常波动等信号
 */

// 组件导入
import { renderSignalCard } from '../components/signal-card.js';

// 数据导入（需要在 data.js 中添加）
import { fetchSignals, fetchSignalHistory } from '../data.js';

// ─── 配置 ────────────────────────────────────────────────
const ITEMS_PER_PAGE = 10; // 每页显示数量

// ─── 状态管理 ─────────────────────────────────────────────
let signalsState = {
  allSignals: [],
  displayedCount: ITEMS_PER_PAGE,
  sortBy: 'time', // time | confidence | level
  isLoading: false,
};

// ─── 排序函数 ─────────────────────────────────────────────
function sortSignals(signals, sortBy) {
  const sorted = [...signals];
  switch (sortBy) {
    case 'time':
      // 按时间倒序（最新的在前）
      sorted.sort((a, b) => {
        const timeA = new Date(a.generated_at || 0).getTime();
        const timeB = new Date(b.generated_at || 0).getTime();
        return timeB - timeA;
      });
      break;
    case 'confidence':
      // 按置信度排序（高 > 中 > 低）
      const confidenceOrder = { high: 3, medium: 2, low: 1 };
      sorted.sort((a, b) => confidenceOrder[b.confidence] - confidenceOrder[a.confidence]);
      break;
    case 'level':
      // 按信号等级排序（强 > 中 > 弱）
      const levelOrder = { strong: 3, medium: 2, weak: 1 };
      sorted.sort((a, b) => levelOrder[b.level] - levelOrder[a.level]);
      break;
  }
  return sorted;
}

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
 * 渲染加载更多按钮
 * @param {number} remaining - 剩余未加载的数量
 * @returns {string} HTML string
 */
function renderLoadMoreButton(remaining) {
  if (remaining <= 0) {
    return `
      <div class="load-more-done">
        <span class="done-text">已加载全部内容</span>
      </div>
    `;
  }

  return `
    <div class="load-more-container">
      <button class="load-more-btn" id="load-more-signals">
        <span class="btn-text">加载更多</span>
        <span class="btn-count">(剩余 ${remaining})</span>
      </button>
    </div>
  `;
}

/**
 * 渲染排序选择器
 * @param {string} currentSort - 当前排序方式
 * @returns {string} HTML string
 */
function renderSortSelector(currentSort = 'time') {
  const options = [
    { value: 'time', label: '时间' },
    { value: 'confidence', label: '置信度' },
    { value: 'level', label: '信号等级' },
  ];

  return `
    <div class="sort-selector">
      <label class="sort-label">排序：</label>
      <select class="sort-select" id="signals-sort">
        ${options.map(opt => `
          <option value="${opt.value}" ${opt.value === currentSort ? 'selected' : ''}>
            ${opt.label}
          </option>
        `).join('')}
      </select>
    </div>
  `;
}

/**
 * 渲染信号列表容器
 * @param {Array} signals - 信号列表
 * @param {string} generatedAt - 信号生成时间
 * @returns {string} HTML string
 */
function renderSignalsList(signals, generatedAt = null) {
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
      ${signals.map(signal => renderSignalCard(signal, generatedAt)).join('')}
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
 * 渲染信号骨架屏（用于导出）
 * @param {number} count - 骨架屏卡片数量
 * @returns {string} HTML string
 */
export function renderSignalsSkeleton(count = 3) {
  return `
    <div class="signals-list">
      ${Array(count).fill(0).map(() => `
        <div class="skeleton-card signal-card skeleton">
          <div class="skeleton-header">
            <div class="skeleton skeleton-title"></div>
            <div class="skeleton skeleton-meta"></div>
          </div>
          <div class="skeleton skeleton-action"></div>
          <div class="skeleton skeleton-reason"></div>
          <div class="skeleton skeleton-reason"></div>
        </div>
      `).join('')}
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
    const { signals, metadata, generated_at } = await fetchSignals(filters);
    const history = await fetchSignalHistory();

    // 保存到状态
    signalsState.allSignals = signals || [];
    signalsState.displayedCount = ITEMS_PER_PAGE;
    signalsState.sortBy = 'time';

    // 如果没有信号，显示优化的空状态
    if (!signals || signals.length === 0) {
      renderEmptySignalsView(container);
      return;
    }

    // 渲染完整视图
    renderSignalsContent(container, generated_at);

    // 绑定事件
    bindSignalsEvents(container);

  } catch (error) {
    console.error('Failed to render signals view:', error);
    container.innerHTML = `
      <div class="signals-view">
        <div class="signals-error">
          <p class="error-state">加载信号数据失败</p>
          <p class="error-detail">${error.message}</p>
        </div>
      </div>
    `;
  }
}

/**
 * 渲染空状态视图
 */
function renderEmptySignalsView(container) {
  container.innerHTML = `
    <div class="signals-view">
      <div class="signals-header">
        <h2 class="signals-title">交易信号</h2>
        <p class="signals-subtitle">基于板块异动和市场趋势自动生成</p>
      </div>
      <div class="empty-state empty-signals">
        <svg class="empty-icon" xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
          <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
        </svg>
        <h3 class="empty-title">暂无信号</h3>
        <p class="empty-desc">
          当市场出现板块突破、趋势反转或异常波动时，系统会自动生成信号
        </p>
      </div>
    </div>
  `;
}

/**
 * 渲染信号内容（支持增量更新）
 */
function renderSignalsContent(container, generatedAt = null) {
  const sortedSignals = sortSignals(signalsState.allSignals, signalsState.sortBy);
  const displayedSignals = sortedSignals.slice(0, signalsState.displayedCount);
  const remainingCount = sortedSignals.length - signalsState.displayedCount;

  container.innerHTML = `
    <div class="signals-view">
      <div class="signals-list" id="signals-list">
        ${displayedSignals.map(signal => renderSignalCard(signal, generatedAt)).join('')}
      </div>
      ${renderLoadMoreButton(remainingCount)}
    </div>
  `;
}

/**
 * 加载更多信号
 */
function loadMoreSignals() {
  if (signalsState.isLoading) return;

  signalsState.isLoading = true;

  // 显示加载中状态
  const loadMoreBtn = document.getElementById('load-more-signals');
  const signalsList = document.getElementById('signals-list');

  if (loadMoreBtn) {
    loadMoreBtn.classList.add('loading');
    loadMoreBtn.disabled = true;
    loadMoreBtn.innerHTML = `
      <div class="spinner"></div>
      <span class="btn-text">加载中...</span>
    `;
  }

  // 模拟异步加载（实际项目中这里应该是真实的 API 调用）
  setTimeout(() => {
    signalsState.displayedCount += ITEMS_PER_PAGE;
    const sortedSignals = sortSignals(signalsState.allSignals, signalsState.sortBy);
    const newSignals = sortedSignals.slice(
      signalsState.displayedCount - ITEMS_PER_PAGE,
      signalsState.displayedCount
    );

    // 追加新内容
    if (signalsList) {
      newSignals.forEach(signal => {
        const card = document.createElement('div');
        card.innerHTML = renderSignalCard(signal, null);
        signalsList.appendChild(card.firstElementChild);
      });
    }

    // 更新加载更多按钮
    const remainingCount = sortedSignals.length - signalsState.displayedCount;
    const loadMoreContainer = document.querySelector('.load-more-container');

    if (loadMoreContainer) {
      if (remainingCount <= 0) {
        loadMoreContainer.outerHTML = `
          <div class="load-more-done">
            <span class="done-text">已加载全部内容</span>
          </div>
        `;
      } else {
        loadMoreContainer.innerHTML = `
          <button class="load-more-btn" id="load-more-signals">
            <span class="btn-text">加载更多</span>
            <span class="btn-count">(剩余 ${remainingCount})</span>
          </button>
        `;
      }
    }

    signalsState.isLoading = false;

    // 重新绑定事件
    const newLoadMoreBtn = document.getElementById('load-more-signals');
    if (newLoadMoreBtn) {
      newLoadMoreBtn.addEventListener('click', loadMoreSignals);
    }
  }, 300);
}

/**
 * 绑定事件处理器
 */
function bindSignalsEvents(container) {
  // 加载更多按钮
  const loadMoreBtn = document.getElementById('load-more-signals');
  if (loadMoreBtn) {
    loadMoreBtn.addEventListener('click', loadMoreSignals);
  }

  // 排序选择器
  const sortSelect = document.getElementById('signals-sort');
  if (sortSelect) {
    sortSelect.addEventListener('change', (e) => {
      signalsState.sortBy = e.target.value;
      signalsState.displayedCount = ITEMS_PER_PAGE;
      renderSignalsContent(container, null);
      bindSignalsEvents(container);
    });
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
