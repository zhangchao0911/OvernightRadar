"""
美股涨了，A股呢？ — 每日数据采集与统计计算脚本
用法: python scripts/run_daily.py
"""
import json
import os
import sys
import time
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
        "supply_chain": [
            {"name": "中际旭创", "code": "300308"},
            {"name": "北方华创", "code": "002371"},
            {"name": "中微公司", "code": "688012"},
        ],
    },
    {
        "id": 2,
        "us_name": "科技",
        "us_etf": "XLK",
        "cn_name": "电子",
        "cn_index": "801080",
        "cn_etf_name": "科技ETF",
        "cn_etf_code": "515000",
        "supply_chain": [
            {"name": "立讯精密", "code": "002475"},
            {"name": "歌尔股份", "code": "002241"},
            {"name": "京东方A", "code": "000725"},
        ],
    },
    {
        "id": 3,
        "us_name": "新能源车",
        "us_etf": "DRIV",
        "cn_name": "汽车",
        "cn_index": "801880",
        "cn_etf_name": "新能源车ETF",
        "cn_etf_code": "515030",
        "supply_chain": [
            {"name": "宁德时代", "code": "300750"},
            {"name": "拓普集团", "code": "601689"},
            {"name": "比亚迪", "code": "002594"},
        ],
    },
    {
        "id": 4,
        "us_name": "AI/算力",
        "us_etf": "THNQ",
        "cn_name": "计算机",
        "cn_index": "801750",
        "cn_etf_name": "计算机ETF",
        "cn_etf_code": "512720",
        "supply_chain": [
            {"name": "寒武纪", "code": "688256"},
            {"name": "海光信息", "code": "688041"},
            {"name": "浪潮信息", "code": "000977"},
        ],
    },
    {
        "id": 5,
        "us_name": "黄金",
        "us_etf": "GLD",
        "cn_name": "有色金属",
        "cn_index": "801050",
        "cn_etf_name": "黄金ETF",
        "cn_etf_code": "518880",
        "supply_chain": [
            {"name": "山东黄金", "code": "600547"},
            {"name": "紫金矿业", "code": "601899"},
            {"name": "中金黄金", "code": "600489"},
        ],
    },
    {
        "id": 6,
        "us_name": "机器人",
        "us_etf": "BOTZ",
        "cn_name": "机械设备",
        "cn_index": "801890",
        "cn_etf_name": "机器人ETF",
        "cn_etf_code": "159770",
        "supply_chain": [
            {"name": "拓斯达", "code": "300607"},
            {"name": "绿的谐波", "code": "688017"},
            {"name": "埃斯顿", "code": "002747"},
        ],
    },
    {
        "id": 7,
        "us_name": "商业航天",
        "us_etf": "UFO",
        "cn_name": "国防军工",
        "cn_index": "801740",
        "cn_etf_name": "航天ETF",
        "cn_etf_code": "159819",
        "supply_chain": [
            {"name": "中国卫星", "code": "600118"},
            {"name": "航天电器", "code": "002025"},
            {"name": "中科星图", "code": "688568"},
        ],
    },
    {
        "id": 8,
        "us_name": "存储",
        "us_etf": "DRAM",
        "cn_name": "存储",
        "cn_index": "",
        "cn_etf_name": "存储",
        "cn_etf_code": "",
        "supply_chain": [
            {"name": "兆易创新", "code": "603986"},
            {"name": "北京君正", "code": "300223"},
            {"name": "东芯股份", "code": "688110"},
        ],
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


# ─── V1.1 新增计算函数 ─────────────────────────────────────

def calc_relative_strength(sector_change: float, spy_change: float) -> float:
    """板块相对强度 = 板块涨跌幅 - 标普500涨跌幅。"""
    return round(sector_change - spy_change, 2)


def calc_volatility_surprise(returns: pd.Series, window: int = 20) -> dict:
    """
    波动率偏离：当日波动相对近期日均波动的倍数。

    返回:
        {"daily_vol_20d": float, "vol_multiple": float, "is_abnormal": bool}
    """
    if len(returns) < 2:
        return {"daily_vol_20d": 0.0, "vol_multiple": 0.0, "is_abnormal": False}

    recent = returns.abs().iloc[-window:] if len(returns) >= window else returns.abs()
    daily_vol = float(recent.mean())
    today_abs = float(abs(returns.iloc[-1]))
    vol_multiple = round(today_abs / daily_vol, 1) if daily_vol > 0 else 0.0

    return {
        "daily_vol_20d": round(daily_vol, 2),
        "vol_multiple": vol_multiple,
        "is_abnormal": vol_multiple > 2.0,
    }


def calc_trend(returns: pd.Series) -> dict:
    """
    连涨/连跌趋势。

    返回:
        {"direction": "up"/"down"/"flat", "consecutive_days": int, "cumulative_pct": float}
    """
    if len(returns) < 1:
        return {"direction": "flat", "consecutive_days": 0, "cumulative_pct": 0.0}

    last = returns.iloc[-1]
    if abs(last) < 0.01:
        return {"direction": "flat", "consecutive_days": 0, "cumulative_pct": 0.0}

    direction = "up" if last > 0 else "down"
    consecutive = 0
    cumulative = 0.0

    for i in range(len(returns) - 1, -1, -1):
        r = returns.iloc[i]
        if direction == "up" and r > 0:
            consecutive += 1
            cumulative += r
        elif direction == "down" and r < 0:
            consecutive += 1
            cumulative += r
        else:
            break

    return {
        "direction": direction,
        "consecutive_days": consecutive,
        "cumulative_pct": round(cumulative, 2),
    }


def calc_sentiment(
    relative_strength: float,
    vol_multiple: float,
    direction: str,
    consecutive_days: int,
) -> dict:
    """
    情绪等级判定。从等级4开始往下匹配，命中即止。

    返回:
        {"sentiment": str, "sentiment_level": int}
    """
    # 等级 4: 强烈看多
    if relative_strength > 2.0 and (
        vol_multiple > 2.0 or (direction == "up" and consecutive_days >= 3)
    ):
        return {"sentiment": "强烈看多", "sentiment_level": 4}
    # 等级 3: 偏多
    if relative_strength > 0.5 and (
        vol_multiple > 1.5 or (direction == "up" and consecutive_days >= 2)
    ):
        return {"sentiment": "偏多", "sentiment_level": 3}
    # 等级 0: 强烈看空
    if relative_strength < -2.0 and (
        vol_multiple > 2.0 or (direction == "down" and consecutive_days >= 3)
    ):
        return {"sentiment": "强烈看空", "sentiment_level": 0}
    # 等级 1: 偏空
    if relative_strength < -0.5 and (
        vol_multiple > 1.5 or (direction == "down" and consecutive_days >= 2)
    ):
        return {"sentiment": "偏空", "sentiment_level": 1}
    # 等级 2: 中性
    return {"sentiment": "中性", "sentiment_level": 2}


def build_market_summary(sectors: list) -> str:
    """市场总览文案：X强Y弱Z中性。"""
    strong = sum(1 for s in sectors if s.get("sentiment_level", 2) >= 3)
    weak = sum(1 for s in sectors if s.get("sentiment_level", 2) <= 1)
    neutral = len(sectors) - strong - weak
    return f"{strong}强{weak}弱{neutral}中性"


# ─── 数据采集 ─────────────────────────────────────────────

def fetch_us_data(tickers: list, days: int = 150) -> dict:
    """
    拉取美股 ETF 日线数据。
    返回: {ticker: DataFrame(date_index, close)} ，每个包含最近 `days` 个交易日。
    """
    import yfinance as yf

    end_date = datetime.now()
    start_date = end_date - timedelta(days=int(days * 1.8))

    raw = yf.download(
        tickers=" ".join(tickers),
        start=start_date.strftime("%Y-%m-%d"),
        end=end_date.strftime("%Y-%m-%d"),
        auto_adjust=True,
        progress=False,
    )

    result = {}
    for ticker in tickers:
        try:
            if len(tickers) > 1:
                close = raw[("Close", ticker)].dropna()
            else:
                close = raw["Close"].dropna()
            df = pd.DataFrame({"close": close})
            df = df.tail(days)
            if len(df) > 1:
                result[ticker] = df
        except (KeyError, TypeError):
            print(f"WARNING: 无法获取 {ticker} 数据", file=sys.stderr)

    return result


def fetch_cn_index_data(index_code: str, days: int = 150):
    """
    拉取申万行业指数日线数据。
    返回: DataFrame(date_index, open, close)，最近 `days` 个交易日。失败返回 None。
    """
    import akshare as ak

    try:
        df = ak.index_hist_sw(
            symbol=index_code,
            period="day",
        )
        if df is None or df.empty:
            return None

        df = df.tail(days)
        # Rename columns - handle both possible column name formats
        col_map = {}
        for col in df.columns:
            if col in ("日期", "date"):
                col_map[col] = "date"
            elif col in ("开盘", "open"):
                col_map[col] = "open"
            elif col in ("收盘", "close"):
                col_map[col] = "close"
        df = df.rename(columns=col_map)

        if "date" not in df.columns:
            return None

        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date")
        # Only keep open and close columns
        keep_cols = [c for c in ["open", "close"] if c in df.columns]
        if not keep_cols:
            return None
        df = df[keep_cols].astype(float)
        return df
    except Exception as e:
        print(f"WARNING: 获取申万指数 {index_code} 失败: {e}", file=sys.stderr)
        return None


def fetch_cn_stocks(stock_codes: list) -> dict:
    """
    批量拉取 A 股个股最新涨跌幅。

    参数:
        stock_codes: 股票代码列表（6位数字字符串）

    返回:
        {code: change_pct} 最近一个交易日的涨跌幅
    """
    import akshare as ak

    result = {}
    for code in stock_codes:
        try:
            df = ak.stock_zh_a_hist(symbol=code, period="daily", adjust="qfq")
            if df is not None and len(df) >= 2:
                df = df.tail(2)
                close_col = None
                for col in df.columns:
                    if col in ("收盘", "close"):
                        close_col = col
                        break
                if close_col:
                    prev_close = float(df[close_col].iloc[0])
                    latest_close = float(df[close_col].iloc[1])
                    change_pct = round(
                        (latest_close - prev_close) / prev_close * 100, 2
                    )
                    result[code] = change_pct
            time.sleep(0.3)
        except Exception as e:
            print(
                f"WARNING: 获取个股 {code} 失败: {e}", file=sys.stderr
            )
    return result


def compute_daily_return(close_series: pd.Series) -> pd.Series:
    """计算日涨跌幅（%）。"""
    return close_series.pct_change() * 100


# ─── 主运行逻辑 ───────────────────────────────────────────

def run_daily(output_dir: str = "data/results"):
    """
    V1.1 主入口：采集数据 → 计算新指标 → 输出 JSON。
    返回生成的报告 dict，失败返回 None。
    """
    # ─── 1. 拉取美股数据（8 板块 ETF + 三大指数） ─────────────
    # 使用真实指数代码，而非 ETF（QQQ 追踪 Nasdaq-100，非 Nasdaq Composite）
    index_tickers = {"^GSPC": "sp500", "^IXIC": "nasdaq", "^DJI": "dow"}
    tickers = [s["us_etf"] for s in SECTOR_MAP] + list(index_tickers.keys())

    print("Fetching US data...")
    us_data = fetch_us_data(tickers)
    if not us_data:
        print("ERROR: 无美股数据", file=sys.stderr)
        return None

    # 确定报告日期：最近的美股交易日
    latest_dates = [df.index[-1] for df in us_data.values()]
    report_date = max(latest_dates).strftime("%Y-%m-%d")

    # 检查今天是否已经生成过
    output_path = os.path.join(output_dir, f"{report_date}.json")
    if os.path.exists(output_path):
        print(f"SKIP: {output_path} already exists")
        return None

    # ─── 2. 提取市场指数涨跌幅 ─────────────────────────────
    market_indices = {}
    index_map = index_tickers
    for ticker, key in index_map.items():
        if ticker in us_data:
            returns = compute_daily_return(us_data[ticker]["close"]).dropna()
            market_indices[key] = {
                "change_pct": round(float(returns.iloc[-1]), 2)
            }

    spy_change = market_indices.get("sp500", {}).get("change_pct", 0.0)

    # ─── 3. 拉取 A 股个股数据 ──────────────────────────────
    all_stock_codes = []
    for sector in SECTOR_MAP:
        for stock in sector["supply_chain"]:
            all_stock_codes.append(stock["code"])

    print(f"Fetching {len(all_stock_codes)} CN stocks...")
    cn_stock_changes = fetch_cn_stocks(all_stock_codes)

    # ─── 4. 逐板块计算 ─────────────────────────────────────
    sectors = []

    for sector in SECTOR_MAP:
        us_ticker = sector["us_etf"]

        if us_ticker not in us_data:
            print(f"SKIP: {sector['us_name']} 无美股数据")
            continue

        # 美股涨跌幅序列
        us_returns = compute_daily_return(us_data[us_ticker]["close"]).dropna()

        if len(us_returns) < 2:
            print(f"SKIP: {sector['us_name']} 数据不足")
            continue

        us_change_pct = round(float(us_returns.iloc[-1]), 2)

        # 计算新指标
        rs = calc_relative_strength(us_change_pct, spy_change)
        vol = calc_volatility_surprise(us_returns)
        trend = calc_trend(us_returns)
        sentiment = calc_sentiment(
            rs, vol["vol_multiple"], trend["direction"], trend["consecutive_days"]
        )

        # 产业链标的涨跌幅
        supply_chain = []
        for stock in sector["supply_chain"]:
            change_pct = cn_stock_changes.get(stock["code"])
            supply_chain.append(
                {
                    "name": stock["name"],
                    "code": stock["code"],
                    "change_pct": change_pct,
                }
            )

        sectors.append(
            {
                "us_name": sector["us_name"],
                "us_etf": sector["us_etf"],
                "us_change_pct": us_change_pct,
                "relative_strength": rs,
                "volatility": vol,
                "trend": trend,
                "cn_name": sector["cn_name"],
                "cn_etf_name": sector["cn_etf_name"],
                "cn_etf_code": sector["cn_etf_code"],
                "sentiment": sentiment["sentiment"],
                "sentiment_level": sentiment["sentiment_level"],
                "supply_chain": supply_chain,
            }
        )

    # ─── 5. 排序：情绪等级降序，同等级按相对强度绝对值降序 ─────
    sectors.sort(
        key=lambda s: (s["sentiment_level"], abs(s["relative_strength"])),
        reverse=True,
    )

    # ─── 6. 组装报告 ──────────────────────────────────────
    report = {
        "date": report_date,
        "weekday": _weekday_cn(report_date),
        "market_indices": market_indices,
        "market_summary": build_market_summary(sectors),
        "sectors": sectors,
        "updated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00"),
    }

    # ─── 7. 输出 JSON ────────────────────────────────────
    os.makedirs(output_dir, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"OK: {output_path} ({len(sectors)} sectors)")
    return report


def _weekday_cn(date_str: str) -> str:
    """日期字符串 → 中文星期"""
    weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return weekdays[dt.weekday()]


if __name__ == "__main__":
    run_daily()
