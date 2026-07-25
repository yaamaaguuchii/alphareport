"""
财务侦探（Financial Detective）
自动识别财务异常与粉饰信号，输出红黄绿灯健康评分卡

检测维度：
1. 勾稽关系校验 - 经营性现金流 vs 净利润
2. 应收账款异常 - 应收账款增速 vs 营收增速
3. 存货异常 - 存货周转天数变化
4. 关联交易排查 - 关联交易占比
5. 现金流画像 - 经营/投资/筹资组合
6. 偿债能力 - 资产负债率、流动比率
7. 营收质量 - 毛利率稳定性
"""

from typing import Dict, List, Tuple
import numpy as np

from src.config import (
    RECEIVABLE_REVENUE_RATIO_THRESHOLD,
    CASHFLOW_PROFIT_RATIO_THRESHOLD,
    INVENTORY_TURNOVER_INCREASE_THRESHOLD,
    RELATED_PARTY_RATIO_THRESHOLD,
    DEBT_RATIO_THRESHOLD,
    CASHFLOW_PROFILES,
)


class DetectiveReportItem:
    """单个检测项的结果"""

    def __init__(self, name: str, status: str, detail: str, score: float):
        """
        status: "red" / "yellow" / "green"
        score: 0.0 (最差) ~ 1.0 (最佳)
        """
        self.name = name
        self.status = status
        self.detail = detail
        self.score = score

    def to_dict(self):
        return {
            "name": self.name,
            "status": self.status,
            "detail": self.detail,
            "score": self.score,
        }


class FinancialDetective:
    """财务侦探引擎"""

    def __init__(self, company_data: dict):
        self.data = company_data
        self.items: List[DetectiveReportItem] = []
        self._run_all_checks()

    def _run_all_checks(self):
        """运行所有检测"""
        self._check_cashflow_profit()
        self._check_receivable_revenue()
        self._check_inventory()
        self._check_related_party()
        self._check_debt_ratio()
        self._check_cashflow_profile()
        self._check_gross_margin()

    def _safe_get(self, key: str, default=None):
        """安全获取数据"""
        return self.data.get(key, default)

    def _check_cashflow_profit(self):
        """
        规则1：利润含金量检测
        经营性现金流净额 / 净利润 比率
        """
        net_profits = self._safe_get("net_profit", [])
        cashflows = self._safe_get("operating_cashflow", [])

        if len(net_profits) < 3 or len(cashflows) < 3:
            self.items.append(DetectiveReportItem(
                "利润含金量", "yellow",
                "数据不足，无法完整评估利润质量", 0.5
            ))
            return

        ratios = []
        details = []
        years = self._safe_get("revenue_years", list(range(len(net_profits))))

        for i in range(len(net_profits)):
            if net_profits[i] and net_profits[i] > 0:
                ratio = cashflows[i] / net_profits[i]
                ratios.append(ratio)
                details.append(f"{years[i]}: {ratio:.2f}")

        if not ratios:
            self.items.append(DetectiveReportItem(
                "利润含金量", "yellow",
                "净利润数据异常，无法计算", 0.5
            ))
            return

        avg_ratio = np.mean(ratios)
        recent_ratio = ratios[-1] if ratios else 0

        if avg_ratio < CASHFLOW_PROFIT_RATIO_THRESHOLD or recent_ratio < CASHFLOW_PROFIT_RATIO_THRESHOLD:
            status = "red"
            detail = (f"该公司近3年经营现金流/净利润比率均值{avg_ratio:.2f}，"
                      f"低于阈值{CASHFLOW_PROFIT_RATIO_THRESHOLD}。"
                      f"净利润含金量偏低，赚到的钱没有真正变成现金，"
                      f"可能存在大量应收账款或利润操纵风险。"
                      f"比率趋势：{' → '.join(details[-3:])}")
            score = max(0, avg_ratio)
        elif avg_ratio < 0.7:
            status = "yellow"
            detail = (f"该公司近3年经营现金流/净利润比率均值{avg_ratio:.2f}，"
                      f"处于需要关注的水平。比率趋势：{' → '.join(details[-3:])}")
            score = avg_ratio
        else:
            status = "green"
            detail = (f"该公司近3年经营现金流/净利润比率均值{avg_ratio:.2f}，"
                      f"利润含金量良好。比率趋势：{' → '.join(details[-3:])}")
            score = min(1.0, avg_ratio)

        self.items.append(DetectiveReportItem("利润含金量", status, detail, score))

    def _check_receivable_revenue(self):
        """
        规则2：应收账款增速 vs 营收增速
        如果前者长期大幅高于后者，可能意味着公司通过放宽信用政策突击营收
        """
        receivables = self._safe_get("receivables", [])
        revenues = self._safe_get("revenue", [])

        if len(receivables) < 3 or len(revenues) < 3:
            self.items.append(DetectiveReportItem(
                "应收账款异常", "yellow",
                "数据不足，无法完整评估", 0.5
            ))
            return

        # 计算增速
        rec_growths = []
        rev_growths = []
        for i in range(1, len(receivables)):
            if receivables[i - 1] > 0 and revenues[i - 1] > 0:
                rec_growths.append((receivables[i] - receivables[i - 1]) / receivables[i - 1])
                rev_growths.append((revenues[i] - revenues[i - 1]) / revenues[i - 1])

        if not rec_growths:
            self.items.append(DetectiveReportItem(
                "应收账款异常", "yellow",
                "数据异常，无法计算增速", 0.5
            ))
            return

        # 判断是否有连续报警
        alert_count = sum(
            1 for i in range(len(rec_growths))
            if rev_growths[i] > 0 and rec_growths[i] > rev_growths[i] * RECEIVABLE_REVENUE_RATIO_THRESHOLD
        )

        rec_avg = np.mean(rec_growths[-2:]) if len(rec_growths) >= 2 else rec_growths[-1]
        rev_avg = np.mean(rev_growths[-2:]) if len(rev_growths) >= 2 else rev_growths[-1]

        if alert_count >= 2:
            status = "red"
            detail = (f"应收账款增速（近2年均值{rec_avg:.1%}）连续多期显著高于营收增速"
                      f"（近2年均值{rev_avg:.1%}），超过阈值{RECEIVABLE_REVENUE_RATIO_THRESHOLD}倍。"
                      f"可能意味着：① 公司放松信用政策刺激销售；② 回款困难，坏账风险上升；"
                      f"③ 存在财务粉饰嫌疑。建议查阅应收账款账龄结构。")
            score = max(0, 1.0 - alert_count * 0.3)
        elif alert_count >= 1:
            status = "yellow"
            detail = (f"应收账款增速（{rec_avg:.1%}）高于营收增速（{rev_avg:.1%}），"
                      f"需关注回款情况。")
            score = 0.6
        else:
            status = "green"
            detail = (f"应收账款增速（{rec_avg:.1%}）与营收增速（{rev_avg:.1%}）基本匹配，"
                      f"回款状况正常。")
            score = 0.9

        self.items.append(DetectiveReportItem("应收账款异常", status, detail, score))

    def _check_inventory(self):
        """
        规则3：存货周转天数异常检测
        存货周转天数突然上升 + 营收增长放缓 → 可能存在滞销风险
        """
        inventory_days = self._safe_get("inventory_days", [])
        revenues = self._safe_get("revenue", [])

        if len(inventory_days) < 3:
            self.items.append(DetectiveReportItem(
                "存货异常", "yellow",
                "数据不足，无法完整评估", 0.5
            ))
            return

        # 计算最近一年的周转天数增幅
        if inventory_days[-2] > 0:
            latest_change = (inventory_days[-1] - inventory_days[-2]) / inventory_days[-2]
        else:
            latest_change = 0

        # 检查营收增长是否放缓
        rev_growth = 0
        if len(revenues) >= 2 and revenues[-2] > 0:
            rev_growth = (revenues[-1] - revenues[-2]) / revenues[-2]

        days_trend = " → ".join([str(d) for d in inventory_days[-4:]])

        if latest_change > INVENTORY_TURNOVER_INCREASE_THRESHOLD and rev_growth < 0.05:
            status = "red"
            detail = (f"存货周转天数从{inventory_days[-2]}天上升至{inventory_days[-1]}天"
                      f"（增幅{latest_change:.1%}），同时营收增长放缓（{rev_growth:.1%}）。"
                      f"可能存在滞销风险或存货积压问题。趋势：{days_trend}")
            score = max(0, 1.0 - latest_change)
        elif latest_change > INVENTORY_TURNOVER_INCREASE_THRESHOLD * 0.5:
            status = "yellow"
            detail = (f"存货周转天数从{inventory_days[-2]}天上升至{inventory_days[-1]}天"
                      f"（增幅{latest_change:.1%}），需关注存货管理效率。趋势：{days_trend}")
            score = 0.6
        else:
            status = "green"
            detail = (f"存货周转天数稳定在{inventory_days[-1]}天左右，存货管理正常。"
                      f"趋势：{days_trend}")
            score = 0.9

        self.items.append(DetectiveReportItem("存货异常", status, detail, score))

    def _check_related_party(self):
        """
        规则4：关联交易排查
        """
        related_ratio = self._safe_get("related_party_ratio", 0)

        if related_ratio > RELATED_PARTY_RATIO_THRESHOLD:
            status = "red"
            detail = (f"关联交易占总采购/销售比例达{related_ratio:.0%}，"
                      f"超过阈值{RELATED_PARTY_RATIO_THRESHOLD:.0%}。"
                      f"需要关注交易定价的公允性，可能存在利益输送风险。"
                      f"建议查阅关联交易明细及独立董事意见。")
            score = max(0, 1.0 - related_ratio * 2)
        elif related_ratio > RELATED_PARTY_RATIO_THRESHOLD * 0.5:
            status = "yellow"
            detail = (f"关联交易占比{related_ratio:.0%}，处于需要关注的水平。"
                      f"建议后续持续跟踪。")
            score = 0.6
        else:
            status = "green"
            detail = (f"关联交易占比{related_ratio:.0%}，处于正常水平。")
            score = 0.9

        self.items.append(DetectiveReportItem("关联交易排查", status, detail, score))

    def _check_debt_ratio(self):
        """
        规则5：偿债能力检测
        """
        debt_ratios = self._safe_get("debt_ratio", [])
        current_ratios = self._safe_get("current_ratio", [])

        if not debt_ratios:
            self.items.append(DetectiveReportItem(
                "偿债能力", "yellow",
                "数据不足，无法评估", 0.5
            ))
            return

        latest_debt = debt_ratios[-1]
        latest_current = current_ratios[-1] if current_ratios else 1.0

        issues = []
        score = 1.0

        if latest_debt > DEBT_RATIO_THRESHOLD:
            issues.append(f"资产负债率{latest_debt:.0%}超过阈值{DEBT_RATIO_THRESHOLD:.0%}")
            score -= 0.3

        if latest_current < 1.5:
            issues.append(f"流动比率{latest_current:.1f}偏低")
            score -= 0.2

        if issues:
            if latest_debt > DEBT_RATIO_THRESHOLD and latest_current < 1.0:
                status = "red"
                detail = (f"偿债能力存在显著风险：{'；'.join(issues)}。"
                          f"该公司可能面临短期偿债压力。")
            elif latest_debt > DEBT_RATIO_THRESHOLD or latest_current < 1.2:
                status = "red"
                detail = (f"偿债能力需关注：{'；'.join(issues)}。"
                          f"建议持续跟踪债务结构和现金流状况。")
            else:
                status = "yellow"
                detail = f"偿债能力略有隐忧：{'；'.join(issues)}。"
        else:
            status = "green"
            detail = (f"资产负债率{latest_debt:.0%}，流动比率{latest_current:.1f}，"
                      f"偿债能力健康。")

        self.items.append(DetectiveReportItem("偿债能力", status, detail, max(0.0, score)))

    def _check_cashflow_profile(self):
        """
        规则6：现金流画像分析
        通过经营/投资/筹资现金流的正负组合判断公司所处阶段
        """
        net_profits = self._safe_get("net_profit", [])
        cashflows = self._safe_get("operating_cashflow", [])

        if len(net_profits) < 1:
            self.items.append(DetectiveReportItem(
                "现金流画像", "yellow",
                "数据不足，无法判断现金流模式", 0.5
            ))
            return

        # 简化判断：根据经营现金流和净利润的关系给出画像
        latest_cf = cashflows[-1] if cashflows else 0
        latest_profit = net_profits[-1] if net_profits else 0

        if latest_cf > 0 and latest_profit > 0:
            profile = "奶牛型"
            status = "green"
            detail = (f"现金流画像：{profile}。经营活动现金流为正且利润为正，"
                      f"公司具备自我造血能力，属于成熟健康型公司。")
            score = 0.9
        elif latest_cf > 0 and latest_profit <= 0:
            profile = "金牛型"
            status = "yellow"
            detail = (f"现金流画像：{profile}。虽然经营现金流为正，"
                      f"但净利润为负，需关注是否有大规模非经常性损益。")
            score = 0.5
        elif latest_cf <= 0 and latest_profit > 0:
            profile = "风险型"
            status = "red"
            detail = (f"现金流画像：{profile}。经营活动现金流为负但净利润为正，"
                      f"利润含金量极低，赚到的钱没有变成真金白银，"
                      f"需要警惕财务粉饰风险。")
            score = 0.2
        else:
            profile = "问题型"
            status = "red"
            detail = (f"现金流画像：{profile}。经营现金流和净利润均为负，"
                      f"公司处于持续失血状态，需谨慎评估持续经营能力。")
            score = 0.1

        self.items.append(DetectiveReportItem("现金流画像", status, detail, score))

    def _check_gross_margin(self):
        """
        规则7：毛利率稳定性检测
        毛利率大幅波动可能意味着业务结构变化或财务操纵
        """
        margins = self._safe_get("gross_margin", [])

        if len(margins) < 3:
            self.items.append(DetectiveReportItem(
                "毛利率稳定性", "yellow",
                "数据不足，无法完整评估", 0.5
            ))
            return

        margin_std = np.std(margins)
        margin_mean = np.mean(margins)

        if margin_mean > 0:
            cv = margin_std / margin_mean  # 变异系数
        else:
            cv = 1.0

        margin_trend = " → ".join([f"{m:.1%}" for m in margins[-4:]])

        if cv > 0.15:
            status = "red"
            detail = (f"毛利率波动较大（变异系数{cv:.2f}），"
                      f"近4年趋势：{margin_trend}。"
                      f"可能原因：① 业务结构发生重大变化；"
                      f"② 产品竞争力不稳定；③ 存在财务调节嫌疑。")
            score = max(0, 1.0 - cv * 3)
        elif cv > 0.08:
            status = "yellow"
            detail = (f"毛利率有一定波动（变异系数{cv:.2f}），"
                      f"近4年趋势：{margin_trend}。需关注业务稳定性。")
            score = 0.6
        else:
            status = "green"
            detail = (f"毛利率保持稳定（均值{margin_mean:.1%}），"
                      f"近4年趋势：{margin_trend}。产品竞争力稳健。")
            score = 0.9

        self.items.append(DetectiveReportItem("毛利率稳定性", status, detail, score))

    def get_overall_score(self) -> float:
        """获取综合健康评分 0-100"""
        if not self.items:
            return 0
        scores = [item.score for item in self.items]
        return round(np.mean(scores) * 100, 1)

    def get_overall_status(self) -> str:
        """获取综合健康状态"""
        score = self.get_overall_score()
        if score >= 80:
            return "green"
        elif score >= 55:
            return "yellow"
        else:
            return "red"

    def get_summary(self) -> Dict:
        """获取完整的检测报告"""
        red_count = sum(1 for item in self.items if item.status == "red")
        yellow_count = sum(1 for item in self.items if item.status == "yellow")
        green_count = sum(1 for item in self.items if item.status == "green")

        return {
            "company_name": self._safe_get("name", ""),
            "ticker": self._safe_get("ticker", ""),
            "overall_score": self.get_overall_score(),
            "overall_status": self.get_overall_status(),
            "total_checks": len(self.items),
            "red_flags": red_count,
            "yellow_flags": yellow_count,
            "green_flags": green_count,
            "items": [item.to_dict() for item in self.items],
        }


def run_detective(company_data: dict) -> Dict:
    """快捷入口：运行财务侦探"""
    detective = FinancialDetective(company_data)
    return detective.get_summary()
