"""
Market Watchlist 数据获取脚本
从 Google Sheet CSV 导出读取 ETF 数据，计算 REL，输出 JSON。
用法: python scripts/fetch_watchlist.py
"""
import csv
import io
import json
import os
import sys
from datetime import datetime

import requests

sys.path.insert(0, os.path.dirname(__file__))
from etf_config import ETF_GROUPS, CN_LINKED_TICKERS, ALL_TICKERS, get_group_key

# ─── 配置 ─────────────────────────────────────────────────

SHEET_ID = "1_xv9pPrxhx9A4OyhrvyTTJuKNXk8rn0m-eAWvnbdXWI"
SHEET_GID = "1071980810"  # Market Watchlist sheet gid
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={SHEET_GID}"

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "watchlist")


# ─── 数据获取 ─────────────────────────────────────────────

def fetch_sheet_csv(url: str = CSV_URL) -> str:
    """下载 Google Sheet CSV 内容。"""
    print(f"Fetching Google Sheet...")
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.text


def parse_sheet_data(csv_text: str) -> list:
    """
    解析 Google Sheet CSV 为 ETF 数据列表。

    Sheet 结构（预期列顺序）：
    A: (空/序号), B: Ticker, C: Name, D: Price, E: 1D%,
    F: R20, G: R60, H: R120, I: Rank,
    J: REL5, K: REL20, L: REL60, M: REL120,
    N: From 2025-12-31 (YTD), ...
    P: Tradetime
    """
    reader = csv.reader(io.StringIO(csv_text))
    rows = list(reader)

    etfs = []
    for row in rows:
        # 跳过空行和标题行
        if len(row) < 5:
            continue

        ticker = row[1].strip().upper() if len(row) > 1 else ""
        if not ticker or ticker not in ALL_TICKERS:
            continue

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

        etf_data = {
            "ticker": ticker,
            "name": row[2].strip() if len(row) > 2 else "",
            "price": safe_float(row[3]) if len(row) > 3 else 0.0,
            "change_pct": safe_float(row[4]) if len(row) > 4 else 0.0,
            "rank": {
                "r_20": safe_int(row[5]) if len(row) > 5 else 0,
                "r_60": safe_int(row[6]) if len(row) > 6 else 0,
                "r_120": safe_int(row[7]) if len(row) > 7 else 0,
            },
            "rel": {
                "rel_5": safe_float(row[9]) if len(row) > 9 else 0.0,
                "rel_20": safe_float(row[10]) if len(row) > 10 else 0.0,
                "rel_60": safe_float(row[11]) if len(row) > 11 else 0.0,
                "rel_120": safe_float(row[12]) if len(row) > 12 else 0.0,
            },
            "ytd": safe_float(row[13]) if len(row) > 13 else 0.0,
            "has_cn_mapping": ticker in CN_LINKED_TICKERS,
            "group": get_group_key(ticker),
        }
        etfs.append(etf_data)

    return etfs


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
    """主入口：获取数据 → 解析 → 输出 JSON。"""
    if output_dir is None:
        output_dir = OUTPUT_DIR

    output_dir = os.path.abspath(output_dir)

    try:
        csv_text = fetch_sheet_csv()
        etfs = parse_sheet_data(csv_text)

        if not etfs:
            print("WARNING: 未解析到有效 ETF 数据", file=sys.stderr)
            return None

        report = build_output(etfs)

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

    except requests.RequestException as e:
        print(f"ERROR: 获取 Google Sheet 失败: {e}", file=sys.stderr)
        return None


if __name__ == "__main__":
    run_fetch()
