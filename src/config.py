# AlphaReport 配置文件
# 使用 .env 文件或在 Streamlit secrets 中设置 API 密钥

import os
from pathlib import Path

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent

# 数据缓存目录
CACHE_DIR = ROOT_DIR / "cache"
CACHE_DIR.mkdir(exist_ok=True)

# 示例输出目录
EXAMPLES_DIR = ROOT_DIR / "examples"

# ===== API 配置 =====
# LLM API 配置（可选，不使用 LLM 时仍可运行模板报告）
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_API_BASE = os.getenv("LLM_API_BASE", "https://api.openai.com/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

# 如果使用 DeepSeek，取消注释下面两行
# LLM_API_BASE = "https://api.deepseek.com/v1"
# LLM_MODEL = "deepseek-chat"

# ===== 股市数据配置 =====
# 默认股票代码（贵州茅台）
DEFAULT_TICKER = "600519"
DEFAULT_MARKET = "A股"

# AKShare 数据获取超时（秒）
AKSHARE_TIMEOUT = 30

# ===== 财务侦探规则阈值 =====
# 这些阈值基于 A 股历史数据统计分析

# 规则1：应收账款增速 vs 营收增速
# 当应收账款增速连续 N 年高于营收增速超过此倍数时报警
RECEIVABLE_REVENUE_RATIO_THRESHOLD = 1.5

# 规则2：经营性现金流 / 净利润 比率
# 低于此值报警（利润含金量低）
CASHFLOW_PROFIT_RATIO_THRESHOLD = 0.5

# 规则3：存货周转天数同比增幅
# 超过此百分比报警
INVENTORY_TURNOVER_INCREASE_THRESHOLD = 0.3

# 规则4：关联交易占比
# 超过此百分比报警
RELATED_PARTY_RATIO_THRESHOLD = 0.20

# 规则5：资产负债率
# 超过此值报警（高负债风险）
DEBT_RATIO_THRESHOLD = 0.70

# ===== 现金流画像定义 =====
# 经营/投资/筹资现金流符号组合的判断逻辑
CASHFLOW_PROFILES = {
    "金牛型": {"经营": "+", "投资": "+", "筹资": "-"},
    "奶牛型": {"经营": "+", "投资": "-", "筹资": "+"},
    "蛮牛型": {"经营": "+", "投资": "-", "筹资": "-"},
    "赌徒型": {"经营": "-", "投资": "-", "筹资": "+"},
    "破产型": {"经营": "-", "投资": "-", "筹资": "-"},
    "妖精型": {"经营": "-", "投资": "+", "筹资": "+"},
    "混账型": {"经营": "+", "投资": "+", "筹资": "+"},
}
