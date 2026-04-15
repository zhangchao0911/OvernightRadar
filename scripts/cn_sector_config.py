"""
A股 ETF 市场观察配置
含：宽基、行业、主题、跨境、商品/债券 五大分组
同指数 ETF 优先选规模最大的产品
"""
from typing import Dict, Optional

# ─── ETF 分组定义 ─────────────────────────────────────────

CN_ETF_GROUPS: Dict[str, Dict] = {
    "broad": {
        "display_name": "宽基指数",
        "etfs": [
            {"code": "510300", "name": "沪深300ETF", "note": "华泰柏瑞 规模最大"},
            {"code": "510500", "name": "中证500ETF", "note": "华夏"},
            {"code": "512100", "name": "中证1000ETF", "note": "南方"},
            {"code": "159915", "name": "创业板ETF", "note": "易方达 规模最大"},
            {"code": "588000", "name": "科创50ETF", "note": "华夏 规模最大"},
            {"code": "510050", "name": "上证50ETF", "note": "华夏"},
            {"code": "159901", "name": "深证100ETF", "note": "易方达"},
            {"code": "159338", "name": "中证A500ETF", "note": "华夏 2025爆款"},
            {"code": "562660", "name": "中证2000ETF", "note": "建信"},
            {"code": "159967", "name": "创50ETF", "note": "华安"},
        ],
    },
    "industry": {
        "display_name": "行业ETF",
        "etfs": [
            {"code": "512480", "name": "半导体ETF", "note": "国联安"},
            {"code": "159995", "name": "芯片ETF", "note": "华夏"},
            {"code": "159346", "name": "存储芯片ETF", "note": "易方达"},
            {"code": "512010", "name": "医药ETF", "note": "国泰"},
            {"code": "512170", "name": "医疗ETF", "note": "华宝"},
            {"code": "512690", "name": "酒ETF", "note": "鹏华"},
            {"code": "159928", "name": "消费ETF", "note": "华夏"},
            {"code": "512660", "name": "军工ETF", "note": "国泰"},
            {"code": "159819", "name": "航天ETF", "note": "富国"},
            {"code": "512720", "name": "计算机ETF", "note": "国泰"},
            {"code": "512980", "name": "传媒ETF", "note": "鹏华"},
            {"code": "515050", "name": "通信ETF", "note": "华夏"},
            {"code": "512400", "name": "有色ETF", "note": "华宝"},
            {"code": "516160", "name": "新能源ETF", "note": "华夏"},
            {"code": "515790", "name": "光伏ETF", "note": "华泰柏瑞"},
            {"code": "515030", "name": "新能源车ETF", "note": "华夏"},
            {"code": "512200", "name": "房地产ETF", "note": "南方"},
            {"code": "159766", "name": "旅游ETF", "note": "富国"},
            {"code": "512800", "name": "银行ETF", "note": "南方"},
            {"code": "512070", "name": "非银ETF", "note": "易方达"},
        ],
    },
    "thematic": {
        "display_name": "主题ETF",
        "etfs": [
            {"code": "159770", "name": "机器人ETF", "note": "国泰"},
            {"code": "515070", "name": "人工智能ETF", "note": "易方达"},
            {"code": "510880", "name": "红利ETF", "note": "华夏"},
            {"code": "562030", "name": "央企ETF", "note": "华夏"},
            {"code": "159605", "name": "A50ETF", "note": "易方达 MSCI中国A50"},
            {"code": "159992", "name": "创新药ETF", "note": "银华"},
            {"code": "562500", "name": "科创芯片ETF", "note": "华夏"},
            {"code": "588030", "name": "科创信息ETF", "note": "华夏"},
            {"code": "159869", "name": "游戏ETF", "note": "华夏"},
            {"code": "159632", "name": "新材料ETF", "note": "华宝"},
            {"code": "159891", "name": "沪深300成长ETF", "note": "易方达"},
            {"code": "159845", "name": "碳中和ETF", "note": "易方达"},
        ],
    },
    "cross_border": {
        "display_name": "跨境ETF",
        "etfs": [
            {"code": "513100", "name": "纳指100ETF", "note": "国泰"},
            {"code": "513500", "name": "标普500ETF", "note": "博时"},
            {"code": "159509", "name": "纳指科技ETF", "note": "华夏"},
            {"code": "513090", "name": "标普信息科技ETF", "note": "易方达"},
            {"code": "513520", "name": "日经ETF", "note": "华夏"},
            {"code": "513030", "name": "德国ETF", "note": "华夏"},
            {"code": "513080", "name": "法国CAC40ETF", "note": "华安"},
            {"code": "513000", "name": "东南亚科技ETF", "note": "南方"},
            {"code": "159920", "name": "恒生ETF", "note": "华夏"},
            {"code": "513180", "name": "恒生科技ETF", "note": "华夏"},
            {"code": "513060", "name": "恒生医疗ETF", "note": "易方达"},
            {"code": "513050", "name": "港股通互联网ETF", "note": "易方达"},
        ],
    },
    "commodity": {
        "display_name": "商品/债券",
        "etfs": [
            {"code": "518880", "name": "黄金ETF", "note": "华安 规模最大"},
            {"code": "159937", "name": "博时黄金ETF", "note": "博时"},
            {"code": "159985", "name": "豆粕ETF", "note": "华夏"},
            {"code": "561560", "name": "有色ETF", "note": "华夏"},
            {"code": "511010", "name": "国债ETF", "note": "国泰"},
            {"code": "511260", "name": "十年国债ETF", "note": "博时"},
            {"code": "511380", "name": "可转债ETF", "note": "博时"},
            {"code": "159927", "name": "中证转债ETF", "note": "易方达"},
        ],
    },
}

# ─── 基准指数 ─────────────────────────────────────────────────────

BENCHMARKS = {
    "hs300": {"code": "000300", "name": "沪深300", "name_en": "CSI 300"},
    "zz500": {"code": "000905", "name": "中证500", "name_en": "CSI 500"},
}

DEFAULT_BENCHMARK = "hs300"

# ─── 辅助函数 ─────────────────────────────────────────────────────

# 所有 ETF 代码 → 信息映射
_ALL_ETF_MAP: Dict[str, Dict] = {}
for _group_key, _group_val in CN_ETF_GROUPS.items():
    for _etf in _group_val["etfs"]:
        _ALL_ETF_MAP[_etf["code"]] = {
            **_etf,
            "group": _group_key,
            "group_name": _group_val["display_name"],
        }

ALL_ETF_CODES = list(_ALL_ETF_MAP.keys())


def get_etf_by_code(code: str) -> Optional[Dict]:
    """根据代码获取 ETF 信息"""
    return _ALL_ETF_MAP.get(code)


def get_benchmark_info(benchmark_key: str) -> Optional[Dict]:
    """获取基准指数信息"""
    return BENCHMARKS.get(benchmark_key)
