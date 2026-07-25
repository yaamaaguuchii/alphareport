"""AlphaReport 核心功能测试"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_fetcher import get_company_data, get_mock_announcements, get_available_mock_tickers
from src.financial_detective import run_detective
from src.announcement_analyzer import build_event_timeline, get_announcement_summary
from src.report_generator import generate_report

def test_financial_detective():
    """测试财务侦探：三个公司的评分差异"""
    tickers = get_available_mock_tickers()
    assert len(tickers) == 3
    
    for ticker in tickers:
        data = get_company_data(ticker, use_mock=True)
        result = run_detective(data)
        assert "overall_score" in result
        assert "overall_status" in result
        assert len(result["items"]) == 7
        print(f"[OK] {data['name']}: {result['overall_score']}/100, {result['red_flags']} red flags")


def test_report_generation():
    """测试研报生成"""
    data = get_company_data("600519", use_mock=True)
    result = run_detective(data)
    anns = build_event_timeline(get_mock_announcements("600519"))
    report = generate_report(data, result, anns)
    assert len(report) > 500
    assert "贵州茅台" in report
    print(f"[OK] Report generated: {len(report)} chars")


def test_announcement_analysis():
    """测试公告分析"""
    anns = build_event_timeline(get_mock_announcements("600519"))
    summary = get_announcement_summary(anns)
    assert summary["total"] > 0
    print(f"[OK] Announcements: {summary['total']} total, {summary['s_count']} S-level")


if __name__ == "__main__":
    test_financial_detective()
    test_report_generation()
    test_announcement_analysis()
    print("\n=== All tests passed! ===")
