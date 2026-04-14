/**
 * 隔夜雷达视图 — Tab 容器
 * 子视图：信号、板块、新闻
 */
import { fetchRadarData } from '../data.js';
import { renderSectorCard } from '../components/radar-card.js';
import { renderSignalsView as renderSignalsViewFull, renderSignalsSkeleton } from './signals.js';

// ─── 配置 ────────────────────────────────────────────────
const SECTORS_PER_PAGE = 8; // 板块每页显示数量

// ─── 状态管理 ─────────────────────────────────────────────
let sectorsState = {
  allSectors: [],
  displayedCount: SECTORS_PER_PAGE,
  sortBy: 'change', // change | sentiment | volatility
  isLoading: false,
};

// ─── 排序函数 ─────────────────────────────────────────────
function sortSectors(sectors, sortBy) {
  const sorted = [...sectors];
  switch (sortBy) {
    case 'change':
      // 按涨跌幅排序（绝对值大的在前）
      sorted.sort((a, b) => Math.abs(b.change_pct) - Math.abs(a.change_pct));
      break;
    case 'sentiment':
      // 按情绪排序（强 > 中 > 弱）
      const sentimentOrder = { strong: 3, neutral: 2, weak: 1 };
      sorted.sort((a, b) => sentimentOrder[b.sentiment] - sentimentOrder[a.sentiment]);
      break;
    case 'volatility':
      // 按波动率排序（高的在前）
      sorted.sort((a, b) => (b.volatility || 0) - (a.volatility || 0));
      break;
  }
  return sorted;
}

/**
 * 渲染板块骨架屏
 * @param {number} count - 骨架屏卡片数量
 * @returns {string} HTML string
 */
function renderSectorsSkeleton(count = 4) {
  return `
    <div class="sectors-list">
      ${Array(count).fill(0).map(() => `
        <div class="skeleton-card card skeleton">
          <div class="skeleton-sentiment skeleton"></div>
          <div class="skeleton skeleton-detail"></div>
          <div class="skeleton skeleton-detail"></div>
          <div class="skeleton-stocks">
            <div class="skeleton skeleton-stock-item"></div>
            <div class="skeleton skeleton-stock-item"></div>
            <div class="skeleton skeleton-stock-item"></div>
          </div>
        </div>
      `).join('')}
    </div>
  `;
}

/**
 * 渲染板块排序选择器
 * @param {string} currentSort - 当前排序方式
 * @returns {string} HTML string
 */
function renderSectorsSortSelector(currentSort = 'change') {
  const options = [
    { value: 'change', label: '涨跌幅' },
    { value: 'sentiment', label: '情绪' },
    { value: 'volatility', label: '波动率' },
  ];

  return `
    <div class="sort-selector">
      <label class="sort-label">排序：</label>
      <select class="sort-select" id="sectors-sort">
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
 * 渲染加载更多按钮
 * @param {number} remaining - 剩余未加载的数量
 * @returns {string} HTML string
 */
function renderSectorsLoadMoreButton(remaining) {
  if (remaining <= 0) {
    return `
      <div class="load-more-done">
        <span class="done-text">已加载全部内容</span>
      </div>
    `;
  }

  return `
    <div class="load-more-container">
      <button class="load-more-btn" id="load-more-sectors">
        <span class="btn-text">加载更多</span>
        <span class="btn-count">(剩余 ${remaining})</span>
      </button>
    </div>
  `;
}

function formatChange(value) {
  if (value === null || value === undefined) return '—';
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
}

function formatUpdateTime(isoString) {
  if (!isoString) return '';
  const match = isoString.match(/(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):/);
  if (match) {
    const [, year, month, day, hours, minutes] = match;
    return `${year}-${month}-${day} ${hours}:${minutes}`;
  }
  return isoString;
}

/**
 * 渲染顶部 Tab 导航（信号/板块）
 * @param {string} activeTab - 当前激活的 tab key
 * @returns {string} HTML string
 */
function renderRadarTabs(activeTab = 'sectors') {
  // 信号图标（铃铛）- 金色 #F59E0B
  const signalsIcon = `
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
      <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
    </svg>
  `;

  // 板块图标（网格）- 紫色 #8B5CF6
  const sectorsIcon = `
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <rect x="3" y="3" width="7" height="7"></rect>
      <rect x="14" y="3" width="7" height="7"></rect>
      <rect x="3" y="14" width="7" height="7"></rect>
      <rect x="14" y="14" width="7" height="7"></rect>
    </svg>
  `;

  const tabs = [
    { key: 'sectors', icon: sectorsIcon, label: '板块' },
    { key: 'signals', icon: signalsIcon, label: '信号' },
  ];

  return `
    <div class="radar-tabs">
      ${tabs.map(tab => `
        <button class="radar-tab ${tab.key === activeTab ? 'active' : ''}" data-tab="${tab.key}">
          <span class="radar-tab-icon">${tab.icon}</span>
          <span class="radar-tab-label">${tab.label}</span>
        </button>
      `).join('')}
    </div>
  `;
}

/**
 * 渲染信号视图
 * @param {Object} report - 雷达数据报告
 * @returns {string} HTML string
 */
async function renderSignalsView(report) {
  const tempContainer = document.createElement('div');
  try {
    await renderSignalsViewFull(tempContainer);
    return `<div class="radar-content">${tempContainer.innerHTML}</div>`;
  } catch (e) {
    console.error('渲染信号视图失败:', e);
    return `<div class="radar-content"><p class="empty-state">信号视图加载失败</p></div>`;
  }
}

/**
 * 渲染板块视图（原雷达卡片内容）
 * @param {Object} report - 雷达数据报告
 * @returns {string} HTML string
 */
function renderSectorsView(report) {
  const disclaimerHtml = `
    <div class="disclaimer wl-top-disclaimer">
      <p>仅供数据参考，不构成投资建议。数据来源：Yahoo Finance、AKShare、公开市场数据。</p>
    </div>
  `;

  if (!report.sectors || report.sectors.length === 0) {
    return `
      <div class="radar-content">
        ${disclaimerHtml}
        <div class="empty-state empty-sectors">
          <svg class="empty-icon" xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="3" width="7" height="7"></rect>
            <rect x="14" y="3" width="7" height="7"></rect>
            <rect x="3" y="14" width="7" height="7"></rect>
            <rect x="14" y="14" width="7" height="7"></rect>
          </svg>
          <h3 class="empty-title">暂无板块数据</h3>
          <p class="empty-desc">
            数据更新中，请稍后刷新查看
          </p>
        </div>
      </div>
    `;
  }

  // 保存到状态
  sectorsState.allSectors = report.sectors;
  sectorsState.displayedCount = SECTORS_PER_PAGE;
  sectorsState.sortBy = 'change';

  const sortedSectors = sortSectors(sectorsState.allSectors, sectorsState.sortBy);
  const displayedSectors = sortedSectors.slice(0, sectorsState.displayedCount);
  const remainingCount = sortedSectors.length - sectorsState.displayedCount;

  return `
    <div class="radar-content" id="sectors-content">
      ${disclaimerHtml}
      ${renderSectorsSortSelector(sectorsState.sortBy)}
      <div class="sectors-list" id="sectors-list">
        ${displayedSectors.map(renderSectorCard).join('')}
      </div>
      ${renderSectorsLoadMoreButton(remainingCount)}
    </div>
  `;
}

/**
 * 加载更多板块
 */
function loadMoreSectors() {
  if (sectorsState.isLoading) return;

  sectorsState.isLoading = true;

  // 显示加载中状态
  const loadMoreBtn = document.getElementById('load-more-sectors');
  const sectorsList = document.getElementById('sectors-list');

  if (loadMoreBtn) {
    loadMoreBtn.classList.add('loading');
    loadMoreBtn.disabled = true;
    loadMoreBtn.innerHTML = `
      <div class="spinner"></div>
      <span class="btn-text">加载中...</span>
    `;
  }

  // 模拟异步加载
  setTimeout(() => {
    sectorsState.displayedCount += SECTORS_PER_PAGE;
    const sortedSectors = sortSectors(sectorsState.allSectors, sectorsState.sortBy);
    const newSectors = sortedSectors.slice(
      sectorsState.displayedCount - SECTORS_PER_PAGE,
      sectorsState.displayedCount
    );

    // 追加新内容
    if (sectorsList) {
      newSectors.forEach(sector => {
        const card = document.createElement('div');
        card.innerHTML = renderSectorCard(sector);
        sectorsList.appendChild(card.firstElementChild);
      });
    }

    // 更新加载更多按钮
    const remainingCount = sortedSectors.length - sectorsState.displayedCount;
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
          <button class="load-more-btn" id="load-more-sectors">
            <span class="btn-text">加载更多</span>
            <span class="btn-count">(剩余 ${remainingCount})</span>
          </button>
        `;
      }
    }

    sectorsState.isLoading = false;

    // 重新绑定事件
    const newLoadMoreBtn = document.getElementById('load-more-sectors');
    if (newLoadMoreBtn) {
      newLoadMoreBtn.addEventListener('click', loadMoreSectors);
    }
  }, 300);
}

/**
 * 绑定板块视图事件
 */
function bindSectorsEvents() {
  // 加载更多按钮
  const loadMoreBtn = document.getElementById('load-more-sectors');
  if (loadMoreBtn) {
    loadMoreBtn.addEventListener('click', loadMoreSectors);
  }

  // 排序选择器
  const sortSelect = document.getElementById('sectors-sort');
  if (sortSelect) {
    sortSelect.addEventListener('change', () => {
      sectorsState.sortBy = sortSelect.value;
      sectorsState.displayedCount = SECTORS_PER_PAGE;

      // 重新渲染
      const sortedSectors = sortSectors(sectorsState.allSectors, sectorsState.sortBy);
      const displayedSectors = sortedSectors.slice(0, sectorsState.displayedCount);
      const remainingCount = sortedSectors.length - sectorsState.displayedCount;

      const sectorsList = document.getElementById('sectors-list');
      if (sectorsList) {
        sectorsList.innerHTML = displayedSectors.map(renderSectorCard).join('');
      }

      const loadMoreContainer = document.querySelector('.load-more-container');
      if (loadMoreContainer) {
        loadMoreContainer.outerHTML = renderSectorsLoadMoreButton(remainingCount);
      }

      bindSectorsEvents();
    });
  }
}

/**
 * 渲染隔夜雷达视图（Tab 容器）。
 * @param {HTMLElement} container - #view-container
 * @param {HTMLElement} header - #app-header
 * @param {string} initialTab - 初始显示的 tab (signals | sectors | news)
 */
export async function renderRadarView(container, header, initialTab = 'sectors') {
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
  const indexNames = { sp500: '标普500', nasdaq: '纳斯达克', dow: '道琼斯' };
  let indicesHtml = '';
  for (const [key, name] of Object.entries(indexNames)) {
    if (report.market_indices && report.market_indices[key]) {
      const change = report.market_indices[key].change_pct;
      const cls = change >= 0 ? 'up' : 'down';
      // 使用 SVG 图标替代 emoji
      const trendIcon = change >= 0
        ? `<svg class="icon icon-sm" style="color: var(--color-bull);" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline></svg>`
        : `<svg class="icon icon-sm" style="color: var(--color-bear);" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 18 13.5 8.5 8.5 13.5 1 6"></polyline><polyline points="17 18 23 18 23 12"></polyline></svg>`;
      indicesHtml += `<span class="index-item">${trendIcon} ${name}<span class="${cls}">${formatChange(change)}</span></span>`;
    }
  }

  header.innerHTML = `
    <h1 class="title">隔夜雷达</h1>
    <p class="slogan">昨夜美股异动，今日A股看点</p>
    <div class="market-indices">${indicesHtml}</div>
    <p class="date">${report.market_summary} · ${formatUpdateTime(report.updated_at)}</p>
  `;

  // 根据当前 tab 渲染内容（异步）
  async function renderContent(tab) {
    switch (tab) {
      case 'signals':
        return await renderSignalsView(report);
      case 'sectors':
        return renderSectorsView(report);
      default:
        return renderSectorsView(report);
    }
  }

  // 渲染完整页面（Tab 导航 + 内容）
  const initialContent = await renderContent(initialTab);
  container.innerHTML = renderRadarTabs(initialTab) + initialContent;

  // 绑定 Tab 切换事件
  container.querySelectorAll('.radar-tab').forEach(tab => {
    tab.addEventListener('click', async () => {
      const newTab = tab.dataset.tab;
      // 更新 Tab 激活状态
      container.querySelectorAll('.radar-tab').forEach(t => {
        t.classList.toggle('active', t.dataset.tab === newTab);
      });
      // 替换内容区
      const contentEl = container.querySelector('.radar-content');
      if (contentEl) {
        // 显示骨架屏
        if (newTab === 'sectors') {
          contentEl.innerHTML = renderSectorsSkeleton(4);
        } else if (newTab === 'signals') {
          contentEl.innerHTML = renderSignalsSkeleton ? renderSignalsSkeleton(3) : '<div class="loading"><div class="loading-spinner"></div></div>';
        }

        // 异步加载内容
        setTimeout(async () => {
          const newContent = await renderContent(newTab);
          const match = newContent.match(/<div class="radar-content">([\s\S]*)<\/div>/);
          contentEl.innerHTML = match ? match[1] : newContent;

          // 绑定事件
          if (newTab === 'sectors') {
            bindSectorsEvents();
          }
        }, 200);
      }
    });
  });

  // 绑定初始视图事件
  if (initialTab === 'sectors') {
    bindSectorsEvents();
  }
}
