/**
 * 热力图视图 — 分组方块热力图 + 指标切换
 */
import { fetchWatchlistData } from '../data.js';
import { renderBlock, findEtf } from '../components/heatmap-block.js';
import { renderIndicators } from '../components/indicators.js';
import { showDetail } from '../components/sector-detail.js';

const INDICATORS = [
  { key: 'change_pct', label: '1D%' },
  { key: 'rel_5', label: 'REL5' },
  { key: 'rel_20', label: 'REL20' },
  { key: 'rel_60', label: 'REL60' },
  { key: 'rel_120', label: 'REL120' },
];

const GROUP_ORDER = [
  'broad', 'equal_weighted', 'market_cap_weighted',
  'factors', 'growth', 'thematic', 'ark',
];

let currentIndicator = 'change_pct';
let watchlistData = null;

/**
 * 渲染热力图视图。
 * @param {HTMLElement} container - #view-container
 * @param {HTMLElement} header - #app-header
 */
export async function renderHeatmapView(container, header) {
  // 只加载一次数据
  if (!watchlistData) {
    watchlistData = await fetchWatchlistData();
  }

  if (!watchlistData) {
    header.innerHTML = `
      <h1 class="title">市场观察表</h1>
      <p class="slogan">Market Watchlist · 美股 ETF 相对强度热力图</p>
    `;
    container.innerHTML = '<p class="empty-state">暂无热力图数据</p>';
    return;
  }

  // Header
  header.innerHTML = `
    <h1 class="title">市场观察表</h1>
    <p class="slogan">Market Watchlist · 美股 ETF 相对强度热力图</p>
    <p class="date">更新时间: ${watchlistData.updated_at || watchlistData.date}</p>
  `;

  // 指标切换
  const indicatorsHtml = '<nav class="wl-indicators" id="wl-indicators"></nav>';

  // 热力图容器
  const heatmapHtml = '<div id="wl-heatmap"></div>';

  // 详情面板
  const detailHtml = '<section id="wl-detail" class="wl-detail" style="display:none"></section>';

  // 免责声明
  const disclaimerHtml = `
    <footer class="disclaimer">
      <p class="disclaimer-title">⚠️ 免责声明</p>
      <p>本工具仅供数据参考，不构成任何投资建议。</p>
      <p>数据来源：TheMarketMemo Market Watchlist、Yahoo Finance。</p>
      <p>REL (相对强度) = ETF 涨跌幅 - 标普500 涨跌幅。</p>
    </footer>
  `;

  container.innerHTML = indicatorsHtml + heatmapHtml + detailHtml + disclaimerHtml;

  // 渲染指标切换
  renderIndicators(
    document.getElementById('wl-indicators'),
    INDICATORS,
    currentIndicator,
    (key) => {
      currentIndicator = key;
      renderHeatmapContent(document.getElementById('wl-heatmap'), watchlistData.groups, currentIndicator);
    }
  );

  // 渲染热力图
  renderHeatmapContent(document.getElementById('wl-heatmap'), watchlistData.groups, currentIndicator);

  // 初始化详情面板
  showDetail(null, null); // reset
}

function renderHeatmapContent(container, groups, indicatorKey) {
  if (!groups) {
    container.innerHTML = '<p class="empty-state">暂无数据</p>';
    return;
  }

  let html = '';
  for (const groupKey of GROUP_ORDER) {
    const group = groups[groupKey];
    if (!group || !group.etfs || group.etfs.length === 0) continue;

    html += `
      <div class="wl-group">
        <h2 class="wl-group-title">${group.display_name}</h2>
        <div class="wl-blocks">
          ${group.etfs.map(etf => renderBlock(etf, indicatorKey)).join('')}
        </div>
      </div>
    `;
  }

  container.innerHTML = html;

  // 绑定点击事件
  container.querySelectorAll('.wl-block').forEach(block => {
    block.addEventListener('click', () => {
      const ticker = block.dataset.ticker;
      const etf = findEtf(groups, ticker);
      if (etf) {
        const detailEl = document.getElementById('wl-detail');
        showDetail(etf, detailEl);
      }
    });
  });
}
