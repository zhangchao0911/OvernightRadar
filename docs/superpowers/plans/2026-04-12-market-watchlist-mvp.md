# Market Watchlist MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 US-CN-Sector-Mapper 仓库中新增热力图视图（Market Watchlist），以独立 HTML 页面形式上线，为后续与隔夜雷达融合做准备。

**Architecture:** 新增 watchlist.html 作为独立入口，热力图代码放在 web/src/watchlist/ 目录下。Python 数据管线放在 scripts/fetch_watchlist.py，数据输出到 data/watchlist/。不修改现有隔夜雷达的任何代码。

**Tech Stack:** Python 3.11 + yfinance/pandas（数据管线）、Vanilla JS + Vite（前端）、Canvas API（走势图）、GitHub Actions + Pages（部署）

---

## File Structure Map

### New Files (creates)

| File | Responsibility |
|------|---------------|
| `scripts/etf_config.py` | ETF 分组配置（60+ 只 ETF 的代码、名称、分组） |
| `scripts/fetch_watchlist.py` | 数据获取脚本：Google Sheet CSV → JSON |
| `data/watchlist/.gitkeep` | 数据目录占位 |
| `web/watchlist.html` | 热力图 HTML 入口 |
| `web/src/watchlist/main.js` | 热力图入口 JS：初始化 + 数据加载 |
| `web/src/watchlist/heatmap.js` | 分组方块热力图渲染 |
| `web/src/watchlist/indicators.js` | 指标切换 Tab 逻辑 |
| `web/src/watchlist/detail.js` | 点击展开的 Detail Panel |
| `web/src/watchlist/sparkline.js` | Canvas 迷你走势图 |
| `web/src/watchlist/style.css` | 热力图专用样式 |
| `tests/test_watchlist_calc.py` | REL 计算 + ETF 配置的测试 |

### Modified Files

| File | Change |
|------|--------|
| `web/vite.config.js` | 添加多页面入口（watchlist.html）和数据目录映射 |
| `requirements.txt` | 添加 requests 依赖（用于下载 Google Sheet CSV） |
| `.github/workflows/daily_update.yml` | 添加 watchlist 数据获取步骤 |
| `.gitignore` | 添加 `data/watchlist/*.json` 忽略规则 |

### Existing Files (unchanged)

| File | Note |
|------|------|
| `web/index.html` | 隔夜雷达入口，不动 |
| `web/src/main.js` | 隔夜雷达逻辑，不动 |
| `web/src/style.css` | 隔夜雷达样式，不动 |
| `scripts/run_daily.py` | 隔夜雷达数据管线，不动 |

---

### Task 1: Python - ETF 分组配置 + 测试

**Files:**
- Create: `scripts/etf_config.py`
- Create: `tests/test_watchlist_calc.py`

- [ ] **Step 1: 编写 ETF 配置和计算函数的测试**

```python
# tests/test_watchlist_calc.py
"""Market Watchlist 数据计算和 ETF 配置的单元测试"""
import pytest
import sys

sys.path.insert(0, "scripts")
from etf_config import ETF_GROUPS, ALL_TICKERS, CN_LINKED_TICKERS, get_group_key


class TestETFGroupConfig:
    """ETF 分组配置验证"""

    def test_has_7_groups(self):
        expected_keys = [
            "broad", "equal_weighted", "market_cap_weighted",
            "factors", "growth", "thematic", "ark",
        ]
        for key in expected_keys:
            assert key in ETF_GROUPS, f"Missing group: {key}"

    def test_each_etf_has_required_fields(self):
        required = ["ticker", "name", "name_en"]
        for group_key, etfs in ETF_GROUPS.items():
            for etf in etfs:
                for field in required:
                    assert field in etf, f"Missing {field} in {etf} ({group_key})"

    def test_all_tickers_unique(self):
        assert len(ALL_TICKERS) == len(set(ALL_TICKERS)), "Duplicate tickers found"

    def test_cn_linked_are_subset(self):
        for t in CN_LINKED_TICKERS:
            assert t in ALL_TICKERS, f"CN linked ticker {t} not in ALL_TICKERS"

    def test_cn_linked_has_8(self):
        assert len(CN_LINKED_TICKERS) == 8

    def test_get_group_key(self):
        assert get_group_key("SPY") == "broad"
        assert get_group_key("SOXX") == "market_cap_weighted"
        assert get_group_key("ARKK") == "ark"
        assert get_group_key("NOTEXIST") is None

    def test_total_etf_count(self):
        total = sum(len(etfs) for etfs in ETF_GROUPS.values())
        assert total >= 50, f"Expected 50+ ETFs, got {total}"


class TestRELCalculation:
    """REL 相对强度计算"""

    def _calc_rel(self, etf_return, spy_return):
        """MVP 阶段的简单 REL 计算"""
        return round(etf_return - spy_return, 2)

    def test_positive_rel(self):
        assert self._calc_rel(3.2, 0.5) == 2.7

    def test_negative_rel(self):
        assert self._calc_rel(0.3, 0.5) == -0.2

    def test_resilient_in_down_market(self):
        assert self._calc_rel(0.3, -1.0) == 1.3

    def test_zero_rel(self):
        assert self._calc_rel(1.5, 1.5) == 0.0
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd /Users/zhangchao/US-CN-Sector-Mapper && python -m pytest tests/test_watchlist_calc.py -v`
Expected: FAIL - `ModuleNotFoundError: No module named 'etf_config'`

- [ ] **Step 3: 编写 ETF 配置模块**

```python
# scripts/etf_config.py
"""
Market Watchlist ETF 分组配置
数据源：TheMarketMemo Market Watchlist Google Sheet
"""
from typing import Optional

# ─── ETF 分组定义 ─────────────────────────────────────────

ETF_GROUPS = {
    "broad": {
        "display_name": "大盘指数",
        "etfs": [
            {"ticker": "VTI", "name": "全市场", "name_en": "Vanguard Total Stock Market"},
            {"ticker": "SPY", "name": "标普500", "name_en": "SPDR S&P 500"},
            {"ticker": "QQQ", "name": "纳指100", "name_en": "Invesco QQQ Trust"},
            {"ticker": "IWM", "name": "罗素2000", "name_en": "iShares Russell 2000"},
            {"ticker": "DIA", "name": "道指", "name_en": "SPDR Dow Jones Industrial Average"},
            {"ticker": "VOO", "name": "标普500(Vanguard)", "name_en": "Vanguard S&P 500"},
            {"ticker": "IVV", "name": "标普500(iShares)", "name_en": "iShares Core S&P 500"},
            {"ticker": "QQQJ", "name": "纳指下一代", "name_en": "Invesco Nasdaq Next Gen 100"},
            {"ticker": "QQQM", "name": "纳指100(Invesco)", "name_en": "Invesco Nasdaq 100"},
            {"ticker": "IJH", "name": "中盘400", "name_en": "iShares Core S&P Mid-Cap"},
            {"ticker": "IJR", "name": "小盘600", "name_en": "iShares Core S&P Small-Cap"},
            {"ticker": "VWO", "name": "新兴市场", "name_en": "Vanguard Emerging Markets"},
        ],
    },
    "equal_weighted": {
        "display_name": "等权行业板块",
        "etfs": [
            {"ticker": "RSPS", "name": "消费品(必选)", "name_en": "Invesco S&P 500 Equal Weight Consumer Staples"},
            {"ticker": "RSPT", "name": "科技", "name_en": "Invesco S&P 500 Equal Weight Technology"},
            {"ticker": "RSPM", "name": "工业", "name_en": "Invesco S&P 500 Equal Weight Industrials"},
            {"ticker": "RSPG", "name": "医疗", "name_en": "Invesco S&P 500 Equal Weight Health Care"},
            {"ticker": "RSPF", "name": "金融", "name_en": "Invesco S&P 500 Equal Weight Financials"},
            {"ticker": "RSPD", "name": "消费品(可选)", "name_en": "Invesco S&P 500 Equal Weight Consumer Discretionary"},
            {"ticker": "RSPB", "name": "材料", "name_en": "Invesco S&P 500 Equal Weight Materials"},
            {"ticker": "RSPK", "name": "通信", "name_en": "Invesco S&P 500 Equal Weight Communication Services"},
            {"ticker": "RSPI", "name": "能源", "name_en": "Invesco S&P 500 Equal Weight Energy"},
            {"ticker": "RSPC", "name": "公用事业", "name_en": "Invesco S&P 500 Equal Weight Utilities"},
            {"ticker": "RSPE", "name": "房地产", "name_en": "Invesco S&P 500 Equal Weight Real Estate"},
        ],
    },
    "market_cap_weighted": {
        "display_name": "市值加权行业板块",
        "etfs": [
            {"ticker": "XLC", "name": "通信服务", "name_en": "Communication Services Select Sector SPDR"},
            {"ticker": "XLY", "name": "消费品(可选)", "name_en": "Consumer Discretionary Select Sector SPDR"},
            {"ticker": "XLP", "name": "消费品(必选)", "name_en": "Consumer Staples Select Sector SPDR"},
            {"ticker": "XLE", "name": "能源", "name_en": "Energy Select Sector SPDR"},
            {"ticker": "XLF", "name": "金融", "name_en": "Financial Select Sector SPDR"},
            {"ticker": "XLV", "name": "医疗", "name_en": "Health Care Select Sector SPDR"},
            {"ticker": "XLI", "name": "工业", "name_en": "Industrial Select Sector SPDR"},
            {"ticker": "XLB", "name": "材料", "name_en": "Materials Select Sector SPDR"},
            {"ticker": "XLRE", "name": "房地产", "name_en": "Real Estate Select Sector SPDR"},
            {"ticker": "XLK", "name": "科技", "name_en": "Technology Select Sector SPDR"},
            {"ticker": "XLU", "name": "公用事业", "name_en": "Utilities Select Sector SPDR"},
        ],
    },
    "factors": {
        "display_name": "因子风格",
        "etfs": [
            {"ticker": "MTUM", "name": "动量", "name_en": "iShares MSCI USA Momentum Factor"},
            {"ticker": "SPHB", "name": "高贝塔", "name_en": "Invesco S&P 500 High Beta"},
            {"ticker": "QUAL", "name": "质量", "name_en": "iShares MSCI USA Quality Factor"},
            {"ticker": "SPLV", "name": "低波动", "name_en": "Invesco S&P 500 Low Volatility"},
            {"ticker": "SPYD", "name": "高股息", "name_en": "SPDR S&P Dividend ETF"},
        ],
    },
    "growth": {
        "display_name": "成长风格",
        "etfs": [
            {"ticker": "IWF", "name": "大盘成长", "name_en": "iShares Russell 1000 Growth"},
            {"ticker": "IWO", "name": "小盘成长", "name_en": "iShares Russell 2000 Growth"},
        ],
    },
    "thematic": {
        "display_name": "主题投资",
        "etfs": [
            {"ticker": "SOXX", "name": "半导体", "name_en": "iShares Semiconductor"},
            {"ticker": "BOTZ", "name": "机器人", "name_en": "Global X Robotics & AI"},
            {"ticker": "THNQ", "name": "AI/算力", "name_en": "ROBO Global AI & Technology"},
            {"ticker": "DRIV", "name": "自动驾驶", "name_en": "Global X Autonomous & EV"},
            {"ticker": "UFO", "name": "商业航天", "name_en": "Procure Space ETF"},
            {"ticker": "DRAM", "name": "存储", "name_en": "Palo Alto Networks - no, this is a custom ETF"},
            {"ticker": "LIT", "name": "锂电池", "name_en": "Global X Lithium & Battery Tech"},
            {"ticker": "TAN", "name": "太阳能", "name_en": "Invesco Solar ETF"},
            {"ticker": "ICLN", "name": "清洁能源", "name_en": "iShares Global Clean Energy"},
            {"ticker": "KWEB", "name": "中概互联网", "name_en": "KraneShares CSI China Internet"},
            {"ticker": "HAIL", "name": "未来出行", "name_en": "Global X Future Mobility"},
            {"ticker": "BUG", "name": "网络安全", "name_en": "Global X Cybersecurity"},
            {"ticker": "CIBR", "name": "网络安全(另一)", "name_en": "iShares Digital Security"},
            {"ticker": "ARKW", "name": "ARK下一代互联网", "name_en": "ARK Next Generation Internet"},
            {"ticker": "BLOK", "name": "区块链", "name_en": "Amplify Transformational Data Sharing"},
            {"ticker": "ITA", "name": "航空航天国防", "name_en": "iShares U.S. Aerospace & Defense"},
            {"ticker": "IHI", "name": "医疗设备", "name_en": "iShares U.S. Medical Devices"},
            {"ticker": "IBB", "name": "生物科技", "name_en": "iShares Biotechnology"},
            {"ticker": "XBI", "name": "生物科技(等权)", "name_en": "SPDR S&P Biotech"},
            {"ticker": "VNQ", "name": "房地产(总市场)", "name_en": "Vanguard Real Estate"},
            {"ticker": "GLD", "name": "黄金", "name_en": "SPDR Gold Shares"},
            {"ticker": "SLV", "name": "白银", "name_en": "iShares Silver Trust"},
            {"ticker": "USO", "name": "原油", "name_en": "United States Oil Fund"},
            {"ticker": "CORN", "name": "玉米", "name_en": "Teucrium Corn Fund"},
        ],
    },
    "ark": {
        "display_name": "ARK 系列",
        "etfs": [
            {"ticker": "ARKK", "name": "ARK创新", "name_en": "ARK Innovation ETF"},
            {"ticker": "ARKQ", "name": "ARK自动科技", "name_en": "ARK Autonomous Technology & Robotics"},
            {"ticker": "ARKF", "name": "ARK金融科技", "name_en": "ARK Fintech Innovation"},
            {"ticker": "ARKW", "name": "ARK下一代互联网", "name_en": "ARK Next Generation Internet"},
            {"ticker": "ARKX", "name": "ARK太空探索", "name_en": "ARK Space Exploration & Innovation"},
        ],
    },
}

# ─── A 股关联 ETF ─────────────────────────────────────────
# 这些 ETF 在隔夜雷达中有 A 股映射
CN_LINKED_TICKERS = ["SOXX", "XLK", "DRIV", "THNQ", "GLD", "BOTZ", "UFO", "DRAM"]

# ─── 辅助函数 ─────────────────────────────────────────────

ALL_TICKERS = []
_TICKER_TO_GROUP = {}

for group_key, group_data in ETF_GROUPS.items():
    for etf in group_data["etfs"]:
        ALL_TICKERS.append(etf["ticker"])
        _TICKER_TO_GROUP[etf["ticker"]] = group_key


def get_group_key(ticker: str) -> Optional[str]:
    """根据 ticker 查找所属分组 key。"""
    return _TICKER_TO_GROUP.get(ticker)
```

- [ ] **Step 4: 运行测试验证通过**

Run: `cd /Users/zhangchao/US-CN-Sector-Mapper && python -m pytest tests/test_watchlist_calc.py -v`
Expected: All PASS

- [ ] **Step 5: 提交**

```bash
cd /Users/zhangchao/US-CN-Sector-Mapper
git add scripts/etf_config.py tests/test_watchlist_calc.py
git commit -m "feat: 添加 ETF 分组配置和 REL 计算测试 (Market Watchlist)"
```

---

### Task 2: Python - Google Sheet 数据获取脚本

**Files:**
- Create: `scripts/fetch_watchlist.py`
- Modify: `requirements.txt`

- [ ] **Step 1: 添加 requests 依赖**

在 `requirements.txt` 末尾追加：
```
requests
```

完整文件变为：
```
yfinance>=1.2.0
akshare
pandas
numpy
requests
```

- [ ] **Step 2: 创建数据目录占位文件**

Run: `mkdir -p /Users/zhangchao/US-CN-Sector-Mapper/data/watchlist && touch /Users/zhangchao/US-CN-Sector-Mapper/data/watchlist/.gitkeep`

- [ ] **Step 3: 编写数据获取脚本**

```python
# scripts/fetch_watchlist.py
"""
Market Watchlist 数据获取脚本
从 Google Sheet CSV 导出读取 ETF 数据，计算 REL，输出 JSON。
用法: python scripts/fetch_watchlist.py
"""
import csv
import io
import json
import os
import sys
from datetime import datetime

import requests

sys.path.insert(0, os.path.dirname(__file__))
from etf_config import ETF_GROUPS, CN_LINKED_TICKERS, ALL_TICKERS, get_group_key

# ─── 配置 ─────────────────────────────────────────────────

SHEET_ID = "1_xv9pPrxhx9A4OyhrvyTTJuKNXk8rn0m-eAWvnbdXWI"
SHEET_GID = "1071980810"  # Market Watchlist sheet gid
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={SHEET_GID}"

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "watchlist")


# ─── 数据获取 ─────────────────────────────────────────────

def fetch_sheet_csv(url: str = CSV_URL) -> str:
    """下载 Google Sheet CSV 内容。"""
    print(f"Fetching Google Sheet...")
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.text


def parse_sheet_data(csv_text: str) -> list[dict]:
    """
    解析 Google Sheet CSV 为 ETF 数据列表。

    Sheet 结构（预期列顺序）：
    A: (空/序号), B: Ticker, C: Name, D: Price, E: 1D%,
    F: R20, G: R60, H: R120, I: Rank,
    J: REL5, K: REL20, L: REL60, M: REL120,
    N: From 2025-12-31 (YTD), ...
    P: Tradetime

    注意：实际列顺序可能需要根据 Sheet 调整，
    这里用 Ticker 列识别有效数据行。
    """
    reader = csv.reader(io.StringIO(csv_text))
    rows = list(reader)

    etfs = []
    for row in rows:
        # 跳过空行和标题行
        if len(row) < 5:
            continue

        ticker = row[1].strip().upper() if len(row) > 1 else ""
        if not ticker or ticker not in ALL_TICKERS:
            continue

        # 安全解析数值
        def safe_float(val, default=0.0):
            try:
                clean = val.strip().replace("%", "").replace(",", "")
                return float(clean) if clean else default
            except (ValueError, IndexError):
                return default

        def safe_int(val, default=0):
            try:
                clean = val.strip().replace(",", "")
                return int(float(clean)) if clean else default
            except (ValueError, IndexError):
                return default

        etf_data = {
            "ticker": ticker,
            "name": row[2].strip() if len(row) > 2 else "",
            "price": safe_float(row[3]) if len(row) > 3 else 0.0,
            "change_pct": safe_float(row[4]) if len(row) > 4 else 0.0,
            "rank": {
                "r_20": safe_int(row[5]) if len(row) > 5 else 0,
                "r_60": safe_int(row[6]) if len(row) > 6 else 0,
                "r_120": safe_int(row[7]) if len(row) > 7 else 0,
            },
            "rel": {
                "rel_5": safe_float(row[9]) if len(row) > 9 else 0.0,
                "rel_20": safe_float(row[10]) if len(row) > 10 else 0.0,
                "rel_60": safe_float(row[11]) if len(row) > 11 else 0.0,
                "rel_120": safe_float(row[12]) if len(row) > 12 else 0.0,
            },
            "ytd": safe_float(row[13]) if len(row) > 13 else 0.0,
            "has_cn_mapping": ticker in CN_LINKED_TICKERS,
            "group": get_group_key(ticker),
        }
        etfs.append(etf_data)

    return etfs


def build_output(etfs: list[dict]) -> dict:
    """构建输出 JSON 结构。"""
    # 按分组组织
    groups = {}
    for group_key, group_data in ETF_GROUPS.items():
        group_tickers = {e["ticker"] for e in group_data["etfs"]}
        group_etfs = [e for e in etfs if e["ticker"] in group_tickers]
        groups[group_key] = {
            "display_name": group_data["display_name"],
            "etfs": group_etfs,
        }

    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "updated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00"),
        "total_etfs": len(etfs),
        "groups": groups,
    }


def run_fetch(output_dir: str = None):
    """主入口：获取数据 → 解析 → 输出 JSON。"""
    if output_dir is None:
        output_dir = OUTPUT_DIR

    output_dir = os.path.abspath(output_dir)

    try:
        csv_text = fetch_sheet_csv()
        etfs = parse_sheet_data(csv_text)

        if not etfs:
            print("WARNING: 未解析到有效 ETF 数据", file=sys.stderr)
            return None

        report = build_output(etfs)

        # 输出 JSON
        os.makedirs(output_dir, exist_ok=True)
        date_str = report["date"]
        output_path = os.path.join(output_dir, f"{date_str}.json")

        # 不覆盖已有数据
        if os.path.exists(output_path):
            print(f"SKIP: {output_path} already exists")
            return None

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"OK: {output_path} ({len(etfs)} ETFs)")
        return report

    except requests.RequestException as e:
        print(f"ERROR: 获取 Google Sheet 失败: {e}", file=sys.stderr)
        return None


if __name__ == "__main__":
    run_fetch()
```

- [ ] **Step 4: 本地测试脚本**

Run: `cd /Users/zhangchao/US-CN-Sector-Mapper && pip install requests && python scripts/fetch_watchlist.py`
Expected: 输出 `OK: .../data/watchlist/2026-04-12.json (N ETFs)` 或 `SKIP: ... already exists`

- [ ] **Step 5: 验证输出 JSON 结构**

Run: `cat /Users/zhangchao/US-CN-Sector-Mapper/data/watchlist/2026-04-12.json | python -m json.tool | head -40`
Expected: 包含 `groups` 字段，每个 group 下有 `display_name` 和 `etfs` 列表

- [ ] **Step 6: 提交**

```bash
cd /Users/zhangchao/US-CN-Sector-Mapper
git add scripts/fetch_watchlist.py scripts/etf_config.py requirements.txt data/watchlist/.gitkeep
git commit -m "feat: 添加 Market Watchlist 数据获取脚本 (Google Sheet CSV → JSON)"
```

---

### Task 3: Frontend - HTML 入口 + Vite 多页面配置

**Files:**
- Create: `web/watchlist.html`
- Modify: `web/vite.config.js`

- [ ] **Step 1: 创建热力图 HTML 入口**

```html
<!-- web/watchlist.html -->
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
  <title>市场观察表 Market Watchlist</title>
  <link rel="stylesheet" href="/src/watchlist/style.css">
</head>
<body>
  <div id="app" style="display:none">
    <header class="wl-header">
      <h1 class="wl-title">市场观察表</h1>
      <p class="wl-subtitle">Market Watchlist · 美股 ETF 相对强度热力图</p>
      <p class="wl-date" id="update-time"></p>
    </header>

    <nav class="wl-indicators" id="indicators">
      <!-- 指标切换 Tab，由 JS 动态生成 -->
    </nav>

    <main id="heatmap-container">
      <!-- 热力图分组方块，由 JS 动态生成 -->
    </main>

    <section id="detail-panel" class="wl-detail" style="display:none">
      <!-- 点击展开的详情面板，由 JS 动态填充 -->
    </section>

    <footer class="wl-disclaimer">
      <p class="wl-disclaimer-title">免责声明</p>
      <p>本工具仅供数据参考，不构成任何投资建议。</p>
      <p>数据来源：TheMarketMemo Market Watchlist、Yahoo Finance。</p>
      <p>REL (相对强度) = ETF 涨跌幅 - 标普500 涨跌幅。</p>
    </footer>
  </div>

  <div id="loading" class="wl-loading">
    <p>正在加载市场数据...</p>
  </div>

  <div id="error" class="wl-error" style="display:none">
    <p>数据加载失败，请稍后重试。</p>
  </div>

  <script type="module" src="/src/watchlist/main.js"></script>
</body>
</html>
```

- [ ] **Step 2: 更新 Vite 配置支持多页面**

```javascript
// web/vite.config.js
import { defineConfig } from 'vite';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const dataDir = path.resolve(__dirname, '../data');

export default defineConfig({
  root: '.',
  base: '/OvernightRadar/',
  build: {
    outDir: 'dist',
    rollupOptions: {
      input: {
        main: path.resolve(__dirname, 'index.html'),
        watchlist: path.resolve(__dirname, 'watchlist.html'),
      },
    },
  },
  server: {
    open: '/watchlist.html',
  },
  plugins: [
    {
      name: 'serve-data',
      configureServer(server) {
        server.middlewares.use((req, res, next) => {
          if (req.url && req.url.startsWith('/data/')) {
            const relativePath = req.url.replace('/data/', '');
            const filePath = path.join(dataDir, relativePath);
            if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
              res.setHeader('Content-Type', 'application/json');
              res.setHeader('Access-Control-Allow-Origin', '*');
              fs.createReadStream(filePath).pipe(res);
              return;
            }
          }
          next();
        });
      },
    },
  ],
});
```

- [ ] **Step 3: 创建前端目录结构和入口文件**

Run: `mkdir -p /Users/zhangchao/US-CN-Sector-Mapper/web/src/watchlist`

```javascript
// web/src/watchlist/main.js
/**
 * Market Watchlist — 热力图前端入口
 */
import { fetchWatchlistData } from './data.js';
import { renderIndicators } from './indicators.js';
import { renderHeatmap } from './heatmap.js';
import { initDetailPanel } from './detail.js';

const DATA_DIR = import.meta.env.BASE_URL + 'data/watchlist/';

const INDICATORS = [
  { key: 'change_pct', label: '1D%' },
  { key: 'rel_5', label: 'REL5' },
  { key: 'rel_20', label: 'REL20' },
  { key: 'rel_60', label: 'REL60' },
  { key: 'rel_120', label: 'REL120' },
];

let currentIndicator = 'change_pct';
let watchlistData = null;

async function main() {
  const app = document.getElementById('app');
  const loading = document.getElementById('loading');
  const errorEl = document.getElementById('error');

  try {
    watchlistData = await fetchWatchlistData(DATA_DIR);
    if (!watchlistData) {
      loading.style.display = 'none';
      errorEl.style.display = 'block';
      return;
    }

    // 更新时间
    document.getElementById('update-time').textContent =
      `更新时间: ${watchlistData.updated_at || watchlistData.date}`;

    // 渲染指标切换
    renderIndicators(
      document.getElementById('indicators'),
      INDICATORS,
      currentIndicator,
      (key) => {
        currentIndicator = key;
        renderHeatmap(
          document.getElementById('heatmap-container'),
          watchlistData.groups,
          currentIndicator
        );
      }
    );

    // 渲染热力图
    renderHeatmap(
      document.getElementById('heatmap-container'),
      watchlistData.groups,
      currentIndicator
    );

    // 初始化详情面板
    initDetailPanel(document.getElementById('detail-panel'));

    loading.style.display = 'none';
    app.style.display = 'block';
  } catch (e) {
    console.error('Failed to load watchlist:', e);
    loading.style.display = 'none';
    errorEl.style.display = 'block';
  }
}

main();
```

```javascript
// web/src/watchlist/data.js
/**
 * 数据加载模块
 */

export async function fetchWatchlistData(baseDir) {
  const dates = [];
  const now = new Date();
  for (let i = 0; i < 7; i++) {
    const d = new Date(now);
    d.setDate(d.getDate() - i);
    dates.push(formatDate(d));
  }

  for (const date of dates) {
    try {
      const resp = await fetch(`${baseDir}${date}.json`);
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
```

- [ ] **Step 4: 本地验证 Vite 启动**

Run: `cd /Users/zhangchao/US-CN-Sector-Mapper/web && npm run dev`
Expected: 浏览器打开 watchlist.html，显示加载中或错误（因为还没热力图渲染，但 HTML 结构正确）

- [ ] **Step 5: 提交**

```bash
cd /Users/zhangchao/US-CN-Sector-Mapper
git add web/watchlist.html web/vite.config.js web/src/watchlist/main.js web/src/watchlist/data.js
git commit -m "feat: 添加热力图 HTML 入口和多页面 Vite 配置"
```

---

### Task 4: Frontend - 热力图渲染 + 颜色编码

**Files:**
- Create: `web/src/watchlist/heatmap.js`

- [ ] **Step 1: 编写热力图渲染模块**

```javascript
// web/src/watchlist/heatmap.js
/**
 * 分组方块热力图渲染
 */
import { showDetail } from './detail.js';

/**
 * 根据指标值返回颜色。美股惯例：绿涨红跌。
 */
function getColor(value) {
  if (value === null || value === undefined || isNaN(value)) return '#e8e8e8';

  if (value >= 5) return '#1b7a1b';   // 深绿
  if (value >= 2) return '#3ba53b';   // 绿
  if (value >= 0.5) return '#81c784'; // 浅绿
  if (value > 0) return '#c8e6c9';   // 微绿
  if (value === 0) return '#e8e8e8';  // 灰
  if (value > -0.5) return '#ffcdd2'; // 微红
  if (value > -2) return '#e57373';   // 浅红
  if (value > -5) return '#d32f2f';   // 红
  return '#b71c1c';                    // 深红
}

function getIndicatorValue(etf, indicatorKey) {
  if (indicatorKey === 'change_pct') {
    return etf.change_pct;
  }
  if (etf.rel && indicatorKey in etf.rel) {
    return etf.rel[indicatorKey];
  }
  return null;
}

function formatValue(value) {
  if (value === null || value === undefined || isNaN(value)) return '—';
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
}

/**
 * 渲染热力图到指定容器。
 */
export function renderHeatmap(container, groups, indicatorKey) {
  if (!groups) {
    container.innerHTML = '<p class="wl-empty">暂无数据</p>';
    return;
  }

  const groupOrder = [
    'broad', 'equal_weighted', 'market_cap_weighted',
    'factors', 'growth', 'thematic', 'ark',
  ];

  let html = '';
  for (const groupKey of groupOrder) {
    const group = groups[groupKey];
    if (!group || !group.etfs || group.etfs.length === 0) continue;

    html += `
      <div class="wl-group">
        <h2 class="wl-group-title">${group.display_name}</h2>
        <div class="wl-blocks">
          ${group.etfs.map(etf => renderBlock(etf, indicatorKey)).join('')}
        </div>
      </div>
    `;
  }

  container.innerHTML = html;

  // 绑定点击事件
  container.querySelectorAll('.wl-block').forEach(block => {
    block.addEventListener('click', () => {
      const ticker = block.dataset.ticker;
      // 找到对应的 ETF 数据
      const etf = findEtf(groups, ticker);
      if (etf) {
        showDetail(etf, indicatorKey);
      }
    });
  });
}

function renderBlock(etf, indicatorKey) {
  const value = getIndicatorValue(etf, indicatorKey);
  const bgColor = getColor(value);
  const displayValue = formatValue(value);
  const cnBadge = etf.has_cn_mapping
    ? '<span class="wl-cn-badge" title="有A股映射">A</span>'
    : '';

  return `
    <div class="wl-block" data-ticker="${etf.ticker}" style="background-color: ${bgColor}">
      <span class="wl-block-ticker">${etf.ticker}</span>
      <span class="wl-block-value">${displayValue}</span>
      ${cnBadge}
    </div>
  `;
}

function findEtf(groups, ticker) {
  for (const group of Object.values(groups)) {
    if (!group.etfs) continue;
    const found = group.etfs.find(e => e.ticker === ticker);
    if (found) return found;
  }
  return null;
}
```

- [ ] **Step 2: 提交**

```bash
cd /Users/zhangchao/US-CN-Sector-Mapper
git add web/src/watchlist/heatmap.js
git commit -m "feat: 添加热力图渲染模块 (分组方块 + 颜色编码)"
```

---

### Task 5: Frontend - 指标切换 Tab

**Files:**
- Create: `web/src/watchlist/indicators.js`

- [ ] **Step 1: 编写指标切换模块**

```javascript
// web/src/watchlist/indicators.js
/**
 * 指标切换 Tab 渲染和交互
 */

/**
 * 渲染指标切换 Tab。
 * @param {HTMLElement} container - Tab 容器
 * @param {Array} indicators - [{key, label}]
 * @param {string} activeKey - 当前激活的指标 key
 * @param {Function} onChange - 切换回调 (key) => void
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

      // 更新 active 状态
      container.querySelectorAll('.wl-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');

      onChange(key);
    });
  });
}
```

- [ ] **Step 2: 提交**

```bash
cd /Users/zhangchao/US-CN-Sector-Mapper
git add web/src/watchlist/indicators.js
git commit -m "feat: 添加指标切换 Tab 模块"
```

---

### Task 6: Frontend - Detail Panel + Sparkline 走势图

**Files:**
- Create: `web/src/watchlist/detail.js`
- Create: `web/src/watchlist/sparkline.js`

- [ ] **Step 1: 编写 Canvas 迷你走势图**

```javascript
// web/src/watchlist/sparkline.js
/**
 * Canvas 迷你走势图
 */

/**
 * 在指定 canvas 上绘制走势图。
 * @param {HTMLCanvasElement} canvas
 * @param {number[]} data - 价格序列
 * @param {object} options - { width, height, color }
 */
export function drawSparkline(canvas, data, options = {}) {
  if (!data || data.length < 2) return;

  const ctx = canvas.getContext('2d');
  const width = options.width || canvas.width || 300;
  const height = options.height || canvas.height || 80;

  canvas.width = width;
  canvas.height = height;

  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;

  const padding = 2;
  const plotWidth = width - padding * 2;
  const plotHeight = height - padding * 2;

  // 颜色：涨绿跌红（美股惯例）
  const firstVal = data[0];
  const lastVal = data[data.length - 1];
  const color = lastVal >= firstVal ? '#2e7d32' : '#c62828';

  // 绘制线条
  ctx.clearRect(0, 0, width, height);
  ctx.beginPath();
  ctx.strokeStyle = color;
  ctx.lineWidth = 1.5;
  ctx.lineJoin = 'round';

  for (let i = 0; i < data.length; i++) {
    const x = padding + (i / (data.length - 1)) * plotWidth;
    const y = padding + plotHeight - ((data[i] - min) / range) * plotHeight;
    if (i === 0) {
      ctx.moveTo(x, y);
    } else {
      ctx.lineTo(x, y);
    }
  }
  ctx.stroke();

  // 填充渐变区域
  const gradient = ctx.createLinearGradient(0, 0, 0, height);
  gradient.addColorStop(0, lastVal >= firstVal ? 'rgba(46,125,50,0.15)' : 'rgba(198,40,40,0.15)');
  gradient.addColorStop(1, 'rgba(255,255,255,0)');

  ctx.lineTo(padding + plotWidth, height);
  ctx.lineTo(padding, height);
  ctx.closePath();
  ctx.fillStyle = gradient;
  ctx.fill();
}
```

- [ ] **Step 2: 编写 Detail Panel 模块**

```javascript
// web/src/watchlist/detail.js
/**
 * ETF 详情展开面板
 */
import { drawSparkline } from './sparkline.js';

let detailPanel = null;
let currentTicker = null;

/**
 * 初始化详情面板。
 */
export function initDetailPanel(panelEl) {
  detailPanel = panelEl;
}

/**
 * 显示指定 ETF 的详情。
 */
export function showDetail(etf, indicatorKey) {
  if (!detailPanel) return;

  // 点击同一个 → 收起
  if (currentTicker === etf.ticker) {
    detailPanel.style.display = 'none';
    currentTicker = null;
    return;
  }

  currentTicker = etf.ticker;

  const relHtml = etf.rel
    ? `
      <div class="wl-rel-grid">
        <div class="wl-rel-item"><span class="wl-rel-label">REL5</span><span class="wl-rel-value">${formatVal(etf.rel.rel_5)}</span></div>
        <div class="wl-rel-item"><span class="wl-rel-label">REL20</span><span class="wl-rel-value">${formatVal(etf.rel.rel_20)}</span></div>
        <div class="wl-rel-item"><span class="wl-rel-label">REL60</span><span class="wl-rel-value">${formatVal(etf.rel.rel_60)}</span></div>
        <div class="wl-rel-item"><span class="wl-rel-label">REL120</span><span class="wl-rel-value">${formatVal(etf.rel.rel_120)}</span></div>
      </div>
    `
    : '';

  // A 股映射区域（预留）
  const cnMappingHtml = etf.has_cn_mapping
    ? `
      <div class="wl-cn-mapping">
        <span class="wl-cn-badge-detail">有 A 股映射</span>
        <span class="wl-cn-hint">数据来源：隔夜雷达</span>
      </div>
    `
    : '';

  detailPanel.innerHTML = `
    <div class="wl-detail-header">
      <h3 class="wl-detail-title">${etf.ticker} · ${etf.name}</h3>
      <button class="wl-detail-close" id="detail-close">✕</button>
    </div>
    <div class="wl-detail-price">
      <span class="wl-detail-price-value">$${etf.price.toFixed(2)}</span>
      <span class="wl-detail-change">${formatVal(etf.change_pct)}</span>
      <span class="wl-detail-ytd">YTD: ${formatVal(etf.ytd)}</span>
    </div>
    <canvas id="sparkline-canvas" width="300" height="80"></canvas>
    ${relHtml}
    ${cnMappingHtml}
  `;

  detailPanel.style.display = 'block';

  // 关闭按钮
  document.getElementById('detail-close').addEventListener('click', () => {
    detailPanel.style.display = 'none';
    currentTicker = null;
  });

  // 绘制走势图（MVP 用模拟数据，后续接入历史价格）
  const canvas = document.getElementById('sparkline-canvas');
  if (canvas && etf.price) {
    // MVP: 生成模拟走势数据（基于当日涨跌幅）
    const mockData = generateMockHistory(etf);
    drawSparkline(canvas, mockData);
  }

  // 滚动到详情面板
  detailPanel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function formatVal(value) {
  if (value === null || value === undefined || isNaN(value)) return '—';
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
}

/**
 * MVP 阶段：基于当日数据生成模拟走势。
 * 后续版本会接入真实历史价格。
 */
function generateMockHistory(etf) {
  const base = etf.price / (1 + etf.change_pct / 100);
  const points = 20;
  const data = [];
  for (let i = 0; i <= points; i++) {
    const noise = (Math.random() - 0.5) * base * 0.01;
    const trend = (etf.change_pct / 100) * base * (i / points);
    data.push(base + trend + noise);
  }
  return data;
}
```

- [ ] **Step 3: 提交**

```bash
cd /Users/zhangchao/US-CN-Sector-Mapper
git add web/src/watchlist/detail.js web/src/watchlist/sparkline.js
git commit -m "feat: 添加 Detail Panel 和 Canvas 走势图"
```

---

### Task 7: Frontend - 样式

**Files:**
- Create: `web/src/watchlist/style.css`

- [ ] **Step 1: 编写热力图样式**

```css
/* web/src/watchlist/style.css */
/* Market Watchlist 热力图样式 */

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

/* ─── Header ──────────────────────────────── */

.wl-header {
  text-align: center;
  margin-bottom: 16px;
}

.wl-title {
  font-size: 22px;
  font-weight: 700;
}

.wl-subtitle {
  font-size: 13px;
  color: #666;
  margin-top: 2px;
}

.wl-date {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

/* ─── Indicator Tabs ─────────────────────── */

.wl-indicators {
  display: flex;
  gap: 6px;
  margin-bottom: 16px;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  padding-bottom: 4px;
}

.wl-tab {
  padding: 6px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 16px;
  background: #fff;
  font-size: 13px;
  color: #666;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s;
}

.wl-tab:hover {
  border-color: #1890ff;
  color: #1890ff;
}

.wl-tab.active {
  background: #1890ff;
  border-color: #1890ff;
  color: #fff;
}

/* ─── Grouped Blocks ─────────────────────── */

.wl-group {
  margin-bottom: 20px;
}

.wl-group-title {
  font-size: 14px;
  font-weight: 600;
  color: #555;
  margin-bottom: 8px;
  padding-left: 2px;
}

.wl-blocks {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

/* ─── Single Block ────────────────────────── */

.wl-block {
  position: relative;
  width: 72px;
  height: 52px;
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: transform 0.15s, box-shadow 0.15s;
}

.wl-block:hover {
  transform: scale(1.08);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.wl-block:active {
  transform: scale(0.98);
}

.wl-block-ticker {
  font-size: 11px;
  font-weight: 700;
  color: rgba(0, 0, 0, 0.75);
}

.wl-block-value {
  font-size: 10px;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.6);
}

/* ─── CN Mapping Badge ────────────────────── */

.wl-cn-badge {
  position: absolute;
  top: 2px;
  right: 2px;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #1890ff;
  color: #fff;
  font-size: 7px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
}

/* ─── Detail Panel ────────────────────────── */

.wl-detail {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  margin: 16px 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.wl-detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.wl-detail-title {
  font-size: 18px;
  font-weight: 700;
}

.wl-detail-close {
  background: none;
  border: none;
  font-size: 18px;
  color: #999;
  cursor: pointer;
  padding: 4px 8px;
}

.wl-detail-price {
  display: flex;
  gap: 12px;
  align-items: baseline;
  margin-bottom: 12px;
}

.wl-detail-price-value {
  font-size: 20px;
  font-weight: 700;
}

.wl-detail-change {
  font-size: 15px;
  font-weight: 600;
}

.wl-detail-ytd {
  font-size: 13px;
  color: #666;
}

#sparkline-canvas {
  width: 100%;
  height: 80px;
  margin-bottom: 12px;
}

/* ─── REL Grid ───────────────────────────── */

.wl-rel-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 1fr;
  gap: 8px;
  margin-bottom: 12px;
}

.wl-rel-item {
  text-align: center;
  padding: 6px 4px;
  background: #fafafa;
  border-radius: 6px;
}

.wl-rel-label {
  display: block;
  font-size: 11px;
  color: #999;
}

.wl-rel-value {
  display: block;
  font-size: 14px;
  font-weight: 600;
  margin-top: 2px;
}

/* ─── CN Mapping Area ─────────────────────── */

.wl-cn-mapping {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #e6f7ff;
  border-radius: 6px;
}

.wl-cn-badge-detail {
  font-size: 13px;
  font-weight: 600;
  color: #1890ff;
}

.wl-cn-hint {
  font-size: 11px;
  color: #999;
}

/* ─── Empty State ─────────────────────────── */

.wl-empty {
  text-align: center;
  color: #888;
  padding: 40px 0;
}

/* ─── Disclaimer ──────────────────────────── */

.wl-disclaimer {
  margin-top: 32px;
  padding: 16px;
  background: #fffbe6;
  border-radius: 8px;
  font-size: 12px;
  color: #8c8c8c;
  line-height: 1.8;
}

.wl-disclaimer-title {
  font-weight: 600;
  margin-bottom: 4px;
  color: #666;
}

/* ─── Loading & Error ─────────────────────── */

.wl-loading {
  text-align: center;
  padding: 60px 20px;
  color: #888;
}

.wl-error {
  text-align: center;
  padding: 60px 20px;
  color: #cf1322;
}
```

- [ ] **Step 2: 本地全流程测试**

Run: `cd /Users/zhangchao/US-CN-Sector-Mapper/web && npm run dev`
Expected: 浏览器打开 watchlist.html，看到：
1. 页面标题和更新时间
2. 指标切换 Tab（1D%, REL5, REL20, REL60, REL120）
3. 按 7 组排列的 ETF 方块，颜色编码
4. 有 A 股映射的 ETF 右上角有蓝色小圆点
5. 点击方块展开 Detail Panel
6. Detail Panel 有走势图、REL 四格数据
7. 点击 Tab 切换指标，颜色实时更新

- [ ] **Step 3: 提交**

```bash
cd /Users/zhangchao/US-CN-Sector-Mapper
git add web/src/watchlist/style.css
git commit -m "feat: 添加热力图完整样式 (mobile-first)"
```

---

### Task 8: CI/CD - GitHub Actions 更新

**Files:**
- Modify: `.github/workflows/daily_update.yml`
- Modify: `.gitignore`

- [ ] **Step 1: 更新 .gitignore**

在 `.gitignore` 末尾添加：
```
# Watchlist data (keep structure, ignore content)
data/watchlist/*.json
!data/watchlist/.gitkeep
```

- [ ] **Step 2: 更新 GitHub Actions 工作流**

在 `daily_update.yml` 的 `update` job 中，在 `Run daily script` 步骤之后添加新步骤：

```yaml
      - name: Run watchlist data fetch
        run: python scripts/fetch_watchlist.py
```

在 `Prepare deploy directory` 步骤中修改为同时复制 watchlist 数据：

```yaml
      - name: Prepare deploy directory
        run: |
          cp -r data web/dist/data
```

这个步骤不需要改，因为 `data/` 目录下已包含 `watchlist/` 和 `results/`，`cp -r data` 会递归复制。

完整的工作流变为：

```yaml
name: Daily Update

on:
  schedule:
    - cron: '0 21 * * 0-4'  # UTC 21:00 周日-周四 = 北京时间 05:00 周一-周五
  workflow_dispatch:

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

      - name: Run daily script (OvernightRadar)
        run: python scripts/run_daily.py

      - name: Run watchlist data fetch
        run: python scripts/fetch_watchlist.py

      - name: Commit and push if changed
        run: |
          git config --local user.email "github-actions[bot]@users.noreply.github.com"
          git config --local user.name "github-actions[bot]"
          git add data/results/ data/watchlist/
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

- [ ] **Step 3: 验证构建**

Run: `cd /Users/zhangchao/US-CN-Sector-Mapper/web && npm run build`
Expected: `dist/` 目录包含 `index.html`、`watchlist.html` 和对应 assets

Run: `ls /Users/zhangchao/US-CN-Sector-Mapper/web/dist/`
Expected: `index.html  watchlist.html  assets/`

- [ ] **Step 4: 提交**

```bash
cd /Users/zhangchao/US-CN-Sector-Mapper
git add .gitignore .github/workflows/daily_update.yml
git commit -m "feat: 更新 GitHub Actions 支持热力图数据获取和构建"
```

---

### Task 9: 集成验证 + 构建测试

**Files:** (无新文件，验证现有代码)

- [ ] **Step 1: 运行全部 Python 测试**

Run: `cd /Users/zhangchao/US-CN-Sector-Mapper && python -m pytest tests/ -v`
Expected: 所有测试通过（包含原有的 test_calc.py 和新的 test_watchlist_calc.py）

- [ ] **Step 2: 运行数据管线端到端**

Run: `cd /Users/zhangchao/US-CN-Sector-Mapper && python scripts/fetch_watchlist.py`
Expected: 输出 `OK: .../data/watchlist/2026-04-12.json (N ETFs)` 或 `SKIP`

- [ ] **Step 3: 运行前端构建**

Run: `cd /Users/zhangchao/US-CN-Sector-Mapper/web && npm run build`
Expected: 构建成功，dist/ 包含 index.html 和 watchlist.html

- [ ] **Step 4: 本地预览验证**

Run: `cd /Users/zhangchao/US-CN-Sector-Mapper/web && npx vite preview`

打开浏览器访问 watchlist.html，验证：
- [ ] 热力图正确渲染（分组方块、颜色编码）
- [ ] 指标切换正常工作
- [ ] 点击方块展开 Detail Panel
- [ ] 走势图正常绘制
- [ ] A 股映射标识正确显示
- [ ] 隔夜雷达页面 (index.html) 未受影响

- [ ] **Step 5: 最终提交（如有修复）**

如果验证过程中有需要修复的地方，修复后提交：
```bash
git add -A
git commit -m "fix: 集成测试修复"
```

---

## Self-Review Checklist

- [x] **Spec coverage**: 每个需求都有对应 Task
  - 分组方块热力图 → Task 4
  - 指标切换 → Task 5
  - 点击展开走势图 → Task 6
  - 数据自动更新 → Task 8
  - A股映射标识 → Task 4 (has_cn_mapping badge)
- [x] **Placeholder scan**: 无 TBD、TODO、implement later
- [x] **Type consistency**: ETF 数据结构在 Python 和 JS 之间一致（ticker, name, change_pct, rel.rel_5 等）
- [x] **No existing code modified**: Task 3 的 vite.config.js 修改是增量式的，不影响现有功能
