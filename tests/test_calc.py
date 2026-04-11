"""核心计算逻辑的单元测试"""
import pandas as pd
import numpy as np
import pytest

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
        us_values = [3.0] * 5 + [0.1] * 5 + [3.0] * 5 + [0.1] * 5
        cn_values = [1.0] * 5 + [0.0] * 5 + [-1.0] * 5 + [0.0] * 5
        us = self._make_series(us_values, start="2026-01-05")
        cn = self._make_series(cn_values, start="2026-01-05")

        prob_full, _, count_full = calc_conditional_prob(us, cn, threshold=2.0, window=20)
        prob_10, _, count_10 = calc_conditional_prob(us, cn, threshold=2.0, window=10)

        assert count_full > count_10

    def test_negative_avg_impact(self):
        """显著波动后平均低开"""
        us = self._make_series([3.0, 2.5, -2.1, 0.5])
        cn = self._make_series([-1.0, -0.5, -0.3, 0.2])

        prob, avg_impact, count = calc_conditional_prob(us, cn, threshold=2.0)
        assert count == 3
        assert prob == 0.0  # 全部低开
        assert avg_impact < 0
