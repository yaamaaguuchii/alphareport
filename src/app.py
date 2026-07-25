import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_fetcher import get_company_data, get_mock_announcements, get_available_mock_tickers
from src.financial_detective import run_detective
from src.announcement_analyzer import analyze_announcement, build_event_timeline, get_announcement_summary
from src.report_generator import generate_report

st.set_page_config(
    page_title="AlphaReport - 智能投研工作台",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .main-header { font-size: 2rem; font-weight: 700; color: #1a1a2e; }
    .sub-header { font-size: 1rem; color: #666; margin-bottom: 2rem; }
    .score-green { color: #00a86b; font-weight: bold; }
    .score-yellow { color: #e6a817; font-weight: bold; }
    .score-red { color: #e74c3c; font-weight: bold; }
    .status-badge { padding: 0.25rem 0.75rem; border-radius: 12px; font-size: 0.85rem; font-weight: 600; }
    .badge-green { background-color: #d4edda; color: #155724; }
    .badge-yellow { background-color: #fff3cd; color: #856404; }
    .badge-red { background-color: #f8d7da; color: #721c24; }
    .section-card { background: #f8f9fa; border-radius: 10px; padding: 1.5rem; margin: 1rem 0; border: 1px solid #e9ecef; }
    .metric-card { background: white; border-radius: 10px; padding: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    .footer { text-align: center; color: #999; font-size: 0.8rem; margin-top: 3rem; padding-top: 1rem; border-top: 1px solid #eee; }
    h2 { margin-top: 1.5rem; }
    .stTab { font-size: 1.1rem; font-weight: 500; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">📊 AlphaReport 智能投研工作台</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">面向长期价值投资者的 AI 投研工具 — 机构级研究能力，一键触达</div>', unsafe_allow_html=True)

stock_options = {
    "600519": "贵州茅台 (600519)",
    "300750": "宁德时代 (300750)",
    "000002": "万科A (000002)",
}

col1, col2 = st.columns([3, 1])
with col1:
    selected_label = st.selectbox(
        "选择股票",
        options=list(stock_options.values()),
        index=0,
        label_visibility="collapsed",
    )
    ticker = [k for k, v in stock_options.items() if v == selected_label][0]

with col2:
    use_mock = st.checkbox("使用模拟数据(演示模式)", value=True, help="勾选后使用预置数据，无需网络连接")

load_btn = st.button("🔍 开始分析", type="primary", use_container_width=True)

if load_btn or "analyzed" in st.session_state:
    st.session_state["analyzed"] = True

    with st.spinner("正在获取数据并进行分析..."):
        company_data = get_company_data(ticker, use_mock=use_mock)
        detective_result = run_detective(company_data)
        announcements_raw = get_mock_announcements(ticker) if use_mock else []
        announcements = build_event_timeline(announcements_raw)

    st.session_state["company_data"] = company_data
    st.session_state["detective_result"] = detective_result
    st.session_state["announcements"] = announcements

    if "company_data" in st.session_state:
        data = st.session_state["company_data"]
        detective = st.session_state["detective_result"]
        anns = st.session_state["announcements"]

        tab1, tab2, tab3, tab4 = st.tabs(["📄 完整研报", "🔍 财务侦探", "📢 公告追踪", "📊 数据看板"])

        with tab1:
            col_left, col_right = st.columns([2, 1])

            with col_left:
                st.subheader(f"{data.get('name', '')}（{data.get('ticker', '')}）")
                st.markdown(f"行业：{data.get('industry', '')} | 市值：{data.get('market_cap', '')}")

            with col_right:
                score = detective.get("overall_score", 0)
                if score >= 70:
                    st.markdown(f'<div class="score-green" style="font-size:1.5rem;">🟢 财务健康评分：{score}/100</div>', unsafe_allow_html=True)
                elif score >= 55:
                    st.markdown(f'<div class="score-yellow" style="font-size:1.5rem;">🟡 财务健康评分：{score}/100</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="score-red" style="font-size:1.5rem;">🔴 财务健康评分：{score}/100</div>', unsafe_allow_html=True)

            st.markdown(f"**公司简介**")
            st.markdown(data.get("description", "暂无数据"))

            st.divider()

            st.subheader("财务分析")
            revenues = data.get("revenue", [])
            years = data.get("revenue_years", [])
            net_profits = data.get("net_profit", [])
            margins = data.get("gross_margin", [])

            if revenues:
                fin_df = pd.DataFrame({
                    "年份": years,
                    "营收(亿元)": revenues,
                    "净利润(亿元)": net_profits,
                })
                st.dataframe(fin_df, use_container_width=True, hide_index=True)

                fig = go.Figure()
                fig.add_trace(go.Bar(name="营收(亿元)", x=years, y=revenues, marker_color="#3498db"))
                fig.add_trace(go.Bar(name="净利润(亿元)", x=years, y=net_profits, marker_color="#2ecc71"))
                fig.update_layout(title="营收与净利润趋势", barmode="group", height=350)
                st.plotly_chart(fig, use_container_width=True)

            st.divider()

            st.subheader("近期重大事件")
            for ann in anns[:5]:
                level = ann.get("level", "C")
                icons = {"S": "🔴", "A": "🟠", "B": "🔵", "C": "⚪"}
                st.markdown(f"- {icons.get(level, '⚪')} **{ann['date']}** {ann['title']}")
                st.markdown(f"  - {ann.get('summary', '')}")

            st.divider()

            st.subheader("风险提示")
            items = detective.get("items", [])
            red_items = [i for i in items if i["status"] == "red"]
            if red_items:
                for item in red_items:
                    st.warning(f"**{item['name']}**：{item['detail'][:80]}...")
            st.info("免责声明：本报告由 AI 自动生成，仅供参考，不构成投资建议。")

            st.divider()

            report_md = generate_report(data, detective, anns, include_llm=False)
            with st.expander("📝 查看完整 Markdown 研报"):
                st.markdown(report_md)

            st.download_button(
                label="📥 下载研报 (Markdown)",
                data=report_md,
                file_name=f"{data.get('ticker', 'stock')}_AlphaReport_{datetime.now().strftime('%Y%m%d')}.md",
                mime="text/markdown",
                use_container_width=True,
            )

        with tab2:
            st.subheader("🔍 财务侦探 - 健康评分卡")
            st.markdown("AlphaReport 独家财务异常检测引擎，基于7大维度自动识别财务粉饰信号。")

            score = detective.get("overall_score", 0)
            status = detective.get("overall_status", "yellow")
            st.markdown(f"### 综合评分：{score}/100")
            st.progress(score / 100)

            col1, col2, col3 = st.columns(3)
            col1.metric("🟢 正常项", detective.get("green_flags", 0))
            col2.metric("🟡 需关注", detective.get("yellow_flags", 0))
            col3.metric("🔴 风险项", detective.get("red_flags", 0))

            st.divider()

            for item in detective.get("items", []):
                if item["status"] == "green":
                    icon, border = "🟢", "2px solid #00a86b"
                elif item["status"] == "yellow":
                    icon, border = "🟡", "2px solid #e6a817"
                else:
                    icon, border = "🔴", "2px solid #e74c3c"

                st.markdown(f"""
                <div style="border-left: {border}; padding-left: 1rem; margin: 0.8rem 0; background: #fafafa; border-radius: 4px; padding: 0.8rem;">
                    <strong>{icon} {item['name']}</strong> &nbsp; 评分：{item['score']:.2f}
                    <br><small style="color: #666;">{item['detail'][:150]}</small>
                </div>
                """, unsafe_allow_html=True)

        with tab3:
            st.subheader("📢 公告追踪 - 智能摘要与关联分析")

            summary = get_announcement_summary(anns)
            st.info(summary["summary"])

            col1, col2, col3 = st.columns(3)
            col1.metric("🔴 重大(S级)", summary.get("s_count", 0))
            col2.metric("🟠 重要(A级)", summary.get("a_count", 0))
            col3.metric("🔵 一般(B级)", summary.get("b_count", 0))

            st.divider()

            if anns:
                ann_df = pd.DataFrame([
                    {"日期": a["date"], "标题": a["title"], "类型": a.get("type", ""),
                     "级别": a.get("level", "C"), "摘要": a.get("summary", "")}
                    for a in anns
                ])
                st.dataframe(ann_df, use_container_width=True, hide_index=True)

                st.divider()
                st.subheader("⏱ 事件时间线")

                ann_sorted = sorted(anns, key=lambda x: x["date"])
                fig = go.Figure()
                level_colors = {"S": "red", "A": "orange", "B": "blue", "C": "gray"}
                level_sizes = {"S": 18, "A": 12, "B": 8, "C": 5}

                for ann in ann_sorted:
                    lv = ann.get("level", "C")
                    fig.add_trace(go.Scatter(
                        x=[ann["date"]], y=[ann.get("type", "其他")],
                        mode="markers",
                        marker=dict(size=level_sizes.get(lv, 6), color=level_colors.get(lv, "gray")),
                        name=ann["title"][:20],
                        text=ann["title"],
                        hoverinfo="text",
                        showlegend=False,
                    ))

                fig.update_layout(title="公告时间线（红色=重大，橙色=重要，蓝色=一般）",
                                  height=300, xaxis_title="日期", yaxis_title="公告类型")
                st.plotly_chart(fig, use_container_width=True)

                st.divider()
                st.subheader("历史类似事件统计")
                types_found = set(a.get("type", "其他") for a in anns)
                for t in types_found:
                    hist = analyze_announcement({"type": t, "level": "A", "title": "", "date": ""})
                    hs = hist.get("historical_stat", {})
                    st.markdown(f"- **{t}**：历史5日平均涨幅{hs.get('avg_return_5d', 0):+.1f}%，上涨概率{hs.get('win_rate', 0):.0%}（样本{hs.get('sample_count', 0)}次）")

        with tab4:
            st.subheader("📊 数据看板 - 核心指标一览")

            revenues = data.get("revenue", [])
            years = data.get("revenue_years", [])
            net_profits = data.get("net_profit", [])
            margins = data.get("gross_margin", [])
            roe = data.get("roe", [])
            debt_ratios = data.get("debt_ratio", [])
            cashflows = data.get("operating_cashflow", [])

            cols = st.columns(4)
            if margins:
                cols[0].metric("最新毛利率", f"{margins[-1]:.1%}", f"{margins[-1]-margins[-2]:+.1%}" if len(margins)>=2 else None)
            if roe:
                cols[1].metric("最新ROE", f"{roe[-1]:.1%}", f"{roe[-1]-roe[-2]:+.1%}" if len(roe)>=2 else None)
            if cashflows and net_profits and net_profits[-1] > 0:
                cf_ratio = cashflows[-1] / net_profits[-1]
                cols[2].metric("利润含金量", f"{cf_ratio:.2f}")
            if debt_ratios:
                cols[3].metric("资产负债率", f"{debt_ratios[-1]:.0%}")

            st.divider()

            if revenues and years:
                tab_charts = st.tabs(["营收与利润", "毛利率与ROE", "现金流分析"])

                with tab_charts[0]:
                    fig1 = go.Figure()
                    fig1.add_trace(go.Scatter(x=years, y=revenues, mode="lines+markers", name="营收(亿元)", line=dict(color="#3498db", width=3)))
                    fig1.add_trace(go.Scatter(x=years, y=net_profits, mode="lines+markers", name="净利润(亿元)", line=dict(color="#2ecc71", width=3)))
                    fig1.update_layout(title="营收与净利润趋势", height=350)
                    st.plotly_chart(fig1, use_container_width=True)

                with tab_charts[1]:
                    fig2 = go.Figure()
                    fig2.add_trace(go.Scatter(x=years, y=[m*100 for m in margins], mode="lines+markers", name="毛利率(%)", line=dict(color="#e74c3c", width=3)))
                    fig2.add_trace(go.Scatter(x=years, y=[r*100 for r in roe], mode="lines+markers", name="ROE(%)", line=dict(color="#9b59b6", width=3)))
                    fig2.update_layout(title="毛利率与ROE趋势", height=350, yaxis_title="%")
                    st.plotly_chart(fig2, use_container_width=True)

                with tab_charts[2]:
                    fig3 = go.Figure()
                    fig3.add_trace(go.Scatter(x=years, y=net_profits, mode="lines+markers", name="净利润", line=dict(color="#2ecc71", width=3)))
                    fig3.add_trace(go.Scatter(x=years, y=cashflows if cashflows else net_profits, mode="lines+markers", name="经营性现金流", line=dict(color="#f39c12", width=3)))
                    fig3.update_layout(title="净利润 vs 经营性现金流", height=350)
                    st.plotly_chart(fig3, use_container_width=True)

else:
    st.info("👆 选择股票后点击「开始分析」")

st.markdown("""
<div class="footer">
AlphaReport — 面向长期价值投资者的 AI 投研工具<br>
数据来源：AKShare 公开数据 / 预置示例数据 | 仅供参考，不构成投资建议
</div>
""", unsafe_allow_html=True)
