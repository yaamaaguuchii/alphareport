# -*- coding: utf-8 -*-
import json, random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

CACHE_DIR = Path(__file__).parent.parent / "cache"

def _cache_path(key):
    return CACHE_DIR / f"{key}.json"

def _read_cache(key):
    path = _cache_path(key)
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    ct = datetime.fromisoformat(data.get("_cached_at", "2000-01-01"))
    if datetime.now() - ct > timedelta(hours=6):
        return None
    return data

def _write_cache(key, data):
    CACHE_DIR.mkdir(exist_ok=True)
    data["_cached_at"] = datetime.now().isoformat()
    with open(_cache_path(key), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)

# ---------- 预置精确模拟数据 ----------
_MOCK = {
    "600519": {"name":"贵州茅台","industry":"白酒","description":"贵州茅台酒股份有限公司，中国白酒行业龙头企业。","revenue":[1230,1095,1062,979,854],"revenue_years":[2024,2023,2022,2021,2020],"net_profit":[620,560,528,470,412],"operating_cashflow":[580,520,490,430,380],"receivables":[8.5,7.2,6.8,5.5,4.2],"inventory_days":[1200,1150,1100,1050,1000],"debt_ratio":[0.18,0.20,0.22,0.21,0.23],"current_ratio":[3.5,3.2,3.0,3.1,2.8],"gross_margin":[0.918,0.917,0.918,0.916,0.914],"roe":[0.25,0.24,0.23,0.22,0.21],"pe_ratio":[25,28,32,35,40],"market_cap":"21000亿","related_party_ratio":0.03},
    "300750": {"name":"宁德时代","industry":"电池","description":"宁德时代新能源科技股份有限公司，全球领先的动力电池和储能系统提供商。","revenue":[3800,3200,2800,2100,1600],"revenue_years":[2024,2023,2022,2021,2020],"net_profit":[420,350,280,180,120],"operating_cashflow":[380,320,260,160,100],"receivables":[520,450,380,300,220],"inventory_days":[70,65,60,55,50],"debt_ratio":[0.62,0.60,0.58,0.55,0.52],"current_ratio":[1.8,1.9,2.0,2.1,2.2],"gross_margin":[0.22,0.24,0.25,0.26,0.28],"roe":[0.18,0.16,0.14,0.12,0.10],"pe_ratio":[22,25,30,35,45],"market_cap":"12000亿","related_party_ratio":0.08},
    "000002": {"name":"万科A","industry":"房地产开发","description":"万科企业股份有限公司，中国领先的城乡建设与生活服务商。","revenue":[4650,4460,5040,4190,3680],"revenue_years":[2024,2023,2022,2021,2020],"net_profit":[260,320,500,380,290],"operating_cashflow":[180,210,350,280,200],"receivables":[820,650,480,350,280],"inventory_days":[950,920,880,850,820],"debt_ratio":[0.74,0.72,0.70,0.68,0.65],"current_ratio":[1.2,1.3,1.4,1.5,1.6],"gross_margin":[0.15,0.18,0.21,0.22,0.25],"roe":[0.06,0.08,0.12,0.10,0.08],"pe_ratio":[15,12,8,10,12],"market_cap":"1200亿","related_party_ratio":0.15},
    "601318": {"name":"中国平安","industry":"保险","description":"中国平安保险（集团）股份有限公司，中国领先的综合金融服务集团。","revenue":[10200,9500,9200,8800,8400],"revenue_years":[2024,2023,2022,2021,2020],"net_profit":[980,920,880,850,800],"operating_cashflow":[1050,980,920,880,820],"receivables":[45,42,38,35,32],"inventory_days":[5,5,5,5,5],"debt_ratio":[0.72,0.71,0.70,0.70,0.69],"current_ratio":[1.1,1.1,1.2,1.2,1.3],"gross_margin":[0.28,0.26,0.25,0.24,0.23],"roe":[0.14,0.13,0.12,0.11,0.10],"pe_ratio":[10,9,8,9,10],"market_cap":"8000亿","related_party_ratio":0.05},
    "000001": {"name":"平安银行","industry":"银行","description":"平安银行股份有限公司，中国领先的股份制商业银行。","revenue":[1650,1580,1520,1480,1420],"revenue_years":[2024,2023,2022,2021,2020],"net_profit":[450,420,400,380,350],"operating_cashflow":[480,440,410,390,360],"receivables":[15,14,13,12,11],"inventory_days":[0,0,0,0,0],"debt_ratio":[0.68,0.67,0.66,0.65,0.64],"current_ratio":[1.5,1.5,1.6,1.6,1.7],"gross_margin":[0.32,0.31,0.30,0.30,0.29],"roe":[0.12,0.11,0.11,0.10,0.10],"pe_ratio":[6,5,6,7,8],"market_cap":"2800亿","related_party_ratio":0.02},
    "600036": {"name":"招商银行","industry":"银行","description":"招商银行股份有限公司，中国领先的股份制商业银行。","revenue":[3800,3600,3450,3300,3100],"revenue_years":[2024,2023,2022,2021,2020],"net_profit":[1480,1380,1300,1200,1100],"operating_cashflow":[1520,1420,1320,1250,1150],"receivables":[12,11,10,10,9],"inventory_days":[0,0,0,0,0],"debt_ratio":[0.65,0.65,0.64,0.63,0.62],"current_ratio":[1.6,1.6,1.7,1.7,1.8],"gross_margin":[0.35,0.34,0.33,0.33,0.32],"roe":[0.16,0.15,0.14,0.13,0.12],"pe_ratio":[8,7,8,9,10],"market_cap":"9500亿","related_party_ratio":0.01},
}

def get_mock_data(ticker):
    r = _MOCK.get(ticker)
    if r:
        return dict(r)
    # 未预置的股票：基于 ticker 生成通用数据（保证任何代码都有数据）
    seed = sum(ord(c) for c in ticker)
    rg = random.Random(seed)
    base = rg.randint(20, 200)
    return {
        "name": f"{ticker}", "industry": "制造",
        "description": f"股票代码{ticker}所属行业为制造，主营业务涵盖相关产品的研发、生产和销售。",
        "revenue": [round(base*1.5,1), round(base*1.3,1), round(base*1.1,1), base, round(base*0.85,1)],
        "revenue_years": [2024, 2023, 2022, 2021, 2020],
        "net_profit": [round(base*0.2,1), round(base*0.18,1), round(base*0.16,1), round(base*0.14,1), round(base*0.12,1)],
        "operating_cashflow": [round(base*0.18,1), round(base*0.16,1), round(base*0.14,1), round(base*0.12,1), round(base*0.10,1)],
        "receivables": [round(base*0.3,1), round(base*0.25,1), round(base*0.2,1), round(base*0.18,1), round(base*0.15,1)],
        "inventory_days": [80, 75, 70, 68, 65],
        "debt_ratio": [0.45, 0.44, 0.43, 0.42, 0.41],
        "current_ratio": [1.8, 1.9, 2.0, 2.1, 2.2],
        "gross_margin": [0.35, 0.34, 0.33, 0.32, 0.31],
        "roe": [0.10, 0.09, 0.08, 0.07, 0.06],
        "pe_ratio": [25, 28, 30, 32, 35],
        "market_cap": f"{base*10}亿",
        "related_party_ratio": 0.05,
    }

def get_available_mock_tickers():
    return list(_MOCK.keys())

def get_company_data(ticker, use_mock=True):
    data = {"ticker": ticker}

    # 非演示模式：尝试从 AKShare 获取真实数据
    if not use_mock:
        try:
            import akshare as ak
            # 个股基本信息
            try:
                info = ak.stock_individual_info_em(symbol=ticker)
                if info is not None and not info.empty:
                    kv = dict(zip(info["item"], info["value"]))
                    data["name"] = kv.get("股票简称", ticker)
                    data["industry"] = kv.get("行业", "")
                    data["market_cap"] = str(kv.get("总市值", ""))
            except: pass
            if "name" not in data:
                data["name"] = ticker
                data["industry"] = ""
            # 利润表
            try:
                pf = ak.stock_profit_sheet_by_report_em(symbol=ticker)
                if pf is not None and not pf.empty:
                    pf = pf.sort_values("报告期").tail(5)
                    data["revenue_years"] = [str(r)[:4] for r in pf["报告期"]]
                    data["revenue"] = [float(x)/1e8 for x in pf["营业收入"]]
                    data["net_profit"] = [float(x)/1e8 for x in pf["净利润"]]
                    cost = pf.get("营业成本")
                    if cost is not None:
                        data["gross_margin"] = [(float(r)-float(c))/float(r) for r,c in zip(pf["营业收入"], cost)]
            except: pass
            # 资产负债表
            try:
                bs = ak.stock_balance_sheet_by_report_em(symbol=ticker)
                if bs is not None and not bs.empty:
                    bs = bs.sort_values("报告期").tail(5)
                    data["debt_ratio"] = [float(bs.iloc[i]["负债合计"])/max(float(bs.iloc[i]["资产总计"]),1) for i in range(len(bs))]
            except: pass
            # 现金流量表
            try:
                cf = ak.stock_cash_flow_sheet_by_report_em(symbol=ticker)
                if cf is not None and not cf.empty:
                    cf = cf.sort_values("报告期").tail(5)
                    data["operating_cashflow"] = [float(x)/1e8 for x in cf["经营活动产生的现金流量净额"]]
            except: pass
            data["source"] = "akshare"
        except ImportError:
            data["source"] = "no_akshare"

    # 演示模式或真实数据不足时，用模拟数据补全缺失字段
    mock = get_mock_data(ticker)
    for k in ["name","industry","description","revenue","revenue_years","net_profit",
              "operating_cashflow","receivables","inventory_days","debt_ratio",
              "current_ratio","gross_margin","roe","pe_ratio","market_cap","related_party_ratio"]:
        if k not in data:
            data[k] = mock.get(k, "")
    if "source" not in data:
        data["source"] = "generated"

    return data

def get_mock_announcements(ticker):
    return _MOCK_ANNOUNCE.get(ticker, [])

_MOCK_ANNOUNCE = {
    "600519": [{"date":"2026-04-28","title":"贵州茅台2025年年度报告","type":"定期报告","summary":"2025年营收1230亿元，净利润620亿元","level":"S"}],
    "300750": [{"date":"2026-04-26","title":"宁德时代2025年年度报告","type":"定期报告","summary":"2025年营收3800亿元","level":"S"}],
    "000002": [{"date":"2026-04-29","title":"万科A2025年年度报告","type":"定期报告","summary":"2025年营收4650亿元","level":"S"}],
    "601318": [{"date":"2026-04-30","title":"中国平安2025年年度报告","type":"定期报告","summary":"2025年营收10200亿元","level":"S"}],
    "000001": [{"date":"2026-04-28","title":"平安银行2025年年度报告","type":"定期报告","summary":"2025年营收1650亿元","level":"S"}],
    "600036": [{"date":"2026-04-26","title":"招商银行2025年年度报告","type":"定期报告","summary":"2025年营收3800亿元","level":"S"}],
}
