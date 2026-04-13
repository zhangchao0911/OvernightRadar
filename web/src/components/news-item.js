// web/src/components/news-item.js
/**
 * 新闻条目组件
 * 渲染单条新闻，包括标题、来源、时间、摘要等信息
 */

/**
 * 渲染单条新闻
 * @param {Object} news - 新闻对象
 * @param {string} news.headline - 标题
 * @param {string} news.source - 来源
 * @param {number} news.datetime - Unix 时间戳
 * @param {string} news.summary - 摘要
 * @param {string} news.url - 原文链接
 * @param {boolean} news.has_signal - 是否已生成信号
 * @returns {string} HTML 字符串
 */
export function renderNewsItem(news) {
  const time = formatTime(news.datetime);
  const hasSignal = news.has_signal;

  return `
    <div class="news-item ${hasSignal ? 'has-signal' : ''}">
      <div class="news-header">
        <h4 class="news-headline">${news.headline}</h4>
        ${hasSignal ? '<span class="news-signal-badge">已生成信号</span>' : ''}
      </div>
      <div class="news-meta">
        <span class="news-source">${news.source}</span>
        <span class="news-time">${time}</span>
      </div>
      ${news.summary ? `<p class="news-summary">${news.summary}</p>` : ''}
      ${news.url ? `<a href="${news.url}" target="_blank" class="news-link">阅读原文 →</a>` : ''}
    </div>
  `;
}

/**
 * 格式化时间戳为相对时间
 * @param {number} timestamp - Unix 时间戳
 * @returns {string} 相对时间字符串
 */
function formatTime(timestamp) {
  if (!timestamp) return '';

  const date = new Date(timestamp * 1000);
  const now = new Date();
  const diff = Math.floor((now - date) / 1000 / 60);

  if (diff < 60) return `${diff}分钟前`;
  if (diff < 1440) return `${Math.floor(diff / 60)}小时前`;
  return `${Math.floor(diff / 1440)}天前`;
}
