/**
 * 信号卡片组件
 * 渲染单个交易信号卡片，展示信号级别、方向、板块、操作建议等信息
 */

const LEVEL_CONFIG = {
  '强': { label: '强', cssClass: 'signal-strong' },
  '中': { label: '中', cssClass: 'signal-medium' },
  '弱': { label: '弱', cssClass: 'signal-weak' }
};

const DIR_CONFIG = {
  '利多': { cssClass: 'dir-bullish' },
  '利空': { cssClass: 'dir-bearish' }
};

/**
 * 渲染单个信号卡片
 */
export function renderSignalCard(signal, generatedAt = null) {
  const level = LEVEL_CONFIG[signal.level] || LEVEL_CONFIG['中'];
  const dir = DIR_CONFIG[signal.direction] || DIR_CONFIG['利多'];

  const sectorsHtml = signal.sectors
    ? signal.sectors.map(s => `<span class="signal-sector">${s}</span>`).join('')
    : '';

  const targetsHtml = signal.targets && signal.targets.length > 0
    ? `<div class="signal-targets">目标: ${signal.targets.join(', ')}</div>`
    : '';

  const sourceHtml = signal.source_news
    ? `<div class="signal-source">${signal.source_news.source} · ${formatTime(signal.source_news.datetime)}</div>`
    : '';

  const scoreHtml = signal.score !== undefined
    ? `<span class="signal-score">评分 ${signal.score}<span class="signal-score-bar"><span class="signal-score-bar-fill" style="width:${signal.score}%"></span></span></span>`
    : '';

  const timeHtml = generatedAt
    ? `<span class="signal-time">${formatGeneratedTime(generatedAt)}</span>`
    : '';

  const footerHtml = (scoreHtml || timeHtml)
    ? `<div class="signal-footer">${scoreHtml}${timeHtml}</div>`
    : '';

  return `
    <div class="signal-card ${level.cssClass}">
      <div class="signal-header">
        <span class="signal-badge ${dir.cssClass}">${level.label}级 ${signal.direction}</span>
        <h3 class="signal-title">${signal.title}</h3>
      </div>

      <div class="signal-meta">
        <span class="signal-direction ${dir.cssClass}">${signal.direction}</span>
        ${sectorsHtml}
      </div>

      ${targetsHtml}

      <div class="signal-action">
        <svg class="action-label" viewBox="0 0 24 24" fill="none" stroke="var(--color-primary)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 1 1 7.072 0l-.548.547A3.374 3.374 0 0 0 14 18.469V19a2 2 0 1 1-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/></svg>
        <span class="action-text">${signal.action}</span>
      </div>

      ${signal.reason ? `<div class="signal-reason">${signal.reason}</div>` : ''}

      ${footerHtml}
      ${sourceHtml}
    </div>
  `;
}

/**
 * 格式化时间戳为相对时间
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

/**
 * 格式化信号生成时间为本地时间格式
 */
function formatGeneratedTime(isoString) {
  if (!isoString) return '';

  try {
    const date = new Date(isoString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');

    return `${year}-${month}-${day} ${hours}:${minutes}`;
  } catch (e) {
    return isoString;
  }
}
