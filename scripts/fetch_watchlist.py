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
from datetime import datetime

import requests

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

# Google Sheet
SHEET_ID = "1_xv9pPrxhx9A4OyhrvyTTJuKNXk8rn0m-eAWvnbdXWI"
SHEET_GID = "1071980810"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={SHEET_GID}"


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

def fetch_sheet_csv() -> str:
    """下载 Google Sheet CSV。"""
    print("Fetching Google Sheet...")
    resp = requests.get(CSV_URL, timeout=30)
    resp.raise_for_status()
    return resp.text


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
        "date": datetime.now().strftime("%Y-%m-%d"),
        "updated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00"),
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

        # 2. Google Sheet 获取 REL 数据
        sheet_rel = {}
        try:
            csv_text = fetch_sheet_csv()
            sheet_rel = parse_sheet_rel(csv_text)
            print(f"  Got REL data for {len(sheet_rel)} tickers from Sheet")
        except Exception as e:
            print(f"  WARNING: Sheet 获取失败 ({e})，REL 数据将使用默认值", file=sys.stderr)

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
