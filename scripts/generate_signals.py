"""
信号生成主脚本

核心功能：
1. 从 data/news/YYYY-MM-DD.json 加载新闻
2. 使用 AI 客户端生成交易信号
3. 使用 signal_scorer 评分和筛选信号
4. 保存到 data/signals/YYYY-MM-DD.json

工作流程：
    新闻数据 → AI 分析 → 原始信号 → 评分筛选 → 最终信号

使用示例：
    # 使用默认日期（今天）
    python scripts/generate_signals.py

    # 指定日期
    python scripts/generate_signals.py --date 2026-04-13
"""
import json
import os
import sys
import argparse
from datetime import datetime
from typing import List, Dict, Tuple

# 导入依赖模块
from ai_client import AIClient, load_api_key, Provider
from signal_scorer import (
    enhance_signal_with_analysis,
    calculate_score,
    get_level,
    filter_signals
)

# ─── 路径配置 ───

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
NEWS_DIR = os.path.join(PROJECT_ROOT, "data", "news")
SIGNALS_DIR = os.path.join(PROJECT_ROOT, "data", "signals")


# ─── 数据加载/保存函数 ───

def load_news(date: str) -> Tuple[List[Dict], str]:
    """
    从 JSON 文件加载新闻数据

    Args:
        date: 日期字符串 (YYYY-MM-DD)

    Returns:
        (新闻列表, 文件路径) 元组
        如果文件不存在或格式错误，返回 ([], filepath)
    """
    filepath = os.path.join(NEWS_DIR, f"{date}.json")

    if not os.path.exists(filepath):
        return [], filepath

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 兼容两种格式：
        # 1. {"news": [...]}  (fetch_news.py 输出格式)
        # 2. [...]
        if isinstance(data, dict):
            return data.get("news", []), filepath
        elif isinstance(data, list):
            return data, filepath
        else:
            print(f"WARNING: 未知的文件格式 - {filepath}")
            return [], filepath

    except Exception as e:
        print(f"ERROR: 读取新闻文件失败 - {e}")
        return [], filepath


def save_signals(
    signals: List[Dict],
    date: str,
    metadata: Dict
) -> str:
    """
    保存信号到 JSON 文件

    Args:
        signals: 信号列表
        date: 日期字符串 (YYYY-MM-DD)
        metadata: 元数据（包含 total, avg_score 等）

    Returns:
        保存的文件路径
    """
    os.makedirs(SIGNALS_DIR, exist_ok=True)
    filepath = os.path.join(SIGNALS_DIR, f"{date}.json")

    output = {
        "date": date,
        "generated_at": datetime.now().isoformat(),
        "total": len(signals),
        "metadata": metadata,
        "signals": signals
    }

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    return filepath


# ─── 信号处理函数 ───

def process_signals(raw_signals: List[Dict]) -> List[Dict]:
    """
    处理 AI 生成的原始信号：
    1. 增强信号（添加分析标记）
    2. 计算评分
    3. 添加等级和评分明细

    Args:
        raw_signals: AI 生成的原始信号列表

    Returns:
        处理后的信号列表
    """
    processed = []

    for signal in raw_signals:
        # ─── 1. 增强信号 ───
        enhanced = enhance_signal_with_analysis(signal)

        # ─── 2. 计算评分 ───
        score, detail = calculate_score(enhanced)

        # ─── 3. 添加等级 ───
        level = get_level(score)

        # ─── 4. 组装最终信号 ───
        final_signal = {
            **enhanced,
            "score": score,
            "level": level,
            "score_detail": detail
        }

        processed.append(final_signal)

    return processed


def generate_signals_for_date(
    date: str,
    min_score: int = 50,
    max_signals: int = 5
) -> Tuple[List[Dict], Dict]:
    """
    为指定日期生成信号

    完整流程：
    1. 加载新闻数据
    2. 初始化 AI 客户端
    3. 生成原始信号
    4. 评分和处理
    5. 筛选高质量信号

    Args:
        date: 日期字符串 (YYYY-MM-DD)
        min_score: 最低分数阈值（默认 50）
        max_signals: 最大信号数量（默认 5）

    Returns:
        (信号列表, 元数据) 元组
        元数据包含：news_count, raw_count, final_count, avg_score 等
    """
    # ─── 1. 加载新闻 ───
    news, news_path = load_news(date)

    if not news:
        print(f"WARNING: 未找到新闻数据 - {news_path}")
        return [], {"error": "no_news"}

    print(f"✓ 加载新闻: {len(news)} 条")

    # ─── 2. 初始化 AI 客户端 ───
    provider, api_key = load_api_key()

    if not api_key:
        print("ERROR: 未设置 AI API Key (ANTHROPIC_API_KEY 或 OPENAI_API_KEY)")
        return [], {"error": "no_api_key"}

    client = AIClient(provider=provider, api_key=api_key)
    print(f"✓ AI 客户端: {provider.value}")

    # ─── 3. 生成原始信号 ───
    print("正在调用 AI 生成信号...")
    raw_signals = client.generate_signals(news)

    if not raw_signals:
        print("WARNING: AI 未生成任何信号")
        return [], {"error": "no_signals"}

    print(f"✓ 生成原始信号: {len(raw_signals)} 条")

    # ─── 4. 评分和处理 ───
    processed_signals = process_signals(raw_signals)

    # 计算平均分
    avg_score = sum(s["score"] for s in processed_signals) / len(processed_signals)
    print(f"✓ 评分完成: 平均 {avg_score:.1f} 分")

    # ─── 5. 筛选高质量信号 ───
    final_signals = filter_signals(
        processed_signals,
        min_score=min_score,
        max_count=max_signals
    )

    print(f"✓ 筛选完成: {len(final_signals)} 条 (≥{min_score}分)")

    # ─── 6. 构建元数据 ───
    metadata = {
        "news_count": len(news),
        "raw_count": len(raw_signals),
        "processed_count": len(processed_signals),
        "final_count": len(final_signals),
        "avg_score": round(avg_score, 1),
        "min_score": min_score,
        "ai_provider": provider.value
    }

    return final_signals, metadata


# ─── 命令行接口 ───

def main():
    """命令行主函数"""
    parser = argparse.ArgumentParser(description="生成交易信号")
    parser.add_argument(
        "--date",
        type=str,
        default=datetime.now().strftime("%Y-%m-%d"),
        help="日期 (YYYY-MM-DD)，默认为今天"
    )
    parser.add_argument(
        "--min-score",
        type=int,
        default=50,
        help="最低分数阈值 (默认: 50)"
    )
    parser.add_argument(
        "--max-signals",
        type=int,
        default=5,
        help="最大信号数量 (默认: 5)"
    )

    args = parser.parse_args()

    print(f"{'='*50}")
    print(f"信号生成: {args.date}")
    print(f"{'='*50}")

    # ─── 生成信号 ───
    signals, metadata = generate_signals_for_date(
        date=args.date,
        min_score=args.min_score,
        max_signals=args.max_signals
    )

    # ─── 检查错误 ───
    if "error" in metadata:
        error = metadata["error"]
        if error == "no_news":
            print("\n提示: 请先运行 fetch_news.py 获取新闻数据")
        elif error == "no_api_key":
            print("\n提示: 请设置 ANTHROPIC_API_KEY 或 OPENAI_API_KEY 环境变量")
        sys.exit(1)

    # ─── 保存结果 ───
    filepath = save_signals(signals, args.date, metadata)
    print(f"\n✓ 已保存到: {filepath}")

    # ─── 输出摘要 ───
    print(f"\n信号摘要:")
    for i, signal in enumerate(signals, 1):
        print(f"  {i}. [{signal['level']}] {signal['title']} ({signal['score']}分)")


if __name__ == "__main__":
    main()
