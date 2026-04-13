#!/bin/bash
# 端到端测试脚本
# 测试完整的数据流：新闻获取 → 信号生成 → 信号跟踪 → 前端构建

set -e  # 遇到错误立即退出

# ─── 配置 ───
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=========================================="
echo "端到端测试开始"
echo "=========================================="

# ─── 测试 1: 新闻获取 ───
echo ""
echo "测试 1: 新闻获取"
echo "----------------------------------------"

if [ -n "$NEWS_API_KEY" ]; then
    echo "使用 NEWS_API_KEY 测试..."
    python scripts/fetch_news.py

    # 检查输出
    TODAY=$(date +%Y-%m-%d)
    if [ -f "data/news/$TODAY.json" ]; then
        COUNT=$(python -c "import json; print(len(json.load(open('data/news/$TODAY.json')).get('news', [])))")
        echo "✓ 获取到 $COUNT 条新闻"
    else
        echo "✗ 未找到输出文件 data/news/$TODAY.json"
        exit 1
    fi
else
    echo "⚠ 跳过：未设置 NEWS_API_KEY"
fi

# ─── 测试 2: 信号生成 ───
echo ""
echo "测试 2: 信号生成"
echo "----------------------------------------"

if [ -n "$ANTHROPIC_API_KEY" ] || [ -n "$OPENAI_API_KEY" ]; then
    echo "使用 AI API 测试..."
    python scripts/generate_signals.py --min-score 0 --max-signals 10

    # 检查输出
    if [ -f "data/signals/$TODAY.json" ]; then
        SIGNALS_COUNT=$(python -c "import json; data=json.load(open('data/signals/$TODAY.json')); print(len(data.get('signals', [])))")
        echo "✓ 生成 $SIGNALS_COUNT 条信号"
    else
        echo "✗ 未找到输出文件 data/signals/$TODAY.json"
        exit 1
    fi
else
    echo "⚠ 跳过：未设置 ANTHROPIC_API_KEY 或 OPENAI_API_KEY"
fi

# ─── 测试 3: 信号跟踪 ───
echo ""
echo "测试 3: 信号跟踪"
echo "----------------------------------------"

# 创建测试信号
TEST_SIGNAL_DATE=$(date -v-1d +%Y-%m-%d 2>/dev/null || date -d "1 day ago" +%Y-%m-%d)
mkdir -p "data/signals"

cat > "data/signals/$TEST_SIGNAL_DATE.json" << EOF
{
  "date": "$TEST_SIGNAL_DATE",
  "generated_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "total": 2,
  "metadata": {
    "test": true,
    "news_count": 5,
    "final_count": 2
  },
  "signals": [
    {
      "ticker": "SOXX",
      "direction": "LONG",
      "entry_price": 200.0,
      "title": "测试信号 1",
      "level": "A",
      "score": 85
    },
    {
      "ticker": "GDX",
      "direction": "SHORT",
      "entry_price": 35.0,
      "title": "测试信号 2",
      "level": "B",
      "score": 70
    }
  ]
}
EOF

echo "创建测试信号文件: data/signals/$TEST_SIGNAL_DATE.json"

# 运行信号跟踪
python scripts/track_signals.py --date "$TEST_SIGNAL_DATE"

# 检查 history.json
if [ -f "data/history.json" ]; then
    TOTAL=$(python -c "import json; print(json.load(open('data/history.json'))['stats']['total'])")
    echo "✓ 历史记录更新，当前总计: $TOTAL 条"
else
    echo "✗ 未找到 data/history.json"
    exit 1
fi

# ─── 测试 4: Watchlist 获取 ───
echo ""
echo "测试 4: Watchlist 获取"
echo "----------------------------------------"

if [ -n "$FINNHUB_API_KEY" ]; then
    echo "使用 FINNHUB_API_KEY 测试..."
    python scripts/fetch_watchlist.py

    # 检查输出
    if ls data/watchlist/*.json 1> /dev/null 2>&1; then
        LATEST=$(ls -t data/watchlist/*.json | head -1)
        echo "✓ Watchlist 文件: $LATEST"
    else
        echo "⚠ 未找到 watchlist 输出文件"
    fi
else
    echo "⚠ 跳过：未设置 FINNHUB_API_KEY"
fi

# ─── 测试 5: 板块联动统计 ───
echo ""
echo "测试 5: 板块联动统计"
echo "----------------------------------------"

python scripts/run_daily.py

if ls data/results/*.json 1> /dev/null 2>&1; then
    LATEST=$(ls -t data/results/*.json | head -1)
    SECTORS=$(python -c "import json; print(len(json.load(open('$LATEST')).get('sectors', [])))")
    echo "✓ 板块统计文件: $LATEST ($SECTORS 个板块)"
else
    echo "✗ 未找到 results 输出文件"
    exit 1
fi

# ─── 测试 6: 前端构建 ───
echo ""
echo "测试 6: 前端构建"
echo "----------------------------------------"

cd web
echo "安装依赖..."
npm install

echo "构建前端..."
npm run build

if [ -d "dist" ]; then
    echo "✓ 前端构建成功: dist/"
    FILES=$(find dist -type f | wc -l)
    echo "  共 $FILES 个文件"
else
    echo "✗ 前端构建失败：未找到 dist 目录"
    exit 1
fi

cd "$PROJECT_ROOT"

# ─── 测试 7: 数据准备 ───
echo ""
echo "测试 7: 数据准备"
echo "----------------------------------------"

cp -r data web/dist/data
echo "✓ 数据已复制到 web/dist/data/"

# ─── 测试摘要 ───
echo ""
echo "=========================================="
echo "测试摘要"
echo "=========================================="
echo "新闻获取: $([ -n "$NEWS_API_KEY" ] && echo '✓ 已测试' || echo '⚠ 跳过')"
echo "信号生成: $([ -n "$ANTHROPIC_API_KEY" ] || [ -n "$OPENAI_API_KEY" ] && echo '✓ 已测试' || echo '⚠ 跳过')"
echo "信号跟踪: ✓ 已测试"
echo "Watchlist: $([ -n "$FINNHUB_API_KEY" ] && echo '✓ 已测试' || echo '⚠ 跳过')"
echo "板块统计: ✓ 已测试"
echo "前端构建: ✓ 已测试"
echo "=========================================="
echo "✓ 所有测试完成！"
