/**
 * 指标切换 Tab 组件
 */

/**
 * 渲染指标切换 Tab。
 */
export function renderIndicators(container, indicators, activeKey, onChange) {
  const tabsHtml = indicators.map(ind => {
    const isActive = ind.key === activeKey ? ' active' : '';
    return `<button class="wl-tab${isActive}" data-key="${ind.key}">${ind.label}</button>`;
  }).join('');

  container.innerHTML = tabsHtml;

  container.querySelectorAll('.wl-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      const key = tab.dataset.key;
      if (key === activeKey) return;

      container.querySelectorAll('.wl-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');

      onChange(key);
    });
  });
}
