// web/src/components/stats-panel.js
/**
 * 统计面板组件
 * 展示历史信号的命中率统计，包括总体命中率、强信号命中率、平均收益等
 */

/**
 * 渲染统计面板
 * @param {Object} history - 历史信号数据
 * @param {Object[]} history.signals - 历史信号列表
 * @returns {string} HTML 字符串
 */
export function renderStatsPanel(history) {
  if (!history || !history.signals || history.signals.length === 0) {
    return `
      <div class="stats-panel collapsed">
        <div class="stats-header">
          <h3>📊 历史命中率统计</h3>
          <span class="stats-toggle">▼</span>
        </div>
        <div class="stats-content" style="display: none;">
          <p class="stats-empty">暂无历史数据</p>
        </div>
      </div>
    `;
  }

  const stats = calculateStats(history.signals);

  return `
    <div class="stats-panel collapsed">
      <div class="stats-header">
        <h3>📊 历史命中率统计</h3>
        <span class="stats-toggle">▼</span>
      </div>
      <div class="stats-content" style="display: none;">
        ${renderStatsTable(stats)}
        ${renderBreakdown(history.signals)}
      </div>
    </div>
  `;
}

/**
 * 计算统计数据
 * @param {Object[]} signals - 信号列表
 * @returns {Object} 统计数据
 */
function calculateStats(signals) {
  const verifiedSignals = signals.filter(s => s.tracking && s.tracking.hit !== null);

  if (verifiedSignals.length === 0) {
    return {
      total: signals.length,
      verified: 0,
      hitRate: null,
      strongHitRate: null,
      avgReturn: null
    };
  }

  const hitCount = verifiedSignals.filter(s => s.tracking.hit).length;
  const strongSignals = verifiedSignals.filter(s => s.level === '强');
  const strongHitCount = strongSignals.filter(s => s.tracking.hit).length;

  const returns = verifiedSignals
    .filter(s => s.tracking.return !== null)
    .map(s => s.tracking.return);

  const avgReturn = returns.length > 0
    ? returns.reduce((a, b) => a + b, 0) / returns.length
    : null;

  return {
    total: signals.length,
    verified: verifiedSignals.length,
    hitRate: hitCount / verifiedSignals.length,
    strongHitRate: strongSignals.length > 0 ? strongHitCount / strongSignals.length : null,
    avgReturn: avgReturn
  };
}

/**
 * 渲染统计表格
 * @param {Object} stats - 统计数据
 * @returns {string} HTML 字符串
 */
function renderStatsTable(stats) {
  const formatPct = (val) => val !== null ? `${(val * 100).toFixed(1)}%` : '—';

  return `
    <div class="stats-table">
      <div class="stats-row">
        <span class="stats-label">总信号数</span>
        <span class="stats-value">${stats.total}</span>
      </div>
      <div class="stats-row">
        <span class="stats-label">已验证</span>
        <span class="stats-value">${stats.verified}</span>
      </div>
      <div class="stats-row">
        <span class="stats-label">命中率</span>
        <span class="stats-value ${stats.hitRate >= 0.6 ? 'good' : ''}">${formatPct(stats.hitRate)}</span>
      </div>
      <div class="stats-row">
        <span class="stats-label">强信号命中率</span>
        <span class="stats-value ${stats.strongHitRate >= 0.7 ? 'good' : ''}">${formatPct(stats.strongHitRate)}</span>
      </div>
      <div class="stats-row">
        <span class="stats-label">平均收益</span>
        <span class="stats-value ${stats.avgReturn > 0 ? 'good' : ''}">${stats.avgReturn !== null ? stats.avgReturn.toFixed(2) + '%' : '—'}</span>
      </div>
    </div>
  `;
}

/**
 * 渲染分层统计（按信号等级）
 * @param {Object[]} signals - 信号列表
 * @returns {string} HTML 字符串
 */
function renderBreakdown(signals) {
  const byLevel = { '强': [], '中': [], '弱': [] };
  signals.forEach(s => {
    if (s.level && byLevel[s.level]) {
      byLevel[s.level].push(s);
    }
  });

  const rows = Object.entries(byLevel).map(([level, sigs]) => {
    const verified = sigs.filter(s => s.tracking && s.tracking.hit !== null);
    const hit = verified.filter(s => s.tracking.hit).length;
    const rate = verified.length > 0 ? hit / verified.length : null;

    return `
      <div class="stats-row">
        <span class="stats-label">${level}信号</span>
        <span class="stats-value">${sigs.length}条</span>
        <span class="stats-value">${rate !== null ? (rate * 100).toFixed(1) + '%' : '—'}</span>
      </div>
    `;
  }).join('');

  return `
    <div class="stats-breakdown">
      <h4>按等级统计</h4>
      ${rows}
    </div>
  `;
}
