/**
 * 数据加载模块 — 统一管理热力图和雷达数据
 */

const BASE_URL = import.meta.env.BASE_URL + 'data/';

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
    } catch {
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
export function fetchCNWatchlistData() {
  return fetchLatest('cn_watchlist');
}

/** 获取交易信号数据 */
export async function fetchSignals(filters = {}) {
  const report = await fetchLatest('results');
  if (!report || !report.signals) return [];

  let signals = [...report.signals];

  // 应用过滤器
  if (filters.direction && filters.direction !== 'all') {
    signals = signals.filter(s => s.direction === filters.direction);
  }
  if (filters.confidence && filters.confidence !== 'all') {
    signals = signals.filter(s => s.confidence === filters.confidence);
  }
  if (filters.type && filters.type !== 'all') {
    signals = signals.filter(s => s.type === filters.type);
  }

  return signals;
}

/** 获取信号历史数据 */
export async function fetchSignalHistory() {
  const report = await fetchLatest('results');
  return report?.signal_history || [];
}

/** 获取新闻数据 */
export async function fetchNews(options = {}) {
  const report = await fetchLatest('results');
  if (!report || !report.news) return [];

  let news = [...report.news];

  // 应用分类过滤
  if (options.category && options.category !== 'all') {
    news = news.filter(n => n.category === options.category);
  }

  // 应用搜索过滤
  if (options.searchQuery) {
    const query = options.searchQuery.toLowerCase();
    news = news.filter(n =>
      n.title?.toLowerCase().includes(query) ||
      n.summary?.toLowerCase().includes(query) ||
      n.sectors?.some(s => s.toLowerCase().includes(query))
    );
  }

  return news;
}
