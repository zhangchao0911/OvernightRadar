/**
 * 热力图视图 — 分组方块热力图 + 指标切换
 */
import { fetchWatchlistData, fetchCNWatchlistData } from '../data.js';
import { renderBlock, findEtf } from '../components/heatmap-block.js';
import { renderIndicators } from '../components/indicators.js';
import { showDetail } from '../components/sector-detail.js';

/**
 * 格式化更新时间为北京时间 (YYYY-MM-DD HH:mm)
 * 直接解析 ISO 字符串，不受浏览器时区影响
 */
function formatUpdateTime(isoString) {
  if (!isoString) return '';
  // ISO 格式: 2026-04-13T00:57:28+08:00
  // 提取日期时间部分，忽略时区（后端已确保是北京时间）
  const match = isoString.match(/(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):/);
  if (match) {
    const [, year, month, day, hours, minutes] = match;
    return `${year}-${month}-${day} ${hours}:${minutes}`;
  }
  return isoString;
}

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
let currentMarket = 'us'; // 'us' or 'cn'
let usWatchlistData = null;
let cnWatchlistData = null;
let currentBenchmark = 'hs300'; // A股基准

// ─── 市场切换器渲染 ───────────────────────────────────────
function renderMarketSwitcher(container, currentMarket, onSwitch) {
  const markets = [
    { key: 'us', label: '美股' },
    { key: 'cn', label: 'A股' },
  ];

  container.innerHTML = `
    <div class="wl-market-switcher">
      ${markets.map(m => `
        <button
          class="wl-market-btn ${m.key === currentMarket ? 'active' : ''}"
          data-market="${m.key}"
        >
          ${m.label}
        </button>
      `).join('')}
    </div>
  `;

  container.querySelectorAll('.wl-market-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const market = btn.dataset.market;
      console.log('[MarketSwitcher] Button clicked:', market);
      // 直接触发切换，不再检查 currentMarket（因为参数可能过期）
      onSwitch(market);
    });
  });
}

/**
 * 渲染热力图视图。
 * @param {HTMLElement} container - #view-container
 * @param {HTMLElement} header - #app-header
 */
export async function renderHeatmapView(container, header) {
  console.log('[HeatmapView] renderHeatmapView called');
  // 加载美股数据（如果还没加载）
  if (!usWatchlistData) {
    console.log('[HeatmapView] Loading US data...');
    usWatchlistData = await fetchWatchlistData();
    console.log('[HeatmapView] US data loaded:', usWatchlistData ? `${usWatchlistData.total_etfs} etfs` : 'null');
  }

  // 默认显示美股
  console.log('[HeatmapView] Rendering US market view');
  await renderMarketView(container, header, 'us');
}

// ─── 渲染指定市场的视图 ──────────────────────────────────
async function renderMarketView(container, header, market, benchmark = null) {
  console.log('[MarketView] Switching to market:', market);
  currentMarket = market;
  const isCN = market === 'cn';

  // 显示加载状态
  const marketName = isCN ? 'A股' : '美股';
  header.innerHTML = `
    <h1 class="title">市场观察表</h1>
    <p class="slogan">正在加载${marketName}数据...</p>
  `;
  container.innerHTML = '<p class="empty-state">加载中...</p>';

  // 加载数据
  let data;
  if (market === 'us') {
    console.log('[MarketView] Loading US data...');
    if (!usWatchlistData) {
      usWatchlistData = await fetchWatchlistData();
    }
    data = usWatchlistData;
  } else {
    console.log('[MarketView] Loading CN data...');
    if (!cnWatchlistData) {
      cnWatchlistData = await fetchCNWatchlistData(currentBenchmark);
    }
    data = cnWatchlistData;
  }

  console.log('[MarketView] Data loaded:', data ? `${data.total_sectors || '?'} sectors` : 'null');

  if (!data) {
    header.innerHTML = `
      <h1 class="title">市场观察表</h1>
      <p class="slogan">暂无数据</p>
    `;
    container.innerHTML = '<p class="empty-state">暂无数据</p>';
    return;
  }
  const updateTime = formatUpdateTime(data.updated_at);

  // Header
  header.innerHTML = `
    <div class="wl-header-top">
      <div>
        <h1 class="title">市场观察表</h1>
        <p class="slogan">
          Market Watchlist ·
          ${isCN ? 'A股申万板块相对强度热力图' : '美股 ETF 相对强度热力图'}
        </p>
        <p class="date">更新时间: ${updateTime || data.date}</p>
      </div>
    </div>
  `;

  // 市场切换器（顶部水平）
  const marketSwitcherHtml = '<div id="wl-market-switcher" class="wl-market-switcher-top"></div>';

  // 免责声明
  const disclaimerHtml = `
    <div class="disclaimer wl-top-disclaimer">
      <p>仅供数据参考，不构成投资建议。数据来源：${isCN ? 'AkShare' : 'TheMarketMemo、Yahoo Finance'}。</p>
      <p>REL (相对强度) = ${isCN ? '行业' : 'ETF'}涨跌幅 - ${isCN ? '基准指数' : '标普500'}涨跌幅，正值表示跑赢大盘。</p>
    </div>
  `;

  // 主内容区
  const mainContentHtml = `
    <div class="wl-main-layout">
      <div class="wl-right-content">
        ${marketSwitcherHtml}
        <nav class="wl-indicators" id="wl-indicators"></nav>
        <div id="wl-heatmap"></div>
      </div>
    </div>
  `;

  // 详情面板
  const detailHtml = '<section id="wl-detail" class="wl-detail" style="display:none"></section>';

  container.innerHTML = disclaimerHtml + mainContentHtml + detailHtml;

  // 渲染市场切换器（使用最新的 currentMarket）
  const switcherContainer = document.getElementById('wl-market-switcher');
  renderMarketSwitcher(
    switcherContainer,
    currentMarket,
    (newMarket) => {
      // 更新按钮状态
      switcherContainer.querySelectorAll('.wl-market-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.market === newMarket);
      });
      renderMarketView(container, header, newMarket);
    }
  );

  // 渲染指标切换
  const cnIndicators = isCN ? [
    { key: 'change_pct', label: '日涨跌', desc: '当日涨跌幅 (%)', hasBenchmark: true },
    { key: 'rel_5', label: '5日强弱', desc: `近5日相对${data.benchmark?.name || '沪深300'}的超额收益` },
    { key: 'rel_20', label: '20日强弱', desc: `近20日(约1月)相对${data.benchmark?.name || '沪深300'}的超额收益` },
    { key: 'rel_60', label: '60日强弱', desc: `近60日(约1季)相对${data.benchmark?.name || '沪深300'}的超额收益` },
    { key: 'rel_120', label: '120日强弱', desc: `近120日(约半年)相对${data.benchmark?.name || '沪深300'}的超额收益` },
  ] : INDICATORS;

  renderIndicators(
    document.getElementById('wl-indicators'),
    cnIndicators,
    currentIndicator,
    (key) => {
      currentIndicator = key;
      renderHeatmapContent(document.getElementById('wl-heatmap'), data.groups, currentIndicator, isCN);
    }
  );

  // 渲染基准切换器（仅A股，单独一行）
  if (isCN) {
    const indicatorsContainer = document.getElementById('wl-indicators');
    const benchmarkHtml = `
      <div class="wl-benchmark-row">
        <span class="wl-benchmark-label">基准:</span>
        <button class="wl-benchmark-btn ${currentBenchmark === 'hs300' ? 'active' : ''}" data-benchmark="hs300">沪深300</button>
        <button class="wl-benchmark-btn ${currentBenchmark === 'zz500' ? 'active' : ''}" data-benchmark="zz500">中证500</button>
      </div>
    `;
    // 插入到指标按钮行之前
    const indicatorsRow = indicatorsContainer.querySelector('.wl-indicators-row');
    if (indicatorsRow) {
      indicatorsRow.insertAdjacentHTML('beforebegin', benchmarkHtml);
    }

    // 绑定基准切换事件
    indicatorsContainer.querySelectorAll('.wl-benchmark-btn').forEach(btn => {
      btn.addEventListener('click', async () => {
        const newBenchmark = btn.dataset.benchmark;
        if (newBenchmark !== currentBenchmark) {
          currentBenchmark = newBenchmark;
          // 更新按钮状态
          indicatorsContainer.querySelectorAll('.wl-benchmark-btn').forEach(b => {
            b.classList.toggle('active', b.dataset.benchmark === newBenchmark);
          });
          // 重新获取对应基准的数据
          cnWatchlistData = null;
          await renderMarketView(container, header, 'cn');
        }
      });
    });
  }

  // 渲染热力图
  renderHeatmapContent(document.getElementById('wl-heatmap'), data.groups, currentIndicator, isCN);

  // 初始化详情面板
  showDetail(null, null);

  console.log('[MarketView] Render complete for market:', market);
}

function renderHeatmapContent(container, groups, indicatorKey, isCN = false) {
  if (!groups) {
    container.innerHTML = '<p class="empty-state">暂无数据</p>';
    return;
  }

  let html = '';
  for (const groupKey of Object.keys(groups)) {
    const group = groups[groupKey];

    // 美股用 etfs，A股用 sectors
    const items = group.etfs || group.sectors;
    if (!items || items.length === 0) continue;

    html += `
      <div class="wl-group">
        <h2 class="wl-group-title">${group.display_name}</h2>
        <div class="wl-blocks">
          ${items.map(item => renderBlock(item, indicatorKey, isCN)).join('')}
        </div>
      </div>
    `;
  }

  container.innerHTML = html;

  // 绑定点击事件（同时支持 ticker 和 code）
  container.querySelectorAll('.wl-block').forEach(block => {
    block.addEventListener('click', () => {
      const tickerOrCode = block.dataset.code || block.dataset.ticker;
      const item = findEtf(groups, tickerOrCode);
      if (item) {
        const detailEl = document.getElementById('wl-detail');
        showDetail(item, detailEl);
      }
    });
  });
}
