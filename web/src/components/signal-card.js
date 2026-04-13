// web/src/components/signal-card.js
/**
 * 信号卡片组件
 * 渲染单个交易信号卡片，展示信号级别、方向、板块、操作建议等信息
 */

const LEVEL_CONFIG = {
  '强': { icon: '🔥', cssClass: 'signal-strong' },
  '中': { icon: '⚠️', cssClass: 'signal-medium' },
  '弱': { icon: '🧊', cssClass: 'signal-weak' }
};

const DIR_CONFIG = {
  '利多': { icon: '🟢', cssClass: 'dir-bullish' },
  '利空': { icon: '🔴', cssClass: 'dir-bearish' }
};

/**
 * 渲染单个信号卡片
 * @param {Object} signal - 信号对象
 * @param {string} signal.level - 信号等级 (强/中/弱)
 * @param {string} signal.direction - 方向 (利多/利空)
 * @param {string} signal.title - 标题
 * @param {string[]} signal.sectors - 涉及板块
 * @param {string} signal.action - 操作建议
 * @param {string} signal.reason - 理由
 * @param {number} signal.score - 评分
 * @param {string[]} signal.targets - 目标 ETF 代码
 * @param {Object} signal.source_news - 源新闻
 * @returns {string} HTML 字符串
 */
export function renderSignalCard(signal) {
  const level = LEVEL_CONFIG[signal.level] || LEVEL_CONFIG['中'];
  const dir = DIR_CONFIG[signal.direction] || DIR_CONFIG['利多'];

  const sectorsHtml = signal.sectors
    ? signal.sectors.map(s => `<span class="signal-sector">${s}</span>`).join('')
    : '';

  const targetsHtml = signal.targets && signal.targets.length > 0
    ? `<div class="signal-targets">目标: ${signal.targets.join(', ')}</div>`
    : '';

  const sourceHtml = signal.source_news
    ? `<div class="signal-source">📰 ${signal.source_news.source} · ${formatTime(signal.source_news.datetime)}</div>`
    : '';

  const scoreHtml = signal.score !== undefined
    ? `<div class="signal-score">📊 评分: ${signal.score}</div>`
    : '';

  return `
    <div class="signal-card ${level.cssClass}">
      <div class="signal-header">
        <span class="signal-badge ${dir.cssClass}">${level.icon} [${signal.level}]</span>
        <h3 class="signal-title">${signal.title}</h3>
      </div>

      <div class="signal-meta">
        <span class="signal-direction">${dir.icon} ${signal.direction}</span>
        ${sectorsHtml}
      </div>

      ${targetsHtml}

      <div class="signal-action">
        <span class="action-label">💡</span>
        <span class="action-text">${signal.action}</span>
      </div>

      ${scoreHtml}
      ${sourceHtml}

      ${signal.reason ? `<div class="signal-reason">${signal.reason}</div>` : ''}
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
  const diff = Math.floor((now - date) / 1000 / 60);  // 分钟差

  if (diff < 60) return `${diff}分钟前`;
  if (diff < 1440) return `${Math.floor(diff / 60)}小时前`;
  return `${Math.floor(diff / 1440)}天前`;
}
