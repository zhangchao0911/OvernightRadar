"""V1.1 核心计算逻辑的单元测试"""
import pandas as pd
import numpy as np
import pytest

import sys
sys.path.insert(0, "scripts")
from run_daily import (
    SECTOR_MAP,
    calc_relative_strength,
    calc_volatility_surprise,
    calc_trend,
    calc_sentiment,
    build_market_summary,
)


class TestSectorMap:
    """板块映射配置验证"""

    def test_has_8_sectors(self):
        assert len(SECTOR_MAP) == 8

    def test_each_sector_has_required_fields(self):
        required = [
            "us_etf", "cn_name", "cn_etf_name", "cn_etf_code",
            "us_name", "supply_chain",
        ]
        for sector in SECTOR_MAP:
            for field in required:
                assert field in sector, f"Missing {field} in {sector}"

    def test_each_sector_has_3_supply_chain_stocks(self):
        for sector in SECTOR_MAP:
            assert len(sector["supply_chain"]) == 3, \
                f"{sector['us_name']} has {len(sector['supply_chain'])} stocks, expected 3"
            for stock in sector["supply_chain"]:
                assert "name" in stock, f"Missing name in {sector['us_name']}"
                assert "code" in stock, f"Missing code in {sector['us_name']}"

    def test_us_etfs_are_unique(self):
        etfs = [s["us_etf"] for s in SECTOR_MAP]
        assert len(etfs) == len(set(etfs))

    def test_stock_codes_are_unique(self):
        codes = []
        for sector in SECTOR_MAP:
            for stock in sector["supply_chain"]:
                codes.append(stock["code"])
        assert len(codes) == len(set(codes)), "Duplicate stock codes found"

    def test_total_24_supply_chain_stocks(self):
        total = sum(len(s["supply_chain"]) for s in SECTOR_MAP)
        assert total == 24


class TestRelativeStrength:
    """板块相对强度"""

    def test_outperform(self):
        """板块涨3.2%，标普涨0.5% → 相对强度+2.7%"""
        assert calc_relative_strength(3.2, 0.5) == 2.7

    def test_underperform(self):
        """板块涨0.3%，标普涨0.5% → 相对强度-0.2%"""
        assert calc_relative_strength(0.3, 0.5) == -0.2

    def test_resilient_in_down_market(self):
        """大盘跌1%，板块涨0.3% → 相对强度+1.3%"""
        assert calc_relative_strength(0.3, -1.0) == 1.3

    def test_both_negative(self):
        """板块跌2%，标普跌0.5% → 相对强度-1.5%"""
        assert calc_relative_strength(-2.0, -0.5) == -1.5


class TestVolatilitySurprise:
    """波动率偏离"""

    def _make_returns(self, values):
        return pd.Series(values)

    def test_abnormal_volatility(self):
        """最后一天波动远超均值 → is_abnormal=True"""
        values = [0.5, -0.3, 0.8, -0.6, 0.4, -0.5, 0.7, -0.8, 0.3, -0.4,
                  0.6, -0.5, 0.9, -0.7, 0.5, -0.6, 0.8, -0.4, 0.5, 3.0]
        result = calc_volatility_surprise(self._make_returns(values), window=20)
        assert result["is_abnormal"] is True
        assert result["vol_multiple"] > 2.0
        assert result["daily_vol_20d"] > 0

    def test_normal_volatility(self):
        """最后一天波动在均值附近 → is_abnormal=False"""
        values = [0.5, -0.3, 0.8, -0.6, 0.4, -0.5, 0.7, -0.8, 0.3, -0.4,
                  0.6, -0.5, 0.9, -0.7, 0.5, -0.6, 0.8, -0.4, 0.5, -0.3]
        result = calc_volatility_surprise(self._make_returns(values), window=20)
        assert result["is_abnormal"] is False
        assert result["vol_multiple"] < 2.0

    def test_short_series(self):
        """少于20天数据 → 使用可用数据"""
        values = [0.5, -0.3, 1.5]
        result = calc_volatility_surprise(self._make_returns(values), window=20)
        assert "vol_multiple" in result
        assert "is_abnormal" in result

    def test_zero_volatility(self):
        """所有涨跌幅为0 → vol_multiple=0"""
        values = [0.0] * 20
        result = calc_volatility_surprise(self._make_returns(values), window=20)
        assert result["vol_multiple"] == 0.0
        assert result["is_abnormal"] is False


class TestTrend:
    """连涨连跌趋势"""

    def _make_returns(self, values):
        return pd.Series(values)

    def test_consecutive_up(self):
        """连涨3天"""
        returns = self._make_returns([0.5, -0.3, 1.2, 2.1, 1.5])
        result = calc_trend(returns)
        assert result["direction"] == "up"
        assert result["consecutive_days"] == 3
        assert result["cumulative_pct"] == 4.8

    def test_consecutive_down(self):
        """连跌3天"""
        returns = self._make_returns([0.5, -0.3, -1.2, -0.8])
        result = calc_trend(returns)
        assert result["direction"] == "down"
        assert result["consecutive_days"] == 3
        assert result["cumulative_pct"] == -2.3

    def test_single_day_up(self):
        """只涨1天"""
        returns = self._make_returns([-0.5, -0.3, 1.0])
        result = calc_trend(returns)
        assert result["direction"] == "up"
        assert result["consecutive_days"] == 1
        assert result["cumulative_pct"] == 1.0

    def test_flat(self):
        """最后一天平盘"""
        returns = self._make_returns([0.5, -0.3, 0.0])
        result = calc_trend(returns)
        assert result["direction"] == "flat"
        assert result["consecutive_days"] == 0

    def test_empty_series(self):
        """空序列"""
        returns = self._make_returns([])
        result = calc_trend(returns)
        assert result["direction"] == "flat"
        assert result["consecutive_days"] == 0


class TestSentiment:
    """情绪等级判定"""

    def test_strong_bull_with_vol(self):
        result = calc_sentiment(2.7, 4.0, "up", 1)
        assert result["sentiment_level"] == 4
        assert result["sentiment"] == "强烈看多"

    def test_strong_bull_with_trend(self):
        result = calc_sentiment(2.5, 1.0, "up", 3)
        assert result["sentiment_level"] == 4

    def test_bull_with_vol(self):
        result = calc_sentiment(1.2, 1.8, "up", 1)
        assert result["sentiment_level"] == 3
        assert result["sentiment"] == "偏多"

    def test_bull_with_trend(self):
        result = calc_sentiment(0.8, 1.0, "up", 2)
        assert result["sentiment_level"] == 3

    def test_neutral_low_rs(self):
        result = calc_sentiment(0.3, 1.0, "up", 1)
        assert result["sentiment_level"] == 2
        assert result["sentiment"] == "中性"

    def test_neutral_flat(self):
        result = calc_sentiment(0.0, 0.5, "flat", 0)
        assert result["sentiment_level"] == 2

    def test_bear_with_vol(self):
        result = calc_sentiment(-0.7, 1.6, "down", 1)
        assert result["sentiment_level"] == 1
        assert result["sentiment"] == "偏空"

    def test_bear_with_trend(self):
        result = calc_sentiment(-0.8, 1.0, "down", 2)
        assert result["sentiment_level"] == 1

    def test_strong_bear(self):
        result = calc_sentiment(-2.5, 3.0, "down", 1)
        assert result["sentiment_level"] == 0
        assert result["sentiment"] == "强烈看空"

    def test_strong_bear_with_trend(self):
        result = calc_sentiment(-2.3, 1.0, "down", 3)
        assert result["sentiment_level"] == 0

    def test_strong_bull_priority_over_bull(self):
        result = calc_sentiment(2.5, 3.0, "up", 1)
        assert result["sentiment_level"] == 4

    def test_strong_bear_priority_over_bear(self):
        result = calc_sentiment(-2.5, 3.0, "down", 1)
        assert result["sentiment_level"] == 0


class TestMarketSummary:
    """市场总览文案"""

    def test_mixed(self):
        sectors = [
            {"sentiment_level": 4}, {"sentiment_level": 3}, {"sentiment_level": 3},
            {"sentiment_level": 1}, {"sentiment_level": 0},
            {"sentiment_level": 2}, {"sentiment_level": 2}, {"sentiment_level": 2},
        ]
        assert build_market_summary(sectors) == "3强2弱3中性"

    def test_all_neutral(self):
        sectors = [{"sentiment_level": 2}] * 8
        assert build_market_summary(sectors) == "0强0弱8中性"

    def test_all_strong(self):
        sectors = [{"sentiment_level": 4}] * 8
        assert build_market_summary(sectors) == "8强0弱0中性"
