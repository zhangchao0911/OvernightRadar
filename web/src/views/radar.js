/**
 * 隔夜雷达视图 — Tab 容器
 * 子视图：信号、板块、新闻
 */
import { fetchRadarData } from '../data.js';
import { renderSectorCard } from '../components/radar-card.js';

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
 * 渲染顶部 Tab 导航（信号/板块/新闻）
 * @param {string} activeTab - 当前激活的 tab key
 * @returns {string} HTML string
 */
function renderRadarTabs(activeTab = 'signals') {
  const tabs = [
    { key: 'signals', icon: '🚨', label: '信号' },
    { key: 'sectors', icon: '📊', label: '板块' },
    { key: 'news', icon: '📰', label: '新闻' },
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
 * 渲染信号视图（占位符）
 * @param {Object} report - 雷达数据报告
 * @returns {string} HTML string
 */
function renderSignalsView(report) {
  return `
    <div class="radar-content">
      <p class="empty-state">信号视图开发中...</p>
      <p class="empty-state" style="font-size: 12px; margin-top: 8px;">
        将显示板块突破、趋势反转、异常波动等交易信号
      </p>
    </div>
  `;
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
        <p class="empty-state">暂无板块数据</p>
      </div>
    `;
  }

  return `
    <div class="radar-content">
      ${disclaimerHtml}
      ${report.sectors.map(renderSectorCard).join('')}
    </div>
  `;
}

/**
 * 渲染新闻视图（占位符）
 * @param {Object} report - 雷达数据报告
 * @returns {string} HTML string
 */
function renderNewsView(report) {
  return `
    <div class="radar-content">
      <p class="empty-state">新闻视图开发中...</p>
      <p class="empty-state" style="font-size: 12px; margin-top: 8px;">
        将显示相关板块的新闻快讯和事件提醒
      </p>
    </div>
  `;
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
    <p class="date">${report.market_summary} · ${formatUpdateTime(report.updated_at)}</p>
  `;

  // 根据当前 tab 渲染内容
  function renderContent(tab) {
    switch (tab) {
      case 'signals':
        return renderSignalsView(report);
      case 'sectors':
        return renderSectorsView(report);
      case 'news':
        return renderNewsView(report);
      default:
        return renderSectorsView(report);
    }
  }

  // 渲染完整页面（Tab 导航 + 内容）
  container.innerHTML = renderRadarTabs(initialTab) + renderContent(initialTab);

  // 绑定 Tab 切换事件
  container.querySelectorAll('.radar-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      const newTab = tab.dataset.tab;
      // 更新 Tab 激活状态
      container.querySelectorAll('.radar-tab').forEach(t => {
        t.classList.toggle('active', t.dataset.tab === newTab);
      });
      // 替换内容区
      const contentEl = container.querySelector('.radar-content');
      if (contentEl) {
        contentEl.innerHTML = renderContent(newTab).match(/<div class="radar-content">([\s\S]*)<\/div>/)?.[1] || '';
      }
    });
  });
}
