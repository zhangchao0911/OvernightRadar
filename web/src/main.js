/**
 * SPA 入口 — hash 路由 + Tab 导航 + 视图切换
 */
import { renderTabNav, setActiveTab } from './components/nav.js';
import { renderRadarView } from './views/radar.js';
import { renderHeatmapView } from './views/heatmap.js';
import { renderSectorsView } from './views/sectors.js';

const VIEWS = {
  heatmap: renderHeatmapView,
  radar: renderRadarView,
  sectors: renderSectorsView,
};

const DEFAULT_VIEW = 'heatmap';

async function main() {
  const app = document.getElementById('app');
  const loading = document.getElementById('loading');
  const errorEl = document.getElementById('error');
  const tabNav = document.getElementById('tab-nav');

  try {
    // 初始化 Tab 导航
    renderTabNav(tabNav, (view) => {
      window.location.hash = `#/${view}`;
    });

    // 监听 hash 变化
    window.addEventListener('hashchange', () => handleRoute());

    // 首次路由
    await handleRoute();

    loading.style.display = 'none';
    app.style.display = 'block';
    tabNav.style.display = 'flex';
  } catch (e) {
    console.error('Failed to initialize app:', e);
    loading.style.display = 'none';
    errorEl.style.display = 'block';
  }
}

async function handleRoute() {
  const hash = window.location.hash || '';
  const viewKey = hash.replace('#/', '') || DEFAULT_VIEW;

  if (!VIEWS[viewKey]) {
    console.warn(`Unknown view: ${viewKey}, falling back to ${DEFAULT_VIEW}`);
    window.location.hash = `#/${DEFAULT_VIEW}`;
    return;
  }

  const container = document.getElementById('view-container');
  const header = document.getElementById('app-header');

  // 更新 Tab 激活状态
  setActiveTab(viewKey);

  // 渲染对应视图
  await VIEWS[viewKey](container, header);
}

main();
