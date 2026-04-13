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
    # 按时间戳降序排序，确保先处理最新的
    sorted_news = sorted(news, key=lambda x: x.get('datetime', 0), reverse=True)

    seen = set()
    deduped = []

    for item in sorted_news:
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
