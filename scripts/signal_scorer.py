"""
信号评分模块

核心功能：
1. calculate_score() - 计算信号得分（0-100分）
2. enhance_signal_with_analysis() - 增强信号，添加分析标记
3. get_level() - 根据分数获取等级（强/中/弱）
4. filter_signals() - 筛选和排序信号

评分维度（总分 100）：
1. 事件重要性 (0-30) - 宏观政策 > 行业动态 > 个股消息
2. 影响范围 (0-25) - 跨板块 > 单板块 > 个股
3. 定价程度 (0-25) - 未定价越高越好（反向指标）
4. 信号清晰度 (0-20) - 具体操作建议 > 模糊建议

使用示例：
    signal = {"title": "美联储降息", "direction": "利多", ...}
    enhanced = enhance_signal_with_analysis(signal)
    score, detail = calculate_score(enhanced)
    level = get_level(score)
"""
from typing import List, Dict, Tuple


# ─── 评分关键词配置 ───

MACRO_KEYWORDS = [
    "美联储", "降息", "加息", "通胀", "GDP", "非农", "政策", "国会",
    "政策", "降息", "加息", "通胀", "gdp"
]

INDUSTRY_KEYWORDS = [
    "行业", "板块", "etf", "ETF", "科技", "半导体", "新能源",
    "算力", "AI", "机器人"
]

UNDER_PRICED_KEYWORDS = [
    "未定价", "超预期", "意外", "出乎意料", "市场未预期"
]

PARTIALLY_PRICED_KEYWORDS = [
    "部分定价", "已部分反映", "部分反映"
]

# ─── 核心评分函数 ───


def calculate_score(signal: Dict) -> Tuple[int, Dict]:
    """
    计算信号得分

    评分逻辑：
    1. 事件重要性 (0-30): 宏观事件得分最高
    2. 影响范围 (0-25): 影响板块越多得分越高
    3. 定价程度 (0-25): 未定价得分高（反向指标）
    4. 信号清晰度 (0-20): 有明确操作建议得分高

    Args:
        signal: 信号字典，包含 title, direction, sectors, action, reason
                以及 is_macro, under_priced, clear_action 等增强字段

    Returns:
        (总分, 评分明细) 元组
    """
    score = 0
    detail = {
        "importance": 0,
        "reach": 0,
        "pricing": 0,
        "clarity": 0
    }

    # ─── 1. 事件重要性 (0-30) ───
    title = signal.get("title", "").lower()
    reason = signal.get("reason", "").lower()

    if signal.get("is_macro"):
        # 宏观事件
        detail["importance"] = 25
    elif any(kw in title or kw in reason for kw in MACRO_KEYWORDS):
        # 包含宏观关键词
        detail["importance"] = 22
    elif any(kw in title or kw in reason for kw in INDUSTRY_KEYWORDS):
        # 行业/板块事件
        detail["importance"] = 15
    else:
        # 个股或其他
        detail["importance"] = 8

    # ─── 2. 影响范围 (0-25) ───
    sectors = signal.get("sectors", [])
    sector_count = len(sectors)

    if sector_count >= 3:
        detail["reach"] = 20
    elif sector_count >= 2:
        detail["reach"] = 15
    elif sector_count >= 1:
        detail["reach"] = 10
    else:
        detail["reach"] = 5

    # ─── 3. 定价程度 (0-25) ───
    # 反向指标：未定价得分高，已定价得分低
    if signal.get("under_priced"):
        detail["pricing"] = 22
    elif any(kw in reason for kw in UNDER_PRICED_KEYWORDS):
        detail["pricing"] = 18
    elif any(kw in reason for kw in PARTIALLY_PRICED_KEYWORDS):
        detail["pricing"] = 10
    else:
        detail["pricing"] = 5

    # ─── 4. 信号清晰度 (0-20) ───
    action = signal.get("action", "")
    if signal.get("clear_action"):
        detail["clarity"] = 18
    elif "若" in action and any(kw in action for kw in [">", "<", "%"]):
        # 有条件判断
        detail["clarity"] = 15
    elif len(action) > 10:
        # 有一定建议
        detail["clarity"] = 10
    else:
        detail["clarity"] = 5

    # ─── 计算总分 ───
    score = sum(detail.values())

    return score, detail


def enhance_signal_with_analysis(signal: Dict) -> Dict:
    """
    增强信号，添加分析标记

    分析维度：
    1. is_macro: 是否为宏观事件
    2. under_priced: 是否未定价
    3. clear_action: 是否有清晰操作建议

    Args:
        signal: 原始信号

    Returns:
        增强后的信号（添加了 is_macro, under_priced, clear_action 字段）
    """
    title = signal.get("title", "")
    reason = signal.get("reason", "")
    action = signal.get("action", "")

    enhanced = signal.copy()

    # ─── 判断是否宏观 ───
    enhanced["is_macro"] = any(kw in title or kw in reason for kw in MACRO_KEYWORDS)

    # ─── 判断是否未定价 ───
    enhanced["under_priced"] = any(kw in reason for kw in UNDER_PRICED_KEYWORDS)

    # ─── 判断是否有清晰操作 ───
    enhanced["clear_action"] = (
        "若" in action and
        any(kw in action for kw in [">", "<", "%", "追", "观望", "止损"])
    )

    return enhanced


def get_level(score: int) -> str:
    """
    根据分数获取等级

    分级标准：
    - 强: >= 70 分
    - 中: >= 50 分
    - 弱: < 50 分

    Args:
        score: 信号得分 (0-100)

    Returns:
        等级字符串 ("强" / "中" / "弱")
    """
    if score >= 70:
        return "强"
    elif score >= 50:
        return "中"
    else:
        return "弱"


def filter_signals(
    signals: List[Dict],
    min_score: int = 50,
    max_count: int = 5
) -> List[Dict]:
    """
    筛选和排序信号

    筛选逻辑：
    1. 过滤低于 min_score 的信号
    2. 按分数降序排序
    3. 限制最多返回 max_count 条

    Args:
        signals: 原始信号列表
        min_score: 最低分数阈值（默认 50）
        max_count: 最大返回数量（默认 5）

    Returns:
        筛选后的信号列表
    """
    # ─── 过滤低分 ───
    filtered = [s for s in signals if s.get("score", 0) >= min_score]

    # ─── 按分数降序 ───
    filtered.sort(key=lambda x: x.get("score", 0), reverse=True)

    # ─── 限制数量 ───
    return filtered[:max_count]
