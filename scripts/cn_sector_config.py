"""
A股申万一级行业配置
数据源：AkShare 申万行业指数
"""
from typing import List, Dict, Optional

# ─── 申万一级行业定义 (31个) ─────────────────────────────────────────

SW_LEVEL1_SECTORS: List[Dict[str, str]] = [
    {"code": "801010", "name": "农林牧渔", "name_en": "Agriculture"},
    {"code": "801020", "name": "煤炭", "name_en": "Coal"},
    {"code": "801030", "name": "基础化工", "name_en": "Basic Chemicals"},
    {"code": "801040", "name": "钢铁", "name_en": "Steel"},
    {"code": "801050", "name": "有色金属", "name_en": "Non-Ferrous Metals"},
    {"code": "801080", "name": "电子", "name_en": "Electronics"},
    {"code": "801110", "name": "家用电器", "name_en": "Home Appliances"},
    {"code": "801120", "name": "食品饮料", "name_en": "Food & Beverage"},
    {"code": "801130", "name": "纺织服饰", "name_en": "Textile & Apparel"},
    {"code": "801140", "name": "轻工制造", "name_en": "Light Manufacturing"},
    {"code": "801150", "name": "医药生物", "name_en": "Healthcare"},
    {"code": "801160", "name": "公用事业", "name_en": "Utilities"},
    {"code": "801170", "name": "交通运输", "name_en": "Transportation"},
    {"code": "801180", "name": "房地产", "name_en": "Real Estate"},
    {"code": "801200", "name": "商贸零售", "name_en": "Commerce"},
    {"code": "801210", "name": "社会服务", "name_en": "Social Services"},
    {"code": "801230", "name": "银行", "name_en": "Bank"},
    {"code": "801710", "name": "建筑材料", "name_en": "Building Materials"},
    {"code": "801720", "name": "建筑装饰", "name_en": "Construction"},
    {"code": "801730", "name": "电力设备", "name_en": "Electric Equipment"},
    {"code": "801740", "name": "机械设备", "name_en": "Machinery"},
    {"code": "801750", "name": "国防军工", "name_en": "Defense"},
    {"code": "801760", "name": "计算机", "name_en": "IT"},
    {"code": "801770", "name": "传媒", "name_en": "Media"},
    {"code": "801780", "name": "通信", "name_en": "Telecom"},
    {"code": "801790", "name": "非银金融", "name_en": "Non-Bank Financial"},
    {"code": "801880", "name": "汽车", "name_en": "Auto"},
    {"code": "801890", "name": "综合", "name_en": "Conglomerates"},
    {"code": "801950", "name": "石油石化", "name_en": "Oil & Gas"},
    {"code": "801960", "name": "环保", "name_en": "Environmental Protection"},
    {"code": "801980", "name": "美容护理", "name_en": "Beauty & Care"},
]

# ─── 基准指数 ─────────────────────────────────────────────────────

BENCHMARKS = {
    "hs300": {"code": "000300", "name": "沪深300", "name_en": "CSI 300"},
    "zz500": {"code": "000905", "name": "中证500", "name_en": "CSI 500"},
}

DEFAULT_BENCHMARK = "hs300"

# ─── 辅助函数 ─────────────────────────────────────────────────────

ALL_SECTOR_CODES = [s["code"] for s in SW_LEVEL1_SECTORS]
_CODE_TO_SECTOR = {s["code"]: s for s in SW_LEVEL1_SECTORS}


def get_sector_by_code(code: str) -> Optional[Dict[str, str]]:
    """根据代码获取行业信息"""
    return _CODE_TO_SECTOR.get(code)


def get_benchmark_info(benchmark_key: str) -> Optional[Dict[str, str]]:
    """获取基准指数信息"""
    return BENCHMARKS.get(benchmark_key)
