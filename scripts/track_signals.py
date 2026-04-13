"""
T+1 信号验证脚本

核心功能：
1. 从 history.json 加载历史信号记录
2. 从 watchlist 获取最新市场数据
3. 计算信号的命中/未命中情况和收益率
4. 更新 history.json 并生成统计报告

工作流程：
    历史信号 → 获取T+1价格 → 计算收益 → 判定命中 → 更新统计

使用示例：
    # 验证所有未跟踪的信号
    python scripts/track_signals.py

    # 指定日期
    python scripts/track_signals.py --date 2026-04-13
"""
import json
import os
import sys
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from collections import defaultdict

import requests
import yfinance as yf

# ─── 路径配置 ───

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
SIGNALS_DIR = os.path.join(PROJECT_ROOT, "data", "signals")
WATCHLIST_DIR = os.path.join(PROJECT_ROOT, "data", "watchlist")
HISTORY_PATH = os.path.join(PROJECT_ROOT, "data", "history.json")
STATS_DIR = os.path.join(PROJECT_ROOT, "data", "stats")


# ─── 常量定义 ───

# 命中阈值：涨跌幅超过此值视为命中
HIT_THRESHOLD_LONG = 1.0  # 做多信号：涨幅 >= 1%
HIT_THRESHOLD_SHORT = -1.0  # 做空信号：跌幅 <= -1%

# 持有期：信号生成后的交易日数
HOLDING_DAYS = 1


# ─── 数据加载/保存函数 ───

def load_history() -> Dict:
    """
    从 history.json 加载历史记录

    Returns:
        历史记录字典，格式：{"signals": [...], "stats": {...}}
    """
    if not os.path.exists(HISTORY_PATH):
        # 初始化空的历史记录
        return {
            "signals": [],
            "stats": {
                "total": 0,
                "hits": 0,
                "misses": 0,
                "pending": 0,
                "hit_rate": 0.0,
                "avg_return": 0.0,
                "last_updated": None
            },
            "by_level": defaultdict(lambda: {"total": 0, "hits": 0, "avg_return": 0.0})
        }

    try:
        with open(HISTORY_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # 确保 by_level 字段存在
        if "by_level" not in data:
            data["by_level"] = {}
        return data
    except Exception as e:
        print(f"ERROR: 读取历史记录失败 - {e}")
        return {"signals": [], "stats": {}, "by_level": {}}


def save_history(history: Dict) -> None:
    """
    保存历史记录到 history.json

    Args:
        history: 历史记录字典
    """
    # 更新统计时间戳
    history["stats"]["last_updated"] = datetime.now().isoformat()

    with open(HISTORY_PATH, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def load_signals(date: str) -> Tuple[List[Dict], str]:
    """
    从 JSON 文件加载指定日期的信号

    Args:
        date: 日期字符串 (YYYY-MM-DD)

    Returns:
        (信号列表, 文件路径) 元组
    """
    filepath = os.path.join(SIGNALS_DIR, f"{date}.json")

    if not os.path.exists(filepath):
        return [], filepath

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        signals = data.get("signals", [])
        return signals, filepath
    except Exception as e:
        print(f"ERROR: 读取信号文件失败 - {e}")
        return [], filepath


def load_watchlist_data() -> Dict:
    """
    从最新的 watchlist 文件加载数据

    Returns:
        watchlist 数据字典
    """
    # 查找最新的 watchlist 文件
    if not os.path.exists(WATCHLIST_DIR):
        return {}

    files = [f for f in os.listdir(WATCHLIST_DIR) if f.endswith('.json')]
    if not files:
        return {}

    # 按日期排序，取最新的
    latest_file = sorted(files)[-1]
    filepath = os.path.join(WATCHLIST_DIR, latest_file)

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"WARNING: 读取 watchlist 失败 - {e}")
        return {}


# ─── 价格获取函数 ───

def get_ticker_price_yf(ticker: str) -> Optional[float]:
    """
    使用 yfinance 获取股票最新价格

    Args:
        ticker: 股票代码

    Returns:
        最新价格，失败返回 None
    """
    try:
        stock = yf.Ticker(ticker)
        # 使用 fast_info 快速获取当前价格
        if hasattr(stock, 'fast_info') and stock.fast_info:
            return stock.fast_info.last_price
        else:
            # 回退到常规方法
            hist = stock.history(period="1d")
            if not hist.empty:
                return float(hist['Close'].iloc[-1])
        return None
    except Exception as e:
        print(f"  WARNING: 获取 {ticker} 价格失败 - {e}")
        return None


def calculate_return(entry_price: float, current_price: float) -> float:
    """
    计算收益率（%）

    Args:
        entry_price: 入场价格
        current_price: 当前价格

    Returns:
        收益率（百分比）
    """
    if entry_price <= 0:
        return 0.0
    return round((current_price - entry_price) / entry_price * 100, 2)


# ─── 信号验证函数 ───

def determine_hit(signal: Dict, return_pct: float) -> bool:
    """
    判定信号是否命中

    判定规则：
    - 做多信号 (LONG): 收益率 >= HIT_THRESHOLD_LONG 视为命中
    - 做空信号 (SHORT): 收益率 <= HIT_THRESHOLD_SHORT 视为命中
    - 观望信号 (NEUTRAL): 不判定

    Args:
        signal: 信号字典
        return_pct: 收益率（%）

    Returns:
        是否命中
    """
    direction = signal.get("direction", "NEUTRAL").upper()

    if direction == "LONG":
        return return_pct >= HIT_THRESHOLD_LONG
    elif direction == "SHORT":
        return return_pct <= HIT_THRESHOLD_SHORT
    else:
        # NEUTRAL 信号不判定
        return False


def track_signal(signal: Dict, watchlist_data: Dict) -> Optional[Dict]:
    """
    跟踪单个信号，获取 T+1 价格并计算收益

    Args:
        signal: 信号字典
        watchlist_data: watchlist 数据

    Returns:
        更新后的信号记录，失败返回 None
    """
    ticker = signal.get("ticker")

    if not ticker:
        print(f"  SKIP: 信号缺少 ticker")
        return None

    # ─── 1. 尝试从 watchlist 获取价格 ───
    current_price = None
    if watchlist_data and "groups" in watchlist_data:
        for group_data in watchlist_data["groups"].values():
            for etf in group_data.get("etfs", []):
                if etf.get("ticker") == ticker:
                    current_price = etf.get("price")
                    break
            if current_price:
                break

    # ─── 2. 如果 watchlist 没有数据，使用 yfinance ───
    if not current_price:
        print(f"  Fetching price for {ticker} via yfinance...")
        current_price = get_ticker_price_yf(ticker)

    if not current_price:
        print(f"  SKIP: {ticker} 无法获取当前价格")
        return None

    # ─── 3. 计算收益率 ───
    entry_price = signal.get("entry_price")
    if not entry_price:
        print(f"  SKIP: {ticker} 信号缺少入场价格")
        return None

    return_pct = calculate_return(entry_price, current_price)

    # ─── 4. 判定命中 ───
    is_hit = determine_hit(signal, return_pct)

    # ─── 5. 构建跟踪记录 ───
    tracked_signal = {
        **signal,
        "current_price": current_price,
        "return_pct": return_pct,
        "is_hit": is_hit,
        "tracked_at": datetime.now().isoformat(),
        "status": "tracked"  # tracked | pending | failed
    }

    direction = signal.get("direction", "NEUTRAL")
    hit_status = "✓ HIT" if is_hit else "✗ MISS"
    print(f"  {ticker} [{direction}] {return_pct:+.2f}% {hit_status}")

    return tracked_signal


def update_stats(history: Dict) -> None:
    """
    更新统计数据

    Args:
        history: 历史记录字典（会被原地修改）
    """
    signals = history.get("signals", [])

    # 初始化统计
    total = len(signals)
    hits = sum(1 for s in signals if s.get("is_hit") is True and s.get("status") == "tracked")
    misses = sum(1 for s in signals if s.get("is_hit") is False and s.get("status") == "tracked")
    pending = sum(1 for s in signals if s.get("status") == "pending")

    # 计算平均收益（只计算已跟踪的）
    tracked_signals = [s for s in signals if s.get("status") == "tracked" and "return_pct" in s]
    avg_return = sum(s["return_pct"] for s in tracked_signals) / len(tracked_signals) if tracked_signals else 0.0

    hit_rate = hits / (hits + misses) * 100 if (hits + misses) > 0 else 0.0

    # 按等级统计
    by_level = defaultdict(lambda: {"total": 0, "hits": 0, "avg_return": 0.0})
    for signal in signals:
        if signal.get("status") != "tracked":
            continue
        level = signal.get("level", "C")
        by_level[level]["total"] += 1
        if signal.get("is_hit"):
            by_level[level]["hits"] += 1
        if "return_pct" in signal:
            by_level[level]["avg_return"] += signal["return_pct"]

    # 计算各等级平均收益
    for level in by_level:
        if by_level[level]["total"] > 0:
            by_level[level]["avg_return"] = round(
                by_level[level]["avg_return"] / by_level[level]["total"], 2
            )
        by_level[level]["hit_rate"] = round(
            by_level[level]["hits"] / by_level[level]["total"] * 100, 2
        ) if by_level[level]["total"] > 0 else 0.0

    # 更新统计
    history["stats"] = {
        "total": total,
        "hits": hits,
        "misses": misses,
        "pending": pending,
        "hit_rate": round(hit_rate, 2),
        "avg_return": round(avg_return, 2),
        "last_updated": datetime.now().isoformat()
    }

    history["by_level"] = dict(by_level)


# ─── 主运行逻辑 ───

def track_signals_for_date(date: str, force: bool = False) -> int:
    """
    跟踪指定日期的信号

    Args:
        date: 日期字符串 (YYYY-MM-DD)
        force: 是否强制重新跟踪（即使已经跟踪过）

    Returns:
        跟踪的信号数量
    """
    print(f"\n{'='*50}")
    print(f"信号跟踪: {date}")
    print(f"{'='*50}")

    # ─── 1. 加载信号 ───
    signals, filepath = load_signals(date)

    if not signals:
        print(f"WARNING: 未找到信号数据 - {filepath}")
        return 0

    print(f"✓ 加载信号: {len(signals)} 条")

    # ─── 2. 加载历史记录 ───
    history = load_history()

    # ─── 3. 加载 watchlist 数据 ───
    watchlist_data = load_watchlist_data()
    if watchlist_data:
        print(f"✓ 加载 watchlist: {watchlist_data.get('date', 'unknown')}")
    else:
        print("⚠ 未找到 watchlist 数据，将使用 yfinance")

    # ─── 4. 过滤需要跟踪的信号 ───
    tracked_count = 0
    existing_dates = {s.get("date") for s in history.get("signals", [])}

    for signal in signals:
        signal_date = signal.get("date", date)

        # 检查是否已经跟踪过
        if not force and signal_date in existing_dates:
            print(f"  SKIP: {signal.get('ticker')} 已跟踪")
            continue

        # ─── 5. 跟踪信号 ───
        tracked_signal = track_signal(signal, watchlist_data)

        if tracked_signal:
            # 添加到历史记录
            tracked_signal["date"] = signal_date
            history["signals"].append(tracked_signal)
            tracked_count += 1

    # ─── 6. 更新统计 ───
    if tracked_count > 0:
        update_stats(history)
        save_history(history)
        print(f"\n✓ 已跟踪 {tracked_count} 条信号")

    # ─── 7. 打印统计摘要 ───
    stats = history.get("stats", {})
    print(f"\n统计摘要:")
    print(f"  总计: {stats.get('total', 0)}")
    print(f"  命中: {stats.get('hits', 0)}")
    print(f"  未中: {stats.get('misses', 0)}")
    print(f"  待定: {stats.get('pending', 0)}")
    print(f"  命中率: {stats.get('hit_rate', 0):.1f}%")
    print(f"  平均收益: {stats.get('avg_return', 0):.2f}%")

    return tracked_count


def track_all_pending() -> int:
    """
    跟踪所有未跟踪的信号

    Returns:
        跟踪的信号数量
    """
    history = load_history()
    existing_dates = {s.get("date") for s in history.get("signals", [])}

    # 获取所有信号文件
    if not os.path.exists(SIGNALS_DIR):
        print("ERROR: 信号目录不存在")
        return 0

    signal_files = [f for f in os.listdir(SIGNALS_DIR) if f.endswith('.json')]
    signal_dates = sorted([f.replace('.json', '') for f in signal_files])

    total_tracked = 0
    for date in signal_dates:
        if date not in existing_dates:
            count = track_signals_for_date(date)
            total_tracked += count

    return total_tracked


def export_stats() -> None:
    """
    导出统计数据到 stats 目录
    """
    history = load_history()
    stats = history.get("stats", {})
    by_level = history.get("by_level", {})

    os.makedirs(STATS_DIR, exist_ok=True)

    # 导出整体统计
    stats_path = os.path.join(STATS_DIR, "overview.json")
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump({
            "stats": stats,
            "by_level": by_level,
            "exported_at": datetime.now().isoformat()
        }, f, ensure_ascii=False, indent=2)

    print(f"✓ 统计已导出: {stats_path}")


# ─── 命令行接口 ───

def main():
    """命令行主函数"""
    parser = argparse.ArgumentParser(description="T+1 信号验证")
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="日期 (YYYY-MM-DD)，不指定则跟踪所有未跟踪的信号"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制重新跟踪（即使已经跟踪过）"
    )
    parser.add_argument(
        "--export",
        action="store_true",
        help="导出统计数据"
    )

    args = parser.parse_args()

    if args.export:
        export_stats()
        return

    if args.date:
        track_signals_for_date(args.date, force=args.force)
    else:
        count = track_all_pending()
        if count == 0:
            print("\n所有信号均已跟踪")
        else:
            print(f"\n共跟踪 {count} 条新信号")


if __name__ == "__main__":
    main()
