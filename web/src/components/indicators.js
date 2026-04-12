/**
 * 指标切换 Tab 组件
 */

/**
 * 渲染指标切换 Tab。
 */
export function renderIndicators(container, indicators, activeKey, onChange) {
  let currentActive = activeKey;
  const activeInd = indicators.find(i => i.key === activeKey);
  const descText = activeInd ? activeInd.desc : '';

  const tabsHtml = indicators.map(ind => {
    const isActive = ind.key === activeKey ? ' active' : '';
    return `<button class="wl-tab${isActive}" data-key="${ind.key}">${ind.label}</button>`;
  }).join('');

  container.innerHTML = `
    <div class="wl-tabs-row">${tabsHtml}</div>
    <p class="wl-indicator-desc">${descText}</p>
  `;

  container.querySelectorAll('.wl-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      const key = tab.dataset.key;
      if (key === currentActive) return;

      currentActive = key;
      container.querySelectorAll('.wl-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');

      // 更新说明文字
      const ind = indicators.find(i => i.key === key);
      const descEl = container.querySelector('.wl-indicator-desc');
      if (descEl && ind) {
        descEl.textContent = ind.desc;
      }

      onChange(key);
    });
  });
}
