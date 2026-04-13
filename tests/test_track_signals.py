"""
track_signals.py 单元测试
"""
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

# 添加 scripts 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from track_signals import (
    calculate_return,
    determine_hit,
    track_signal,
    update_stats,
    load_history,
    save_history,
    HIT_THRESHOLD_LONG,
    HIT_THRESHOLD_SHORT
)


class TestCalculateReturn(unittest.TestCase):
    """测试收益率计算"""

    def test_positive_return(self):
        """测试正收益"""
        result = calculate_return(100.0, 105.0)
        self.assertEqual(result, 5.0)

    def test_negative_return(self):
        """测试负收益"""
        result = calculate_return(100.0, 95.0)
        self.assertEqual(result, -5.0)

    def test_zero_return(self):
        """测试零收益"""
        result = calculate_return(100.0, 100.0)
        self.assertEqual(result, 0.0)

    def test_invalid_entry_price(self):
        """测试无效入场价格"""
        result = calculate_return(0.0, 100.0)
        self.assertEqual(result, 0.0)

        result = calculate_return(-10.0, 100.0)
        self.assertEqual(result, 0.0)


class TestDetermineHit(unittest.TestCase):
    """测试命中判定"""

    def test_long_signal_hit(self):
        """测试做多信号命中"""
        signal = {"direction": "LONG"}
        self.assertTrue(determine_hit(signal, 2.0))
        self.assertTrue(determine_hit(signal, 1.0))
        self.assertFalse(determine_hit(signal, 0.5))
        self.assertFalse(determine_hit(signal, -1.0))

    def test_short_signal_hit(self):
        """测试做空信号命中"""
        signal = {"direction": "SHORT"}
        self.assertTrue(determine_hit(signal, -2.0))
        self.assertTrue(determine_hit(signal, -1.0))
        self.assertFalse(determine_hit(signal, -0.5))
        self.assertFalse(determine_hit(signal, 1.0))

    def test_neutral_signal(self):
        """测试中性信号不判定"""
        signal = {"direction": "NEUTRAL"}
        self.assertFalse(determine_hit(signal, 5.0))
        self.assertFalse(determine_hit(signal, -5.0))

    def test_case_insensitive(self):
        """测试大小写不敏感"""
        signal = {"direction": "long"}
        self.assertTrue(determine_hit(signal, 2.0))

        signal = {"direction": "Long"}
        self.assertTrue(determine_hit(signal, 2.0))


class TestTrackSignal(unittest.TestCase):
    """测试信号跟踪"""

    def setUp(self):
        """设置测试环境"""
        self.sample_signal = {
            "ticker": "SOXX",
            "direction": "LONG",
            "entry_price": 100.0,
            "title": "半导体突破"
        }

    @patch('track_signals.get_ticker_price_yf')
    def test_track_signal_success(self, mock_get_price):
        """测试成功跟踪信号"""
        mock_get_price.return_value = 105.0

        watchlist_data = {}
        result = track_signal(self.sample_signal, watchlist_data)

        self.assertIsNotNone(result)
        self.assertEqual(result["ticker"], "SOXX")
        self.assertEqual(result["current_price"], 105.0)
        self.assertEqual(result["return_pct"], 5.0)
        self.assertTrue(result["is_hit"])
        self.assertEqual(result["status"], "tracked")

    @patch('track_signals.get_ticker_price_yf')
    def test_track_signal_miss(self, mock_get_price):
        """测试信号未命中"""
        mock_get_price.return_value = 100.5

        watchlist_data = {}
        result = track_signal(self.sample_signal, watchlist_data)

        self.assertIsNotNone(result)
        self.assertEqual(result["return_pct"], 0.5)
        self.assertFalse(result["is_hit"])

    def test_track_signal_missing_ticker(self):
        """测试缺少 ticker 的信号"""
        signal = {"direction": "LONG", "entry_price": 100.0}
        watchlist_data = {}

        result = track_signal(signal, watchlist_data)
        self.assertIsNone(result)

    @patch('track_signals.get_ticker_price_yf')
    def test_track_signal_missing_entry_price(self, mock_get_price):
        """测试缺少入场价格的信号"""
        signal = {"ticker": "SOXX", "direction": "LONG"}
        mock_get_price.return_value = 105.0

        result = track_signal(signal, {})
        self.assertIsNone(result)

    @patch('track_signals.get_ticker_price_yf')
    def test_track_signal_from_watchlist(self, mock_get_price):
        """测试从 watchlist 获取价格"""
        mock_get_price.return_value = None  # yfinance 失败

        watchlist_data = {
            "groups": {
                "semiconductors": {
                    "etfs": [
                        {"ticker": "SOXX", "price": 103.0}
                    ]
                }
            }
        }

        result = track_signal(self.sample_signal, watchlist_data)

        self.assertIsNotNone(result)
        self.assertEqual(result["current_price"], 103.0)
        self.assertEqual(result["return_pct"], 3.0)


class TestUpdateStats(unittest.TestCase):
    """测试统计更新"""

    def test_update_stats_empty(self):
        """测试空信号列表的统计"""
        history = {"signals": [], "stats": {}, "by_level": {}}
        update_stats(history)

        stats = history["stats"]
        self.assertEqual(stats["total"], 0)
        self.assertEqual(stats["hits"], 0)
        self.assertEqual(stats["misses"], 0)
        self.assertEqual(stats["pending"], 0)
        self.assertEqual(stats["hit_rate"], 0.0)
        self.assertEqual(stats["avg_return"], 0.0)

    def test_update_stats_with_signals(self):
        """测试有信号的统计"""
        history = {
            "signals": [
                {
                    "ticker": "SOXX",
                    "level": "A",
                    "is_hit": True,
                    "status": "tracked",
                    "return_pct": 5.0,
                    "date": "2026-04-13"
                },
                {
                    "ticker": "XLK",
                    "level": "B",
                    "is_hit": False,
                    "status": "tracked",
                    "return_pct": -2.0,
                    "date": "2026-04-13"
                },
                {
                    "ticker": "GDX",
                    "level": "A",
                    "status": "pending",
                    "date": "2026-04-14"
                }
            ],
            "stats": {},
            "by_level": {}
        }

        update_stats(history)

        stats = history["stats"]
        self.assertEqual(stats["total"], 3)
        self.assertEqual(stats["hits"], 1)
        self.assertEqual(stats["misses"], 1)
        self.assertEqual(stats["pending"], 1)
        self.assertEqual(stats["hit_rate"], 50.0)
        self.assertEqual(stats["avg_return"], 1.5)

        # 检查按等级统计
        by_level = history["by_level"]
        self.assertEqual(by_level["A"]["total"], 1)
        self.assertEqual(by_level["A"]["hits"], 1)
        self.assertEqual(by_level["A"]["avg_return"], 5.0)
        self.assertEqual(by_level["B"]["total"], 1)
        self.assertEqual(by_level["B"]["hits"], 0)
        self.assertEqual(by_level["B"]["avg_return"], -2.0)


class TestHistoryPersistence(unittest.TestCase):
    """测试历史记录持久化"""

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.history_path = os.path.join(self.temp_dir, "history.json")

    def tearDown(self):
        """清理测试环境"""
        if os.path.exists(self.history_path):
            os.remove(self.history_path)
        os.rmdir(self.temp_dir)

    @patch('track_signals.HISTORY_PATH')
    def test_load_history_not_exists(self, mock_path):
        """测试加载不存在的历史文件"""
        # 使用临时路径
        mock_path.__str__ = lambda self: self.history_path
        with patch('track_signals.HISTORY_PATH', self.history_path):
            history = load_history()

            self.assertIn("signals", history)
            self.assertIn("stats", history)
            self.assertEqual(history["signals"], [])
            self.assertEqual(history["stats"]["total"], 0)

    def test_save_and_load_history(self):
        """测试保存和加载历史记录"""
        # 准备测试数据
        history = {
            "signals": [
                {
                    "ticker": "SOXX",
                    "level": "A",
                    "is_hit": True,
                    "status": "tracked",
                    "return_pct": 5.0,
                    "date": "2026-04-13"
                }
            ],
            "stats": {
                "total": 1,
                "hits": 1,
                "misses": 0,
                "pending": 0,
                "hit_rate": 100.0,
                "avg_return": 5.0
            },
            "by_level": {
                "A": {
                    "total": 1,
                    "hits": 1,
                    "avg_return": 5.0
                }
            }
        }

        # 保存
        with patch('track_signals.HISTORY_PATH', self.history_path):
            save_history(history)

            # 加载
            loaded = load_history()

            self.assertEqual(loaded["signals"][0]["ticker"], "SOXX")
            self.assertEqual(loaded["stats"]["total"], 1)
            self.assertEqual(loaded["stats"]["hit_rate"], 100.0)
            self.assertIn("last_updated", loaded["stats"])


if __name__ == '__main__':
    unittest.main()
