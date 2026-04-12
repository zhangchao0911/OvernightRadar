/**
 * 底部 Tab 导航组件
 */

/**
 * 初始化 Tab 导航事件绑定。
 * @param {HTMLElement} navEl - #tab-nav 容器
 * @param {Function} onViewChange - (viewKey) => void
 */
export function renderTabNav(navEl, onViewChange) {
  navEl.querySelectorAll('.tab-item').forEach(tab => {
    tab.addEventListener('click', () => {
      const view = tab.dataset.view;
      onViewChange(view);
    });
  });
}

/**
 * 更新 Tab 激活状态。
 * @param {string} activeView - 当前视图 key (heatmap | radar)
 */
export function setActiveTab(activeView) {
  const navEl = document.getElementById('tab-nav');
  if (!navEl) return;

  navEl.querySelectorAll('.tab-item').forEach(tab => {
    tab.classList.toggle('active', tab.dataset.view === activeView);
  });
}
