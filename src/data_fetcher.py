"""
数据采集模块
基于 AKShare 获取 A 股金融数据和公告信息
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import json
from pathlib import Path

from src.config import CACHE_DIR, AKSHARE_TIMEOUT

# 缓存有效期（小时）
CACHE_EXPIRY_HOURS = 6


def _cache_path(key: str) -> Path:
    """获取缓存文件路径"""
    return CACHE_DIR / f"{key}.json"


def _read_cache(key: str) -> Optional[dict]:
    """读取缓存"""
    path = _cache_path(key)
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    cache_time = datetime.fromisoformat(data.get("_cached_at", "2000-01-01"))
    if datetime.now() - cache_time > timedelta(hours=CACHE_EXPIRY_HOURS):
        return None
    return data


def _write_cache(key: str, data: dict):
    """写入缓存"""
    data["_cached_at"] = datetime.now().isoformat()
    path = _cache_path(key)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)


def _safe_akshare(func, *args, **kwargs):
    """安全调用 AKShare 函数，失败时返回空 DataFrame"""
    try:
        import akshare as ak
        result = func(*args, **kwargs)
        if result is None or (isinstance(result, pd.DataFrame) and result.empty):
            return pd.DataFrame()
        return result
    except Exception as e:
        print(f"[AKShare 错误] {func.__name__}: {e}")
        return pd.DataFrame()


# ============================================================
# 预置模拟数据（当网络不可用或 API 限流时使用）
# ============================================================

_MOCK_COMPANIES = {
    "600519": {
        "name": "贵州茅台",
        "industry": "白酒",
        "description": "贵州茅台酒股份有限公司，主营茅台酒及系列酒的生产与销售，是中国白酒行业的龙头企业。",
        "revenue": [1230, 1095, 1062, 979, 854],  # 近5年营收（亿元）
        "revenue_years": [2024, 2023, 2022, 2021, 2020],
        "net_profit": [620, 560, 528, 470, 412],
        "operating_cashflow": [580, 520, 490, 430, 380],
        "receivables": [8.5, 7.2, 6.8, 5.5, 4.2],
        "inventory_days": [1200, 1150, 1100, 1050, 1000],
        "debt_ratio": [0.18, 0.20, 0.22, 0.21, 0.23],
        "current_ratio": [3.5, 3.2, 3.0, 3.1, 2.8],
        "gross_margin": [0.918, 0.917, 0.918, 0.916, 0.914],
        "roe": [0.25, 0.24, 0.23, 0.22, 0.21],
        "pe_ratio": [25, 28, 32, 35, 40],
        "market_cap": "21000亿",
        "related_party_ratio": 0.03,
    },
    "000002": {
        "name": "万科A",
        "industry": "房地产开发",
        "description": "万科企业股份有限公司，中国领先的城乡建设与生活服务商，主营业务为房地产开发及相关资产经营。",
        "revenue": [4650, 4460, 5040, 4190, 3680],
        "revenue_years": [2024, 2023, 2022, 2021, 2020],
        "net_profit": [260, 320, 500, 380, 290],
        "operating_cashflow": [180, 210, 350, 280, 200],
        "receivables": [820, 650, 480, 350, 280],
        "inventory_days": [950, 920, 880, 850, 820],
        "debt_ratio": [0.74, 0.72, 0.70, 0.68, 0.65],
        "current_ratio": [1.2, 1.3, 1.4, 1.5, 1.6],
        "gross_margin": [0.15, 0.18, 0.21, 0.22, 0.25],
        "roe": [0.06, 0.08, 0.12, 0.10, 0.08],
        "pe_ratio": [15, 12, 8, 10, 12],
        "market_cap": "1200亿",
        "related_party_ratio": 0.15,
    },
    "300750": {
        "name": "宁德时代",
        "industry": "电池",
        "description": "宁德时代新能源科技股份有限公司，全球领先的动力电池和储能系统提供商。",
        "revenue": [3800, 3200, 2800, 2100, 1600],
        "revenue_years": [2024, 2023, 2022, 2021, 2020],
        "net_profit": [420, 350, 280, 180, 120],
        "operating_cashflow": [380, 320, 260, 160, 100],
        "receivables": [520, 450, 380, 300, 220],
        "inventory_days": [70, 65, 60, 55, 50],
        "debt_ratio": [0.62, 0.60, 0.58, 0.55, 0.52],
        "current_ratio": [1.8, 1.9, 2.0, 2.1, 2.2],
        "gross_margin": [0.22, 0.24, 0.25, 0.26, 0.28],
        "roe": [0.18, 0.16, 0.14, 0.12, 0.10],
        "pe_ratio": [22, 25, 30, 35, 45],
        "market_cap": "12000亿",
        "related_party_ratio": 0.08,
    },
}


def get_mock_data(ticker: str) -> Optional[dict]:
    """获取预置模拟数据"""
    return _MOCK_COMPANIES.get(ticker)


def get_available_mock_tickers():
    """获取所有可用的模拟股票代码"""
    return list(_MOCK_COMPANIES.keys())


# ============================================================
# AKShare 实时数据获取
# ============================================================

def fetch_stock_info(ticker: str) -> dict:
    """获取个股基本信息"""
    import akshare as ak
    try:
        df = _safe_akshare(ak.stock_individual_info_em, symbol=ticker)
        if not df.empty:
            info = dict(zip(df["item"], df["value"]))
            return info
    except:
        pass
    return {}


def fetch_financial_data(ticker: str, years: int = 5) -> pd.DataFrame:
    """
    获取个股财务数据（利润表）
    返回 DataFrame，列包含：股票代码、报告期、营业收入、净利润等
    """
    import akshare as ak
    try:
        df = _safe_akshare(ak.stock_profit_sheet_by_report_em, symbol=ticker)
        if not df.empty:
            df = df.sort_values("报告期", ascending=False).head(years * 4)
            return df
    except:
        pass
    return pd.DataFrame()


def fetch_balance_sheet(ticker: str, years: int = 5) -> pd.DataFrame:
    """获取资产负债表数据"""
    import akshare as ak
    try:
        df = _safe_akshare(ak.stock_balance_sheet_by_report_em, symbol=ticker)
        if not df.empty:
            df = df.sort_values("报告期", ascending=False).head(years * 4)
            return df
    except:
        pass
    return pd.DataFrame()


def fetch_cashflow_data(ticker: str, years: int = 5) -> pd.DataFrame:
    """获取现金流量表数据"""
    import akshare as ak
    try:
        df = _safe_akshare(ak.stock_cash_flow_sheet_by_report_em, symbol=ticker)
        if not df.empty:
            df = df.sort_values("报告期", ascending=False).head(years * 4)
            return df
    except:
        pass
    return pd.DataFrame()


def fetch_announcements(ticker: str, days: int = 365) -> pd.DataFrame:
    """
    获取个股公告列表
    """
    import akshare as ak
    try:
        df = _safe_akshare(ak.stock_notice_report, symbol=ticker)
        if not df.empty:
            return df.head(50)
    except:
        pass
    return pd.DataFrame()


def fetch_financial_indicators(ticker: str) -> pd.DataFrame:
    """获取财务分析指标（含 ROE、毛利率、资产负债率等）"""
    import akshare as ak
    try:
        df = _safe_akshare(ak.stock_financial_analysis_indicator, symbol=ticker)
        if not df.empty:
            return df.sort_values("报告期", ascending=False).head(10)
    except:
        pass
    return pd.DataFrame()


def get_company_data(ticker: str, use_mock: bool = True) -> Dict:
    """
    统一的公司数据获取入口
    先尝试 AKShare 实时数据，失败则回退到模拟数据
    """
    # 先检查缓存
    cache_key = f"company_{ticker}"
    cached = _read_cache(cache_key)
    if cached:
        return cached

    data = {"ticker": ticker}

    # 尝试获取实时数据
    try:
        info = fetch_stock_info(ticker)
        if info:
            data["name"] = info.get("股票简称", ticker)
            data["industry"] = info.get("行业", "")
            data["market_cap"] = info.get("总市值", "")
            data["pe_ratio"] = info.get("市盈率-动态", "")
    except:
        pass

    # 如果实时数据不足且允许模拟数据，使用模拟数据
    if (not data.get("name") or data.get("name") == ticker) and use_mock:
        mock = get_mock_data(ticker)
        if mock:
            data.update(mock)
            data["source"] = "mock"
            _write_cache(cache_key, data)
            return data

    data["source"] = "realtime"
    _write_cache(cache_key, data)
    return data


def get_mock_announcements(ticker: str) -> list:
    """获取模拟的公告数据（用于演示）"""
    mock_announcements = {
        "600519": [
            {
                "date": "2026-06-15",
                "title": "贵州茅台关于2025年度利润分配方案的公告",
                "type": "分红",
                "summary": "拟每10股派发现金红利200元（含税），总计派发约250亿元",
                "level": "A"
            },
            {
                "date": "2026-04-28",
                "title": "贵州茅台2025年年度报告",
                "type": "定期报告",
                "summary": "2025年营收1230亿元，同比增长12.3%；净利润620亿元，同比增长10.7%",
                "level": "S"
            },
            {
                "date": "2026-04-10",
                "title": "贵州茅台关于参与设立产业投资基金的公告",
                "type": "投资",
                "summary": "拟出资50亿元参与设立消费产业投资基金",
                "level": "B"
            },
            {
                "date": "2026-03-01",
                "title": "贵州茅台关于董事长变更的公告",
                "type": "人事变动",
                "summary": "张德芹辞去董事长职务，由王莉接任",
                "level": "A"
            },
            {
                "date": "2026-01-20",
                "title": "贵州茅台2025年度业绩预告",
                "type": "业绩预告",
                "summary": "预计2025年净利润约620亿元，同比增长约11%",
                "level": "S"
            },
            {
                "date": "2025-12-15",
                "title": "贵州茅台关于回购股份实施结果的公告",
                "type": "回购",
                "summary": "累计回购股份120万股，耗资约20亿元",
                "level": "B"
            },
            {
                "date": "2025-11-08",
                "title": "贵州茅台关于控股股东增持计划的公告",
                "type": "增持",
                "summary": "控股股东茅台集团拟在未来6个月内增持15-30亿元",
                "level": "A"
            },
        ],
        "300750": [
            {
                "date": "2026-06-20",
                "title": "宁德时代关于匈牙利工厂投产的公告",
                "type": "业务进展",
                "summary": "匈牙利第二座电池工厂正式投产，设计产能40GWh",
                "level": "S"
            },
            {
                "date": "2026-04-26",
                "title": "宁德时代2025年年度报告",
                "type": "定期报告",
                "summary": "2025年营收3800亿元，同比增长18.8%；净利润420亿元，同比增长20%",
                "level": "S"
            },
            {
                "date": "2026-02-15",
                "title": "宁德时代关于与某国际车企签订供货协议的公告",
                "type": "合同",
                "summary": "与某国际知名车企签订5年动力电池供货协议，总金额约200亿元",
                "level": "A"
            },
        ],
        "000002": [
            {
                "date": "2026-06-10",
                "title": "万科A关于为子公司提供担保的公告",
                "type": "担保",
                "summary": "为子公司向银行申请贷款提供担保，合计金额约30亿元",
                "level": "B"
            },
            {
                "date": "2026-04-29",
                "title": "万科A2025年年度报告",
                "type": "定期报告",
                "summary": "2025年营收4650亿元，同比增长4.3%；净利润260亿元，同比下降18.8%",
                "level": "S"
            },
            {
                "date": "2026-03-20",
                "title": "万科A关于成功发行中期票据的公告",
                "type": "融资",
                "summary": "成功发行20亿元中期票据，利率3.2%",
                "level": "B"
            },
        ],
    }
    return mock_announcements.get(ticker, [])
