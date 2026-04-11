# US-CN Sector Mapper 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 2 天内完成 MVP——每日自动采集 5 对美股/A股板块数据，计算条件概率，H5 卡片展示，GitHub Pages 零成本部署。

**Architecture:** Python 脚本（数据采集 + 统计计算）→ 输出 JSON → 原生 H5（Vite 构建）读取展示。GitHub Actions 每日定时执行 Python 脚本，结果 JSON push 到仓库，触发 Pages 部署。

**Tech Stack:** Python 3.11+ / yfinance / AKShare / pandas / numpy | 原生 HTML+CSS+JS / Vite | GitHub Actions + GitHub Pages

---

## 文件结构

```
US-CN-Sector-Mapper/
├── data/
│   └── results/                    # 每日输出（.gitkeep）
├── scripts/
│   └── run_daily.py                # 主脚本：采集 + 计算 + 输出 JSON
├── tests/
│   ├── __init__.py
│   └── test_calc.py                # 计算逻辑单元测试
├── web/
│   ├── index.html                  # 入口 HTML
│   ├── src/
│   │   ├── main.js                 # 前端逻辑
│   │   └── style.css               # 样式
│   ├── vite.config.js
│   └── package.json
├── .github/
│   └── workflows/
│       └── daily_update.yml        # 定时任务
├── requirements.txt
├── .gitignore
└── docs/                           # 已有
```

---

## Task 1: 项目脚手架

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `web/package.json`
- Create: `web/vite.config.js`
- Create: `data/results/.gitkeep`
- Create: `tests/__init__.py`

- [ ] **Step 1: 初始化 git 仓库**

```bash
cd /Users/zhangchao/US-CN-Sector-Mapper
git init
```

- [ ] **Step 2: 创建 .gitignore**

```
# Python
__pycache__/
*.pyc
.env
venv/

# Node
web/node_modules/
web/dist/

# OS
.DS_Store

# IDE
.idea/
.vscode/

# Data (keep structure, ignore content except .gitkeep)
data/results/*.json
!data/results/.gitkeep
```

- [ ] **Step 3: 创建 requirements.txt**

```
yfinance>=1.2.0
akshare
pandas
numpy
```

- [ ] **Step 4: 创建目录结构**

```bash
mkdir -p data/results
touch data/results/.gitkeep
mkdir -p scripts tests web/src .github/workflows
touch tests/__init__.py
```

- [ ] **Step 5: 创建 web/package.json**

```json
{
  "name": "us-cn-sector-mapper",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "devDependencies": {
    "vite": "^5.0.0"
  }
}
```

- [ ] **Step 6: 创建 web/vite.config.js**

```js
import { defineConfig } from 'vite';
import path from 'path';

export default defineConfig({
  root: '.',
  build: {
    outDir: 'dist',
  },
  server: {
    open: true,
    proxy: {
      '/data': {
        target: 'http://localhost:5173',
        rewrite: (path) => path.replace('/data', '../data'),
    },
  },
});
```

- [ ] **Step 7: 安装依赖**

```bash
pip install -r requirements.txt
cd web && npm install
```

- [ ] **Step 8: 首次提交**

```bash
git add -A
git commit -m "chore: project scaffolding

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 2: 板块配置 + 计算逻辑 + 测试

**Files:**
- Create: `scripts/run_daily.py`（前半部分：配置 + 计算函数）
- Create: `tests/test_calc.py`

- [ ] **Step 1: 先写测试 `tests/test_calc.py`**

```python
"""核心计算逻辑的单元测试"""
import pandas as pd
import numpy as np
import pytest

# 我们将 calc_conditional_prob 定义在 scripts/run_daily.py 中
# 测试时通过 sys.path 导入
import sys
sys.path.insert(0, "scripts")
from run_daily import calc_conditional_prob, SECTOR_MAP


class TestSectorMap:
    """板块映射配置验证"""

    def test_has_5_sectors(self):
        assert len(SECTOR_MAP) == 5

    def test_each_sector_has_required_fields(self):
        required = ["us_etf", "cn_index", "cn_etf_code", "us_name", "cn_name", "cn_etf_name"]
        for sector in SECTOR_MAP:
            for field in required:
                assert field in sector, f"Missing {field} in {sector}"

    def test_us_etfs_are_unique(self):
        etfs = [s["us_etf"] for s in SECTOR_MAP]
        assert len(etfs) == len(set(etfs))


class TestConditionalProb:
    """条件概率计算"""

    def _make_series(self, values, start="2026-01-05"):
        dates = pd.bdate_range(start=start, periods=len(values))
        return pd.Series(values, index=dates)

    def test_basic_case(self):
        """3 次显著波动，2 次高开 → 概率 2/3 ≈ 0.667"""
        us_values = [0.1, 2.5, -0.3, -2.8, 1.0, 3.1, -0.5, 0.0, -1.0, 0.5]
        cn_values = [0.2, 0.8, -0.1, -0.5, 0.3, 1.2, 0.0, -0.2, 0.1, 0.4]
        us = self._make_series(us_values)
        cn = self._make_series(cn_values)

        prob, avg_impact, count = calc_conditional_prob(us, cn, threshold=2.0)
        assert count == 3  # 2.5, -2.8, 3.1
        assert abs(prob - 2 / 3) < 0.01  # 2 of 3 positive
        assert avg_impact > 0

    def test_no_significant_moves(self):
        """无显著波动 → 返回 None"""
        us = self._make_series([0.1, -0.3, 0.5, -0.2, 1.0])
        cn = self._make_series([0.2, -0.1, 0.3, 0.0, 0.1])

        prob, avg_impact, count = calc_conditional_prob(us, cn, threshold=2.0)
        assert prob is None
        assert avg_impact is None
        assert count == 0

    def test_all_high_open(self):
        """4 次显著波动全部高开 → 概率 1.0"""
        us = self._make_series([3.0, 2.5, -2.1, -3.0, 0.5])
        cn = self._make_series([1.0, 0.5, 0.3, 0.8, 0.2])

        prob, avg_impact, count = calc_conditional_prob(us, cn, threshold=2.0)
        assert count == 4
        assert prob == 1.0
        assert avg_impact > 0

    def test_window_parameter(self):
        """window 参数限制计算范围"""
        # 20 个数据点，window=10 时只看最后 10 个
        us_values = [3.0] * 5 + [0.1] * 5 + [3.0] * 5 + [0.1] * 5
        cn_values = [1.0] * 5 + [0.0] * 5 + [-1.0] * 5 + [0.0] * 5
        us = self._make_series(us_values, start="2026-01-05")
        cn = self._make_series(cn_values, start="2026-01-05")

        prob_full, _, count_full = calc_conditional_prob(us, cn, threshold=2.0, window=20)
        prob_10, _, count_10 = calc_conditional_prob(us, cn, threshold=2.0, window=10)

        # window=20 包含前 5 个(全部高开) + 后 5 个(全部低开)
        # window=10 只包含后 10 个中的显著波动(全部低开)
        assert count_full > count_10

    def test_negative_avg_impact(self):
        """显著波动后平均低开"""
        us = self._make_series([3.0, 2.5, -2.1, 0.5])
        cn = self._make_series([-1.0, -0.5, -0.3, 0.2])

        prob, avg_impact, count = calc_conditional_prob(us, cn, threshold=2.0)
        assert count == 3
        assert prob == 0.0  # 全部低开
        assert avg_impact < 0
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd /Users/zhangchao/US-CN-Sector-Mapper
python -m pytest tests/test_calc.py -v
```

Expected: FAIL（`ModuleNotFoundError: No module named 'run_daily'`）

- [ ] **Step 3: 创建 `scripts/run_daily.py`（第一部分：配置 + 计算函数）**

```python
"""
美股涨了，A股呢？ — 每日数据采集与统计计算脚本
用法: python scripts/run_daily.py
"""
import json
import os
import sys
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

# ─── 板块映射配置 ───────────────────────────────────────────

SECTOR_MAP = [
    {
        "id": 1,
        "us_name": "半导体",
        "us_etf": "SOXX",
        "cn_name": "半导体",
        "cn_index": "801081",
        "cn_etf_name": "半导体ETF",
        "cn_etf_code": "512480",
    },
    {
        "id": 2,
        "us_name": "科技",
        "us_etf": "XLK",
        "cn_name": "电子",
        "cn_index": "801080",
        "cn_etf_name": "科技ETF",
        "cn_etf_code": "515000",
    },
    {
        "id": 3,
        "us_name": "新能源车",
        "us_etf": "DRIV",
        "cn_name": "汽车",
        "cn_index": "801880",
        "cn_etf_name": "新能源车ETF",
        "cn_etf_code": "515030",
    },
    {
        "id": 4,
        "us_name": "AI/算力",
        "us_etf": "THNQ",
        "cn_name": "计算机",
        "cn_index": "801750",
        "cn_etf_name": "计算机ETF",
        "cn_etf_code": "512720",
    },
    {
        "id": 5,
        "us_name": "黄金",
        "us_etf": "GLD",
        "cn_name": "有色金属",
        "cn_index": "801050",
        "cn_etf_name": "黄金ETF",
        "cn_etf_code": "518880",
    },
]

WINDOW = 60       # 滚动窗口天数
THRESHOLD = 2.0   # 显著波动阈值（%）


# ─── 核心计算函数 ───────────────────────────────────────────

def calc_conditional_prob(
    us_changes: pd.Series,
    cn_changes: pd.Series,
    threshold: float = THRESHOLD,
    window: int = WINDOW,
) -> tuple:
    """
    计算条件概率：当美股板块涨跌幅绝对值 > threshold 时，
    A 股板块次日高开的概率和平均幅度。

    参数:
        us_changes: 美股板块每日涨跌幅 Series（索引为日期）
        cn_changes: A 股板块次日开盘涨跌幅 Series（索引为日期）
        threshold: 显著波动阈值（%）
        window: 滚动窗口天数

    返回:
        (prob_high_open, avg_impact, sample_count)
        无显著波动时返回 (None, None, 0)
    """
    # 取最近 window 个数据
    us = us_changes.iloc[-window:].copy()
    cn = cn_changes.iloc[-window:].copy()

    # 按索引对齐
    common_idx = us.index.intersection(cn.index)
    if len(common_idx) == 0:
        return None, None, 0

    us = us.loc[common_idx]
    cn = cn.loc[common_idx]

    # 筛选显著波动
    significant_mask = us.abs() > threshold
    sample_count = significant_mask.sum()

    if sample_count == 0:
        return None, None, 0

    cn_on_sig = cn[significant_mask]
    prob_high_open = float((cn_on_sig > 0).mean())
    avg_impact = float(cn_on_sig.mean())

    return prob_high_open, avg_impact, int(sample_count)
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd /Users/zhangchao/US-CN-Sector-Mapper
python -m pytest tests/test_calc.py -v
```

Expected: 全部 PASS（6 tests）

- [ ] **Step 5: 提交**

```bash
git add scripts/run_daily.py tests/test_calc.py
git commit -m "feat: sector mapping config + conditional probability calculation with tests

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 3: 数据采集函数

**Files:**
- Modify: `scripts/run_daily.py`（追加数据采集函数）

- [ ] **Step 1: 在 `scripts/run_daily.py` 末尾追加数据采集函数**

在 `calc_conditional_prob` 函数后面追加：

```python
# ─── 数据采集 ─────────────────────────────────────────────

def fetch_us_data(tickers: list[str], days: int = 150) -> dict[str, pd.DataFrame]:
    """
    拉取美股 ETF 日线数据。
    返回: {ticker: DataFrame(date, close)} ，每个 DataFrame 包含最近 `days` 个交易日。
    """
    import yfinance as yf

    end_date = datetime.now()
    start_date = end_date - timedelta(days=int(days * 1.8))

    raw = yf.download(
        tickers=" ".join(tickers),
        start=start_date.strftime("%Y-%m-%d"),
        end=end_date.strftime("%Y-%m-%d"),
        auto_adjust=True,
        progress=False,
    )

    result = {}
    for ticker in tickers:
        try:
            if len(tickers) > 1:
                close = raw[("Close", ticker)].dropna()
            else:
                close = raw["Close"].dropna()
            df = pd.DataFrame({"close": close})
            df = df.tail(days)
            if len(df) > 1:
                result[ticker] = df
        except (KeyError, TypeError):
            print(f"WARNING: 无法获取 {ticker} 数据", file=sys.stderr)

    return result


def fetch_cn_index_data(index_code: str, days: int = 150) -> pd.DataFrame | None:
    """
    拉取申万行业指数日线数据。
    返回: DataFrame(date, open, close)，最近 `days` 个交易日。
    """
    import akshare as ak

    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=int(days * 1.8))).strftime("%Y%m%d")

    try:
        df = ak.sw_index_daily(
            symbol=index_code,
            start_date=start_date,
            end_date=end_date,
        )
        if df is None or df.empty:
            return None

        df = df.tail(days)
        df = df.rename(columns={
            "日期": "date",
            "开盘": "open",
            "收盘": "close",
        })
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date")
        df = df[["open", "close"]].astype(float)
        return df
    except Exception as e:
        print(f"WARNING: 获取申万指数 {index_code} 失败: {e}", file=sys.stderr)
        return None


def compute_daily_return(close_series: pd.Series) -> pd.Series:
    """计算日涨跌幅（%）。"""
    return close_series.pct_change() * 100


def compute_open_return(df: pd.DataFrame) -> pd.Series:
    """
    计算次日开盘涨跌幅（%）。
    open_return[T] = (open[T] - close[T-1]) / close[T-1] * 100
    """
    prev_close = df["close"].shift(1)
    return (df["open"] - prev_close) / prev_close * 100
```

- [ ] **Step 2: 本地验证数据采集（手动运行）**

```bash
cd /Users/zhangchao/US-CN-Sector-Mapper
python -c "
import sys; sys.path.insert(0, 'scripts')
from run_daily import fetch_us_data, SECTOR_MAP
tickers = [s['us_etf'] for s in SECTOR_MAP]
data = fetch_us_data(tickers)
for t, df in data.items():
    print(f'{t}: {len(df)} days, latest={df.index[-1].strftime(\"%Y-%m-%d\")}')
"
```

Expected: 打印 5 行类似 `SOXX: 150 days, latest=2026-04-10`

- [ ] **Step 3: 验证 A 股数据采集**

```bash
python -c "
import sys; sys.path.insert(0, 'scripts')
from run_daily import fetch_cn_index_data, SECTOR_MAP
for s in SECTOR_MAP:
    df = fetch_cn_index_data(s['cn_index'])
    if df is not None:
        print(f'{s[\"cn_name\"]}({s[\"cn_index\"]}): {len(df)} days')
    else:
        print(f'{s[\"cn_name\"]}({s[\"cn_index\"]}): FAILED')
"
```

Expected: 打印 5 行，每行显示天数

- [ ] **Step 4: 提交**

```bash
git add scripts/run_daily.py
git commit -m "feat: US/CN data fetching functions (yfinance + AKShare)

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 4: 主运行器（编排 + JSON 输出）

**Files:**
- Modify: `scripts/run_daily.py`（追加 main 函数）

- [ ] **Step 1: 在 `scripts/run_daily.py` 末尾追加编排逻辑**

```python
# ─── 主运行逻辑 ───────────────────────────────────────────

def align_dates(us_date, cn_dates: pd.DatetimeIndex):
    """找到美股日期 T 之后最近的 A 股交易日 T'。"""
    future = cn_dates[cn_dates > us_date]
    if len(future) == 0:
        return None
    return future[0]


def run_daily(output_dir: str = "data/results") -> dict | None:
    """
    主入口：采集数据 → 计算 → 输出 JSON。
    返回生成的报告 dict，失败返回 None。
    """
    tickers = [s["us_etf"] for s in SECTOR_MAP]

    # 1. 拉取美股数据
    print("Fetching US data...")
    us_data = fetch_us_data(tickers)
    if not us_data:
        print("ERROR: 无美股数据", file=sys.stderr)
        return None

    # 确定报告日期：最近的美股交易日
    latest_dates = [df.index[-1] for df in us_data.values()]
    report_date = max(latest_dates).strftime("%Y-%m-%d")

    # 检查今天是否已经生成过
    output_path = os.path.join(output_dir, f"{report_date}.json")
    if os.path.exists(output_path):
        print(f"SKIP: {output_path} already exists")
        return None

    # 2. 拉取 A 股数据
    print("Fetching CN data...")
    cn_data = {}
    for sector in SECTOR_MAP:
        df = fetch_cn_index_data(sector["cn_index"])
        if df is not None:
            cn_data[sector["cn_index"]] = df

    # 3. 计算每对板块
    cards = []
    quiet_sectors = []

    for sector in SECTOR_MAP:
        us_ticker = sector["us_etf"]
        cn_idx_code = sector["cn_index"]

        if us_ticker not in us_data or cn_idx_code not in cn_data:
            print(f"SKIP: {sector['us_name']} 数据不完整")
            continue

        us_df = us_data[us_ticker]
        cn_df = cn_data[cn_idx_code]

        # 计算美股日涨跌幅
        us_returns = compute_daily_return(us_df["close"]).dropna()

        # 计算 A 股次日开盘涨跌幅
        cn_open_returns = compute_open_return(cn_df).dropna()

        # 对齐日期：美股 T → A 股 T+1
        us_aligned = []
        cn_aligned = []
        cn_dates = cn_open_returns.index

        for us_date in us_returns.index:
            cn_date = align_dates(us_date, cn_dates)
            if cn_date is not None:
                us_aligned.append(us_returns[us_date])
                cn_aligned.append(cn_open_returns[cn_date])

        if len(us_aligned) < 10:
            print(f"SKIP: {sector['us_name']} 配对数据不足({len(us_aligned)})")
            continue

        us_series = pd.Series(us_aligned)
        cn_series = pd.Series(cn_aligned)

        # 当日美股涨跌幅（最新一天）
        us_today_change = float(us_returns.iloc[-1])

        # 计算条件概率
        prob, avg_impact, sample_count = calc_conditional_prob(
            us_series, cn_series, threshold=THRESHOLD, window=WINDOW
        )

        is_significant = abs(us_today_change) > THRESHOLD

        card = {
            "us_name": sector["us_name"],
            "us_etf": sector["us_etf"],
            "us_change_pct": round(us_today_change, 2),
            "cn_name": sector["cn_name"],
            "cn_etf_name": sector["cn_etf_name"],
            "cn_etf_code": sector["cn_etf_code"],
            "is_significant": is_significant,
        }

        if prob is not None:
            card["prob_high_open"] = round(prob, 2)
            card["avg_impact"] = round(avg_impact, 2)
            card["sample_count"] = sample_count
            card["window_days"] = WINDOW
        else:
            card["prob_high_open"] = None
            card["avg_impact"] = None
            card["sample_count"] = 0
            card["window_days"] = WINDOW

        if is_significant:
            cards.append(card)
        else:
            quiet_sectors.append(card)

    # 按条件概率 × 涨跌幅绝对值 降序排列
    cards.sort(
        key=lambda c: (c.get("prob_high_open") or 0) * abs(c["us_change_pct"]),
        reverse=True,
    )

    # 4. 组装报告
    report = {
        "date": report_date,
        "weekday": _weekday_cn(report_date),
        "cards": cards,
        "quiet_sectors": quiet_sectors,
        "updated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00"),
    }

    # 5. 输出 JSON
    os.makedirs(output_dir, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"OK: {output_path} ({len(cards)} cards, {len(quiet_sectors)} quiet)")
    return report


def _weekday_cn(date_str: str) -> str:
    """日期字符串 → 中文星期"""
    weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return weekdays[dt.weekday()]


if __name__ == "__main__":
    run_daily()
```

- [ ] **Step 2: 本地运行完整脚本**

```bash
cd /Users/zhangchao/US-CN-Sector-Mapper
python scripts/run_daily.py
```

Expected: 输出 `OK: data/results/YYYY-MM-DD.json (N cards, M quiet)`

- [ ] **Step 3: 检查生成的 JSON**

```bash
cat data/results/*.json | python -m json.tool | head -40
```

Expected: 包含 `date`, `cards`, `quiet_sectors`, `updated_at` 的合法 JSON

- [ ] **Step 4: 提交**

```bash
git add scripts/run_daily.py data/results/
git commit -m "feat: main runner - fetch, calculate, output daily JSON

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 5: 前端 HTML + CSS

**Files:**
- Create: `web/index.html`
- Create: `web/src/style.css`

- [ ] **Step 1: 创建 `web/index.html`**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
  <title>美股涨了，A股呢？</title>
  <link rel="stylesheet" href="/src/style.css">
</head>
<body>
  <div id="app">
    <header class="header">
      <h1 class="title">美股涨了，A股呢？</h1>
      <p class="subtitle">每日开盘前 · 数据参考</p>
      <p class="date" id="report-date"></p>
    </header>

    <main id="cards-container"></main>

    <section id="quiet-section" class="quiet-section" style="display:none">
      <h2 class="section-title">今日无显著波动</h2>
      <div id="quiet-list"></div>
    </section>

    <footer class="disclaimer">
      <p class="disclaimer-title">⚠️ 免责声明</p>
      <p>本工具仅供数据参考，不构成任何投资建议或投资指导。</p>
      <p>统计数据基于历史表现，不代表未来走势。</p>
      <p>数据来源：Yahoo Finance、公开市场数据。</p>
      <p>股市有风险，投资需谨慎。</p>
    </footer>
  </div>

  <div id="loading" class="loading">
    <p>正在加载今日数据...</p>
  </div>

  <div id="error" class="error" style="display:none">
    <p>数据加载失败，请稍后重试。</p>
  </div>

  <script type="module" src="/src/main.js"></script>
</body>
</html>
```

- [ ] **Step 2: 创建 `web/src/style.css`**

```css
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  background: #f5f5f5;
  color: #1a1a1a;
  line-height: 1.5;
}

#app {
  max-width: 480px;
  margin: 0 auto;
  padding: 20px 16px;
  min-height: 100vh;
}

/* Header */
.header {
  text-align: center;
  margin-bottom: 24px;
}

.title {
  font-size: 22px;
  font-weight: 700;
  margin-bottom: 4px;
}

.subtitle {
  font-size: 14px;
  color: #888;
}

.date {
  font-size: 15px;
  color: #555;
  margin-top: 8px;
  font-weight: 500;
}

/* Cards */
.card {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.card-us {
  font-size: 18px;
  font-weight: 700;
}

.card-change {
  font-size: 18px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 6px;
}

.card-change.up {
  color: #cf1322;
  background: #fff1f0;
}

.card-change.down {
  color: #389e0d;
  background: #f6ffed;
}

.card-arrow {
  text-align: center;
  color: #bbb;
  font-size: 16px;
  margin: 4px 0 8px;
}

.card-cn {
  font-size: 15px;
  color: #333;
  margin-bottom: 8px;
}

.card-prob {
  font-size: 28px;
  font-weight: 700;
  color: #cf1322;
  margin-bottom: 4px;
}

.card-prob span {
  font-size: 14px;
  font-weight: 400;
  color: #888;
}

.card-impact {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

.card-etf {
  font-size: 14px;
  color: #1890ff;
  background: #e6f7ff;
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
}

.card-meta {
  font-size: 12px;
  color: #aaa;
  margin-top: 8px;
}

/* Quiet section */
.quiet-section {
  margin-top: 24px;
}

.section-title {
  font-size: 14px;
  color: #888;
  margin-bottom: 12px;
}

.quiet-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
  font-size: 14px;
  color: #555;
}

.quiet-change.up { color: #cf1322; }
.quiet-change.down { color: #389e0d; }

/* Disclaimer */
.disclaimer {
  margin-top: 32px;
  padding: 16px;
  background: #fffbe6;
  border-radius: 8px;
  font-size: 12px;
  color: #8c8c8c;
  line-height: 1.8;
}

.disclaimer-title {
  font-weight: 600;
  margin-bottom: 4px;
  color: #666;
}

/* Loading & Error */
.loading {
  text-align: center;
  padding: 60px 20px;
  color: #888;
}

.error {
  text-align: center;
  padding: 60px 20px;
  color: #cf1322;
}

/* Empty state */
.empty-msg {
  text-align: center;
  padding: 40px 20px;
  color: #888;
  font-size: 15px;
}
```

- [ ] **Step 3: 提交**

```bash
git add web/index.html web/src/style.css
git commit -m "feat: HTML structure + mobile-first CSS

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 6: 前端 JavaScript

**Files:**
- Create: `web/src/main.js`

- [ ] **Step 1: 创建 `web/src/main.js`**

```js
/**
 * 美股涨了，A股呢？ — 前端逻辑
 * 从 data/results/ 目录加载最新 JSON，渲染卡片。
 */

const RESULTS_DIR = '/data/results/';

async function main() {
  const app = document.getElementById('app');
  const loading = document.getElementById('loading');
  const errorEl = document.getElementById('error');

  try {
    const report = await fetchLatestReport();
    if (!report) {
      loading.style.display = 'none';
      errorEl.style.display = 'block';
      return;
    }

    renderReport(report);
    loading.style.display = 'none';
    app.style.display = 'block';
  } catch (e) {
    console.error('Failed to load report:', e);
    loading.style.display = 'none';
    errorEl.style.display = 'block';
  }
}

async function fetchLatestReport() {
  // 尝试最近 5 天的日期
  const dates = [];
  const now = new Date();
  for (let i = 0; i < 7; i++) {
    const d = new Date(now);
    d.setDate(d.getDate() - i);
    dates.push(formatDate(d));
  }

  for (const date of dates) {
    try {
      const resp = await fetch(`${RESULTS_DIR}${date}.json`);
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

function renderReport(report) {
  // Header
  document.getElementById('report-date').textContent =
    `${report.date} ${report.weekday}`;

  // Cards
  const container = document.getElementById('cards-container');
  if (report.cards.length === 0) {
    container.innerHTML = '<p class="empty-msg">今日美股无板块涨跌幅超过 2%</p>';
  } else {
    container.innerHTML = report.cards.map(renderCard).join('');
  }

  // Quiet sectors
  const quietSection = document.getElementById('quiet-section');
  if (report.quiet_sectors.length > 0) {
    quietSection.style.display = 'block';
    document.getElementById('quiet-list').innerHTML =
      report.quiet_sectors.map(renderQuietItem).join('');
  }
}

function renderCard(card) {
  const isUp = card.us_change_pct >= 0;
  const changeClass = isUp ? 'up' : 'down';
  const changeSign = isUp ? '+' : '';
  const changeStr = `${changeSign}${card.us_change_pct.toFixed(2)}%`;

  let probHtml = '';
  if (card.prob_high_open !== null) {
    const probPct = (card.prob_high_open * 100).toFixed(0);
    const impactSign = card.avg_impact >= 0 ? '+' : '';
    const impactStr = `${impactSign}${card.avg_impact.toFixed(2)}%`;
    probHtml = `
      <div class="card-prob">${probPct}% <span>概率高开</span></div>
      <div class="card-impact">平均幅度 ${impactStr}</div>
    `;
  } else {
    probHtml = '<div class="card-prob" style="font-size:14px;color:#aaa">样本不足</div>';
  }

  return `
    <div class="card">
      <div class="card-header">
        <span class="card-us">${card.us_etf} ${card.us_name}</span>
        <span class="card-change ${changeClass}">${changeStr}</span>
      </div>
      <div class="card-arrow">↓</div>
      <div class="card-cn">→ A股 ${card.cn_name}</div>
      ${probHtml}
      <span class="card-etf">${card.cn_etf_name}(${card.cn_etf_code})</span>
      ${card.sample_count > 0 ? `<div class="card-meta">(${card.window_days}日 · ${card.sample_count}次样本)</div>` : ''}
    </div>
  `;
}

function renderQuietItem(item) {
  const isUp = item.us_change_pct >= 0;
  const changeClass = isUp ? 'up' : 'down';
  const changeSign = isUp ? '+' : '';
  return `
    <div class="quiet-item">
      <span>${item.us_name} (${item.us_etf})</span>
      <span class="quiet-change ${changeClass}">${changeSign}${item.us_change_pct.toFixed(2)}%</span>
    </div>
  `;
}

// Start
main();
```

- [ ] **Step 2: 启动开发服务器验证**

```bash
cd /Users/zhangchao/US-CN-Sector-Mapper/web
npm run dev
```

在浏览器中打开 `http://localhost:5173`，检查页面结构是否正确（加载状态显示"正在加载"，因为本地开发服务器没有 `/data/results/` 路径）。

- [ ] **Step 3: 配置 Vite 静态文件代理**

修改 `web/vite.config.js` 添加 `/data` 路径代理（开发环境访问 data 目录）：

```js
import { defineConfig } from 'vite';
import path from 'path';

export default defineConfig({
  root: '.',
  build: {
    outDir: 'dist',
  },
  server: {
    open: true,
    proxy: {
      '/data': {
        target: 'http://localhost:5173',
        rewrite: (path) => path.replace('/data', '../data'),
      },
    },
  },
});
```

- [ ] **Step 4: 再次验证开发服务器**

刷新浏览器，应能看到数据卡片。

- [ ] **Step 5: 提交**

```bash
git add web/src/main.js web/vite.config.js
git commit -m "feat: frontend JS - fetch JSON + render cards

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 7: GitHub Actions 工作流

**Files:**
- Create: `.github/workflows/daily_update.yml`

- [ ] **Step 1: 创建 GitHub Actions 工作流**

```yaml
name: Daily Update

on:
  schedule:
    - cron: '0 21 * * 0-4'  # UTC 21:00 周日-周四 = 北京时间 05:00 周一-周五
  workflow_dispatch:  # 支持手动触发

permissions:
  contents: write

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install Python dependencies
        run: pip install -r requirements.txt

      - name: Run daily script
        run: python scripts/run_daily.py

      - name: Commit and push if changed
        run: |
          git config --local user.email "github-actions[bot]@users.noreply.github.com"
          git config --local user.name "github-actions[bot]"
          git add data/results/
          git diff --staged --quiet || git commit -m "data: daily update $(date +%Y-%m-%d)"
          git push

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Build web
        run: |
          cd web
          npm install
          npm run build

      - name: Prepare deploy directory
        run: |
          cp -r data web/dist/data

      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./web/dist
```

- [ ] **Step 2: 提交**

```bash
git add .github/workflows/daily_update.yml
git commit -m "ci: GitHub Actions daily update workflow

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 8: 端到端验证

**Files:** 无新文件，验证现有功能

- [ ] **Step 1: 运行全部测试**

```bash
cd /Users/zhangchao/US-CN-Sector-Mapper
python -m pytest tests/ -v
```

Expected: 全部 PASS

- [ ] **Step 2: 运行主脚本生成 JSON**

```bash
python scripts/run_daily.py
```

Expected: 输出 `OK: data/results/YYYY-MM-DD.json`

- [ ] **Step 3: 验证 JSON 内容完整性**

```bash
python -c "
import json, sys
with open('data/results/latest.json' if False else sorted(__import__('glob').glob('data/results/*.json'))[-1]) as f:
    data = json.load(f)
checks = [
    ('date' in data, 'has date'),
    ('weekday' in data, 'has weekday'),
    ('cards' in data, 'has cards'),
    ('quiet_sectors' in data, 'has quiet_sectors'),
    (isinstance(data['cards'], list), 'cards is list'),
    (isinstance(data['quiet_sectors'], list), 'quiet is list'),
    (len(data['cards']) + len(data['quiet_sectors']) == 5, 'total 5 sectors'),
]
for ok, msg in checks:
    print(f'  {\"✅\" if ok else \"❌\"} {msg}')
    if not ok:
        sys.exit(1)
print('All checks passed!')
"
```

Expected: 全部 ✅

- [ ] **Step 4: 启动前端并验证展示**

```bash
cd web && npm run dev
```

在浏览器（最好是手机模式 375px）中检查：
- 标题"美股涨了，A股呢？"显示正确
- 卡片显示：美股板块名 + 涨跌幅 + A股板块 + 概率 + ETF
- 涨红跌绿颜色正确
- "今日无显著波动"区域显示非异动板块
- 免责声明在底部

- [ ] **Step 5: 最终提交**

```bash
git add -A
git commit -m "chore: end-to-end verification complete

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## 验收清单（对应 PRD section 6）

- [ ] 能拉取 5 对板块最近 60 个交易日数据
- [ ] 条件概率计算正确（test_calc.py 6 个测试全部通过）
- [ ] H5 在 iPhone SE（375px）正常展示
- [ ] 涨跌幅 > 2% 正确标记为显著波动
- [ ] 卡片展示关联 A 股 ETF 代码
- [ ] 含免责声明
- [ ] GitHub Actions 每日自动执行配置完成
- [ ] 页面首屏 < 3 秒
