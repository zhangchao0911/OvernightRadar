"""
美股涨了，A股呢？ — 每日数据采集与统计计算脚本
用法: python scripts/run_daily.py
"""
import json
import os
import sys
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

# ─── 板块映射配置 ───────────────────────────────────────────

SECTOR_MAP = [
    {
        "id": 1,
        "us_name": "半导体",
        "us_etf": "SOXX",
        "cn_name": "半导体",
        "cn_index": "801081",
        "cn_etf_name": "半导体ETF",
        "cn_etf_code": "512480",
    },
    {
        "id": 2,
        "us_name": "科技",
        "us_etf": "XLK",
        "cn_name": "电子",
        "cn_index": "801080",
        "cn_etf_name": "科技ETF",
        "cn_etf_code": "515000",
    },
    {
        "id": 3,
        "us_name": "新能源车",
        "us_etf": "DRIV",
        "cn_name": "汽车",
        "cn_index": "801880",
        "cn_etf_name": "新能源车ETF",
        "cn_etf_code": "515030",
    },
    {
        "id": 4,
        "us_name": "AI/算力",
        "us_etf": "THNQ",
        "cn_name": "计算机",
        "cn_index": "801750",
        "cn_etf_name": "计算机ETF",
        "cn_etf_code": "512720",
    },
    {
        "id": 5,
        "us_name": "黄金",
        "us_etf": "GLD",
        "cn_name": "有色金属",
        "cn_index": "801050",
        "cn_etf_name": "黄金ETF",
        "cn_etf_code": "518880",
    },
]

WINDOW = 60       # 滚动窗口天数
THRESHOLD = 2.0   # 显著波动阈值（%）


# ─── 核心计算函数 ───────────────────────────────────────────

def calc_conditional_prob(
    us_changes: pd.Series,
    cn_changes: pd.Series,
    threshold: float = THRESHOLD,
    window: int = WINDOW,
) -> tuple:
    """
    计算条件概率：当美股板块涨跌幅绝对值 > threshold 时，
    A 股板块次日高开的概率和平均幅度。

    参数:
        us_changes: 美股板块每日涨跌幅 Series（索引为日期）
        cn_changes: A 股板块次日开盘涨跌幅 Series（索引为日期）
        threshold: 显著波动阈值（%）
        window: 滚动窗口天数

    返回:
        (prob_high_open, avg_impact, sample_count)
        无显著波动时返回 (None, None, 0)
    """
    # 取最近 window 个数据
    us = us_changes.iloc[-window:].copy()
    cn = cn_changes.iloc[-window:].copy()

    # 按索引对齐
    common_idx = us.index.intersection(cn.index)
    if len(common_idx) == 0:
        return None, None, 0

    us = us.loc[common_idx]
    cn = cn.loc[common_idx]

    # 筛选显著波动
    significant_mask = us.abs() > threshold
    sample_count = significant_mask.sum()

    if sample_count == 0:
        return None, None, 0

    cn_on_sig = cn[significant_mask]
    prob_high_open = float((cn_on_sig > 0).mean())
    avg_impact = float(cn_on_sig.mean())

    return prob_high_open, avg_impact, int(sample_count)
