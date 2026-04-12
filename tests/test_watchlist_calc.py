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
        for group_key, group_data in ETF_GROUPS.items():
            for etf in group_data["etfs"]:
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
        assert get_group_key("SOXX") == "thematic"
        assert get_group_key("ARKK") == "ark"
        assert get_group_key("NOTEXIST") is None

    def test_total_etf_count(self):
        total = sum(len(g["etfs"]) for g in ETF_GROUPS.values())
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
