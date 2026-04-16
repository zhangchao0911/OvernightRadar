"""
A股 ETF 市场观察数据获取脚本
数据源：AkShare ETF 行情接口
输出：按分组的 ETF 数据 JSON

用法: python scripts/fetch_cn_watchlist.py
"""
import json
import os
import sys
import time
from datetime import datetime, timedelta

import akshare as ak
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from cn_sector_config import (
    BENCHMARKS, DEFAULT_BENCHMARK,
    ALL_ETF_CODES, CN_ETF_GROUPS, get_etf_by_code, get_benchmark_info,
)

# ─── 配置 ─────────────────────────────────────────────────

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "cn_watchlist")
HISTORY_POINTS = 30
REL_PERIODS = [5, 20, 60, 120]
MAX_RETRIES = 5
ETF_SPOT_TIMEOUT = 60  # fund_etf_spot_em 超时（秒），批量获取62只ETF数据量大


# ─── 基准指数数据获取 ─────────────────────────────────────────────

def fetch_benchmark_history(benchmark_key: str, period_days: int = 150) -> pd.Series:
    """
    获取基准指数历史数据。

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
            df = ak.stock_zh_index_daily(
                symbol=f"sh{code}" if code.startswith("00") else f"sz{code}"
            )
            if df.empty:
                print(f"    WARNING: 基准指数 {code} 返回空数据")
                return pd.Series()

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

            df['date'] = pd.to_datetime(df['date'])
            df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
            df = df.sort_values('date')

            return df.set_index('date')['close']

        except Exception as e:
            if retry < MAX_RETRIES - 1:
                print(f"    重试 {retry + 1}/{MAX_RETRIES}: {e}")
                continue
            print(f"    ERROR: 获取基准指数失败 - {e}")
            return pd.Series()


# ─── ETF 实时行情 ─────────────────────────────────────────────

def fetch_etf_realtime(etf_codes: list) -> dict:
    """
    批量获取 ETF 实时行情。

    Returns:
        {code: {"name": str, "price": float, "change_pct": float}}
    """
    print(f"获取 ETF 实时行情 ({len(etf_codes)} 只)...")

    result = {}

    for retry in range(MAX_RETRIES):
        try:
            # 增加 requests 超时，AkShare 内部用 requests 但不暴露 timeout 参数
            import requests
            original_get = requests.Session.get
            def _patched_get(self, url, **kwargs):
                kwargs.setdefault('timeout', ETF_SPOT_TIMEOUT)
                return original_get(self, url, **kwargs)
            requests.Session.get = _patched_get
            try:
                df = ak.fund_etf_spot_em()
            finally:
                requests.Session.get = original_get
            if df is None or df.empty:
                print("  WARNING: ETF 行情返回空数据")
                continue

            # 找到代码和涨跌幅列
            code_col = None
            name_col = None
            price_col = None
            change_col = None

            for col in df.columns:
                if col in ("代码", "code"):
                    code_col = col
                elif col in ("名称", "name"):
                    name_col = col
                elif col in ("最新价", "price"):
                    price_col = col
                elif col in ("涨跌幅", "change_pct"):
                    change_col = col

            if not code_col or not change_col:
                print(f"  WARNING: 列名不匹配 {list(df.columns)}")
                continue

            code_set = set(etf_codes)
            matched = df[df[code_col].astype(str).isin(code_set)]

            for _, row in matched.iterrows():
                code = str(row[code_col])
                try:
                    price = float(row[price_col]) if price_col else 0.0
                    change_pct = round(float(row[change_col]), 2)
                    name = str(row[name_col]) if name_col else ""
                    result[code] = {
                        "name": name,
                        "price": price,
                        "change_pct": change_pct,
                    }
                except (ValueError, TypeError):
                    pass

            print(f"  获取到 {len(result)}/{len(etf_codes)} 只 ETF 行情")
            return result

        except Exception as e:
            if retry < MAX_RETRIES - 1:
                print(f"  重试 {retry + 1}/{MAX_RETRIES}: {e}")
                time.sleep(5)
                continue
            print(f"  ERROR: 获取 ETF 行情失败 - {e}")
            return {}

    return result


# ─── ETF 历史数据 ─────────────────────────────────────────────

def fetch_etf_history(code: str, period_days: int = 150) -> pd.Series:
    """
    获取单个 ETF 历史收盘价。

    Returns:
        收盘价 Series，索引为日期
    """
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=period_days)).strftime("%Y%m%d")

    for retry in range(MAX_RETRIES):
        try:
            # 增加 requests 超时保护
            import requests
            original_get = requests.Session.get
            def _patched_get(self, url, **kwargs):
                kwargs.setdefault('timeout', ETF_SPOT_TIMEOUT)
                return original_get(self, url, **kwargs)
            requests.Session.get = _patched_get
            try:
                df = ak.fund_etf_hist_em(
                    symbol=code,
                    period="daily",
                    start_date=start_date,
                    end_date=end_date,
                    adjust="qfq",
                )
            finally:
                requests.Session.get = original_get
            if df is None or df.empty:
                return pd.Series()

            # 列名映射
            col_map = {}
            for col in df.columns:
                if col in ("日期", "date"):
                    col_map[col] = "date"
                elif col in ("收盘", "close"):
                    col_map[col] = "close"
            df = df.rename(columns=col_map)

            if "date" not in df.columns or "close" not in df.columns:
                return pd.Series()

            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')

            return df.set_index('date')['close']

        except Exception as e:
            if retry < MAX_RETRIES - 1:
                continue
            return pd.Series()

    return pd.Series()


# ─── REL 计算 ─────────────────────────────────────────────

def calculate_rel(
    etf_close: pd.Series,
    benchmark_close: pd.Series,
) -> dict:
    """
    计算相对强度（REL）= ETF_N日收益率 - 基准_N日收益率
    """
    rel_data = {}

    for period in REL_PERIODS:
        if len(etf_close) < period or len(benchmark_close) < period:
            rel_data[f"rel_{period}"] = 0.0
            continue

        etf_ret = (etf_close.iloc[-1] / etf_close.iloc[-period] - 1) * 100
        benchmark_ret = (benchmark_close.iloc[-1] / benchmark_close.iloc[-period] - 1) * 100
        rel = round(etf_ret - benchmark_ret, 2)
        rel_data[f"rel_{period}"] = rel

    return rel_data


def calculate_rank(rel_data: dict) -> dict:
    """根据 REL 值计算简化的 Rank（百分位近似）。"""
    rank = {}
    for period in REL_PERIODS:
        rel_val = rel_data.get(f"rel_{period}", 0)
        rank_val = int(50 + rel_val * 2)
        rank[f"r_{period}"] = max(0, min(100, rank_val))
    return rank


def calculate_ytd(close: pd.Series) -> float:
    """计算年初至今收益率。"""
    if len(close) < 2:
        return 0.0
    year_start = f"{datetime.now().year}-01-01"
    ytd_data = close[close.index >= year_start]
    if len(ytd_data) < 2:
        return 0.0
    return round((ytd_data.iloc[-1] / ytd_data.iloc[0] - 1) * 100, 2)


def generate_history(close: pd.Series, current_price: float) -> list:
    """生成历史走势数据（用于图表）。"""
    if len(close) < HISTORY_POINTS:
        return [current_price] * HISTORY_POINTS
    recent = close.iloc[-HISTORY_POINTS:].tolist()
    recent[-1] = current_price
    return [round(float(x), 2) for x in recent]


# ─── 数据构建 ─────────────────────────────────────────────

def build_etf_data(
    code: str,
    realtime: dict,
    benchmark_close: pd.Series,
) -> dict:
    """构建单个 ETF 的数据对象。"""
    etf_info = get_etf_by_code(code)
    if not etf_info:
        return None

    # 获取历史数据
    etf_close = fetch_etf_history(code)

    # 计算 REL
    rel_data = calculate_rel(etf_close, benchmark_close)
    rank_data = calculate_rank(rel_data)

    # YTD
    ytd_ret = calculate_ytd(etf_close)

    # 历史走势
    history = generate_history(etf_close, realtime["price"])

    return {
        "code": code,
        "name": etf_info["name"],
        "price": realtime["price"],
        "change_pct": realtime["change_pct"],
        "rel": rel_data,
        "rank": rank_data,
        "ytd": ytd_ret,
        "history": history,
    }


def build_output(groups_data: dict, benchmark_key: str) -> dict:
    """构建输出 JSON 结构。"""
    benchmark_info = get_benchmark_info(benchmark_key)
    total = sum(len(g["sectors"]) for g in groups_data.values())

    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "updated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00"),
        "total_sectors": total,
        "benchmark": {
            "key": benchmark_key,
            "name": benchmark_info["name"],
            "name_en": benchmark_info["name_en"],
        },
        "groups": groups_data,
    }


# ─── 主运行函数 ─────────────────────────────────────────────

def run_fetch(output_dir: str = None, benchmark_key: str = None, force: bool = False):
    """
    主入口：获取 ETF 行情 → 计算 REL → 输出 JSON。

    Args:
        force: 为 True 时覆盖已有文件（盘中刷新用）
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
        # 0. 提前检查文件是否已存在（避免浪费 API 调用）
        output_dir_resolved = os.path.abspath(output_dir)
        date_str = datetime.now().strftime("%Y-%m-%d")
        if benchmark_key == DEFAULT_BENCHMARK:
            filename = f"{date_str}.json"
        else:
            filename = f"{date_str}_{benchmark_key}.json"
        output_path = os.path.join(output_dir_resolved, filename)

        if os.path.exists(output_path) and not force:
            print(f"SKIP: {output_path} already exists (use --force to overwrite)")
            return None

        # 1. 获取基准指数历史
        print(f"基准指数: {BENCHMARKS[benchmark_key]['name']}")
        benchmark_close = fetch_benchmark_history(benchmark_key)
        if benchmark_close.empty:
            print("ERROR: 无法获取基准指数数据")
            return None

        # 2. 批量获取 ETF 实时行情
        realtime_data = fetch_etf_realtime(ALL_ETF_CODES)
        if not realtime_data:
            print("ERROR: 无法获取 ETF 行情")
            return None

        # 3. 按分组处理每个 ETF
        groups_output = {}
        for group_key, group_conf in CN_ETF_GROUPS.items():
            sectors = []
            for etf_conf in group_conf["etfs"]:
                code = etf_conf["code"]
                if code not in realtime_data:
                    print(f"  SKIP: {code} {etf_conf['name']} — 无实时数据")
                    continue

                print(f"  处理: {code} {etf_conf['name']}...")
                etf_data = build_etf_data(code, realtime_data[code], benchmark_close)
                if etf_data:
                    sectors.append(etf_data)
                time.sleep(0.3)

            groups_output[group_key] = {
                "display_name": group_conf["display_name"],
                "sectors": sectors,
            }
            print(f"  [{group_conf['display_name']}] {len(sectors)} 只")

        # 4. 构建输出
        output = build_output(groups_output, benchmark_key)

        # 5. 写入文件
        os.makedirs(output_dir, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        total = output["total_sectors"]
        print(f"OK: {output_path} ({total} ETFs, {len(groups_output)} groups)")
        return output

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="获取A股ETF市场观察数据")
    parser.add_argument(
        "--benchmark", "-b",
        choices=list(BENCHMARKS.keys()),
        default=DEFAULT_BENCHMARK,
        help="基准指数 (默认: hs300)",
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="覆盖已有文件（盘中刷新用）",
    )
    args = parser.parse_args()
    run_fetch(benchmark_key=args.benchmark, force=args.force)
