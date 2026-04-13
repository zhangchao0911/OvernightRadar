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
      if (market !== currentMarket) {
        onSwitch(market);
      }
    });
  });
}

// ─── 基准切换器渲染（仅 A 股）─────────────────────────────
function renderBenchmarkSwitcher(container, currentBenchmark, onSwitch) {
  const benchmarks = [
    { key: 'hs300', label: '沪深300' },
    { key: 'zz500', label: '中证500' },
  ];

  container.innerHTML = `
    <div class="wl-benchmark-switcher">
      <span class="wl-benchmark-label">基准:</span>
      ${benchmarks.map(b => `
        <button
          class="wl-benchmark-btn ${b.key === currentBenchmark ? 'active' : ''}"
          data-benchmark="${b.key}"
        >
          ${b.label}
        </button>
      `).join('')}
    </div>
  `;

  container.querySelectorAll('.wl-benchmark-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const benchmark = btn.dataset.benchmark;
      if (benchmark !== currentBenchmark) {
        onSwitch(benchmark);
      }
    });
  });
}

/**
 * 渲染热力图视图。
 * @param {HTMLElement} container - #view-container
 * @param {HTMLElement} header - #app-header
 */
export async function renderHeatmapView(container, header) {
  // 加载美股数据（如果还没加载）
  if (!usWatchlistData) {
    usWatchlistData = await fetchWatchlistData();
  }

  // 默认显示美股
  await renderMarketView(container, header, 'us');
}

// ─── 渲染指定市场的视图 ──────────────────────────────────
async function renderMarketView(container, header, market, benchmark = null) {
  currentMarket = market;

  // 加载数据
  let data;
  if (market === 'us') {
    data = usWatchlistData;
  } else {
    if (!cnWatchlistData) {
      cnWatchlistData = await fetchCNWatchlistData();
    }
    data = cnWatchlistData;
  }

  if (!data) {
    header.innerHTML = `
      <h1 class="title">市场观察表</h1>
      <p class="slogan">暂无数据</p>
    `;
    container.innerHTML = '<p class="empty-state">暂无数据</p>';
    return;
  }

  const isCN = market === 'cn';
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

  // 市场切换器
  const marketSwitcherHtml = '<div id="wl-market-switcher" class="wl-market-switcher-container"></div>';

  // 免责声明
  const disclaimerHtml = `
    <div class="disclaimer wl-top-disclaimer">
      <p>仅供数据参考，不构成投资建议。数据来源：${isCN ? 'AkShare' : 'TheMarketMemo、Yahoo Finance'}。</p>
      <p>REL (相对强度) = ${isCN ? '行业' : 'ETF'}涨跌幅 - ${isCN ? '基准指数' : '标普500'}涨跌幅，正值表示跑赢大盘。</p>
    </div>
  `;

  // 基准切换器（仅A股）
  const benchmarkSwitcherHtml = isCN
    ? '<div id="wl-benchmark-switcher" class="wl-benchmark-switcher-container"></div>'
    : '';

  // 指标切换
  const indicatorsHtml = '<nav class="wl-indicators" id="wl-indicators"></nav>';

  // 热力图容器
  const heatmapHtml = '<div id="wl-heatmap"></div>';

  // 详情面板
  const detailHtml = '<section id="wl-detail" class="wl-detail" style="display:none"></section>';

  container.innerHTML = marketSwitcherHtml + disclaimerHtml + benchmarkSwitcherHtml + indicatorsHtml + heatmapHtml + detailHtml;

  // 渲染市场切换器
  renderMarketSwitcher(
    document.getElementById('wl-market-switcher'),
    currentMarket,
    (newMarket) => renderMarketView(container, header, newMarket)
  );

  // 渲染基准切换器（仅A股）
  if (isCN) {
    renderBenchmarkSwitcher(
      document.getElementById('wl-benchmark-switcher'),
      currentBenchmark,
      (newBenchmark) => {
        currentBenchmark = newBenchmark;
        // TODO: 重新加载对应基准的数据
        alert(`切换到基准: ${newBenchmark}（需要重新获取数据，功能开发中）`);
      }
    );
  }

  // 渲染指标切换
  const cnIndicators = isCN ? [
    { key: 'change_pct', label: '日涨跌', desc: '当日涨跌幅 (%)' },
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

  // 渲染热力图
  renderHeatmapContent(document.getElementById('wl-heatmap'), data.groups, currentIndicator, isCN);

  // 初始化详情面板
  showDetail(null, null);
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
