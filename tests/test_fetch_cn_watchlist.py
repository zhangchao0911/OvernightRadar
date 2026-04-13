"""
A股市场观察数据获取测试
"""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import pytest


def test_cn_sector_config():
    """测试申万行业配置"""
    from cn_sector_config import (
        SW_LEVEL1_SECTORS,
        BENCHMARKS,
        ALL_SECTOR_CODES,
        get_sector_by_code,
        get_benchmark_info,
    )

    # 验证行业数量
    assert len(SW_LEVEL1_SECTORS) == 31

    # 验证基准配置
    assert "hs300" in BENCHMARKS
    assert "zz500" in BENCHMARKS
    assert BENCHMARKS["hs300"]["name"] == "沪深300"

    # 验证代码列表
    assert len(ALL_SECTOR_CODES) == 31
    assert "801010" in ALL_SECTOR_CODES  # 农林牧渔

    # 验证查询函数
    agri = get_sector_by_code("801010")
    assert agri is not None
    assert agri["name"] == "农林牧渔"

    hs300 = get_benchmark_info("hs300")
    assert hs300 is not None
    assert hs300["code"] == "000300"


def test_build_output_structure():
    """测试输出数据结构"""
    from fetch_cn_watchlist import build_output
    from cn_sector_config import get_benchmark_info

    # 模拟行业数据
    mock_sector = {
        "code": "801010",
        "name": "农林牧渔",
        "name_en": "Agriculture",
        "price": 3500.25,
        "change_pct": 1.2,
        "rel": {"rel_5": 0.8, "rel_20": 2.1, "rel_60": -0.5, "rel_120": 3.2},
        "rank": {"r_20": 65, "r_60": 58, "r_120": 70},
        "ytd": 5.2,
        "history": [3480.5] * 30,
    }

    output = build_output([mock_sector], "hs300")

    # 验证顶层结构
    assert "date" in output
    assert "updated_at" in output
    assert output["total_sectors"] == 1
    assert output["benchmark"]["key"] == "hs300"

    # 验证groups结构
    assert "sw_level1" in output["groups"]
    assert output["groups"]["sw_level1"]["display_name"] == "申万一级行业"
    assert len(output["groups"]["sw_level1"]["sectors"]) == 1

    # 验证sector数据
    sector = output["groups"]["sw_level1"]["sectors"][0]
    assert sector["code"] == "801010"
    assert sector["name"] == "农林牧渔"
    assert "rel" in sector
    assert "history" in sector
    assert len(sector["history"]) == 30


def test_calculate_rel():
    """测试REL计算"""
    from fetch_cn_watchlist import calculate_rel
    import pandas as pd

    # 创建测试数据
    dates = pd.date_range("2026-01-01", periods=120)
    sector_prices = pd.Series([100 + i * 0.1 for i in range(120)], index=dates)
    benchmark_prices = pd.Series([100 + i * 0.08 for i in range(120)], index=dates)

    rel = calculate_rel(sector_prices, benchmark_prices)

    # 验证返回结构
    assert "rel_5" in rel
    assert "rel_20" in rel
    assert "rel_60" in rel
    assert "rel_120" in rel

    # 验证REL计算（行业涨幅 > 基准涨幅，所以REL应该为正）
    assert rel["rel_5"] > 0
    assert rel["rel_20"] > 0


def test_generate_history():
    """测试历史走势生成"""
    from fetch_cn_watchlist import generate_history
    import pandas as pd

    dates = pd.date_range("2026-01-01", periods=30)
    prices = pd.Series([100 + i for i in range(30)], index=dates)

    history = generate_history(prices, 130.0)

    # 验证长度
    assert len(history) == 30

    # 验证最后一个值是当前价
    assert history[-1] == 130.0

    # 验证所有值都是数字
    assert all(isinstance(x, float) or isinstance(x, int) for x in history)
