/**
 * 热力图视图 — 分组方块热力图 + 指标切换
 */
import { fetchWatchlistData } from '../data.js';
import { renderBlock, findEtf } from '../components/heatmap-block.js';
import { renderIndicators } from '../components/indicators.js';
import { showDetail } from '../components/sector-detail.js';

const INDICATORS = [
  { key: 'change_pct', label: '日涨跌', desc: '当日涨跌幅 (%)' },
  { key: 'rel_5', label: '5日强弱', desc: '近5日相对标普500的超额收益' },
  { key: 'rel_20', label: '20日强弱', desc: '近20日(约1月)相对标普500的超额收益' },
  { key: 'rel_60', label: '60日强弱', desc: '近60日(约1季)相对标普500的超额收益' },
  { key: 'rel_120', label: '120日强弱', desc: '近120日(约半年)相对标普500的超额收益' },
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

  // 免责声明 (顶部)
  const disclaimerHtml = `
    <div class="disclaimer wl-top-disclaimer">
      <p>仅供数据参考，不构成投资建议。数据来源：TheMarketMemo、Yahoo Finance。</p>
      <p>REL (相对强度) = ETF 涨跌幅 - 标普500 涨跌幅，正值表示跑赢大盘。</p>
    </div>
  `;

  // 指标切换
  const indicatorsHtml = '<nav class="wl-indicators" id="wl-indicators"></nav>';

  // 热力图容器
  const heatmapHtml = '<div id="wl-heatmap"></div>';

  // 详情面板
  const detailHtml = '<section id="wl-detail" class="wl-detail" style="display:none"></section>';

  container.innerHTML = disclaimerHtml + indicatorsHtml + heatmapHtml + detailHtml;

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
