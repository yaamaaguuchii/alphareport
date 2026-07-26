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
        "name": "贵州茅台", "industry": "白酒",
        "description": "贵州茅台酒股份有限公司，主营茅台酒及系列酒的生产与销售，是中国白酒行业的龙头企业。",
        "revenue": [1230, 1095, 1062, 979, 854],
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
    "300750": {
        "name": "宁德时代", "industry": "电池",
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
    "000002": {
        "name": "万科A", "industry": "房地产开发",
        "description": "万科企业股份有限公司，中国领先的城乡建设与生活服务商。",
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
    "601318": {
        "name": "中国平安", "industry": "保险",
        "description": "中国平安保险（集团）股份有限公司，中国领先的综合金融服务集团。",
        "revenue": [10200, 9500, 9200, 8800, 8400],
        "revenue_years": [2024, 2023, 2022, 2021, 2020],
        "net_profit": [980, 920, 880, 850, 800],
        "operating_cashflow": [1050, 980, 920, 880, 820],
        "receivables": [45, 42, 38, 35, 32],
        "inventory_days": [5, 5, 5, 5, 5],
        "debt_ratio": [0.72, 0.71, 0.70, 0.70, 0.69],
        "current_ratio": [1.1, 1.1, 1.2, 1.2, 1.3],
        "gross_margin": [0.28, 0.26, 0.25, 0.24, 0.23],
        "roe": [0.14, 0.13, 0.12, 0.11, 0.10],
        "pe_ratio": [10, 9, 8, 9, 10],
        "market_cap": "8000亿",
        "related_party_ratio": 0.05,
    },
    "000001": {
        "name": "平安银行", "industry": "银行",
        "description": "平安银行股份有限公司，中国领先的股份制商业银行。",
        "revenue": [1650, 1580, 1520, 1480, 1420],
        "revenue_years": [2024, 2023, 2022, 2021, 2020],
        "net_profit": [450, 420, 400, 380, 350],
        "operating_cashflow": [480, 440, 410, 390, 360],
        "receivables": [15, 14, 13, 12, 11],
        "inventory_days": [0, 0, 0, 0, 0],
        "debt_ratio": [0.68, 0.67, 0.66, 0.65, 0.64],
        "current_ratio": [1.5, 1.5, 1.6, 1.6, 1.7],
        "gross_margin": [0.32, 0.31, 0.30, 0.30, 0.29],
        "roe": [0.12, 0.11, 0.11, 0.10, 0.10],
        "pe_ratio": [6, 5, 6, 7, 8],
        "market_cap": "2800亿",
        "related_party_ratio": 0.02,
    },
    "600036": {
        "name": "招商银行", "industry": "银行",
        "description": "招商银行股份有限公司，中国领先的股份制商业银行，以零售银行业务著称。",
        "revenue": [3800, 3600, 3450, 3300, 3100],
        "revenue_years": [2024, 2023, 2022, 2021, 2020],
        "net_profit": [1480, 1380, 1300, 1200, 1100],
        "operating_cashflow": [1520, 1420, 1320, 1250, 1150],
        "receivables": [12, 11, 10, 10, 9],
        "inventory_days": [0, 0, 0, 0, 0],
        "debt_ratio": [0.65, 0.65, 0.64, 0.63, 0.62],
        "current_ratio": [1.6, 1.6, 1.7, 1.7, 1.8],
        "gross_margin": [0.35, 0.34, 0.33, 0.33, 0.32],
        "roe": [0.16, 0.15, 0.14, 0.13, 0.12],
        "pe_ratio": [8, 7, 8, 9, 10],
        "market_cap": "9500亿",
        "related_party_ratio": 0.01,
    },
}


def get_mock_data(ticker: str) -> Optional[dict]:
    return _MOCK_COMPANIES.get(ticker)


def get_available_mock_tickers():
    return list(_MOCK_COMPANIES.keys())


def get_company_data(ticker: str, use_mock: bool = True) -> Dict:
    cache_key = f"company_{ticker}"
    cached = _read_cache(cache_key)
    if cached and "name" in cached and "revenue" in cached:
        return cached
    data = {"ticker": ticker}

    # Demo mode - use mock data
    if use_mock:
        mock = get_mock_data(ticker)
        if mock:
            data.update(mock)
            data["source"] = "mock"
            _write_cache(cache_key, data)
            return data
        data["name"] = f"股票{ticker}"
        data["industry"] = "未知"
        data["source"] = "not_found"
        return data

    # Real mode - fetch from AKShare
    try:
        import akshare as ak

        # 1. Basic info
        try:
            info_df = ak.stock_individual_info_em(symbol=ticker)
            if info_df is not None and not info_df.empty:
                info = dict(zip(info_df["item"], info_df["value"]))
                data["name"] = info.get("股票简称", f"股票{ticker}")
                data["industry"] = info.get("行业", "未知")
                data["market_cap"] = str(info.get("总市值", ""))
                data["pe_ratio"] = info.get("市盈率-动态", "")
        except:
            data["name"] = f"股票{ticker}"
            data["industry"] = "未知"

        # 2. Profit sheet (营收, 净利润, 毛利率)
        years_list = []
        revenue_list = []
        profit_list = []
        gross_list = []
        try:
            pf = ak.stock_profit_sheet_by_report_em(symbol=ticker)
            if pf is not None and not pf.empty:
                pf = pf.sort_values("报告期", ascending=True).tail(5)
                for _, row in pf.iterrows():
                    years_list.append(str(row.get("报告期", ""))[:4])
                    revenue_list.append(float(row.get("营业收入", 0) if row.get("营业收入") else 0))
                    profit_list.append(float(row.get("净利润", 0) if row.get("净利润") else 0))
                    rev = float(row.get("营业收入", 0) if row.get("营业收入") else 0)
                    cost = float(row.get("营业成本", 0) if row.get("营业成本") else 0)
                    if rev > 0:
                        gross_list.append((rev - cost) / rev)
                    else:
                        gross_list.append(0)
                data["revenue_years"] = years_list
                data["revenue"] = revenue_list
                data["net_profit"] = profit_list
                data["gross_margin"] = gross_list
        except:
            pass

        # 3. Balance sheet (应收, 存货, 负债率, 流动比率)
        try:
            bs = ak.stock_balance_sheet_by_report_em(symbol=ticker)
            if bs is not None and not bs.empty:
                bs = bs.sort_values("报告期", ascending=True).tail(5)
                rec_list = []
                inv_list = []
                debt_list = []
                cur_list = []
                for _, row in bs.iterrows():
                    total_assets = float(row.get("资产总计", 0) if row.get("资产总计") else 1)
                    total_liab = float(row.get("负债合计", 0) if row.get("负债合计") else 0)
                    cur_assets = float(row.get("流动资产合计", 0) if row.get("流动资产合计") else 0)
                    cur_liab = float(row.get("流动负债合计", 0) if row.get("流动负债合计") else 1)
                    rec_list.append(float(row.get("应收账款", 0) if row.get("应收账款") else 0))
                    inv_list.append(float(row.get("存货", 0) if row.get("存货") else 0))
                    debt_list.append(total_liab / total_assets if total_assets > 0 else 0)
                    cur_list.append(cur_assets / cur_liab if cur_liab > 0 else 0)
                data["receivables"] = rec_list
                data["inventory_days"] = [d * 365 / max(r, 1) for d, r in zip(inv_list, revenue_list)] if revenue_list else [0]*5
                data["debt_ratio"] = debt_list
                data["current_ratio"] = cur_list
        except:
            pass

        # 4. Cash flow (经营性现金流)
        try:
            cf = ak.stock_cash_flow_sheet_by_report_em(symbol=ticker)
            if cf is not None and not cf.empty:
                cf = cf.sort_values("报告期", ascending=True).tail(5)
                cf_list = []
                for _, row in cf.iterrows():
                    cf_list.append(float(row.get("经营活动产生的现金流量净额", 0) if row.get("经营活动产生的现金流量净额") else 0))
                data["operating_cashflow"] = cf_list
        except:
            pass

        # 5. Financial analysis indicators (ROE)
        try:
            fi = ak.stock_financial_analysis_indicator(symbol=ticker)
            if fi is not None and not fi.empty:
                fi = fi.sort_values("报告期", ascending=True).tail(5)
                roe_list = []
                for _, row in fi.iterrows():
                    roe_list.append(float(row.get("净资产收益率", 0) if row.get("净资产收益率") else 0) / 100)
                data["roe"] = roe_list
        except:
            pass

        data["related_party_ratio"] = 0.05
        data["source"] = "akshare"
        _write_cache(cache_key, data)

    except ImportError:
        data["name"] = f"股票{ticker}"
        data["industry"] = "未知"
        data["source"] = "akshare_not_installed"
        print("请安装 akshare: pip install akshare")

    return data

def get_mock_announcements(ticker: str) -> list:
    mock_data = {
        "600519": [
            {"date": "2026-06-15", "title": "贵州茅台关于2025年度利润分配方案的公告", "type": "分红", "summary": "拟每10股派发现金红利200元", "level": "A"},
            {"date": "2026-04-28", "title": "贵州茅台2025年年度报告", "type": "定期报告", "summary": "2025年营收1230亿元，净利润620亿元", "level": "S"},
            {"date": "2026-03-01", "title": "贵州茅台关于董事长变更的公告", "type": "人事变动", "summary": "张德芹辞去董事长职务，由王莉接任", "level": "A"},
            {"date": "2026-01-20", "title": "贵州茅台2025年度业绩预告", "type": "业绩预告", "summary": "预计2025年净利润约620亿元", "level": "S"},
        ],
        "300750": [
            {"date": "2026-06-20", "title": "宁德时代关于匈牙利工厂投产的公告", "type": "业务进展", "summary": "匈牙利第二座电池工厂正式投产", "level": "S"},
            {"date": "2026-04-26", "title": "宁德时代2025年年度报告", "type": "定期报告", "summary": "2025年营收3800亿元，同比增长18.8%", "level": "S"},
        ],
        "000002": [
            {"date": "2026-04-29", "title": "万科A2025年年度报告", "type": "定期报告", "summary": "2025年营收4650亿元，净利润260亿元", "level": "S"},
            {"date": "2026-03-20", "title": "万科A关于成功发行中期票据的公告", "type": "融资", "summary": "成功发行20亿元中期票据", "level": "B"},
        ],
        "601318": [
            {"date": "2026-04-30", "title": "中国平安2025年年度报告", "type": "定期报告", "summary": "2025年营收10200亿元，净利润980亿元", "level": "S"},
            {"date": "2026-03-15", "title": "中国平安关于2025年度利润分配的公告", "type": "分红", "summary": "拟每股派发现金红利2.5元", "level": "A"},
        ],
        "000001": [
            {"date": "2026-04-28", "title": "平安银行2025年年度报告", "type": "定期报告", "summary": "2025年营收1650亿元，净利润450亿元", "level": "S"},
        ],
        "600036": [
            {"date": "2026-04-26", "title": "招商银行2025年年度报告", "type": "定期报告", "summary": "2025年营收3800亿元，净利润1480亿元", "level": "S"},
        ],
    }
    return mock_data.get(ticker, [])
