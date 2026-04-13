/**
 * 新闻视图 — 显示相关板块的新闻快讯和事件提醒
 */

// 组件导入（Phase 4 创建）
import { renderNewsItem } from '../components/news-item.js';

// 数据导入（需要在 data.js 中添加）
import { fetchNews } from '../data.js';

/**
 * 渲染新闻分类标签
 * @param {string} activeCategory - 当前激活的分类
 * @returns {string} HTML string
 */
function renderNewsCategories(activeCategory = 'all') {
  const categories = [
    { key: 'all', label: '全部', icon: '📰' },
    { key: 'policy', label: '政策', icon: '🏛️' },
    { key: 'earnings', label: '财报', icon: '📊' },
    { key: 'm_a', label: '并购', icon: '🤝' },
    { key: 'products', label: '产品', icon: '🚀' },
    { key: 'regulation', label: '监管', icon: '⚖️' },
  ];

  return `
    <div class="news-categories">
      ${categories.map(cat => `
        <button class="news-category ${cat.key === activeCategory ? 'active' : ''}" data-category="${cat.key}">
          <span class="category-icon">${cat.icon}</span>
          <span class="category-label">${cat.label}</span>
        </button>
      `).join('')}
    </div>
  `;
}

/**
 * 渲染新闻列表
 * @param {Array} newsItems - 新闻列表
 * @returns {string} HTML string
 */
function renderNewsList(newsItems) {
  if (!newsItems || newsItems.length === 0) {
    return `
      <div class="news-empty">
        <p class="empty-state">暂无新闻</p>
        <p class="empty-state" style="font-size: 12px; margin-top: 8px;">
          相关板块的新闻快讯和事件提醒将在此显示
        </p>
      </div>
    `;
  }

  return `
    <div class="news-list">
      ${newsItems.map(item => renderNewsItem(item)).join('')}
    </div>
  `;
}

/**
 * 渲染新闻统计摘要
 * @param {Array} newsItems - 新闻列表
 * @returns {string} HTML string
 */
function renderNewsSummary(newsItems) {
  if (!newsItems || newsItems.length === 0) {
    return '';
  }

  const total = newsItems.length;
  const today = new Date().toISOString().split('T')[0];
  const todayCount = newsItems.filter(item => item.date === today).length;
  const importantCount = newsItems.filter(item => item.importance === 'high').length;

  return `
    <div class="news-summary">
      <span class="summary-item">总计 ${total} 条</span>
      ${todayCount > 0 ? `<span class="summary-item">今日 ${todayCount} 条</span>` : ''}
      ${importantCount > 0 ? `<span class="summary-item important">重要 ${importantCount} 条</span>` : ''}
    </div>
  `;
}

/**
 * 渲染新闻搜索框
 * @returns {string} HTML string
 */
function renderNewsSearch() {
  return `
    <div class="news-search">
      <input
        type="text"
        id="news-search-input"
        class="search-input"
        placeholder="搜索新闻标题、板块或关键词..."
      />
      <button id="news-search-btn" class="search-btn">🔍</button>
    </div>
  `;
}

/**
 * 渲染完整新闻视图
 * @param {HTMLElement} container - 容器元素
 * @param {Object} options - 配置选项
 */
export async function renderNewsView(container, options = {}) {
  const { category = 'all', searchQuery = '' } = options;

  try {
    // 获取新闻数据
    const newsItems = await fetchNews({ category, searchQuery });

    // 渲染视图
    container.innerHTML = `
      <div class="news-view">
        <div class="news-header">
          <h2 class="news-title">市场快讯</h2>
          <p class="news-subtitle">相关板块的新闻动态和事件提醒</p>
        </div>
        ${renderNewsSummary(newsItems)}
        ${renderNewsSearch()}
        ${renderNewsCategories(category)}
        ${renderNewsList(newsItems)}
      </div>
    `;

    // 绑定分类切换事件
    bindCategoryEvents();

    // 绑定搜索事件
    bindSearchEvents();

  } catch (error) {
    console.error('Failed to render news view:', error);
    container.innerHTML = `
      <div class="news-error">
        <p class="error-state">加载新闻数据失败</p>
        <p class="error-detail">${error.message}</p>
      </div>
    `;
  }
}

/**
 * 绑定分类切换事件
 */
function bindCategoryEvents() {
  document.querySelectorAll('.news-category').forEach(btn => {
    btn.addEventListener('click', () => {
      const category = btn.dataset.category;
      const container = document.querySelector('.news-view');
      if (container) {
        renderNewsView(container.parentElement, { category });
      }
    });
  });
}

/**
 * 绑定搜索事件
 */
function bindSearchEvents() {
  const searchInput = document.getElementById('news-search-input');
  const searchBtn = document.getElementById('news-search-btn');

  const performSearch = () => {
    const query = searchInput?.value.trim() || '';
    const container = document.querySelector('.news-view');
    if (container) {
      const activeCategory = document.querySelector('.news-category.active')?.dataset.category || 'all';
      renderNewsView(container.parentElement, { category: activeCategory, searchQuery: query });
    }
  };

  searchBtn?.addEventListener('click', performSearch);
  searchInput?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      performSearch();
    }
  });
}
