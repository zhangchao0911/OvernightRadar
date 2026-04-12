# Market Watchlist MVP - Design Spec

> Date: 2026-04-12
> Status: Draft (v2 - 含深度融合架构)
> Source: Brainstorming session (2026-04-12) + historical design decisions

## 1. Product Overview

### 1.1 What

Market Watchlist 是一个美股市场结构观察仪表盘，将 TheMarketMemo 的 Google Sheet 市場觀察表转化为可视化 H5 网页产品。核心价值：**把枯燥的数字表格变成一眼就能看懂的市场温度计**。

**深度融合规划**：MVP 完成后，将与现有产品「隔夜雷达」(OvernightRadar) 合并为统一的 H5 应用。两个产品共享同一代码仓库和部署，通过 Tab 导航切换。

### 1.2 Product Vision

融合后的产品覆盖完整的投资决策链：

```
热力图全览 → "今天什么在动？" → 点击板块 → "明天A股什么有机会？"
```

- **热力图视图**：60+ ETF 全市场结构观察（"观察"层）
- **隔夜雷达视图**：8 个重点板块的美股→A股传导分析（"行动"层）

### 1.3 Target Users

公开 H5 产品，面向中文投资者。不需要登录，打开即用。手机优先。

### 1.4 Core Concept: Relative Strength (REL)

REL（相对强度）是热力图的核心指标，衡量某个 ETF 相对于 SPY（标普500）的超额收益：

```
REL(ETF, period) = Return(ETF, period) - Return(SPY, period)
```

- REL > 0：该板块跑赢大盘（资金流入）
- REL < 0：该板块跑输大盘（资金流出）
- 多周期对比（5/20/60/120天）可判断趋势持续性

### 1.5 Differentiation

- **分组对比**：大盘 vs 小盘、成长 vs 价值、等权 vs 市值加权 → 判断市场风格轮动
- **热力图可视化**：颜色编码一眼看出强弱，非专业用户也能理解
- **中文界面**：针对中文投资者市场差异化
- **跨市场闭环（融合后）**：美股观察 → A股机会，一站式完成

---

## 2. Scope

### 2.1 MVP Phase (独立开发)

| Feature | Description |
|---------|-------------|
| **分组方块热力图** | 按板块分组的 ETF 方块，颜色编码基于选定指标 |
| **指标切换** | 1D% / REL5 / REL20 / REL60 / REL120 视图切换 |
| **点击展开走势图** | 点击某个 ETF 方块，展开该 ETF 的历史走势小图 |
| **数据自动更新** | 每日收盘后自动更新 |
| **A股映射标识** | 在热力图中，对有 A 股映射的 ETF 标识小图标，为融合做准备 |

### 2.2 Fusion Phase (深度融合，Post-MVP)

| Feature | Description |
|---------|-------------|
| **隔夜雷达视图迁移** | 将 OvernightRadar 的 8 板块卡片视图迁入新应用 |
| **Tab 导航** | 底部 Tab 切换「热力图」和「隔夜雷达」 |
| **深度联动** | 热力图中点击有 A 股映射的 ETF，展开面板直接展示隔夜雷达的 A 股数据 |
| **统一数据管线** | 合并两个 Python 脚本为一条 GitHub Actions 工作流 |
| **旧站重定向** | OvernightRadar 站点 301 重定向到新应用雷达 Tab |

### 2.3 Out of Scope

- 盘中实时数据（MVP + Fusion 均不涉及）
- 用户账户/自选列表
- 推送通知
- 历史回测
- 自定义 ETF 组合

---

## 3. Architecture

### 3.1 Fusion Architecture: Single Repo, Single App

```
Market-Watchlist/                  # 单一代码仓库
├── src/                           # 前端（统一 H5 应用）
│   ├── views/
│   │   ├── heatmap.js             # 热力图视图
│   │   └── radar.js               # 隔夜雷达视图（Fusion 阶段迁入）
│   ├── components/
│   │   ├── nav.js                 # Tab 导航
│   │   ├── heatmap-block.js       # 热力图方块组件
│   │   ├── sector-detail.js       # ETF 详情展开面板
│   │   ├── radar-card.js          # 雷达卡片组件（Fusion）
│   │   └── sparkline.js           # 迷你走势图（共享）
│   ├── data.js                    # 数据加载层
│   ├── main.js                    # 入口 + hash 路由
│   └── style.css                  # 全局样式
├── scripts/
│   ├── fetch_watchlist.py         # 热力图数据获取
│   └── run_radar.py               # 雷达数据获取（从 Sector-Mapper 迁入）
├── data/
│   ├── watchlist/                 # 热力图数据
│   │   ├── 2026-04-12.json
│   │   └── ...
│   └── radar/                     # 雷达数据（Fusion）
│       ├── 2026-04-12.json
│       └── ...
└── .github/workflows/
    └── daily_update.yml           # 统一工作流
```

**选择理由**：
- **同一目标用户**：中文投资者，自然的产品闭环
- **数据重叠**：隔夜雷达的 8 个板块是 Watchlist 的子集（SOXX/XLK/DRIV/THNQ/GLD/BOTZ/UFO/DRAM）
- **同一技术栈**：Vanilla JS + Vite，零迁移成本
- **一个 URL**：用户体验完整，不需要记住两个地址
- **单次部署**：一条 GitHub Actions 工作流处理所有数据

### 3.2 Overall Architecture: Static + GitHub Actions

```
数据源 → GitHub Actions (Python, daily) → data/*.json → Vite SPA → GitHub Pages
```

```
┌──────────────┐    ┌──────────────┐    ┌──────────────────┐
│ 数据源        │    │ GitHub Action │    │ 前端 (Vite SPA)   │
│              │    │              │    │                  │
│ • Google     │───→│ • fetch_     │───→│ data/watchlist/  │
│   Sheet CSV  │    │   watchlist  │    │ data/radar/      │
│ • Yahoo      │    │ • run_radar  │    │                  │
│   Finance    │    │ • npm build  │    │ 热力图 ←→ 雷达    │
│ • AKShare    │    │ • gh-pages   │    │ (Tab 导航)        │
└──────────────┘    └──────────────┘    └──────────────────┘
```

### 3.3 Data Source Abstraction

前端只读 JSON，不关心数据来源。每个视图有独立的数据目录：

```
前端
├── 热力图视图 → data/watchlist/*.json
└── 雷达视图   → data/radar/*.json
```

**热力图数据源策略**：
- MVP：Google Sheet CSV
- 稳定期：yfinance 自计算 REL

**雷达数据源**（从 US-CN-Sector-Mapper 继承）：
- yfinance（US ETF 价格）
- AKShare（A股个股数据）

### 3.4 Routing Strategy

使用 hash 路由，无需服务端配置：

```
#/heatmap            → 热力图视图（默认）
#/radar              → 隔夜雷达视图
#/heatmap/SOXX       → 热力图 + SOXX 详情展开
```

### 3.5 Fusion Timeline

| 阶段 | 时间 | 内容 |
|------|------|------|
| **Phase 1: MVP** | 第 1-3 周 | Market Watchlist 热力图独立上线 |
| **Phase 2: Fusion** | 第 4-5 周 | 迁入隔夜雷达视图，加 Tab 导航 |
| **Phase 3: 深度联动** | 第 6 周+ | 热力图↔雷达数据打通，旧站重定向 |

---

## 4. Tech Stack

| Layer | Choice | Reason |
|-------|--------|--------|
| **Frontend** | Vanilla JS + Vite | 与现有项目一致，不引入框架 |
| **Styling** | CSS（手写） | 项目规模适中，不需要 Tailwind |
| **Charts** | Canvas（轻量自绘） | 走势图用 Canvas API，零依赖 |
| **Router** | Hash 路由（手写） | 两个视图，不需要 router 库 |
| **Data Pipeline** | Python + yfinance + akshare | 与 Sector-Mapper 一致 |
| **Automation** | GitHub Actions | 统一工作流 |
| **Hosting** | GitHub Pages | 零成本静态托管 |

---

## 5. Data Model

### 5.1 Watchlist ETF Data (per ETF)

```json
{
  "ticker": "SOXX",
  "name": "半导体 ETF",
  "name_en": "iShares Semiconductor ETF",
  "group": "market_cap_weighted",
  "price": 245.67,
  "change_pct": 2.1,
  "rel": {
    "rel_5": 1.2,
    "rel_20": 3.5,
    "rel_60": -1.8,
    "rel_120": 8.2
  },
  "rank": {
    "r_20": 5,
    "r_60": 12,
    "r_120": 3
  },
  "ytd": 15.3,
  "has_cn_mapping": true,
  "history": [240, 242, 238, 245, 247]
}
```

> `has_cn_mapping: true` 标识该 ETF 在隔夜雷达中有 A 股映射。MVP 阶段用于显示小图标，Fusion 阶段用于深度联动。

### 5.2 Radar Sector Data (沿用现有格式，从 US-CN-Sector-Mapper 继承)

```json
{
  "us_name": "半导体",
  "us_etf": "SOXX",
  "us_change_pct": 2.1,
  "relative_strength": 2.21,
  "volatility": { "daily_vol_20d": 2.18, "vol_multiple": 1.0, "is_abnormal": false },
  "trend": { "direction": "up", "consecutive_days": 8, "cumulative_pct": 22.64 },
  "cn_name": "半导体",
  "cn_etf_name": "半导体ETF",
  "cn_etf_code": "512480",
  "sentiment": "强烈看多",
  "sentiment_level": 4,
  "supply_chain": [
    { "name": "中际旭创", "code": "300308", "change_pct": 6.01 }
  ]
}
```

### 5.3 Group Definitions

| Group Key | Display Name | ETFs | 有A股映射 |
|-----------|-------------|------|----------|
| `broad` | 大盘指数 | VTI, SPY, QQQ, IWM, 等 12 只 | - |
| `equal_weighted` | 等权行业板块 | 11 个行业 ETF | - |
| `market_cap_weighted` | 市值加权行业板块 | XLC, XLY, XLE 等 11 只 | 部分有 |
| `factors` | 因子风格 | 动量、高贝塔、质量、低波动、高股息 | - |
| `growth` | 成长风格 | 大盘成长、小盘成长 | - |
| `thematic` | 主题投资 | AI、区块链、新能源、军工等 20+ 只 | 部分有 |
| `ark` | ARK 系列 | ARKK, ARKQ, ARKF, ARKW, ARKX | - |
| `cn_linked` | A股关联 | SOXX, XLK, DRIV, THNQ, GLD, BOTZ, UFO, DRAM | 全部有 |

> `cn_linked` 是虚拟分组，用于热力图中标识与 A 股有映射关系的 ETF。实际这些 ETF 仍归属各自的原分组，通过 `has_cn_mapping` 字段标识。

### 5.4 Daily Snapshot Files

```
data/
├── watchlist/
│   ├── 2026-04-12.json
│   ├── 2026-04-11.json
│   └── ...                      # 保留 ~30 天历史（走势图用）
└── radar/
    ├── 2026-04-12.json
    ├── 2026-04-11.json
    └── ...
```

---

## 6. UI Design

### 6.1 Visual Style: Grouped Block Heatmap (方案 C)

用户在 3 个方案中选择了 C：**分组方块热力图**。

特点：
- ETF 按板块分组，每组是一个独立区块
- 每个 ETF 是一个小方块，颜色编码基于选定指标
- 颜色映射：绿（正/强）→ 黄（中性）→ 红（负/弱）
- 方块大小统一，排列整齐
- 有 A 股映射的 ETF 方块右上角显示小标识（MVP）

### 6.2 Color Encoding

热力图颜色映射基于当前选中的指标值：

```
REL >= +5%  → 深绿  (强烈跑赢)
REL >= +2%  → 绿    (跑赢)
REL >= 0%   → 浅绿  (微弱跑赢)
REL == 0%   → 灰    (中性)
REL <= 0%   → 浅红  (微弱跑输)
REL <= -2%  → 红    (跑输)
REL <= -5%  → 深红  (强烈跑输)
```

### 6.3 App Layout (Mobile-first, max-width 480px)

#### MVP 阶段（热力图独立）

```
┌──────────────────────────────┐
│  市场观察表 Market Watchlist  │  Header
│  更新时间: 2026-04-12 16:00  │
├──────────────────────────────┤
│  [1D%] [REL5] [REL20] ...   │  指标切换
├──────────────────────────────┤
│                              │
│  大盘指数                     │  Group Header
│  ┌────┬────┬────┬────┐      │
│  │VTI │SPY │QQQ │IWM │      │  ETF Blocks
│  └────┴────┴────┴────┘      │
│                              │
│  市值加权行业                  │
│  ┌────┬────┬────┬────┐      │
│  │XLC⚡│XLY │XLE │... │      │  ⚡ = 有A股映射
│  └────┴────┴────┴────┘      │
│  ...                         │
│                              │
├──────────────────────────────┤
│  [Detail Panel - SOXX]       │  展开面板
│  半导体 ETF · SOXX            │
│  ┌──────────────────────┐   │
│  │   Canvas 走势图       │   │
│  └──────────────────────┘   │
│  REL5: +1.2%  REL20: +3.5%  │
│  REL60: -1.8% REL120: +8.2% │
│                              │
│  ⚡ A股映射: 半导体ETF(512480) │  A股关联提示
│  [查看隔夜雷达详情 →]         │  (Fusion 后可点击跳转)
├──────────────────────────────┤
│  免责声明                     │  Footer
└──────────────────────────────┘
```

#### Fusion 阶段（加入 Tab 导航）

```
┌──────────────────────────────┐
│  [市场观察]  [隔夜雷达]        │  Top Tab Bar
├──────────────────────────────┤
│                              │
│  (当前选中 Tab 的视图内容)     │
│  · 热力图视图（同上）          │
│  · 或 隔夜雷达卡片视图         │
│                              │
├──────────────────────────────┤
│  🌐 市场观察  |  📡 隔夜雷达   │  Bottom Tab (固定底部)
└──────────────────────────────┘
```

### 6.4 Interactions

#### 热力图视图

1. **指标切换**：点击顶部 Tab（1D% / REL5 / REL20 / REL60 / REL120），热力图颜色实时更新
2. **点击方块**：展开 Detail Panel，显示走势图和 REL 详细数据
3. **A股映射标识**：有 A 股映射的 ETF 显示小图标，展开面板中展示 A 股关联信息
4. **Tab 导航（Fusion）**：底部 Tab 切换到隔夜雷达视图

#### 隔夜雷达视图（Fusion 后迁入）

1. 保持现有卡片交互不变（情绪评级、供应链个股）
2. 卡片顶部新增「查看热力图位置」链接，跳转到热力图中对应 ETF

### 6.5 Deep Linking (Fusion)

热力图 ↔ 雷达的深度联动逻辑：

```
热力图点击 SOXX（有 cn_mapping）
  → Detail Panel 展示:
    ├── 走势图 + REL 多周期数据
    └── A股映射区域:
        ├── 半导体ETF(512480) 昨收 +0.5%
        ├── 中际旭创(300308) +6.01%
        ├── 北方华创(002371) +0.86%
        └── [切换到隔夜雷达 →]  ← 点击跳转到 #/radar (滚动到 SOXX)
```

### 6.6 Language

- 界面文字：中文
- ETF 代码：英文（SOXX, XLK 等）
- 金融术语：中英对照（相对强度 Relative Strength）

---

## 7. File Structure

```
Market-Watchlist/
├── index.html                  # SPA 入口
├── package.json
├── vite.config.js
├── src/
│   ├── main.js                 # 入口：初始化 + hash 路由
│   ├── style.css               # 全局样式（含 Tab 导航、响应式）
│   ├── views/
│   │   ├── heatmap.js          # 热力图视图
│   │   └── radar.js            # 隔夜雷达视图（Fusion 阶段）
│   ├── components/
│   │   ├── heatmap-block.js    # 热力图方块渲染
│   │   ├── sector-detail.js    # ETF 详情展开面板（含 A 股映射区域）
│   │   ├── radar-card.js       # 雷达卡片渲染（Fusion 阶段）
│   │   ├── sparkline.js        # Canvas 迷你走势图
│   │   └── tab-nav.js          # Tab 导航组件（Fusion 阶段）
│   └── data.js                 # 数据加载（watchlist + radar）
├── scripts/
│   ├── fetch_watchlist.py      # 热力图数据获取（Google Sheet / yfinance）
│   └── run_radar.py            # 雷达数据获取（Fusion 阶段迁入）
├── data/
│   ├── watchlist/              # 热力图 JSON 数据
│   │   ├── 2026-04-12.json
│   │   └── ...
│   └── radar/                  # 雷达 JSON 数据（Fusion 阶段）
│       ├── 2026-04-12.json
│       └── ...
├── .github/
│   └── workflows/
│       └── daily_update.yml    # 统一定时任务
├── tests/
│   └── test_calc.py            # REL 计算、数据处理测试
├── docs/
│   └── superpowers/
│       └── specs/
│           └── 2026-04-12-market-watchlist-mvp-design.md
├── requirements.txt            # Python 依赖
└── README.md
```

---

## 8. GitHub Actions Workflow

```yaml
# .github/workflows/daily_update.yml
name: Daily Data Update
on:
  schedule:
    - cron: '0 21 * * 1-5'     # 北京时间 05:00 (UTC 21:00), 周一到周五
    - cron: '0 22 * * 0-4'     # 北京时间 06:00 (UTC 22:00), 热力图数据（美股收盘后）
  workflow_dispatch:

jobs:
  update-radar:
    # 隔夜雷达：05:00 执行，A股开盘前
    # (Fusion 阶段迁入，沿用 Sector-Mapper 逻辑)

  update-watchlist:
    # 热力图：06:00 执行，确保美股收盘数据完整
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python scripts/fetch_watchlist.py
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm install && npm run build
      - run: cp -r data/ dist/data/
      - uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./dist
```

---

## 9. Fusion Migration Plan

### 9.1 从 US-CN-Sector-Mapper 迁入的内容

| 来源 | 迁入到 | 说明 |
|------|--------|------|
| `web/src/main.js` | `src/views/radar.js` | 雷达卡片渲染逻辑 |
| `web/src/style.css` | `src/style.css` (合并) | 雷达相关样式 |
| `scripts/run_daily.py` | `scripts/run_radar.py` | 数据获取脚本 |
| `data/results/*.json` | `data/radar/*.json` | 历史数据迁移 |
| `.github/workflows/` | 合并到 `daily_update.yml` | 工作流合并 |

### 9.2 旧站处理

- `zhangchao0911.github.io/OvernightRadar/` 设置 301 重定向到新站点的 `#/radar`
- 旧 repo 归档，README 指向新项目
- 过渡期双站并行运行 2 周

### 9.3 Fusion Checklist

- [ ] 隔夜雷达视图迁入 `src/views/radar.js`
- [ ] 雷达样式合并到全局 CSS
- [ ] Tab 导航组件实现
- [ ] Hash 路由 (`#/heatmap` / `#/radar`)
- [ ] 热力图 Detail Panel 加入 A 股映射区域
- [ ] `run_radar.py` 迁入 scripts/
- [ ] GitHub Actions 合并为统一工作流
- [ ] 历史数据迁移到 `data/radar/`
- [ ] 旧站 301 重定向
- [ ] 旧 repo 归档

---

## 10. Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Google Sheet 变为私密/删除 | 数据源抽象层，可切换到 Yahoo Finance 自计算 |
| Google CSV 导出接口变更 | 策略模式，只改一个类 |
| REL 数据不一致 | 过渡期双源并行验证 |
| 版权问题 | 不直接复制 TheMarketMemo 的 IP，REL 计算是通用方法论 |
| Fusion 引入回归 bug | 雷达视图独立测试，迁入时保持数据格式不变 |
| 旧站用户流失 | 301 重定向 + 过渡期双站并行 |

---

## 11. Future Roadmap (Post-Fusion)

1. **盘中数据**：加 Cloudflare Worker 代理层
2. **Yahoo Finance 自计算**：独立计算 REL，不依赖第三方 Sheet
3. **用户自选列表**：localStorage 存储个人关注的 ETF
4. **推送通知**：显著板块异动提醒
5. **历史回测**：REL 策略的历史胜率展示
6. **热力图↔雷达更多联动**：雷达板块异动推送回热力图高亮
