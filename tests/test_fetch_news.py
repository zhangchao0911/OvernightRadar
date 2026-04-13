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
