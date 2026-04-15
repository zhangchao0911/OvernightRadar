#!/usr/bin/env python3
"""
A股收盘后数据更新 — 更新个股涨幅和申万行业指数

在北京时间 15:30 运行（A股 15:00 收盘后），更新：
1. 隔夜雷达板块中的 A 股产业链个股涨幅 (results/{date}.json)
2. A股市场观察数据 (cn_watchlist/{date}.json)

用法: python scripts/update_cn_close.py
"""
import json
import os
import sys
from datetime import datetime, timedelta, timezone

BJT = timezone(timedelta(hours=8))


def get_today_str() -> str:
    """获取北京时间今天的日期字符串"""
    return datetime.now(BJT).strftime("%Y-%m-%d")


def is_weekday(date_str: str) -> bool:
    """判断是否为工作日（周一至周五）"""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.weekday() < 5


def fetch_stock_prices(stock_codes: list) -> dict:
    """
    批量获取 A 股个股当日涨跌幅。
    优先使用实时行情接口，失败后逐个回退。

    Returns:
        {code: change_pct}
    """
    import akshare as ak

    result = {}

    # 批量实时行情
    try:
        df = ak.stock_zh_a_spot_em()
        if df is not None and not df.empty:
            code_col = None
            change_col = None
            for col in df.columns:
                if col in ("代码", "code"):
                    code_col = col
                if col in ("涨跌幅", "change_pct"):
                    change_col = col

            if code_col and change_col:
                code_set = set(stock_codes)
                matched = df[df[code_col].astype(str).isin(code_set)]
                for _, row in matched.iterrows():
                    code = str(row[code_col])
                    try:
                        result[code] = round(float(row[change_col]), 2)
                    except (ValueError, TypeError):
                        pass
                print(f"  批量获取: {len(result)}/{len(stock_codes)} 只股票")
    except Exception as e:
        print(f"  WARNING: 批量行情失败: {e}")

    # 逐个回退
    import time
    missing = [c for c in stock_codes if c not in result]
    if missing:
        print(f"  逐个回退: {len(missing)} 只")
        for code in missing:
            try:
                df = ak.stock_zh_a_hist(symbol=code, period="daily", adjust="qfq")
                if df is not None and len(df) >= 2:
                    df = df.tail(2)
                    close_col = next((c for c in df.columns if c in ("收盘", "close")), None)
                    if close_col:
                        prev = float(df[close_col].iloc[0])
                        curr = float(df[close_col].iloc[1])
                        result[code] = round((curr - prev) / prev * 100, 2)
                time.sleep(0.3)
            except Exception as e:
                print(f"  WARNING: {code} 失败: {e}")

    return result


def update_results(today: str) -> bool:
    """
    更新隔夜雷达 results 文件中的 A 股个股涨幅。
    """
    results_dir = os.path.join(os.path.dirname(__file__), "..", "data", "results")
    results_path = os.path.join(results_dir, f"{today}.json")

    if not os.path.exists(results_path):
        print(f"SKIP: {results_path} 不存在，跳过")
        return False

    with open(results_path, "r", encoding="utf-8") as f:
        report = json.load(f)

    # 收集所有股票代码
    all_codes = []
    for sector in report.get("sectors", []):
        for stock in sector.get("supply_chain", []):
            if stock.get("code"):
                all_codes.append(stock["code"])

    if not all_codes:
        print("无个股数据需要更新")
        return False

    print(f"更新 {len(all_codes)} 只个股涨幅...")
    prices = fetch_stock_prices(all_codes)

    # 更新数据
    updated = 0
    for sector in report.get("sectors", []):
        for stock in sector.get("supply_chain", []):
            code = stock.get("code")
            if code in prices:
                stock["change_pct"] = prices[code]
                updated += 1

    # 更新时间戳
    report["updated_at"] = datetime.now(BJT).strftime("%Y-%m-%dT%H:%M:%S+08:00")

    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"OK: results/{today}.json ({updated}/{len(all_codes)} 只已更新)")
    return True


def update_cn_watchlist(today: str) -> bool:
    """
    重新生成 A 股市场观察数据（覆盖已有文件）。
    """
    sys.path.insert(0, os.path.dirname(__file__))
    from fetch_cn_watchlist import run_fetch

    # 重新生成 A 股市场观察数据
    output_dir = os.path.join(os.path.dirname(__file__), "..", "data", "cn_watchlist")

    print("重新生成 A 股市场观察数据...")
    result = run_fetch(output_dir=output_dir, benchmark_key="hs300", force=True)

    if result:
        print(f"OK: cn_watchlist/{today}.json ({result.get('total_sectors', 0)} sectors)")
        return True
    else:
        print("WARNING: A股数据重新生成失败")
        return False


def main():
    today = get_today_str()
    print(f"A股收盘数据更新 — {today}")

    if not is_weekday(today):
        print("SKIP: 今天不是工作日")
        return

    results_ok = update_results(today)
    watchlist_ok = update_cn_watchlist(today)

    if results_ok or watchlist_ok:
        print("完成")
    else:
        print("无数据更新")
        sys.exit(1)


if __name__ == "__main__":
    main()
