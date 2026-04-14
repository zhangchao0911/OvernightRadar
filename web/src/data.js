/**
 * 数据加载模块 — 统一管理热力图和雷达数据
 */

// 兼容 Vite 和直接浏览器访问
let BASE_URL = '../data/';
try {
  if (import.meta && import.meta.env && import.meta.env.BASE_URL) {
    BASE_URL = import.meta.env.BASE_URL + 'data/';
  }
} catch (e) {
  // import.meta 不可用，使用默认相对路径
}
console.log('[Data] BASE_URL:', BASE_URL);

/**
 * 获取最新数据文件，尝试最近 N 天
 */
async function fetchLatest(dir, days = 7) {
  const dates = [];
  const now = new Date();
  for (let i = 0; i < days; i++) {
    const d = new Date(now);
    d.setDate(d.getDate() - i);
    dates.push(formatDate(d));
  }

  for (const date of dates) {
    try {
      const resp = await fetch(`${BASE_URL}${dir}/${date}.json`);
      if (resp.ok) {
        return await resp.json();
      }
    } catch (e) {
      console.warn(`Failed to fetch ${dir}/${date}.json:`, e);
      // continue
    }
  }
  return null;
}

function formatDate(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

/** 获取热力图数据 */
export function fetchWatchlistData() {
  return fetchLatest('watchlist');
}

/** 获取隔夜雷达数据 */
export function fetchRadarData() {
  return fetchLatest('results');
}

/** 获取A股市场观察数据 */
export async function fetchCNWatchlistData(benchmark = 'hs300') {
  console.log(`[Data] Fetching CN watchlist data (benchmark: ${benchmark})...`);
  // 默认基准用 {date}.json，其他基准用 {date}_{benchmark}.json
  const dir = benchmark === 'hs300' ? 'cn_watchlist' : 'cn_watchlist';
  const suffix = benchmark === 'hs300' ? '' : `_${benchmark}`;

  // 自定义 fetchLatest 支持文件名后缀
  const dates = [];
  const now = new Date();
  for (let i = 0; i < 7; i++) {
    const d = new Date(now);
    d.setDate(d.getDate() - i);
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    dates.push(`${y}-${m}-${day}`);
  }

  for (const date of dates) {
    try {
      const resp = await fetch(`${BASE_URL}${dir}/${date}${suffix}.json`);
      if (resp.ok) {
        const data = await resp.json();
        console.log(`[Data] CN watchlist data (${benchmark}): ${data.total_sectors} sectors`);
        return data;
      }
    } catch (e) {
      console.warn(`Failed to fetch ${dir}/${date}${suffix}.json:`, e);
    }
  }

  // 如果指定基准的数据不存在，回退到默认基准
  if (benchmark !== 'hs300') {
    console.log(`[Data] Fallback to hs300 data`);
    return fetchCNWatchlistData('hs300');
  }

  return null;
}

/** 获取交易信号数据 */
export async function fetchSignals(filters = {}) {
  try {
    const signalsData = await fetchLatest('signals');
    if (!signalsData || !signalsData.signals) return { signals: [], metadata: null };

    let signals = [...signalsData.signals];

    // 应用过滤器
    if (filters.direction && filters.direction !== 'all') {
      // 支持中文方向值（利多/利空）和英文方向值（bullish/bearish）
      const directionMap = { 'bullish': '利多', 'bearish': '利空' };
      const targetDir = directionMap[filters.direction] || filters.direction;
      signals = signals.filter(s => s.direction === targetDir);
    }
    if (filters.confidence && filters.confidence !== 'all') {
      signals = signals.filter(s => {
        const level = s.level?.toLowerCase() || '';
        const confidenceMap = { 'high': '高', 'medium': '中', 'low': '低' };
        return level === confidenceMap[filters.confidence] || s.level === filters.confidence;
      });
    }
    if (filters.type && filters.type !== 'all') {
      signals = signals.filter(s => s.type === filters.type);
    }

    return { signals, metadata: signalsData.metadata || null, generated_at: signalsData.generated_at || null };
  } catch (error) {
    console.error('获取信号数据失败:', error);
    return { signals: [], metadata: null, generated_at: null };
  }
}

/** 获取信号历史数据 */
export async function fetchSignalHistory() {
  try {
    const signalsData = await fetchLatest('signals');
    return signalsData?.signal_history || [];
  } catch (error) {
    console.error('获取信号历史失败:', error);
    return [];
  }
}

/** 获取新闻数据 */
export async function fetchNews(options = {}) {
  const report = await fetchLatest('results');
  if (!report || !report.news) return [];

  // report.news 是对象，包含 news 数组
  const newsData = report.news.news || [];

  let news = [...newsData];

  // 应用分类过滤
  if (options.category && options.category !== 'all') {
    news = news.filter(n => n.category === options.category);
  }

  // 应用搜索过滤
  if (options.searchQuery) {
    const query = options.searchQuery.toLowerCase();
    news = news.filter(n =>
      (n.headline || n.title || '')?.toLowerCase().includes(query) ||
      (n.summary || '')?.toLowerCase().includes(query) ||
      n.related?.toLowerCase().includes(query)
    );
  }

  return news;
}
