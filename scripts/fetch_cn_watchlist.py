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
    BENCHMARKS, DEFAULT_BENCHMARK,
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

            # 列名映射：AkShare 返回中文列名，需要统一
            col_map = {}
            for col in df.columns:
                if col in ("日期", "date"):
                    col_map[col] = "date"
                elif col in ("收盘", "close"):
                    col_map[col] = "close"
            df = df.rename(columns=col_map)

            if "date" not in df.columns or "close" not in df.columns:
                print(f"    WARNING: 基准指数 {code} 缺少必要列 {list(df.columns)}")
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
            # 使用 ak.index_realtime_sw 获取申万指数实时行情
            df = ak.index_realtime_sw(symbol="一级行业")
            if df.empty:
                print("  WARNING: 申万指数返回空数据")
                continue

            # 筛选申万一级行业指数
            for _, row in df.iterrows():
                code = row.get('指数代码', '')
                # 申万一级行业代码格式如 801010
                if code in ALL_SECTOR_CODES:
                    close_price = float(row.get('昨收盘', 0))
                    current_price = float(row.get('最新价', 0))
                    # 计算涨跌幅
                    change_pct = round((current_price - close_price) / close_price * 100, 2) if close_price > 0 else 0.0

                    result[code] = {
                        "name": row.get('指数名称', ''),
                        "price": current_price,
                        "change_pct": change_pct,
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
            # 使用 ak.index_hist_sw 获取申万指数历史数据
            df = ak.index_hist_sw(symbol=code, period="day")
            if df.empty:
                return pd.Series()

            # 列名映射：AkShare 返回中文列名，需要统一
            col_map = {}
            for col in df.columns:
                if col in ("日期", "date"):
                    col_map[col] = "date"
                elif col in ("收盘", "close"):
                    col_map[col] = "close"
            df = df.rename(columns=col_map)

            if "date" not in df.columns:
                return pd.Series()

            # 筛选日期范围
            df['date'] = pd.to_datetime(df['date'])
            df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
            df = df.sort_values('date')

            if "close" not in df.columns:
                return pd.Series()

            return df.set_index('date')['close']

        except Exception as e:
            if retry < MAX_RETRIES - 1:
                continue
            else:
                return pd.Series()

    return pd.Series()


# ─── REL 计算 ─────────────────────────────────────────────

def calculate_rel(
    sector_close: pd.Series,
    benchmark_close: pd.Series
) -> dict:
    """
    计算相对强度（REL）。

    REL_n = 行业_n日收益率 - 基准_n日收益率

    Args:
        sector_close: 行业收盘价序列
        benchmark_close: 基准收盘价序列

    Returns:
        {"rel_5": float, "rel_20": float, ...}
    """
    rel_data = {}

    for period in REL_PERIODS:
        if len(sector_close) < period or len(benchmark_close) < period:
            rel_data[f"rel_{period}"] = 0.0
            continue

        # 收益率 = (最新价 - N日前价) / N日前价 * 100
        sector_ret = (sector_close.iloc[-1] / sector_close.iloc[-period] - 1) * 100
        benchmark_ret = (benchmark_close.iloc[-1] / benchmark_close.iloc[-period] - 1) * 100
        rel = round(sector_ret - benchmark_ret, 2)
        rel_data[f"rel_{period}"] = rel

    return rel_data


def calculate_rank(rel_data: dict) -> dict:
    """
    根据REL值计算简化的Rank（百分位近似）。
    """
    rank = {}
    for period in REL_PERIODS:
        rel_val = rel_data.get(f"rel_{period}", 0)
        # 简化：REL每1%对应2分，基准50分
        rank_val = int(50 + rel_val * 2)
        rank_val = max(0, min(100, rank_val))  # 限制在0-100
        rank[f"r_{period}"] = rank_val
    return rank


# ─── 历史走势生成 ─────────────────────────────────────────────

def generate_history(close: pd.Series, current_price: float) -> list:
    """
    生成用于图表的历史走势数据。

    Args:
        close: 历史收盘价序列
        current_price: 当前最新价

    Returns:
        长度为 HISTORY_POINTS 的价格列表
    """
    if len(close) < HISTORY_POINTS:
        # 数据不足，用当前价填充
        return [current_price] * HISTORY_POINTS

    # 取最近 HISTORY_POINTS 个数据点
    recent = close.iloc[-HISTORY_POINTS:].tolist()

    # 确保最后一个值是当前价
    recent[-1] = current_price

    return [round(float(x), 2) for x in recent]


def calculate_ytd(sector_close: pd.Series) -> float:
    """
    计算年初至今收益率。
    """
    if len(sector_close) < 2:
        return 0.0

    year_start = f"{datetime.now().year}-01-01"
    ytd_data = sector_close[sector_close.index >= year_start]

    if len(ytd_data) < 2:
        return 0.0

    ytd_ret = (ytd_data.iloc[-1] / ytd_data.iloc[0] - 1) * 100
    return round(ytd_ret, 2)


# ─── 数据合并和输出 ─────────────────────────────────────────────

def build_sector_data(
    code: str,
    realtime: dict,
    benchmark_close: pd.Series
) -> dict:
    """
    构建单个行业的数据对象。
    """
    sector_info = get_sector_by_code(code)
    if not sector_info:
        return None

    # 获取历史数据
    sector_close = fetch_sector_history(code)

    # 计算REL
    rel_data = calculate_rel(sector_close, benchmark_close)
    rank_data = calculate_rank(rel_data)

    # 计算YTD
    ytd_ret = calculate_ytd(sector_close)

    # 生成历史走势
    history = generate_history(sector_close, realtime["price"])

    return {
        "code": code,
        "name": sector_info["name"],
        "name_en": sector_info["name_en"],
        "price": realtime["price"],
        "change_pct": realtime["change_pct"],
        "rel": rel_data,
        "rank": rank_data,
        "ytd": ytd_ret,
        "history": history,
    }


def build_output(sectors: list, benchmark_key: str) -> dict:
    """
    构建输出JSON结构。
    """
    benchmark_info = get_benchmark_info(benchmark_key)

    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "updated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00"),
        "total_sectors": len(sectors),
        "benchmark": {
            "key": benchmark_key,
            "name": benchmark_info["name"],
            "name_en": benchmark_info["name_en"],
        },
        "groups": {
            "sw_level1": {
                "display_name": "申万一级行业",
                "sectors": sectors,
            }
        },
    }


# ─── 主运行函数 ─────────────────────────────────────────────

def run_fetch(output_dir: str = None, benchmark_key: str = None):
    """
    主入口：获取申万行业指数数据 → 计算REL → 输出JSON。

    Args:
        output_dir: 输出目录，默认为 data/cn_watchlist
        benchmark_key: 基准指数key，默认为 hs300
    """
    if output_dir is None:
        output_dir = OUTPUT_DIR
    output_dir = os.path.abspath(output_dir)

    if benchmark_key is None:
        benchmark_key = DEFAULT_BENCHMARK

    if benchmark_key not in BENCHMARKS:
        print(f"ERROR: Unknown benchmark: {benchmark_key}")
        return None

    try:
        # 1. 获取基准指数历史数据
        print(f"基准指数: {BENCHMARKS[benchmark_key]['name']}")
        benchmark_close = fetch_benchmark_history(benchmark_key)
        if benchmark_close.empty:
            print("ERROR: 无法获取基准指数数据")
            return None

        # 2. 获取申万行业实时行情
        realtime_data = fetch_sector_realtime()
        if not realtime_data:
            print("ERROR: 无法获取申万行业实时行情")
            return None

        # 3. 处理每个行业数据
        sectors = []
        for code in ALL_SECTOR_CODES:
            if code not in realtime_data:
                print(f"  SKIP: {code} — 无实时数据")
                continue

            sector_data = build_sector_data(code, realtime_data[code], benchmark_close)
            if sector_data:
                sectors.append(sector_data)

        # 4. 构建输出
        output = build_output(sectors, benchmark_key)

        # 5. 写入文件
        os.makedirs(output_dir, exist_ok=True)
        # 文件名包含基准信息：默认基准用 {date}.json，其他用 {date}_{benchmark}.json
        if benchmark_key == DEFAULT_BENCHMARK:
            filename = f"{output['date']}.json"
        else:
            filename = f"{output['date']}_{benchmark_key}.json"
        output_path = os.path.join(output_dir, filename)

        if os.path.exists(output_path):
            print(f"SKIP: {output_path} already exists")
            return None

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"OK: {output_path} ({len(sectors)} sectors)")
        return output

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="获取A股申万行业指数数据")
    parser.add_argument(
        "--benchmark", "-b",
        choices=list(BENCHMARKS.keys()),
        default=DEFAULT_BENCHMARK,
        help="基准指数 (默认: hs300)"
    )
    args = parser.parse_args()
    run_fetch(benchmark_key=args.benchmark)
