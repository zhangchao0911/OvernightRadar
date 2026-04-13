"""
A股市场观察数据获取脚本
数据源：AkShare 申万行业指数
输出：合并后的 JSON

用法: python scripts/fetch_cn_watchlist.py
"""
import json
import os
import sys
from datetime import datetime, timedelta

import akshare as ak
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from cn_sector_config import (
    SW_LEVEL1_SECTORS, BENCHMARKS, DEFAULT_BENCHMARK,
    ALL_SECTOR_CODES, get_sector_by_code, get_benchmark_info
)

# ─── 配置 ─────────────────────────────────────────────────

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "cn_watchlist")
HISTORY_POINTS = 30
REL_PERIODS = [5, 20, 60, 120]

# AkShare 请求重试配置
MAX_RETRIES = 3
REQUEST_TIMEOUT = 30


# ─── 基准指数数据获取 ─────────────────────────────────────────────

def fetch_benchmark_history(benchmark_key: str, period_days: int = 150) -> pd.Series:
    """
    获取基准指数历史数据。

    Args:
        benchmark_key: 基准key (hs300/zz500)
        period_days: 历史数据天数

    Returns:
        收盘价 Series，索引为日期
    """
    benchmark_info = get_benchmark_info(benchmark_key)
    if not benchmark_info:
        raise ValueError(f"Unknown benchmark: {benchmark_key}")

    code = benchmark_info["code"]
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=period_days)).strftime("%Y%m%d")

    print(f"  获取基准指数 {benchmark_info['name']} ({code})...")

    for retry in range(MAX_RETRIES):
        try:
            # 使用 ak.stock_zh_index_daily 获取指数历史数据
            df = ak.stock_zh_index_daily(
                symbol=f"sh{code}" if code.startswith("00") else f"sz{code}"
            )
            if df.empty:
                print(f"    WARNING: 基准指数 {code} 返回空数据")
                return pd.Series()

            # 筛选日期范围
            df['date'] = pd.to_datetime(df['date'])
            df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
            df = df.sort_values('date')

            return df.set_index('date')['close']

        except Exception as e:
            if retry < MAX_RETRIES - 1:
                print(f"    重试 {retry + 1}/{MAX_RETRIES}: {e}")
                continue
            else:
                print(f"    ERROR: 获取基准指数失败 - {e}")
                return pd.Series()


# ─── 申万行业指数数据获取 ─────────────────────────────────────────────

def fetch_sector_realtime() -> dict:
    """
    获取申万一级行业指数实时行情。

    Returns:
        {code: {"name": str, "price": float, "change_pct": float}}
    """
    print("获取申万一级行业指数实时行情...")

    result = {}

    for retry in range(MAX_RETRIES):
        try:
            # 使用 ak.sw_index_spot 获取申万指数实时行情
            df = ak.sw_index_spot()
            if df.empty:
                print("  WARNING: 申万指数返回空数据")
                continue

            # 筛选申万一级行业指数
            for _, row in df.iterrows():
                code = row.get('指数代码', '')
                # 申万一级行业代码格式如 801010
                if code in ALL_SECTOR_CODES:
                    result[code] = {
                        "name": row.get('指数名称', ''),
                        "price": float(row.get('最新价', 0)),
                        "change_pct": float(row.get('涨跌幅', 0)),
                    }

            print(f"  获取到 {len(result)} 个行业数据")
            return result

        except Exception as e:
            if retry < MAX_RETRIES - 1:
                print(f"  重试 {retry + 1}/{MAX_RETRIES}: {e}")
                continue
            else:
                print(f"  ERROR: 获取申万指数失败 - {e}")
                return {}

    return result


def fetch_sector_history(code: str, period_days: int = 150) -> pd.Series:
    """
    获取单个行业指数历史数据。

    Args:
        code: 行业代码
        period_days: 历史数据天数

    Returns:
        收盘价 Series，索引为日期
    """
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=period_days)).strftime("%Y%m%d")

    for retry in range(MAX_RETRIES):
        try:
            # 使用 ak.sw_index_daily 获取申万指数历史数据
            df = ak.sw_index_daily(symbol=code)
            if df.empty:
                return pd.Series()

            # 筛选日期范围
            df['date'] = pd.to_datetime(df['date'])
            df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
            df = df.sort_values('date')

            return df.set_index('date')['close']

        except Exception as e:
            if retry < MAX_RETRIES - 1:
                continue
            else:
                return pd.Series()

    return pd.Series()
