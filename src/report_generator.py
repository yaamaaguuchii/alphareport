# AlphaReport - 研报生成器
from typing import Dict, List
from datetime import datetime


def generate_report(company_data: dict, detective_result: dict, announcements: List[dict], include_llm: bool = False) -> str:
    parts = []
    parts.append(_generate_header(company_data))
    parts.append(_generate_company_overview(company_data))
    parts.append(_generate_financial_analysis(company_data))
    parts.append(_generate_health_scorecard(detective_result))
    parts.append(_generate_recent_events(announcements))
    parts.append(_generate_industry_outlook(company_data))
    parts.append(_generate_risk_disclosure(detective_result))
    parts.append(_generate_valuation_summary(company_data, detective_result))
    parts.append(_generate_disclaimer())
    return "\n\n".join(parts)


def _generate_header(data: dict) -> str:
    name = data.get("name", "未知")
    ticker = data.get("ticker", "")
    industry = data.get("industry", "未知行业")
    today = datetime.now().strftime("%Y-%m-%d")
    return f"# AlphaReport 智能投研报告\n\n**{name}（{ticker}）** | 行业：{industry} | 生成日期：{today}\n\n---"


def _generate_company_overview(data: dict) -> str:
    name = data.get("name", "未知")
    ticker = data.get("ticker", "")
    industry = data.get("industry", "未知")
    desc = data.get("description", "暂无详细描述")
    market_cap = data.get("market_cap", "未知")
    return "## 1. 公司概况\n\n| 项目 | 内容 |\n|:---|---:|\n| 公司名称 | " + name + " |\n| 股票代码 | " + ticker + " |\n| 所属行业 | " + industry + " |\n| 总市值 | " + market_cap + " |\n\n**公司简介**\n\n" + desc + "\n\n---"


def _generate_financial_analysis(data: dict) -> str:
    revenues = data.get("revenue", [])
    years = data.get("revenue_years", [])
    net_profits = data.get("net_profit", [])
    margins = data.get("gross_margin", [])
    roe = data.get("roe", [])
    if not revenues:
        return "## 2. 财务分析\n\n数据暂不可用\n\n---"
    rows = ["## 2. 财务分析\n"]
    rows.append("| 年份 | 营收(亿元) | 净利润(亿元) | 毛利率 | ROE |")
    rows.append("|:---|:---:|:---:|:---:|:---:|")
    for i in range(min(len(years), len(revenues))):
        rev = revenues[i]
        np_ = net_profits[i] if i < len(net_profits) else "-"
        gm = f"{margins[i]:.1%}" if i < len(margins) else "-"
        r = f"{roe[i]:.1%}" if i < len(roe) else "-"
        rows.append(f"| {years[i]} | {rev} | {np_} | {gm} | {r} |")
    if len(revenues) >= 2 and revenues[1] > 0:
        growth = (revenues[0] - revenues[1]) / revenues[1] * 100
        rows.append(f"\n近一年营收增速：{growth:.1f}%")
    rows.append("\n---")
    return "\n".join(rows)


def _generate_health_scorecard(detective: dict) -> str:
    score = detective.get("overall_score", 0)
    status = detective.get("overall_status", "yellow")
    items = detective.get("items", [])
    if status == "green":
        status_text = "健康"
    elif status == "yellow":
        status_text = "需关注"
    else:
        status_text = "重大风险"
    bar = "#" * int(score / 10) + "-" * (10 - int(score / 10))
    lines = ["## 3. 财务健康评分卡\n"]
    lines.append(f"综合评分：{bar} {score:.1f}/100 | 状态：{status} {status_text}\n")
    red = detective.get("red_flags", 0)
    yellow = detective.get("yellow_flags", 0)
    if red > 0:
        lines.append(f"发现{red}项红灯 + {yellow}项黄灯，建议深入核查\n")
    else:
        lines.append("所有检测项均为绿灯，财务状况健康\n")
    lines.append("| 检测项 | 状态 | 评分 |")
    lines.append("|:---|---:|:---:|")
    for item in items:
        lines.append(f"| {item['name']} | {item['status']} | {item['score']:.1f} |")
        ds = item["detail"][:50] + "..." if len(item["detail"]) > 50 else item["detail"]
        lines.append(f"| | {ds} | |")
    lines.append("\n---")
    return "\n".join(lines)


def _generate_recent_events(announcements: List[dict]) -> str:
    if not announcements:
        return "## 4. 近期重大事件\n\n暂无公告数据\n\n---"
    level_order = {"S": 0, "A": 1, "B": 2, "C": 3}
    sorted_anns = sorted(announcements, key=lambda x: level_order.get(x.get("level", "C"), 4))
    lines = ["## 4. 近期重大事件\n"]
    labels = {"S": "重大", "A": "重要", "B": "一般", "C": "例行"}
    for ann in sorted_anns[:8]:
        lv = ann.get("level", "C")
        lines.append(f"- **{ann['date']}** [{labels.get(lv, lv)}] **{ann['title']}**")
        lines.append(f"  - {ann.get('summary', '')}")
    lines.append("\n---")
    return "\n".join(lines)


def _generate_industry_outlook(data: dict) -> str:
    industry = data.get("industry", "未知行业")
    outlooks = {
        "白酒": "白酒行业进入存量竞争时代，头部品牌集中度持续提升。关注消费复苏节奏和渠道库存变化。",
        "房地产开发": "房地产行业处于筑底企稳阶段，政策端持续回暖。关注销售复苏和融资环境变化。",
        "电池": "新能源电池行业高增长但竞争加剧。龙头企业在技术迭代和海外布局方面具备优势。",
    }
    outlook = outlooks.get(industry, industry + "行业受宏观环境影响较大，建议关注政策变化。")
    return "## 5. 行业展望\n\n**所属行业：" + industry + "**\n\n" + outlook + "\n\n---"


def _generate_risk_disclosure(detective: dict) -> str:
    items = detective.get("items", [])
    red_items = [i for i in items if i["status"] == "red"]
    risks = ["1. **宏观经济风险**：经济增长放缓可能影响公司经营业绩"]
    if red_items:
        for i, item in enumerate(red_items):
            risks.append(f"{i+2}. **{item['name']}风险**")
    risks.append(f"{len(risks)+1}. 本报告由AI自动生成，仅供参考，不构成投资建议")
    return "## 6. 风险提示\n\n" + "\n".join(risks) + "\n\n---"


def _generate_valuation_summary(data: dict, detective: dict) -> str:
    score = detective.get("overall_score", 0)
    pe = data.get("pe_ratio", [])
    latest_pe = pe[0] if pe else "暂无"
    if score >= 70:
        conclusion = "基本面稳健，适合长期持有关注"
    elif score >= 50:
        conclusion = "需谨慎评估，建议进一步调研"
    else:
        conclusion = "风险较高，不建议重仓"
    return "## 7. 估值总结\n\n| 指标 | 数值 |\n|:---|:---:|\n| 财务健康评分 | " + str(score) + "/100 |\n| 当前市盈率 | " + str(latest_pe) + " |\n| 评估结论 | " + conclusion + " |\n\n---"


def _generate_disclaimer() -> str:
    return "> 免责声明：本报告由 AlphaReport AI 系统自动生成，数据来源于公开信息，仅供参考，不构成投资建议。\n\n---\n\n*AlphaReport - 让每一个投资者都拥有机构级投研能力*"
