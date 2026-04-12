"""
Market Watchlist ETF 分组配置
数据源：TheMarketMemo Market Watchlist Google Sheet
"""
from typing import Optional

# ─── ETF 分组定义 ─────────────────────────────────────────

ETF_GROUPS = {
    "broad": {
        "display_name": "大盘指数",
        "etfs": [
            {"ticker": "VTI", "name": "全市场", "name_en": "Vanguard Total Stock Market"},
            {"ticker": "SPY", "name": "标普500", "name_en": "SPDR S&P 500"},
            {"ticker": "QQQ", "name": "纳指100", "name_en": "Invesco QQQ Trust"},
            {"ticker": "IWM", "name": "罗素2000", "name_en": "iShares Russell 2000"},
            {"ticker": "DIA", "name": "道指", "name_en": "SPDR Dow Jones Industrial Average"},
            {"ticker": "VOO", "name": "标普500(Vanguard)", "name_en": "Vanguard S&P 500"},
            {"ticker": "IVV", "name": "标普500(iShares)", "name_en": "iShares Core S&P 500"},
            {"ticker": "QQQJ", "name": "纳指下一代", "name_en": "Invesco Nasdaq Next Gen 100"},
            {"ticker": "QQQM", "name": "纳指100(Invesco)", "name_en": "Invesco Nasdaq 100"},
            {"ticker": "IJH", "name": "中盘400", "name_en": "iShares Core S&P Mid-Cap"},
            {"ticker": "IJR", "name": "小盘600", "name_en": "iShares Core S&P Small-Cap"},
            {"ticker": "VWO", "name": "新兴市场", "name_en": "Vanguard Emerging Markets"},
        ],
    },
    "equal_weighted": {
        "display_name": "等权行业板块",
        "etfs": [
            {"ticker": "RSPS", "name": "消费品(必选)", "name_en": "Invesco S&P 500 Equal Weight Consumer Staples"},
            {"ticker": "RSPT", "name": "科技", "name_en": "Invesco S&P 500 Equal Weight Technology"},
            {"ticker": "RSPM", "name": "工业", "name_en": "Invesco S&P 500 Equal Weight Industrials"},
            {"ticker": "RSPG", "name": "医疗", "name_en": "Invesco S&P 500 Equal Weight Health Care"},
            {"ticker": "RSPF", "name": "金融", "name_en": "Invesco S&P 500 Equal Weight Financials"},
            {"ticker": "RSPD", "name": "消费品(可选)", "name_en": "Invesco S&P 500 Equal Weight Consumer Discretionary"},
            {"ticker": "RSPB", "name": "材料", "name_en": "Invesco S&P 500 Equal Weight Materials"},
            {"ticker": "RSPK", "name": "通信", "name_en": "Invesco S&P 500 Equal Weight Communication Services"},
            {"ticker": "RSPI", "name": "能源", "name_en": "Invesco S&P 500 Equal Weight Energy"},
            {"ticker": "RSPC", "name": "公用事业", "name_en": "Invesco S&P 500 Equal Weight Utilities"},
            {"ticker": "RSPE", "name": "房地产", "name_en": "Invesco S&P 500 Equal Weight Real Estate"},
        ],
    },
    "market_cap_weighted": {
        "display_name": "市值加权行业板块",
        "etfs": [
            {"ticker": "XLC", "name": "通信服务", "name_en": "Communication Services Select Sector SPDR"},
            {"ticker": "XLY", "name": "消费品(可选)", "name_en": "Consumer Discretionary Select Sector SPDR"},
            {"ticker": "XLP", "name": "消费品(必选)", "name_en": "Consumer Staples Select Sector SPDR"},
            {"ticker": "XLE", "name": "能源", "name_en": "Energy Select Sector SPDR"},
            {"ticker": "XLF", "name": "金融", "name_en": "Financial Select Sector SPDR"},
            {"ticker": "XLV", "name": "医疗", "name_en": "Health Care Select Sector SPDR"},
            {"ticker": "XLI", "name": "工业", "name_en": "Industrial Select Sector SPDR"},
            {"ticker": "XLB", "name": "材料", "name_en": "Materials Select Sector SPDR"},
            {"ticker": "XLRE", "name": "房地产", "name_en": "Real Estate Select Sector SPDR"},
            {"ticker": "XLK", "name": "科技", "name_en": "Technology Select Sector SPDR"},
            {"ticker": "XLU", "name": "公用事业", "name_en": "Utilities Select Sector SPDR"},
        ],
    },
    "factors": {
        "display_name": "因子风格",
        "etfs": [
            {"ticker": "MTUM", "name": "动量", "name_en": "iShares MSCI USA Momentum Factor"},
            {"ticker": "SPHB", "name": "高贝塔", "name_en": "Invesco S&P 500 High Beta"},
            {"ticker": "QUAL", "name": "质量", "name_en": "iShares MSCI USA Quality Factor"},
            {"ticker": "SPLV", "name": "低波动", "name_en": "Invesco S&P 500 Low Volatility"},
            {"ticker": "SPYD", "name": "高股息", "name_en": "SPDR S&P Dividend ETF"},
        ],
    },
    "growth": {
        "display_name": "成长风格",
        "etfs": [
            {"ticker": "IWF", "name": "大盘成长", "name_en": "iShares Russell 1000 Growth"},
            {"ticker": "IWO", "name": "小盘成长", "name_en": "iShares Russell 2000 Growth"},
        ],
    },
    "thematic": {
        "display_name": "主题投资",
        "etfs": [
            {"ticker": "SOXX", "name": "半导体", "name_en": "iShares Semiconductor"},
            {"ticker": "BOTZ", "name": "机器人", "name_en": "Global X Robotics & AI"},
            {"ticker": "THNQ", "name": "AI/算力", "name_en": "ROBO Global AI & Technology"},
            {"ticker": "DRIV", "name": "自动驾驶", "name_en": "Global X Autonomous & EV"},
            {"ticker": "UFO", "name": "商业航天", "name_en": "Procure Space ETF"},
            {"ticker": "DRAM", "name": "存储", "name_en": "VictoryShares Memory Chips ETF"},
            {"ticker": "LIT", "name": "锂电池", "name_en": "Global X Lithium & Battery Tech"},
            {"ticker": "TAN", "name": "太阳能", "name_en": "Invesco Solar ETF"},
            {"ticker": "ICLN", "name": "清洁能源", "name_en": "iShares Global Clean Energy"},
            {"ticker": "KWEB", "name": "中概互联网", "name_en": "KraneShares CSI China Internet"},
            {"ticker": "HAIL", "name": "未来出行", "name_en": "Global X Future Mobility"},
            {"ticker": "BUG", "name": "网络安全", "name_en": "Global X Cybersecurity"},
            {"ticker": "CIBR", "name": "网络安全(另一)", "name_en": "iShares Digital Security"},
            {"ticker": "BLOK", "name": "区块链", "name_en": "Amplify Transformational Data Sharing"},
            {"ticker": "ITA", "name": "航空航天国防", "name_en": "iShares U.S. Aerospace & Defense"},
            {"ticker": "IHI", "name": "医疗设备", "name_en": "iShares U.S. Medical Devices"},
            {"ticker": "IBB", "name": "生物科技", "name_en": "iShares Biotechnology"},
            {"ticker": "XBI", "name": "生物科技(等权)", "name_en": "SPDR S&P Biotech"},
            {"ticker": "VNQ", "name": "房地产(总市场)", "name_en": "Vanguard Real Estate"},
            {"ticker": "GLD", "name": "黄金", "name_en": "SPDR Gold Shares"},
            {"ticker": "SLV", "name": "白银", "name_en": "iShares Silver Trust"},
            {"ticker": "USO", "name": "原油", "name_en": "United States Oil Fund"},
            {"ticker": "CORN", "name": "玉米", "name_en": "Teucrium Corn Fund"},
        ],
    },
    "ark": {
        "display_name": "ARK 系列",
        "etfs": [
            {"ticker": "ARKK", "name": "ARK创新", "name_en": "ARK Innovation ETF"},
            {"ticker": "ARKQ", "name": "ARK自动科技", "name_en": "ARK Autonomous Technology & Robotics"},
            {"ticker": "ARKF", "name": "ARK金融科技", "name_en": "ARK Fintech Innovation"},
            {"ticker": "ARKW", "name": "ARK下一代互联网", "name_en": "ARK Next Generation Internet"},
            {"ticker": "ARKX", "name": "ARK太空探索", "name_en": "ARK Space Exploration & Innovation"},
        ],
    },
}

# ─── A 股关联 ETF ─────────────────────────────────────────
# 这些 ETF 在隔夜雷达中有 A 股映射
CN_LINKED_TICKERS = ["SOXX", "XLK", "DRIV", "THNQ", "GLD", "BOTZ", "UFO", "DRAM"]

# ─── 辅助函数 ─────────────────────────────────────────────

ALL_TICKERS = []
_TICKER_TO_GROUP = {}

for group_key, group_data in ETF_GROUPS.items():
    for etf in group_data["etfs"]:
        ALL_TICKERS.append(etf["ticker"])
        _TICKER_TO_GROUP[etf["ticker"]] = group_key


def get_group_key(ticker: str) -> Optional[str]:
    """根据 ticker 查找所属分组 key。"""
    return _TICKER_TO_GROUP.get(ticker)
