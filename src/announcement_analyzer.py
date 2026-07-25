"""
公告智能摘要与关联挖掘
对上市公司公告进行摘要、分级和事件关联分析
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta


# 公告级别定义
ANNOUNCEMENT_LEVELS = {
    "S": {"label": "重大", "color": "red", "description": "可能对股价产生重大影响"},
    "A": {"label": "重要", "color": "orange", "description": "对公司基本面有显著影响"},
    "B": {"label": "一般", "color": "blue", "description": "常规业务/公司治理信息"},
    "C": {"label": "例行", "color": "gray", "description": "例行公事，无需特别关注"},
}

# 历史类似事件统计（模拟数据）
HISTORICAL_STATS = {
    "分红": {"avg_return_5d": 0.5, "win_rate": 0.55, "sample_count": 120},
    "定期报告": {"avg_return_5d": 1.2, "win_rate": 0.58, "sample_count": 200},
    "投资": {"avg_return_5d": -0.3, "win_rate": 0.48, "sample_count": 85},
    "合同": {"avg_return_5d": 1.5, "win_rate": 0.60, "sample_count": 60},
    "回购": {"avg_return_5d": 2.0, "win_rate": 0.65, "sample_count": 40},
    "增持": {"avg_return_5d": 1.8, "win_rate": 0.62, "sample_count": 35},
    "业绩预告": {"avg_return_5d": 2.5, "win_rate": 0.55, "sample_count": 90},
    "人事变动": {"avg_return_5d": -0.8, "win_rate": 0.45, "sample_count": 50},
    "融资": {"avg_return_5d": 0.1, "win_rate": 0.50, "sample_count": 70},
    "担保": {"avg_return_5d": -0.5, "win_rate": 0.40, "sample_count": 30},
    "业务进展": {"avg_return_5d": 1.0, "win_rate": 0.55, "sample_count": 45},
}


def analyze_announcement(ann: dict) -> dict:
    """
    分析单条公告
    返回带 AI 解读的完整信息
    """
    anl_type = ann.get("type", "其他")
    stats = HISTORICAL_STATS.get(anl_type, {"avg_return_5d": 0, "win_rate": 0.5, "sample_count": 10})

    return {
        **ann,
        "historical_stat": stats,
        "ai_interpretation": _generate_interpretation(ann, stats),
    }


def _generate_interpretation(ann: dict, stats: dict) -> str:
    """生成 AI 解读"""
    level = ann.get("level", "B")
    anl_type = ann.get("type", "其他")
    title = ann.get("title", "")

    interpretations = {
        "S": f"【市场影响】此公告类型'{anl_type}'历史上发布后5日平均涨跌幅{stats['avg_return_5d']:+.1f}%，"
             f"上涨概率{stats['win_rate']:.0%}（样本{stats['sample_count']}次），建议重点关注。",
        "A": f"【需要关注】'{title[:20]}...'属于{anl_type}类公告，"
             f"历史统计显示短期上涨概率{stats['win_rate']:.0%}。建议结合当前估值综合判断。",
        "B": f"【例行信息】属于常规{anl_type}公告，对公司长期价值影响有限，适当关注即可。",
        "C": f"【无需特别关注】属于例行公事型公告，不改变对公司基本面的判断。",
    }

    return interpretations.get(level, interpretations["C"])


def build_event_timeline(announcements: List[dict]) -> List[dict]:
    """
    构建事件时间线
    将公告按时间排序并串联成事件链
    """
    sorted_anns = sorted(announcements, key=lambda x: x["date"], reverse=True)
    return [analyze_announcement(ann) for ann in sorted_anns]


def find_related_events(announcements: List[dict], target_type: str) -> List[dict]:
    """
    关联分析：找到同一类型的事件序列
    例如：定增预案 → 定增获批 → 定增完成
    """
    related = [ann for ann in announcements if ann.get("type") == target_type]
    return sorted(related, key=lambda x: x["date"])


def get_announcement_summary(announcements: List[dict]) -> dict:
    """
    获取公告整体摘要
    - 各等级公告数量
    - 最近重要公告
    - AI 综合判断
    """
    if not announcements:
        return {"summary": "近一年暂无公告数据", "s_count": 0, "a_count": 0, "b_count": 0}

    s_count = sum(1 for a in announcements if a.get("level") == "S")
    a_count = sum(1 for a in announcements if a.get("level") == "A")
    b_count = sum(1 for a in announcements if a.get("level") == "B")

    # 找最近的重要公告
    important = [a for a in announcements if a.get("level") in ("S", "A")]
    recent_important = sorted(important, key=lambda x: x["date"], reverse=True)[:3]

    if s_count > 0:
        summary = f"近一年共有{s_count}条重大公告（S级）、{a_count}条重要公告（A级），建议重点关注。"
    elif a_count > 0:
        summary = f"近一年共有{a_count}条重要公告（A级），无重大级别公告，整体平静。"
    else:
        summary = "近一年无重大或重要公告，公司处于信息平静期。"

    return {
        "summary": summary,
        "s_count": s_count,
        "a_count": a_count,
        "b_count": b_count,
        "recent_important": recent_important,
        "total": len(announcements),
    }


def get_timeline_data_for_plotly(announcements: List[dict]) -> dict:
    """
    生成 Plotly 时间线可视化所需的数据
    """
    colors = {"S": "red", "A": "orange", "B": "blue", "C": "gray"}
    sizes = {"S": 20, "A": 14, "B": 10, "C": 6}

    data = []
    for ann in announcements:
        data.append({
            "date": ann["date"],
            "title": ann["title"],
            "level": ann.get("level", "C"),
            "color": colors.get(ann.get("level", "C"), "gray"),
            "size": sizes.get(ann.get("level", "C"), 6),
            "type": ann.get("type", ""),
        })

    return {"events": sorted(data, key=lambda x: x["date"])}
