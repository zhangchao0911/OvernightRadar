"""
Market Watchlist 数据获取脚本
使用 yfinance 自计算 ETF 价格、涨跌幅、REL (相对强度)，输出 JSON。
REL = ETF 涨跌幅 - 标普500(SPY) 涨跌幅，正值表示跑赢大盘。

用法: python scripts/fetch_watchlist.py
"""
import json
import os
import sys
from datetime import datetime

import yfinance as yf

sys.path.insert(0, os.path.dirname(__file__))
from etf_config import ETF_GROUPS, CN_LINKED_TICKERS, ALL_TICKERS, get_group_key

# ─── 配置 ─────────────────────────────────────────────────

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "watchlist")
BENCHMARK = "SPY"
REL_PERIODS = [5, 20, 60, 120]  # REL 计算周期（交易日）
HISTORY_DAYS = 130  # 走势图历史数据天数（覆盖 120 日 + 余量）


# ─── 数据获取 ─────────────────────────────────────────────

def fetch_price_data(tickers: list) -> dict:
    """
    批量获取 ETF 历史价格数据。
    返回: {ticker: {"history": [价格列表], "close": 最新价, ...}}
    """
    print(f"Fetching price data for {len(tickers)} tickers + {BENCHMARK}...")

    all_tickers = list(set(tickers + [BENCHMARK]))
    data = yf.download(
        tickers=all_tickers,
        period=f"{HISTORY_DAYS}d",
        group_by="ticker",
        auto_adjust=True,
        threads=True,
        progress=False,
    )

    results = {}
    for ticker in all_tickers:
        try:
            if len(all_tickers) > 1:
                hist = data[ticker]["Close"]
            else:
                hist = data["Close"]

            hist = hist.dropna()
            if len(hist) < 2:
                print(f"  SKIP: {ticker} — 数据不足")
                continue

            prices = hist.tolist()
            latest = prices[-1]
            prev_close = prices[-2]
            change_pct = (latest - prev_close) / prev_close * 100

            # YTD: 从年初至今
            year_start = datetime.now().replace(month=1, day=1)
            ytd_prices = hist[hist.index >= year_start.strftime("%Y-%m-%d")]
            if len(ytd_prices) >= 2:
                ytd = (ytd_prices.iloc[-1] - ytd_prices.iloc[0]) / ytd_prices.iloc[0] * 100
            else:
                ytd = 0.0

            # 各周期收益率
            period_returns = {}
            for p in REL_PERIODS:
                if len(prices) > p:
                    period_returns[p] = (prices[-1] - prices[-1 - p]) / prices[-1 - p] * 100
                else:
                    period_returns[p] = 0.0

            results[ticker] = {
                "price": round(latest, 2),
                "change_pct": round(change_pct, 2),
                "ytd": round(ytd, 2),
                "period_returns": period_returns,
                "history": [round(p, 2) for p in prices[-30:]],  # 最近30天走势
            }
        except Exception as e:
            print(f"  ERROR: {ticker} — {e}")

    return results


def compute_rel(etf_data: dict, benchmark_data: dict) -> dict:
    """计算 REL: ETF 各周期收益率 - SPY 同期收益率。"""
    rel = {}
    for p in REL_PERIODS:
        etf_ret = etf_data.get("period_returns", {}).get(p, 0.0)
        spy_ret = benchmark_data.get("period_returns", {}).get(p, 0.0)
        rel[f"rel_{p}"] = round(etf_ret - spy_ret, 2)
    return rel


def compute_ranks(etf_results: dict) -> dict:
    """按各周期 REL 排名（REL 越高排名越靠前，rank=1 最强）。"""
    ranks = {}
    for p in REL_PERIODS:
        key = f"rel_{p}"
        sorted_tickers = sorted(
            etf_results.keys(),
            key=lambda t: etf_results[t].get("rel", {}).get(key, -999),
            reverse=True,
        )
        rank_map = {t: i + 1 for i, t in enumerate(sorted_tickers)}
        ranks[f"r_{p}"] = rank_map
    return ranks


def build_etf_data(ticker: str, price_data: dict, rel: dict, rank: dict) -> dict:
    """构建单个 ETF 的输出数据。"""
    # 从 ETF_GROUPS 找中文名
    group_key = get_group_key(ticker)
    name = ""
    name_en = ""
    if group_key and group_key in ETF_GROUPS:
        for etf in ETF_GROUPS[group_key]["etfs"]:
            if etf["ticker"] == ticker:
                name = etf["name"]
                name_en = etf["name_en"]
                break

    return {
        "ticker": ticker,
        "name": name,
        "name_en": name_en,
        "price": price_data["price"],
        "change_pct": price_data["change_pct"],
        "rel": rel,
        "rank": {f"r_{p}": rank.get(f"r_{p}", {}).get(ticker, 0) for p in REL_PERIODS},
        "ytd": price_data["ytd"],
        "has_cn_mapping": ticker in CN_LINKED_TICKERS,
        "group": group_key,
        "history": price_data.get("history", []),
    }


def build_output(etfs: list) -> dict:
    """构建输出 JSON 结构。"""
    groups = {}
    for group_key, group_data in ETF_GROUPS.items():
        group_tickers = {e["ticker"] for e in group_data["etfs"]}
        group_etfs = [e for e in etfs if e["ticker"] in group_tickers]
        groups[group_key] = {
            "display_name": group_data["display_name"],
            "etfs": group_etfs,
        }

    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "updated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00"),
        "total_etfs": len(etfs),
        "groups": groups,
    }


def run_fetch(output_dir: str = None):
    """主入口：获取价格 → 计算 REL → 排名 → 输出 JSON。"""
    if output_dir is None:
        output_dir = OUTPUT_DIR

    output_dir = os.path.abspath(output_dir)

    try:
        # 1. 获取所有 ETF + SPY 的价格数据
        price_data = fetch_price_data(ALL_TICKERS)

        if BENCHMARK not in price_data:
            print(f"ERROR: 无法获取 {BENCHMARK} 基准数据", file=sys.stderr)
            return None

        benchmark = price_data[BENCHMARK]

        # 2. 计算每个 ETF 的 REL
        etf_results = {}
        for ticker in ALL_TICKERS:
            if ticker not in price_data:
                print(f"  SKIP: {ticker} — 无价格数据")
                continue
            rel = compute_rel(price_data[ticker], benchmark)
            etf_results[ticker] = {"rel": rel}

        # 3. 排名
        ranks = compute_ranks(etf_results)

        # 4. 构建输出
        etfs = []
        for ticker in ALL_TICKERS:
            if ticker not in price_data:
                continue
            etf = build_etf_data(
                ticker,
                price_data[ticker],
                etf_results[ticker]["rel"],
                ranks,
            )
            etfs.append(etf)

        report = build_output(etfs)

        # 5. 输出 JSON
        os.makedirs(output_dir, exist_ok=True)
        date_str = report["date"]
        output_path = os.path.join(output_dir, f"{date_str}.json")

        if os.path.exists(output_path):
            print(f"SKIP: {output_path} already exists")
            return None

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"OK: {output_path} ({len(etfs)} ETFs)")
        return report

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return None


if __name__ == "__main__":
    run_fetch()
