"""
Market Watchlist 数据获取脚本
数据源：Finnhub /quote (实时价格) + Google Sheet CSV (REL 相对强度)
输出：合并后的 JSON

用法: FINNHUB_API_KEY=xxx python scripts/fetch_watchlist.py
"""
import csv
import io
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone

BJT = timezone(timedelta(hours=8))

import requests
import yfinance as yf
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from etf_config import ETF_GROUPS, CN_LINKED_TICKERS, ALL_TICKERS, get_group_key

# ─── 配置 ─────────────────────────────────────────────────

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "watchlist")
HISTORY_POINTS = 30

# Finnhub
FINNHUB_QUOTE = "https://finnhub.io/api/v1/quote"
BATCH_SIZE = 15  # 每批请求数（Finnhub 免费 60 calls/min）
BATCH_DELAY = 2  # 批次间隔（秒）
TICKER_DELAY = 1.1  # 单个请求间隔（秒），确保 <60/min

# Google Sheet (三个 tab: Market Structure, Industry/Thematic, Assets)
SHEET_ID = "1_xv9pPrxhx9A4OyhrvyTTJuKNXk8rn0m-eAWvnbdXWI"
SHEET_GIDS = [1071980810, 878537610, 1224425390]


def load_api_key() -> str:
    """从环境变量或 .env 文件加载 Finnhub API key。"""
    key = os.environ.get("FINNHUB_API_KEY", "").strip()
    if key:
        return key

    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("FINNHUB_API_KEY="):
                    key = line.split("=", 1)[1].strip().strip("'\"")
                    if key and "your_api_key_here" not in key:
                        return key
    return ""


# ─── Finnhub: 实时报价 ───────────────────────────────────

def fetch_quotes(tickers: list, api_key: str) -> dict:
    """
    批量获取 ETF 实时报价。
    返回: {ticker: {"price": float, "change_pct": float}}
    """
    results = {}
    total = len(tickers)

    for i in range(0, total, BATCH_SIZE):
        batch = tickers[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        print(f"  Quotes batch {batch_num}: {len(batch)} tickers")

        for ticker in batch:
            try:
                resp = requests.get(
                    FINNHUB_QUOTE,
                    params={"symbol": ticker, "token": api_key},
                    timeout=10,
                )
                resp.raise_for_status()
                data = resp.json()

                if data.get("c") and data.get("c") > 0:
                    results[ticker] = {
                        "price": round(data["c"], 2),
                        "change_pct": round(data.get("dp", 0.0), 2),
                    }
                else:
                    print(f"    SKIP: {ticker} — 无报价数据")
            except Exception as e:
                print(f"    ERROR: {ticker} — {e}")

            time.sleep(TICKER_DELAY)

        if i + BATCH_SIZE < total:
            time.sleep(BATCH_DELAY)

    return results


# ─── Google Sheet: REL 数据 ───────────────────────────────

def fetch_all_sheet_tabs() -> dict:
    """下载并合并三个 Sheet tab 的 REL 数据。"""
    print("Fetching Google Sheet (3 tabs)...")
    merged = {}

    for gid in SHEET_GIDS:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            tab_data = parse_sheet_rel(resp.text)
            # 合并，已有数据的不覆盖（第一个 tab 优先）
            for ticker, data in tab_data.items():
                if ticker not in merged:
                    merged[ticker] = data
        except Exception as e:
            print(f"  WARNING: Sheet tab {gid} 获取失败 ({e})", file=sys.stderr)

    return merged


def parse_sheet_rel(csv_text: str) -> dict:
    """
    解析 Google Sheet 获取 REL 和 Rank 数据。

    实际 Sheet 列结构 (0-indexed):
    0: 空, 1: 空, 2: Ticker, 3: Name, 4: Price, 5: 1D%,
    6: 60-Day Trend, 7: R20, 8: R60, 9: R120, 10: Rank,
    11: REL5, 12: REL20, 13: REL60, 14: REL120,
    15: YTD (From 2025-12-31), 16: 空, 17: Tradetime
    """
    reader = csv.reader(io.StringIO(csv_text))
    rows = list(reader)

    result = {}

    def safe_float(val, default=0.0):
        try:
            clean = val.strip().replace("%", "").replace(",", "")
            return float(clean) if clean else default
        except (ValueError, IndexError):
            return default

    def safe_int(val, default=0):
        try:
            clean = val.strip().replace(",", "")
            return int(float(clean)) if clean else default
        except (ValueError, IndexError):
            return default

    for row in rows:
        if len(row) < 11:
            continue

        ticker = row[2].strip().upper() if len(row) > 2 else ""
        if not ticker or ticker not in ALL_TICKERS:
            continue

        result[ticker] = {
            "rel": {
                "rel_5": safe_float(row[11]),
                "rel_20": safe_float(row[12]),
                "rel_60": safe_float(row[13]),
                "rel_120": safe_float(row[14]),
            },
            "rank": {
                "r_20": safe_int(row[7]),
                "r_60": safe_int(row[8]),
                "r_120": safe_int(row[9]),
            },
            "ytd": safe_float(row[15]),
        }

    return result


# ─── yfinance: 计算 REL 回退 ──────────────────────────────

def compute_rel_with_yfinance(missing_tickers: list) -> dict:
    """
    用 yfinance 下载历史价格，计算 REL（相对 SPY 的超额收益）。
    返回: {ticker: {"rel": {...}, "rank": {...}, "ytd": float}}

    REL_n = ETF_n日收益率 - SPY_n日收益率
    """
    if not missing_tickers:
        return {}

    periods = [5, 20, 60, 120]
    # 需要多取一些数据点确保有足够交易日
    lookback_days = 200
    end_date = datetime.now()
    start_date = end_date - timedelta(days=lookback_days)

    # 下载所有缺失 ticker + SPY 的历史数据
    all_symbols = list(set(missing_tickers + ["SPY"]))
    print(f"  yfinance: 下载 {len(all_symbols)} 个标的的历史数据...")

    try:
        data = yf.download(
            all_symbols,
            start=start_date.strftime("%Y-%m-%d"),
            end=end_date.strftime("%Y-%m-%d"),
            progress=False,
            auto_adjust=True,
        )
    except Exception as e:
        print(f"  WARNING: yfinance 下载失败 ({e})", file=sys.stderr)
        return {}

    if data.empty:
        print("  WARNING: yfinance 返回空数据", file=sys.stderr)
        return {}

    # 提取收盘价
    close = data["Close"] if "Close" in data.columns else pd.DataFrame()

    # 如果只有单个 ticker，yfinance 返回 Series 而非 DataFrame
    if isinstance(close, pd.Series):
        close = close.to_frame(name=all_symbols[0])

    if close.empty or "SPY" not in close.columns:
        print("  WARNING: 无 SPY 数据，无法计算 REL", file=sys.stderr)
        return {}

    spy_close = close["SPY"].dropna()

    result = {}
    for ticker in missing_tickers:
        if ticker not in close.columns:
            continue

        ticker_close = close[ticker].dropna()
        if len(ticker_close) < 5:
            continue

        rel_data = {}
        rank_data = {}
        for period in periods:
            if len(ticker_close) < period or len(spy_close) < period:
                rel_data[f"rel_{period}"] = 0.0
                rank_data[f"r_{period}"] = 0
                continue

            # 收益率 = (最新价 - N日前价) / N日前价 * 100
            etf_ret = (ticker_close.iloc[-1] / ticker_close.iloc[-period] - 1) * 100
            spy_ret = (spy_close.iloc[-1] / spy_close.iloc[-period] - 1) * 100
            rel = round(etf_ret - spy_ret, 2)
            rel_data[f"rel_{period}"] = rel

            # 简化 Rank: 基于 REL 绝对值排名（100分制近似）
            rank_data[f"r_{period}"] = 50  # 占位，后续可优化

        # YTD 收益率
        ytd_ret = 0.0
        year_start = f"{end_date.year}-01-01"
        ticker_ytd = ticker_close[ticker_close.index >= year_start]
        if len(ticker_ytd) >= 2:
            ytd_ret = round((ticker_ytd.iloc[-1] / ticker_ytd.iloc[0] - 1) * 100, 2)

        result[ticker] = {
            "rel": rel_data,
            "rank": rank_data,
            "ytd": ytd_ret,
        }

    print(f"  yfinance: 计算了 {len(result)} 个 ticker 的 REL")
    return result


# ─── 数据合并与输出 ───────────────────────────────────────

def build_etf_data(ticker: str, quote: dict, sheet_data: dict) -> dict:
    """合并 Finnhub 报价和 Sheet REL 数据。"""
    group_key = get_group_key(ticker)
    name, name_en = "", ""
    if group_key and group_key in ETF_GROUPS:
        for etf in ETF_GROUPS[group_key]["etfs"]:
            if etf["ticker"] == ticker:
                name, name_en = etf["name"], etf["name_en"]
                break

    rel = sheet_data.get("rel", {"rel_5": 0, "rel_20": 0, "rel_60": 0, "rel_120": 0})
    rank = sheet_data.get("rank", {"r_20": 0, "r_60": 0, "r_120": 0})
    ytd = sheet_data.get("ytd", 0.0)

    # 生成模拟走势（基于价格和 REL 趋势），后续可接入真实历史
    history = generate_trend_history(quote["price"], quote["change_pct"], rel)

    return {
        "ticker": ticker,
        "name": name,
        "name_en": name_en,
        "price": quote["price"],
        "change_pct": quote["change_pct"],
        "rel": rel,
        "rank": rank,
        "ytd": ytd,
        "has_cn_mapping": ticker in CN_LINKED_TICKERS,
        "group": group_key,
        "history": history,
    }


def generate_trend_history(price: float, change_pct: float, rel: dict) -> list:
    """基于价格和 REL 趋势生成近似走势。"""
    base = price / (1 + change_pct / 100)
    rel_20 = rel.get("rel_20", 0)
    data = []
    for i in range(HISTORY_POINTS):
        progress = i / (HISTORY_POINTS - 1)
        trend = (change_pct / 100) * base * progress
        rel_trend = (rel_20 / 100) * base * progress * 0.3
        noise = (hash(str(i)) % 100 - 50) / 100 * base * 0.005
        data.append(round(base + trend + rel_trend + noise, 2))
    return data


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
        "date": datetime.now(BJT).strftime("%Y-%m-%d"),
        "updated_at": datetime.now(BJT).strftime("%Y-%m-%dT%H:%M:%S+08:00"),
        "total_etfs": len(etfs),
        "groups": groups,
    }


def run_fetch(output_dir: str = None):
    """主入口：Finnhub 报价 + Sheet REL → 合并输出 JSON。"""
    api_key = load_api_key()
    if not api_key:
        print("ERROR: 未找到 FINNHUB_API_KEY", file=sys.stderr)
        return None

    if output_dir is None:
        output_dir = OUTPUT_DIR
    output_dir = os.path.abspath(output_dir)

    try:
        # 1. Finnhub 获取实时报价
        print(f"Fetching quotes for {len(ALL_TICKERS)} tickers...")
        quotes = fetch_quotes(ALL_TICKERS, api_key)
        print(f"  Got {len(quotes)} quotes")

        # 2. Google Sheet 获取 REL 数据（三个 tab 合并）
        sheet_rel = {}
        try:
            sheet_rel = fetch_all_sheet_tabs()
            print(f"  Got REL data for {len(sheet_rel)} tickers from Sheet")
        except Exception as e:
            print(f"  WARNING: Sheet 获取失败 ({e})，REL 数据将使用默认值", file=sys.stderr)

        # 3. yfinance 回退：为 Sheet 未覆盖的 ticker 计算 REL
        missing_tickers = [t for t in ALL_TICKERS if t not in sheet_rel and t in quotes]
        if missing_tickers:
            print(f"  Computing REL for {len(missing_tickers)} uncovered tickers via yfinance...")
            yf_rel = compute_rel_with_yfinance(missing_tickers)
            sheet_rel.update(yf_rel)

        # 3. 合并数据
        etfs = []
        for ticker in ALL_TICKERS:
            if ticker not in quotes:
                print(f"  SKIP: {ticker} — 无报价")
                continue
            etf = build_etf_data(ticker, quotes[ticker], sheet_rel.get(ticker, {}))
            etfs.append(etf)

        report = build_output(etfs)

        # 4. 输出 JSON
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{report['date']}.json")

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
