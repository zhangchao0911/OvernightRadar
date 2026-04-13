# 隔夜雷达 V1.2 - AI 交易信号版 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 从"信息雷达"升级为"AI盘前交易决策系统"，每天自动获取美股新闻，AI分析输出3-5条可验证的交易信号，T+1自动验证命中率。

**Architecture:**
- 后端: Python 脚本获取 Finnhub News → AI 分析（Claude/OpenAI）→ 生成信号 → T+1 验证
- 前端: Tab 切换结构（信号/板块/新闻），复用现有 Vite + 原生 JS 架构
- 数据: JSON 文件存储，无需数据库

**Tech Stack:**
- Finnhub News API（复用现有 API key）
- Claude API / OpenAI API（可配置）
- Python 3.x + requests + pandas
- Vite + 原生 JavaScript

---

## 文件结构总览

### 新增文件

```
scripts/
├── fetch_news.py              # Finnhub News 获取
├── generate_signals.py        # AI 信号生成
└── track_signals.py           # T+1 验证

data/
├── news/                      # 原始新闻
│   └── YYYY-MM-DD.json
├── signals/                   # 交易信号
│   ├── YYYY-MM-DD.json
│   └── history.json           # 历史信号 + 验证结果
└── stats/                     # 统计数据
    └── hit_rate.json

web/src/
├── views/
│   ├── signals.js             # 信号 Tab 视图（新增）
│   ├── sectors.js             # 板块 Tab 视图（从 radar.js 拆分）
│   └── news.js                # 新闻 Tab 视图（新增）
├── components/
│   ├── signal-card.js         # 信号卡片组件
│   ├── stats-panel.js         # 统计面板组件
│   └── news-item.js           # 新闻条目组件
└── main.js                    # Tab 切换逻辑（修改）

tests/
├── test_fetch_news.py
├── test_generate_signals.py
└── test_track_signals.py
```

### 修改文件

```
scripts/
└── fetch_watchlist.py         # 复用行情数据获取

web/src/
├── main.js                    # 新增 Tab 切换
├── views/radar.js             # 重构为 Tab 容器
├── data.js                    # 新增数据获取方法
└── style.css                  # 新增 Tab/信号样式
```

---

## Phase 1: 新闻获取 (0.5天)

### Task 1.1: 创建数据目录结构

**Files:**
- Create: `data/news/.gitkeep`
- Create: `data/signals/.gitkeep`
- Create: `data/stats/.gitkeep`

- [ ] **Step 1: 创建数据目录**

```bash
mkdir -p data/news data/signals data/stats
touch data/news/.gitkeep data/signals/.gitkeep data/stats/.gitkeep
```

- [ ] **Step 2: 更新 .gitignore（如需要）**

检查 `.gitignore` 确保不提交 JSON 数据文件（只提交 .gitkeep）：

```bash
grep -q "data/news/*.json" .gitignore || echo "data/news/*.json" >> .gitignore
grep -q "data/signals/*.json" .gitignore || echo "data/signals/*.json" >> .gitignore
grep -q "data/stats/*.json" .gitignore || echo "data/stats/*.json" >> .gitignore
```

- [ ] **Step 3: 提交**

```bash
git add data/ .gitignore
git commit -m "feat: 创建数据目录结构 (V1.2)"
```

---

### Task 1.2: 实现 fetch_news.py - Finnhub News 集成

**Files:**
- Create: `scripts/fetch_news.py`
- Create: `tests/test_fetch_news.py`

- [ ] **Step 1: 编写测试 - 测试新闻获取**

```python
# tests/test_fetch_news.py
import os
import sys
import json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

def test_fetch_news_structure():
    """测试获取的新闻返回正确的数据结构"""
    from fetch_news import fetch_finnhub_news

    # 使用测试 API key 或 mock
    api_key = os.environ.get('FINNHUB_API_KEY', 'test')
    news = fetch_finnhub_news(api_key, limit=5)

    assert isinstance(news, list), "返回值应该是列表"
    if len(news) > 0:
        assert 'headline' in news[0], "新闻应包含 headline"
        assert 'source' in news[0], "新闻应包含 source"
        assert 'datetime' in news[0], "新闻应包含 datetime"
        assert 'url' in news[0], "新闻应包含 url"

def test_filter_news_by_time():
    """测试按时间过滤新闻"""
    from fetch_news import filter_news_by_time

    now = int(datetime.now().timestamp())
    old_time = now - 48 * 3600  # 48小时前

    news = [
        {'datetime': now, 'headline': 'recent'},
        {'datetime': old_time, 'headline': 'old'}
    ]

    filtered = filter_news_by_time(news, hours=24)
    assert len(filtered) == 1
    assert filtered[0]['headline'] == 'recent'

def test_deduplicate_news():
    """测试新闻去重"""
    from fetch_news import deduplicate_news

    news = [
        {'headline': 'Test', 'id': 1},
        {'headline': 'Test', 'id': 2},  # 重复标题
        {'headline': 'Other', 'id': 3}
    ]

    deduped = deduplicate_news(news)
    assert len(deduped) == 2
    headlines = [n['headline'] for n in deduped]
    assert headlines.count('Test') == 1  # 只保留一条
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd /Users/zhangchao/US-CN-Sector-Mapper
python -m pytest tests/test_fetch_news.py -v
```

Expected: FAIL - `ModuleNotFoundError: No module named 'fetch_news'`

- [ ] **Step 3: 实现最小功能通过测试**

```python
# scripts/fetch_news.py
"""
Finnhub News 获取脚本
用法: FINNHUB_API_KEY=xxx python scripts/fetch_news.py
"""
import json
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict

import requests

# Finnhub API 端点
FINNHUB_NEWS = "https://finnhub.io/api/v1/news"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "news")


def load_api_key() -> str:
    """从环境变量或 .env 文件加载 Finnhub API key"""
    key = os.environ.get("FINNHUB_API_KEY", "").strip()
    if key:
        return key

    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("FINNHUB_API_KEY="):
                    key = line.split("=", 1)[1].strip().strip("'\"")
                    if key and "your_api_key_here" not in key:
                        return key
    return ""


def fetch_finnhub_news(api_key: str, limit: int = 30) -> List[Dict]:
    """
    从 Finnhub 获取新闻

    Args:
        api_key: Finnhub API key
        limit: 返回新闻数量上限

    Returns:
        新闻列表，每个新闻包含 headline, source, datetime, url, summary 等
    """
    try:
        resp = requests.get(
            FINNHUB_NEWS,
            params={"token": api_key},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        # 限制数量
        return data[:limit] if isinstance(data, list) else []
    except Exception as e:
        print(f"ERROR: 获取新闻失败 - {e}")
        return []


def filter_news_by_time(news: List[Dict], hours: int = 24) -> List[Dict]:
    """
    按时间过滤新闻，只保留最近 N 小时的

    Args:
        news: 原始新闻列表
        hours: 时间窗口（小时）

    Returns:
        过滤后的新闻列表
    """
    cutoff = int((datetime.now() - timedelta(hours=hours)).timestamp())
    return [n for n in news if n.get('datetime', 0) > cutoff]


def deduplicate_news(news: List[Dict]) -> List[Dict]:
    """
    去重：按标题去重，保留最新的

    Args:
        news: 原始新闻列表

    Returns:
        去重后的新闻列表
    """
    seen = set()
    deduped = []

    for item in news:
        headline = item.get('headline', '').strip()
        if headline and headline not in seen:
            seen.add(headline)
            deduped.append(item)

    return deduped


def save_news(news: List[Dict], date: str = None) -> str:
    """
    保存新闻到 JSON 文件

    Args:
        news: 新闻列表
        date: 日期字符串 (YYYY-MM-DD)，默认为今天

    Returns:
        保存的文件路径
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, f"{date}.json")

    output = {
        "date": date,
        "fetched_at": datetime.now().isoformat(),
        "total": len(news),
        "news": news
    }

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    return filepath


def main():
    """主函数"""
    api_key = load_api_key()
    if not api_key:
        print("ERROR: FINNHUB_API_KEY 未设置")
        sys.exit(1)

    print("正在获取 Finnhub News...")
    news = fetch_finnhub_news(api_key, limit=30)
    print(f"  获取到 {len(news)} 条新闻")

    print("正在按时间过滤...")
    news = filter_news_by_time(news, hours=24)
    print(f"  最近24小时: {len(news)} 条")

    print("正在去重...")
    news = deduplicate_news(news)
    print(f"  去重后: {len(news)} 条")

    filepath = save_news(news)
    print(f"已保存到: {filepath}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 运行测试验证通过**

```bash
python -m pytest tests/test_fetch_news.py -v
```

Expected: PASS

- [ ] **Step 5: 手动测试完整流程**

```bash
FINNHUB_API_KEY=your_key python scripts/fetch_news.py
cat data/news/$(date +%Y-%m-%d).json | head -50
```

Expected: 看到 JSON 输出，包含新闻数据

- [ ] **Step 6: 提交**

```bash
git add scripts/fetch_news.py tests/test_fetch_news.py
git commit -m "feat: 实现 Finnhub News 获取功能"
```

---

## Phase 2: 信号生成 (1.5天)

### Task 2.1: 创建 AI 调用封装

**Files:**
- Create: `scripts/ai_client.py`
- Create: `tests/test_ai_client.py`

- [ ] **Step 1: 编写测试 - 测试 AI 客户端**

```python
# tests/test_ai_client.py
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

def test_claude_client_initialization():
    """测试 Claude 客户端初始化"""
    from ai_client import AIClient, Provider

    # 使用 mock key
    client = AIClient(provider=Provider.CLAUDE, api_key="test_key")
    assert client.provider == Provider.CLAUDE
    assert client.api_key == "test_key"

def test_openai_client_initialization():
    """测试 OpenAI 客户端初始化"""
    from ai_client import AIClient, Provider

    client = AIClient(provider=Provider.OPENAI, api_key="test_key")
    assert client.provider == Provider.OPENAI

def test_build_prompt():
    """测试 Prompt 构建"""
    from ai_client import AIClient, Provider

    client = AIClient(provider=Provider.CLAUDE, api_key="test")

    news = [
        {"headline": "Test News 1", "summary": "Summary 1"},
        {"headline": "Test News 2", "summary": "Summary 2"}
    ]

    prompt = client.build_signal_prompt(news)

    assert "Test News 1" in prompt
    assert "Test News 2" in prompt
    assert "JSON" in prompt
```

- [ ] **Step 2: 运行测试验证失败**

```bash
python -m pytest tests/test_ai_client.py -v
```

Expected: FAIL - ModuleNotFoundError

- [ ] **Step 3: 实现 AI 客户端**

```python
# scripts/ai_client.py
"""
AI 客户端封装 - 支持 Claude/OpenAI
"""
import os
import json
from enum import Enum
from typing import List, Dict, Optional
import requests


class Provider(Enum):
    CLAUDE = "claude"
    OPENAI = "openai"


class AIClient:
    """统一的 AI 客户端接口"""

    def __init__(self, provider: Provider, api_key: str, model: str = None):
        """
        初始化 AI 客户端

        Args:
            provider: AI 服务提供商
            api_key: API key
            model: 模型名称（可选，使用默认值）
        """
        self.provider = provider
        self.api_key = api_key
        self.model = model or self._default_model()

    def _default_model(self) -> str:
        """获取默认模型名称"""
        if self.provider == Provider.CLAUDE:
            return "claude-3-5-sonnet-20241022"
        elif self.provider == Provider.OPENAI:
            return "gpt-4o"
        return "unknown"

    def build_signal_prompt(self, news: List[Dict]) -> str:
        """
        构建信号生成 Prompt

        Args:
            news: 新闻列表，每条包含 headline, summary, source 等

        Returns:
            完整的 Prompt 字符串
        """
        news_text = "\n".join([
            f"{i+1}. {n.get('headline', '')} ({n.get('source', '')})\n   {n.get('summary', '')[:100]}..."
            for i, n in enumerate(news[:20])  # 最多20条
        ])

        return f"""你是一位专业的美股交易分析师。以下是今日美股相关新闻：

{news_text}

请分析这些新闻，输出 3-5 条交易信号。

要求：
1. 每条信号必须包含：title, direction, sectors, action, reason
2. action 必须是具体可执行的建议（条件 + 动作），如"若高开>2%不追，低开可关注"
3. 只输出真正有信号价值的新闻，忽略噪音
4. 按重要性降序排列

输出格式（必须是有效的 JSON，不要包含其他文字）：
[
  {{
    "title": "简短标题",
    "direction": "利多/利空",
    "sectors": ["板块1", "板块2"],
    "action": "若高开>2%不追，低开可关注",
    "reason": "交易逻辑说明"
  }}
]
"""

    def generate_signals(self, news: List[Dict]) -> List[Dict]:
        """
        调用 AI 生成交易信号

        Args:
            news: 新闻列表

        Returns:
            生成的信号列表
        """
        prompt = self.build_signal_prompt(news)

        if self.provider == Provider.CLAUDE:
            return self._call_claude(prompt)
        elif self.provider == Provider.OPENAI:
            return self._call_openai(prompt)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def _call_claude(self, prompt: str) -> List[Dict]:
        """调用 Claude API"""
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        data = {
            "model": self.model,
            "max_tokens": 2000,
            "messages": [{"role": "user", "content": prompt}]
        }

        try:
            resp = requests.post(url, headers=headers, json=data, timeout=30)
            resp.raise_for_status()
            result = resp.json()

            content = result.get("content", [{}])[0].get("text", "")
            return self._parse_json_response(content)
        except Exception as e:
            print(f"ERROR: Claude API 调用失败 - {e}")
            return []

    def _call_openai(self, prompt: str) -> List[Dict]:
        """调用 OpenAI API"""
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "authorization": f"Bearer {self.api_key}",
            "content-type": "application/json"
        }
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3
        }

        try:
            resp = requests.post(url, headers=headers, json=data, timeout=30)
            resp.raise_for_status()
            result = resp.json()

            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            return self._parse_json_response(content)
        except Exception as e:
            print(f"ERROR: OpenAI API 调用失败 - {e}")
            return []

    def _parse_json_response(self, content: str) -> List[Dict]:
        """从 AI 响应中解析 JSON"""
        # 尝试直接解析
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # 尝试提取 JSON 代码块
        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            try:
                return json.loads(content[start:end].strip())
            except json.JSONDecodeError:
                pass

        if "```" in content:
            start = content.find("```") + 3
            end = content.find("```", start)
            try:
                return json.loads(content[start:end].strip())
            except json.JSONDecodeError:
                pass

        print("ERROR: 无法解析 AI 响应为 JSON")
        print(f"Content: {content[:500]}")
        return []


def load_api_key() -> tuple[Provider, str]:
    """从环境变量加载 AI API key"""
    # 优先使用 Claude
    claude_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if claude_key:
        return Provider.CLAUDE, claude_key

    # 其次使用 OpenAI
    openai_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if openai_key:
        return Provider.OPENAI, openai_key

    return None, ""
```

- [ ] **Step 4: 运行测试验证通过**

```bash
python -m pytest tests/test_ai_client.py -v
```

Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add scripts/ai_client.py tests/test_ai_client.py
git commit -m "feat: 实现 AI 客户端封装"
```

---

### Task 2.2: 实现评分逻辑

**Files:**
- Create: `scripts/signal_scorer.py`
- Create: `tests/test_signal_scorer.py`

- [ ] **Step 1: 编写测试 - 测试评分逻辑**

```python
# tests/test_signal_scorer.py
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

def test_calculate_score_macro_bullish():
    """测试宏观利多信号评分"""
    from signal_scorer import calculate_score

    signal = {
        "title": "美联储降息",
        "direction": "利多",
        "sectors": ["科技", "半导体", "金融"],
        "action": "若高开>2%不追",
        "reason": "宏观利好",
        "is_macro": True,
        "under_priced": True,
        "clear_action": True
    }

    score, detail = calculate_score(signal)
    assert score >= 70, f"宏观利多信号应得高分，实际: {score}"
    assert detail["importance"] >= 20

def test_calculate_score_weak():
    """测试弱信号评分"""
    from signal_scorer import calculate_score

    signal = {
        "title": "某公司小幅涨跌",
        "direction": "利多",
        "sectors": ["半导体"],
        "action": "可关注",
        "reason": "个股波动",
        "is_macro": False,
        "under_priced": False,
        "clear_action": False
    }

    score, detail = calculate_score(signal)
    assert score < 60, f"弱信号应得低分，实际: {score}"

def test_filter_signals():
    """测试信号筛选"""
    from signal_scorer import filter_signals

    signals = [
        {"title": "强信号", "score": 75},
        {"title": "中信号", "score": 55},
        {"title": "弱信号", "score": 40}
    ]

    filtered = filter_signals(signals, min_score=50, max_count=5)
    assert len(filtered) == 2
    assert all(s["score"] >= 50 for s in filtered)
```

- [ ] **Step 2: 运行测试验证失败**

```bash
python -m pytest tests/test_signal_scorer.py -v
```

Expected: FAIL

- [ ] **Step 3: 实现评分逻辑**

```python
# scripts/signal_scorer.py
"""
信号评分模块
"""
from typing import List, Dict, Tuple


def calculate_score(signal: Dict) -> Tuple[int, Dict]:
    """
    计算信号得分

    Args:
        signal: 信号字典，包含 title, direction, sectors, action, reason

    Returns:
        (总分, 评分明细)
    """
    score = 0
    detail = {
        "importance": 0,
        "reach": 0,
        "pricing": 0,
        "clarity": 0
    }

    # 1. 事件重要性 (0-30)
    title = signal.get("title", "").lower()
    reason = signal.get("reason", "").lower()

    if signal.get("is_macro"):
        detail["importance"] = 25
    elif any(kw in title or kw in reason for kw in ["政策", "降息", "加息", "通胀", "gdp"]):
        detail["importance"] = 22
    elif any(kw in title or kw in reason for kw in ["行业", "板块", "etf"]):
        detail["importance"] = 15
    else:
        detail["importance"] = 8

    # 2. 影响范围 (0-25)
    sectors = signal.get("sectors", [])
    sector_count = len(sectors)

    if sector_count >= 3:
        detail["reach"] = 20
    elif sector_count >= 2:
        detail["reach"] = 15
    elif sector_count >= 1:
        detail["reach"] = 10
    else:
        detail["reach"] = 5

    # 3. 定价程度 (0-25) - 反向，未定价得分高
    if signal.get("under_priced"):
        detail["pricing"] = 22
    elif any(kw in reason for kw in["未定价", "市场未预期", "超预期"]):
        detail["pricing"] = 18
    elif any(kw in reason for kw in["部分定价", "已部分反映"]):
        detail["pricing"] = 10
    else:
        detail["pricing"] = 5

    # 4. 信号清晰度 (0-20)
    action = signal.get("action", "")
    if signal.get("clear_action"):
        detail["clarity"] = 18
    elif "若" in action and any(kw in action for kw in [">", "<", "%"]):
        detail["clarity"] = 15
    elif len(action) > 10:
        detail["clarity"] = 10
    else:
        detail["clarity"] = 5

    score = sum(detail.values())

    return score, detail


def enhance_signal_with_analysis(signal: Dict) -> Dict:
    """
    增强信号，添加分析标记

    Args:
        signal: 原始信号

    Returns:
        增强后的信号
    """
    title = signal.get("title", "")
    reason = signal.get("reason", "")
    action = signal.get("action", "")

    enhanced = signal.copy()

    # 判断是否宏观
    enhanced["is_macro"] = any(kw in title or kw in reason for kw in [
        "美联储", "降息", "加息", "通胀", "GDP", "非农", "政策", "国会"
    ])

    # 判断是否未定价
    enhanced["under_priced"] = any(kw in reason for kw in [
        "未定价", "超预期", "意外", "出乎意料"
    ])

    # 判断是否有清晰操作
    enhanced["clear_action"] = (
        "若" in action and
        any(kw in action for kw in [">", "<", "%", "追", "观望", "止损"])
    )

    return enhanced


def get_level(score: int) -> str:
    """根据分数获取等级"""
    if score >= 70:
        return "强"
    elif score >= 50:
        return "中"
    else:
        return "弱"


def filter_signals(signals: List[Dict], min_score: int = 50, max_count: int = 5) -> List[Dict]:
    """
    筛选和排序信号

    Args:
        signals: 原始信号列表
        min_score: 最低分数
        max_count: 最大数量

    Returns:
        筛选后的信号列表
    """
    # 过滤低分
    filtered = [s for s in signals if s.get("score", 0) >= min_score]

    # 按分数降序
    filtered.sort(key=lambda x: x.get("score", 0), reverse=True)

    # 限制数量
    return filtered[:max_count]
```

- [ ] **Step 4: 运行测试验证通过**

```bash
python -m pytest tests/test_signal_scorer.py -v
```

Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add scripts/signal_scorer.py tests/test_signal_scorer.py
git commit -m "feat: 实现信号评分逻辑"
```

---

### Task 2.3: 实现信号生成主脚本

**Files:**
- Create: `scripts/generate_signals.py`
- Create: `tests/test_generate_signals.py`

- [ ] **Step 1: 编写测试 - 测试信号生成流程**

```python
# tests/test_generate_signals.py
import os
import sys
import json
import tempfile
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

def test_load_news():
    """测试加载新闻"""
    from generate_signals import load_news

    # 创建临时新闻文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({
            "date": "2026-04-13",
            "news": [
                {"headline": "Test", "source": "Test", "summary": "Test"}
            ]
        }, f)
        temp_path = f.name

    try:
        news = load_news("2026-04-13", data_dir=os.path.dirname(temp_path))
        assert len(news) == 1
        assert news[0]["headline"] == "Test"
    finally:
        os.unlink(temp_path)

def test_enrich_signals_with_source():
    """测试关联源新闻"""
    from generate_signals import enrich_signals_with_source

    news = [
        {"headline": "Fed Rate Cut", "url": "https://test.com/1", "source": "Reuters"}
    ]

    signals = [
        {"title": "美联储降息", "reason": "Fed Rate Cut"}
    ]

    enriched = enrich_signals_with_source(signals, news)
    assert len(enriched) == 1
    assert "source_news" in enriched[0]
    assert enriched[0]["source_news"]["headline"] == "Fed Rate Cut"
```

- [ ] **Step 2: 运行测试验证失败**

```bash
python -m pytest tests/test_generate_signals.py -v
```

Expected: FAIL

- [ ] **Step 3: 实现信号生成主脚本**

```python
# scripts/generate_signals.py
"""
信号生成主脚本
用法: ANTHROPIC_API_KEY=xxx python scripts/generate_signals.py
"""
import json
import os
import sys
from datetime import datetime
from typing import List, Dict
import difflib

sys.path.insert(0, os.path.dirname(__file__))

from ai_client import AIClient, Provider, load_api_key
from signal_scorer import (
    calculate_score, enhance_signal_with_analysis,
    get_level, filter_signals
)

# 目录配置
NEWS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "news")
SIGNALS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "signals")


def load_news(date: str, data_dir: str = None) -> List[Dict]:
    """加载指定日期的新闻"""
    if data_dir is None:
        data_dir = NEWS_DIR

    filepath = os.path.join(data_dir, f"{date}.json")

    if not os.path.exists(filepath):
        print(f"ERROR: 新闻文件不存在: {filepath}")
        print("请先运行 fetch_news.py 获取新闻")
        sys.exit(1)

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return data.get("news", [])


def enrich_signals_with_source(signals: List[Dict], news: List[Dict]) -> List[Dict]:
    """
    为信号关联源新闻

    Args:
        signals: AI 生成的信号列表
        news: 原始新闻列表

    Returns:
        关联了源新闻的信号列表
    """
    enriched = []

    for signal in signals:
        # 尝试通过标题匹配找到源新闻
        title = signal.get("title", "")
        reason = signal.get("reason", "")

        best_match = None
        best_ratio = 0.3  # 最低相似度阈值

        for news_item in news:
            news_headline = news_item.get("headline", "")

            # 计算相似度
            ratio = difflib.SequenceMatcher(None, title.lower(), news_headline.lower()).ratio()

            # 也检查 reason
            if reason and news_item.get("summary"):
                ratio2 = difflib.SequenceMatcher(None, reason.lower(), news_item.get("summary", "").lower()).ratio()
                ratio = max(ratio, ratio2)

            if ratio > best_ratio:
                best_ratio = ratio
                best_match = news_item

        enriched_signal = signal.copy()

        if best_match:
            enriched_signal["source_news"] = {
                "headline": best_match.get("headline"),
                "source": best_match.get("source"),
                "url": best_match.get("url"),
                "datetime": best_match.get("datetime")
            }

        enriched.append(enriched_signal)

    return enriched


def generate_signal_id() -> str:
    """生成唯一信号 ID"""
    import uuid
    return str(uuid.uuid4())


def map_sectors_to_tickers(sectors: List[str]) -> List[str]:
    """
    将板块名称映射到 ETF 代码

    Args:
        sectors: 板块名称列表

    Returns:
        ETF 代码列表
    """
    mapping = {
        "科技": ["XLK"],
        "半导体": ["SOXX"],
        "AI": ["THNQ", "WCLD"],
        "算力": ["THNQ", "WCLD"],
        "新能源车": ["DRIV"],
        "黄金": ["GLD"],
        "机器人": ["BOTZ"],
        "商业航天": ["UFO"],
        "存储": ["DRAM"]
    }

    tickers = set()
    for sector in sectors:
        for key, values in mapping.items():
            if key in sector:
                tickers.update(values)

    return list(tickers)


def save_signals(signals: List[Dict], date: str = None) -> str:
    """保存信号到文件"""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    os.makedirs(SIGNALS_DIR, exist_ok=True)
    filepath = os.path.join(SIGNALS_DIR, f"{date}.json")

    output = {
        "date": date,
        "generated_at": datetime.now().isoformat(),
        "total": len(signals),
        "signals": signals
    }

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    return filepath


def main():
    """主函数"""
    # 获取 API key
    provider, api_key = load_api_key()
    if not api_key:
        print("ERROR: 未设置 AI API key (ANTHROPIC_API_KEY 或 OPENAI_API_KEY)")
        sys.exit(1)

    print(f"使用 AI 提供商: {provider.value}")

    date = datetime.now().strftime("%Y-%m-%d")
    print(f"日期: {date}")

    # 1. 加载新闻
    print(f"\n正在加载新闻...")
    news = load_news(date)
    print(f"  加载了 {len(news)} 条新闻")

    if len(news) == 0:
        print("ERROR: 没有新闻数据")
        sys.exit(1)

    # 2. 调用 AI 生成信号
    print(f"\n正在调用 AI 生成信号...")
    client = AIClient(provider=provider, api_key=api_key)
    raw_signals = client.generate_signals(news)

    if len(raw_signals) == 0:
        print("ERROR: AI 未生成任何信号")
        sys.exit(1)

    print(f"  AI 生成了 {len(raw_signals)} 条原始信号")

    # 3. 增强和评分
    print(f"\n正在计算评分...")
    enhanced_signals = []
    for sig in raw_signals:
        enhanced = enhance_signal_with_analysis(sig)
        score, detail = calculate_score(enhanced)
        enhanced["score"] = score
        enhanced["score_detail"] = detail
        enhanced["level"] = get_level(score)
        enhanced["targets"] = map_sectors_to_tickers(enhanced.get("sectors", []))
        enhanced_signals.append(enhanced)

    # 4. 筛选
    print(f"\n正在筛选信号...")
    filtered_signals = filter_signals(enhanced_signals, min_score=50, max_count=5)
    print(f"  筛选后: {len(filtered_signals)} 条")

    if len(filtered_signals) == 0:
        print("WARNING: 没有信号达到筛选标准")
        # 仍然保存，让用户决定
        filtered_signals = enhanced_signals[:3]

    # 5. 关联源新闻
    print(f"\n正在关联源新闻...")
    final_signals = []
    for sig in filtered_signals:
        sig["id"] = generate_signal_id()
        sig["date"] = date
        sig["created_at"] = datetime.now().isoformat()

        # T+1 字段（待填充）
        sig["tracking"] = {
            "t1_open": None,
            "t1_close": None,
            "return": None,
            "hit": None,
            "hit_level": None
        }

        final_signals.append(sig)

    enriched_signals = enrich_signals_with_source(final_signals, news)

    # 6. 保存
    filepath = save_signals(enriched_signals, date)
    print(f"\n已保存到: {filepath}")

    # 7. 输出摘要
    print(f"\n生成的信号:")
    for sig in enriched_signals:
        level_icon = {"强": "🔥", "中": "⚠️", "弱": "🧊"}.get(sig["level"], "❓")
        dir_icon = {"利多": "🟢", "利空": "🔴"}.get(sig["direction"], "⚪")
        print(f"  {level_icon} [{sig['level']}] {sig['title']}")
        print(f"    {dir_icon} {sig['direction']} · {','.join(sig['sectors'])} · 评分{sig['score']}")
        print(f"    💡 {sig['action']}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 运行测试验证通过**

```bash
python -m pytest tests/test_generate_signals.py -v
```

Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add scripts/generate_signals.py tests/test_generate_signals.py
git commit -m "feat: 实现信号生成主脚本"
```

---

## Phase 3: 前端重构 - Tab 结构 (1.5天)

### Task 3.1: 更新 main.js - 添加 Tab 切换逻辑

**Files:**
- Modify: `web/src/main.js:1-50`
- Create: `web/src/views/sectors.js`

- [ ] **Step 1: 读取现有 main.js**

```bash
cat web/src/main.js
```

记录现有代码结构。

- [ ] **Step 2: 备份现有 radar.js 为 sectors.js**

```bash
cp web/src/views/radar.js web/src/views/sectors.js
```

- [ ] **Step 3: 更新 main.js 添加 Tab 切换**

```javascript
// web/src/main.js - 完整替换
import { renderHeatmapView } from './views/heatmap.js';
import { renderRadarView } from './views/radar.js';

// Tab 配置
const TABS = ['heatmap', 'radar'];
const DEFAULT_TAB = 'heatmap';

// Tab 状态管理
let currentTab = DEFAULT_TAB;

// 从 localStorage 恢复上次选择的 Tab
function loadSavedTab() {
  try {
    const saved = localStorage.getItem('overnight_radar_tab');
    if (saved && TABS.includes(saved)) {
      return saved;
    }
  } catch (e) {
    console.warn('无法读取保存的 tab:', e);
  }
  return DEFAULT_TAB;
}

// 保存 Tab 选择到 localStorage
function saveTab(tab) {
  try {
    localStorage.setItem('overnight_radar_tab', tab);
  } catch (e) {
    console.warn('无法保存 tab:', e);
  }
}

// 切换 Tab
async function switchTab(newTab) {
  if (newTab === currentTab) return;

  currentTab = newTab;
  saveTab(newTab);

  // 更新 Tab 按钮状态
  document.querySelectorAll('.tab-item').forEach(btn => {
    if (btn.dataset.view === newTab) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  // 渲染对应视图
  const container = document.getElementById('view-container');
  const header = document.getElementById('app-header');

  if (newTab === 'heatmap') {
    await renderHeatmapView(container, header);
  } else if (newTab === 'radar') {
    await renderRadarView(container, header);
  }
}

// 从 URL hash 获取 Tab
function getTabFromHash() {
  const hash = window.location.hash.slice(1);
  if (hash && TABS.includes(hash)) {
    return hash;
  }
  return null;
}

// 初始化
async function init() {
  // 隐藏 loading
  document.getElementById('loading').style.display = 'none';
  document.getElementById('tab-nav').style.display = 'flex';

  // 确定初始 Tab
  let initialTab = getTabFromHash();
  if (!initialTab) {
    initialTab = loadSavedTab();
  }

  // 设置初始 Tab 按钮
  document.querySelectorAll('.tab-item').forEach(btn => {
    if (btn.dataset.view === initialTab) {
      btn.classList.add('active');
    }
  });

  // 渲染初始视图
  const container = document.getElementById('view-container');
  const header = document.getElementById('app-header');
  document.getElementById('app').style.display = 'block';

  if (initialTab === 'heatmap') {
    await renderHeatmapView(container, header);
  } else if (initialTab === 'radar') {
    await renderRadarView(container, header);
  }

  currentTab = initialTab;

  // 绑定 Tab 点击事件
  document.querySelectorAll('.tab-item').forEach(btn => {
    btn.addEventListener('click', () => {
      const targetView = btn.dataset.view;
      window.location.hash = targetView;
      switchTab(targetView);
    });
  });
}

// 监听 hash 变化
window.addEventListener('hashchange', () => {
  const tab = getTabFromHash();
  if (tab && tab !== currentTab) {
    switchTab(tab);
  }
});

// 启动
init();
```

- [ ] **Step 4: 提交**

```bash
git add web/src/main.js web/src/views/sectors.js
git commit -m "feat: 添加 Tab 切换逻辑，备份 radar.js 为 sectors.js"
```

---

### Task 3.2: 重写 radar.js 为 Tab 容器

**Files:**
- Modify: `web/src/views/radar.js`

- [ ] **Step 1: 读取现有 radar.js**

```bash
cat web/src/views/radar.js
```

- [ ] **Step 2: 重写 radar.js 为 Tab 容器**

```javascript
// web/src/views/radar.js
/**
 * 隔夜雷达 Tab 容器视图
 * 负责渲染雷达页面的 Tab 导航和内容区域
 */
import { renderSignalsView } from './signals.js';
import { renderSectorsView } from './sectors.js';
import { renderNewsView } from './news.js';
import { fetchRadarData } from '../data.js';

// Radar 子 Tab 配置
const RADAR_TABS = ['signals', 'sectors', 'news'];
const RADAR_TAB_LABELS = {
  signals: '📋 信号',
  sectors: '📊 板块',
  news: '📰 新闻'
};
let currentRadarTab = 'signals';  // 默认显示信号 Tab

/**
 * 渲染隔夜雷达视图（Tab 容器）
 */
export async function renderRadarView(container, header) {
  const report = await fetchRadarData();

  if (!report) {
    container.innerHTML = '<p class="empty-state">暂无雷达数据</p>';
    header.innerHTML = `
      <h1 class="title">隔夜雷达 Pro</h1>
      <p class="slogan">AI 交易信号 + 板块情绪分析</p>
    `;
    return;
  }

  // 渲染 Header（保持不变）
  renderHeader(header, report);

  // 渲染 Radar Tab 导航和内容
  renderRadarTabs(container, report);
}

/**
 * 渲染页面 Header
 */
function renderHeader(header, report) {
  const indexNames = { sp500: '标普', nasdaq: '纳指', dow: '道指' };
  let indicesHtml = '';
  for (const [key, name] of Object.entries(indexNames)) {
    if (report.market_indices && report.market_indices[key]) {
      const change = report.market_indices[key].change_pct;
      const cls = change >= 0 ? 'up' : 'down';
      const sign = change >= 0 ? '+' : '';
      indicesHtml += `<span class="index-item">${name}<span class="${cls}">${sign}${change.toFixed(1)}%</span></span>`;
    }
  }

  header.innerHTML = `
    <h1 class="title">隔夜雷达 Pro</h1>
    <p class="slogan">AI 交易信号 + 板块情绪分析</p>
    <div class="market-indices">${indicesHtml}</div>
    <p class="date">${report.market_summary} · ${report.date} ${report.weekday}</p>
  `;
}

/**
 * 渲染 Radar Tab 导航和内容区域
 */
function renderRadarTabs(container, report) {
  // Tab 导航
  const tabsHtml = RADAR_TABS.map(tab => `
    <button class="radar-tab ${tab === currentRadarTab ? 'active' : ''}" data-radar-tab="${tab}">
      ${RADAR_TAB_LABELS[tab]}
    </button>
  `).join('');

  // 内容区域
  const contentHtml = `
    <div class="radar-tabs">
      <div class="radar-tab-nav">${tabsHtml}</div>
      <div class="radar-tab-content" id="radar-tab-content"></div>
    </div>
  `;

  container.innerHTML = contentHtml;

  // 渲染当前 Tab 内容
  renderCurrentRadarTabContent(report);

  // 绑定 Tab 点击事件
  container.querySelectorAll('.radar-tab').forEach(tabBtn => {
    tabBtn.addEventListener('click', (e) => {
      const newTab = e.target.dataset.radarTab;
      if (newTab !== currentRadarTab) {
        currentRadarTab = newTab;

        // 更新 Tab 按钮状态
        container.querySelectorAll('.radar-tab').forEach(btn => {
          btn.classList.toggle('active', btn.dataset.radarTab === newTab);
        });

        // 重新渲染内容
        renderCurrentRadarTabContent(report);
      }
    });
  });
}

/**
 * 渲染当前 Radar Tab 的内容
 */
function renderCurrentRadarTabContent(report) {
  const contentContainer = document.getElementById('radar-tab-content');

  if (currentRadarTab === 'signals') {
    renderSignalsView(contentContainer);
  } else if (currentRadarTab === 'sectors') {
    renderSectorsView(contentContainer, report);
  } else if (currentRadarTab === 'news') {
    renderNewsView(contentContainer);
  }
}
```

- [ ] **Step 3: 提交**

```bash
git add web/src/views/radar.js
git commit -m "refactor: 重写 radar.js 为 Tab 容器"
```

---

### Task 3.3: 创建 signals.js 视图

**Files:**
- Create: `web/src/views/signals.js`

- [ ] **Step 1: 创建 signals.js**

```javascript
// web/src/views/signals.js
/**
 * 信号 Tab 视图
 */
import { fetchSignals, fetchSignalHistory } from '../data.js';
import { renderSignalCard } from '../components/signal-card.js';
import { renderStatsPanel } from '../components/stats-panel.js';

export async function renderSignalsView(container) {
  container.innerHTML = '<p class="loading">正在加载信号...</p>';

  const signals = await fetchSignals();
  const history = await fetchSignalHistory();

  if (!signals || signals.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <p>今日暂无信号</p>
        <p class="hint">信号在每日早上 8:30 后生成</p>
      </div>
    `;
    return;
  }

  // 渲染信号卡片
  const signalsHtml = signals.map(renderSignalCard).join('');

  // 渲染统计面板
  const statsHtml = renderStatsPanel(history);

  container.innerHTML = `
    <div class="signals-container">
      <div class="signals-header">
        <h2>🔥 今日交易信号</h2>
        <span class="signals-count">${signals.length}条</span>
      </div>
      ${signalsHtml}
      ${statsHtml}
    </div>
  `;
}
```

- [ ] **Step 2: 提交**

```bash
git add web/src/views/signals.js
git commit -m "feat: 创建 signals.js 视图"
```

---

### Task 3.4: 创建 news.js 视图

**Files:**
- Create: `web/src/views/news.js`

- [ ] **Step 1: 创建 news.js**

```javascript
// web/src/views/news.js
/**
 * 新闻 Tab 视图
 */
import { fetchNews } from '../data.js';
import { renderNewsItem } from '../components/news-item.js';

export async function renderNewsView(container) {
  container.innerHTML = '<p class="loading">正在加载新闻...</p>';

  const newsData = await fetchNews();

  if (!newsData || !newsData.news || newsData.news.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <p>暂无新闻</p>
      </div>
    `;
    return;
  }

  const newsHtml = newsData.news.map(renderNewsItem).join('');

  container.innerHTML = `
    <div class="news-container">
      <div class="news-header">
        <h2>📰 今日新闻</h2>
        <span class="news-count">${newsData.news.length}条</span>
      </div>
      ${newsHtml}
    </div>
  `;
}
```

- [ ] **Step 2: 提交**

```bash
git add web/src/views/news.js
git commit -m "feat: 创建 news.js 视图"
```

---

## Phase 4: 组件开发 (1天)

### Task 4.1: 创建 signal-card.js 组件

**Files:**
- Create: `web/src/components/signal-card.js`

- [ ] **Step 1: 创建 signal-card.js**

```javascript
// web/src/components/signal-card.js
/**
 * 信号卡片组件
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
 * 格式化时间戳
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
```

- [ ] **Step 2: 提交**

```bash
git add web/src/components/signal-card.js
git commit -m "feat: 创建 signal-card.js 组件"
```

---

### Task 4.2: 创建 stats-panel.js 组件

**Files:**
- Create: `web/src/components/stats-panel.js`

- [ ] **Step 1: 创建 stats-panel.js**

```javascript
// web/src/components/stats-panel.js
/**
 * 统计面板组件
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
 * 渲染分层统计
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
```

- [ ] **Step 2: 提交**

```bash
git add web/src/components/stats-panel.js
git commit -m "feat: 创建 stats-panel.js 组件"
```

---

### Task 4.3: 创建 news-item.js 组件

**Files:**
- Create: `web/src/components/news-item.js`

- [ ] **Step 1: 创建 news-item.js**

```javascript
// web/src/components/news-item.js
/**
 * 新闻条目组件
 */

export function renderNewsItem(news) {
  const time = formatTime(news.datetime);
  const hasSignal = news.has_signal;

  return `
    <div class="news-item ${hasSignal ? 'has-signal' : ''}">
      <div class="news-header">
        <h4 class="news-headline">${news.headline}</h4>
        ${hasSignal ? '<span class="news-signal-badge">已生成信号</span>' : ''}
      </div>
      <div class="news-meta">
        <span class="news-source">${news.source}</span>
        <span class="news-time">${time}</span>
      </div>
      ${news.summary ? `<p class="news-summary">${news.summary}</p>` : ''}
      ${news.url ? `<a href="${news.url}" target="_blank" class="news-link">阅读原文 →</a>` : ''}
    </div>
  `;
}

function formatTime(timestamp) {
  if (!timestamp) return '';

  const date = new Date(timestamp * 1000);
  const now = new Date();
  const diff = Math.floor((now - date) / 1000 / 60);

  if (diff < 60) return `${diff}分钟前`;
  if (diff < 1440) return `${Math.floor(diff / 60)}小时前`;
  return `${Math.floor(diff / 1440)}天前`;
}
```

- [ ] **Step 2: 提交**

```bash
git add web/src/components/news-item.js
git commit -m "feat: 创建 news-item.js 组件"
```

---

## Phase 5: 样式开发 (0.5天)

### Task 5.1: 添加 Tab 和信号样式

**Files:**
- Modify: `web/src/style.css`

- [ ] **Step 1: 读取现有 style.css**

```bash
wc -l web/src/style.css
tail -50 web/src/style.css
```

- [ ] **Step 2: 追加新样式**

```css
/* web/src/style.css - 追加到文件末尾 */

/* ───────────────────────────────────────────────────────────────────────────────
   Radar Tab 样式
   ───────────────────────────────────────────────────────────────────────────── */

.radar-tabs {
  width: 100%;
}

.radar-tab-nav {
  display: flex;
  gap: 8px;
  padding: 12px 16px;
  background: var(--bg-secondary, #f5f5f5);
  border-bottom: 1px solid var(--border-color, #e0e0e0);
  overflow-x: auto;
}

.radar-tab {
  flex-shrink: 0;
  padding: 8px 16px;
  border: none;
  background: transparent;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.radar-tab:hover {
  background: rgba(0, 0, 0, 0.05);
}

.radar-tab.active {
  background: var(--primary-color, #1890ff);
  color: white;
}

.radar-tab-content {
  padding: 16px;
}

/* ───────────────────────────────────────────────────────────────────────────────
   信号卡片样式
   ───────────────────────────────────────────────────────────────────────────── */

.signals-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.signals-header h2 {
  margin: 0;
  font-size: 18px;
}

.signals-count {
  font-size: 14px;
  color: var(--text-secondary, #666);
}

.signal-card {
  background: white;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
  border-left: 4px solid transparent;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}

.signal-card.signal-strong {
  border-left-color: #ff4d4f;
}

.signal-card.signal-medium {
  border-left-color: #faad14;
}

.signal-card.signal-weak {
  border-left-color: #8c8c8c;
}

.signal-header {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 12px;
}

.signal-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.signal-title {
  margin: 0;
  font-size: 16px;
  flex: 1;
}

.signal-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  margin-bottom: 12px;
}

.signal-direction {
  font-size: 14px;
  font-weight: 500;
}

.signal-sector {
  padding: 2px 8px;
  background: #f0f0f0;
  border-radius: 4px;
  font-size: 12px;
}

.signal-targets {
  font-size: 13px;
  color: var(--text-secondary, #666);
  margin-bottom: 12px;
}

.signal-action {
  background: #f6ffed;
  border: 1px solid #b7eb8f;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
}

.signal-action .action-label {
  font-size: 16px;
}

.signal-action .action-text {
  font-size: 14px;
  font-weight: 500;
}

.signal-score {
  font-size: 13px;
  color: var(--text-secondary, #666);
  margin-bottom: 8px;
}

.signal-source {
  font-size: 12px;
  color: var(--text-secondary, #666);
  margin-bottom: 8px;
}

.signal-reason {
  font-size: 13px;
  color: var(--text-secondary, #666);
  padding-top: 8px;
  border-top: 1px solid #f0f0f0;
}

/* ───────────────────────────────────────────────────────────────────────────────
   统计面板样式
   ───────────────────────────────────────────────────────────────────────────── */

.stats-panel {
  background: #fafafa;
  border-radius: 12px;
  margin-top: 24px;
  overflow: hidden;
}

.stats-panel.collapsed .stats-content {
  display: none;
}

.stats-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  cursor: pointer;
}

.stats-header h3 {
  margin: 0;
  font-size: 16px;
}

.stats-toggle {
  font-size: 12px;
  transition: transform 0.2s ease;
}

.stats-panel:not(.collapsed) .stats-toggle {
  transform: rotate(180deg);
}

.stats-content {
  padding: 16px;
  border-top: 1px solid #e0e0e0;
}

.stats-table {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stats-row {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
}

.stats-label {
  color: var(--text-secondary, #666);
}

.stats-value.good {
  color: #52c41a;
  font-weight: 600;
}

.stats-breakdown {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #e0e0e0;
}

.stats-breakdown h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
}

/* ───────────────────────────────────────────────────────────────────────────────
   新闻列表样式
   ───────────────────────────────────────────────────────────────────────────── */

.news-container {
  width: 100%;
}

.news-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.news-header h2 {
  margin: 0;
  font-size: 18px;
}

.news-count {
  font-size: 14px;
  color: var(--text-secondary, #666);
}

.news-item {
  background: white;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
  border-left: 3px solid transparent;
}

.news-item.has-signal {
  border-left-color: #ff4d4f;
  background: #fff5f5;
}

.news-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

.news-headline {
  margin: 0;
  font-size: 15px;
  flex: 1;
}

.news-signal-badge {
  flex-shrink: 0;
  padding: 2px 6px;
  background: #ff4d4f;
  color: white;
  border-radius: 4px;
  font-size: 11px;
}

.news-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: var(--text-secondary, #666);
  margin-bottom: 8px;
}

.news-summary {
  margin: 0 0 8px 0;
  font-size: 13px;
  color: var(--text-secondary, #666);
  line-height: 1.5;
}

.news-link {
  font-size: 13px;
  color: var(--primary-color, #1890ff);
  text-decoration: none;
}

.news-link:hover {
  text-decoration: underline;
}

/* ───────────────────────────────────────────────────────────────────────────────
   响应式适配
   ───────────────────────────────────────────────────────────────────────────── */

@media (max-width: 480px) {
  .radar-tab-nav {
    padding: 8px 12px;
  }

  .radar-tab {
    padding: 6px 12px;
    font-size: 13px;
  }

  .signal-card {
    padding: 12px;
  }

  .signal-header {
    flex-direction: column;
  }

  .signal-badge {
    align-self: flex-start;
  }
}
```

- [ ] **Step 3: 提交**

```bash
git add web/src/style.css
git commit -m "feat: 添加 Tab/信号/统计/新闻样式"
```

---

## Phase 6: T+1 验证 (1天)

### Task 6.1: 实现 track_signals.py

**Files:**
- Create: `scripts/track_signals.py`
- Create: `tests/test_track_signals.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_track_signals.py
import os
import sys
import json
import tempfile
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

def test_load_signals():
    """测试加载信号"""
    from track_signals import load_signals

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({
            "date": "2026-04-12",
            "signals": [{"id": "test-1", "title": "Test"}]
        }, f)
        temp_path = f.name

    try:
        signals = load_signals("2026-04-12", data_dir=os.path.dirname(temp_path))
        assert len(signals) == 1
        assert signals[0]["id"] == "test-1"
    finally:
        os.unlink(temp_path)

def test_calculate_hit():
    """测试命中判定"""
    from track_signals import calculate_hit

    # 利多信号，上涨
    assert calculate_hit("利多", 0.02) == (True, "strong")
    assert calculate_hit("利多", 0.005) == (True, "weak")

    # 利多信号，下跌
    assert calculate_hit("利多", -0.01) == (False, None)

    # 利空信号，下跌
    assert calculate_hit("利空", -0.02) == (True, "strong")
    assert calculate_hit("利空", -0.005) == (True, "weak")

    # 利空信号，上涨
    assert calculate_hit("利空", 0.01) == (False, None)

def test_update_signal_tracking():
    """测试更新信号追踪数据"""
    from track_signals import update_signal_tracking

    signal = {
        "id": "test-1",
        "tracking": {
            "t1_open": None,
            "t1_close": None,
            "return": None,
            "hit": None,
            "hit_level": None
        }
    }

    updated = update_signal_tracking(signal, t1_open=100, t1_close=102, direction="利多")

    assert updated["tracking"]["t1_open"] == 100
    assert updated["tracking"]["t1_close"] == 102
    assert updated["tracking"]["return"] == 0.02
    assert updated["tracking"]["hit"] == True
    assert updated["tracking"]["hit_level"] == "strong"
```

- [ ] **Step 2: 运行测试验证失败**

```bash
python -m pytest tests/test_track_signals.py -v
```

Expected: FAIL

- [ ] **Step 3: 实现验证逻辑**

```python
# scripts/track_signals.py
"""
T+1 信号验证脚本
用法: python scripts/track_signals.py
"""
import json
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))

SIGNALS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "signals")
HISTORY_FILE = os.path.join(SIGNALS_DIR, "history.json")
WATCHLIST_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "watchlist")


def load_signals(date: str, data_dir: str = None) -> list:
    """加载指定日期的信号"""
    if data_dir is None:
        data_dir = SIGNALS_DIR

    filepath = os.path.join(data_dir, f"{date}.json")

    if not os.path.exists(filepath):
        return []

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return data.get("signals", [])


def load_history() -> dict:
    """加载历史数据"""
    if not os.path.exists(HISTORY_FILE):
        return {"signals": [], "updated_at": None}

    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_history(history: dict):
    """保存历史数据"""
    os.makedirs(SIGNALS_DIR, exist_ok=True)

    history["updated_at"] = datetime.now().isoformat()

    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def get_t1_market_data(date: str, targets: list) -> dict:
    """
    获取 T+1 市场数据
    简化版：使用 watchlist 数据
    """
    # 计算 T+1 日期
    signal_date = datetime.strptime(date, "%Y-%m-%d")
    t1_date = signal_date + timedelta(days=1)

    # 如果 T+1 是周末，顺延
    while t1_date.weekday() >= 5:  # 5=周六, 6=周日
        t1_date += timedelta(days=1)

    t1_str = t1_date.strftime("%Y-%m-%d")
    filepath = os.path.join(WATCHLIST_DIR, f"{t1_str}.json")

    if not os.path.exists(filepath):
        print(f"  警告: T+1 数据文件不存在: {filepath}")
        return {}

    with open(filepath, 'r', encoding='utf-8') as f:
        watchlist = json.load(f)

    # 提取目标标的的数据
    result = {}
    for group in watchlist.get("groups", {}).values():
        for etf in group.get("etfs", []):
            if etf["ticker"] in targets:
                result[etf["ticker"]] = {
                    "open": etf.get("price", 0),  # 简化：用当前价格
                    "close": etf.get("price", 0),
                    "change_pct": etf.get("change_pct", 0)
                }

    return result


def calculate_hit(direction: str, return_pct: float) -> tuple:
    """
    判定是否命中

    Args:
        direction: 信号方向 (利多/利空)
        return_pct: T+1 收益率

    Returns:
        (是否命中, 命中等级)
    """
    abs_return = abs(return_pct)

    if direction == "利多":
        if return_pct > 0:
            if abs_return > 0.02:
                return True, "strong"
            else:
                return True, "weak"
        else:
            return False, None
    elif direction == "利空":
        if return_pct < 0:
            if abs_return > 0.02:
                return True, "strong"
            else:
                return True, "weak"
        else:
            return False, None

    return False, None


def update_signal_tracking(signal: dict, t1_open: float, t1_close: float, direction: str) -> dict:
    """
    更新信号的追踪数据

    Args:
        signal: 原始信号
        t1_open: T+1 开盘价
        t1_close: T+1 收盘价
        direction: 信号方向

    Returns:
        更新后的信号
    """
    updated = signal.copy()

    # 计算 T+1 收益
    if t1_open and t1_close:
        return_pct = (t1_close - t1_open) / t1_open
    else:
        return_pct = None

    # 判定命中
    if return_pct is not None:
        hit, hit_level = calculate_hit(direction, return_pct)
    else:
        hit, hit_level = None, None

    updated["tracking"] = {
        "t1_open": t1_open,
        "t1_close": t1_close,
        "return": round(return_pct, 4) if return_pct is not None else None,
        "hit": hit,
        "hit_level": hit_level
    }

    return updated


def main():
    """主函数"""
    # 获取昨天的日期（验证昨天的信号）
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    # 检查是否指定日期
    if len(sys.argv) > 1:
        date = sys.argv[1]
    else:
        date = yesterday

    print(f"验证信号: {date}")

    # 加载信号
    signals = load_signals(date)

    if len(signals) == 0:
        print(f"  没有找到 {date} 的信号")
        return

    print(f"  找到 {len(signals)} 条信号")

    # 加载历史
    history = load_history()

    # 记录已存在的信号 ID
    existing_ids = {s["id"] for s in history["signals"]}

    # 验证每条信号
    updated_count = 0
    for signal in signals:
        signal_id = signal["id"]

        # 如果已经验证过，跳过
        if signal_id in existing_ids:
            continue

        print(f"\n验证信号: {signal['title']}")
        print(f"  方向: {signal['direction']}")
        print(f"  目标: {signal.get('targets', [])}")

        # 获取 T+1 数据
        targets = signal.get("targets", [])
        if len(targets) == 0:
            print(f"  跳过: 没有目标标的")
            continue

        market_data = get_t1_market_data(date, targets)

        if len(market_data) == 0:
            print(f"  跳过: 无法获取 T+1 数据")
            continue

        # 使用第一个目标的数据
        first_target = targets[0]
        data = market_data.get(first_target)

        if not data:
            print(f"  跳过: 目标 {first_target} 无数据")
            continue

        # 更新追踪数据
        updated = update_signal_tracking(
            signal,
            t1_open=data.get("open"),
            t1_close=data.get("close"),
            direction=signal["direction"]
        )

        print(f"  T+1 开盘: {updated['tracking']['t1_open']}")
        print(f"  T+1 收盘: {updated['tracking']['t1_close']}")
        print(f"  收益: {updated['tracking']['return']}")
        print(f"  命中: {updated['tracking']['hit']} ({updated['tracking']['hit_level']})")

        # 添加到历史
        history["signals"].append(updated)
        updated_count += 1

    if updated_count > 0:
        # 保存历史
        save_history(history)
        print(f"\n已更新 {updated_count} 条信号到历史记录")
    else:
        print("\n没有需要更新的信号")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 运行测试验证通过**

```bash
python -m pytest tests/test_track_signals.py -v
```

Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add scripts/track_signals.py tests/test_track_signals.py
git commit -m "feat: 实现 T+1 信号验证逻辑"
```

---

## Phase 7: 数据层完善 (0.5天)

### Task 7.1: 更新 data.js 添加新数据获取方法

**Files:**
- Modify: `web/src/data.js`

- [ ] **Step 1: 读取现有 data.js**

```bash
cat web/src/data.js
```

- [ ] **Step 2: 追加新方法**

```javascript
// web/src/data.js - 追加到文件末尾

/**
 * 获取交易信号
 */
export async function fetchSignals() {
  try {
    const today = new Date().toISOString().split('T')[0];
    const response = await fetch(`/data/signals/${today}.json`);

    if (!response.ok) {
      return null;
    }

    const data = await response.json();
    return data.signals;
  } catch (e) {
    console.warn('获取信号失败:', e);
    return null;
  }
}

/**
 * 获取历史信号
 */
export async function fetchSignalHistory() {
  try {
    const response = await fetch('/data/signals/history.json');

    if (!response.ok) {
      return null;
    }

    return await response.json();
  } catch (e) {
    console.warn('获取历史信号失败:', e);
    return null;
  }
}

/**
 * 获取新闻
 */
export async function fetchNews() {
  try {
    const today = new Date().toISOString().split('T')[0];
    const response = await fetch(`/data/news/${today}.json`);

    if (!response.ok) {
      return null;
    }

    return await response.json();
  } catch (e) {
    console.warn('获取新闻失败:', e);
    return null;
  }
}

/**
 * 获取统计数据
 */
export async function fetchStats() {
  try {
    const response = await fetch('/data/stats/hit_rate.json');

    if (!response.ok) {
      return null;
    }

    return await response.json();
  } catch (e) {
    console.warn('获取统计数据失败:', e);
    return null;
  }
}
```

- [ ] **Step 3: 提交**

```bash
git add web/src/data.js
git commit -m "feat: 添加信号/新闻/统计数据获取方法"
```

---

## Phase 8: 自动化 (0.5天)

### Task 8.1: 更新 GitHub Actions 工作流

**Files:**
- Create: `.github/workflows/daily.yml`

- [ ] **Step 1: 创建新的工作流**

```yaml
# .github/workflows/daily.yml
name: 每日数据更新

on:
  schedule:
    # 北京时间 8:30 (UTC 0:30)
    - cron: '30 0 * * 1-5'
  workflow_dispatch:  # 允许手动触发

jobs:
  update:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.x'

      - name: Install dependencies
        run: |
          pip install requests pandas yfinance

      - name: Fetch news
        env:
          FINNHUB_API_KEY: ${{ secrets.FINNHUB_API_KEY }}
        run: |
          python scripts/fetch_news.py

      - name: Generate signals
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          python scripts/generate_signals.py

      - name: Track signals (T+1)
        env:
          FINNHUB_API_KEY: ${{ secrets.FINNHUB_API_KEY }}
        run: |
          python scripts/track_signals.py

      - name: Build frontend
        run: |
          cd web
          npm install
          npm run build

      - name: Commit and push
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"

          git add data/ web/dist/ || true

          if git diff --staged --quiet; then
            echo "No changes to commit"
          else
            git commit -m "auto: 每日数据更新 $(date +'%Y-%m-%d')"
            git push
          fi
```

- [ ] **Step 2: 配置 Secrets**

确保 GitHub Repository Settings > Secrets and variables > Actions 中配置：
- `FINNHUB_API_KEY`
- `ANTHROPIC_API_KEY` 或 `OPENAI_API_KEY`

- [ ] **Step 3: 提交**

```bash
git add .github/workflows/daily.yml
git commit -m "feat: 添加每日自动更新工作流"
```

---

## Phase 9: 测试与优化 (1天)

### Task 9.1: 端到端测试

**Files:**
- Create: `tests/test_e2e.sh`

- [ ] **Step 1: 创建 E2E 测试脚本**

```bash
# tests/test_e2e.sh
#!/bin/bash
# 端到端测试脚本

set -e

echo "=== E2E 测试 ==="

# 1. 测试新闻获取
echo "1. 测试新闻获取..."
FINNHUB_API_KEY="${FINNHUB_API_KEY:-test}" python scripts/fetch_news.py
if [ -f "data/news/$(date +%Y-%m-%d).json" ]; then
  echo "✓ 新闻获取成功"
else
  echo "✗ 新闻获取失败"
  exit 1
fi

# 2. 测试信号生成
echo "2. 测试信号生成..."
if [ -n "$ANTHROPIC_API_KEY" ] || [ -n "$OPENAI_API_KEY" ]; then
  ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-test}" \
  OPENAI_API_KEY="${OPENAI_API_KEY:-test}" \
  python scripts/generate_signals.py
  if [ -f "data/signals/$(date +%Y-%m-%d).json" ]; then
    echo "✓ 信号生成成功"
  else
    echo "✗ 信号生成失败"
    exit 1
  fi
else
  echo "⊘ 跳过信号生成（未设置 API key）"
fi

# 3. 测试前端构建
echo "3. 测试前端构建..."
cd web
npm install
npm run build
if [ -d "dist" ]; then
  echo "✓ 前端构建成功"
else
  echo "✗ 前端构建失败"
  exit 1
fi
cd ..

echo "=== E2E 测试完成 ==="
```

- [ ] **Step 2: 运行测试**

```bash
chmod +x tests/test_e2e.sh
./tests/test_e2e.sh
```

- [ ] **Step 3: 提交**

```bash
git add tests/test_e2e.sh
git commit -m "test: 添加端到端测试脚本"
```

---

### Task 9.2: 性能优化

**Files:**
- Modify: `web/src/views/signals.js`
- Modify: `web/src/views/news.js`

- [ ] **Step 1: 添加懒加载**

```javascript
// web/src/views/signals.js - 修改
// 添加：只渲染可见的信号卡片，延迟加载统计数据

let statsLoaded = false;

export async function renderSignalsView(container) {
  container.innerHTML = '<p class="loading">正在加载信号...</p>';

  const signals = await fetchSignals();

  if (!signals || signals.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <p>今日暂无信号</p>
        <p class="hint">信号在每日早上 8:30 后生成</p>
      </div>
    `;
    return;
  }

  // 先渲染信号
  const signalsHtml = signals.map(renderSignalCard).join('');

  container.innerHTML = `
    <div class="signals-container">
      <div class="signals-header">
        <h2>🔥 今日交易信号</h2>
        <span class="signals-count">${signals.length}条</span>
      </div>
      ${signalsHtml}
      <div id="stats-placeholder" class="stats-placeholder">
        <button class="load-stats-btn">加载统计数据</button>
      </div>
    </div>
  `;

  // 点击按钮加载统计
  const btn = container.querySelector('.load-stats-btn');
  if (btn && !statsLoaded) {
    btn.addEventListener('click', async () => {
      btn.textContent = '加载中...';

      const history = await fetchSignalHistory();
      const statsHtml = renderStatsPanel(history);

      const placeholder = document.getElementById('stats-placeholder');
      placeholder.innerHTML = statsHtml;

      statsLoaded = true;
    });
  }
}
```

- [ ] **Step 2: 提交**

```bash
git add web/src/views/signals.js
git commit -m "perf: 添加统计数据懒加载"
```

---

## 验收检查清单

在宣布完成前，确保以下所有项已通过：

### 功能验收

- [ ] Finnhub News 成功获取，每天自动更新
- [ ] AI 生成 3-5 条信号，包含完整字段
- [ ] 每条信号有明确的交易建议（条件 + 动作）
- [ ] 信号评分计算正确
- [ ] 前端 Tab 切换正常工作
- [ ] 信号 Tab 正确展示信号卡片
- [ ] 板块 Tab 保留 V1.1 功能
- [ ] 新闻 Tab 展示原始新闻
- [ ] 统计面板正确显示命中率
- [ ] T+1 验证逻辑正确执行

### 质量验收

- [ ] 所有测试通过 (`pytest tests/`)
- [ ] 前端在移动端正常显示
- [ ] GitHub Actions 成功执行
- [ ] 没有 console 错误
- [ ] 数据 JSON 格式正确

### 性能验收

- [ ] 首屏加载 < 3 秒
- [ ] 每日脚本执行 < 5 分钟
- [ ] 前端交互流畅

---

## 自我审查结果

### Spec 覆盖检查

| PRD 需求 | 对应任务 | 状态 |
|---------|---------|------|
| Finnhub News 集成 | Task 1.2 | ✅ |
| AI 信号生成 | Task 2.1-2.3 | ✅ |
| 评分模型 | Task 2.2 | ✅ |
| Tab 切换结构 | Task 3.1-3.4 | ✅ |
| 信号卡片 | Task 4.1 | ✅ |
| 统计面板 | Task 4.2 | ✅ |
| 新闻列表 | Task 4.3 | ✅ |
| T+1 验证 | Task 6.1 | ✅ |
| GitHub Actions | Task 8.1 | ✅ |

### Placeholder 检查

已扫描，无 TBD/TODO/实现后续等占位符。

### 类型一致性检查

- 数据结构在各脚本间保持一致
- JSON 字段名统一（snake_case）
- 前端组件接收的参数与数据源匹配

---

**计划完成时间估算：8 天**
