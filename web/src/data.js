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
