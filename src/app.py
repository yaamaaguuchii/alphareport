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
    .footer { text-align: center; color: #999; font-size: 0.8rem; margin-top: 3rem; padding-top: 1rem; border-top: 1px solid #eee; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">📊 AlphaReport 智能投研工作台</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">面向长期价值投资者的 AI 投研工具 — 机构级研究能力，一键触达</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    ticker = st.text_input("输入A股股票代码", value="600519", placeholder="例如 600519", label_visibility="collapsed").strip()

with col2:
    use_mock = st.checkbox("演示模式", value=True, help="勾选=模拟数据(预置3只); 取消=AKShare实时数据")

with col3:
    load_btn = st.button("🔍 开始分析", type="primary", use_container_width=True)

if load_btn and ticker:
    demo_tickers = {"600519": "贵州茅台", "300750": "宁德时代", "000002": "万科A"}
    if use_mock and ticker not in demo_tickers:
        st.warning(f"演示模式仅支持 {', '.join(demo_tickers.keys())}，已自动切为 600519")
        ticker = "600519"

if (load_btn or "analyzed" in st.session_state) and ticker:
    st.session_state["analyzed"] = True

    wf = st.empty()
    with wf.container():
        st.markdown("### 🤖 Agent 工作流")
        cols = st.columns(4)
        stages = [("📡 数据采集员","⏳ 进行中..."),("🔍 财务侦探","⏳ 进行中..."),("📢 公告分析师","⏳ 进行中..."),("✍️ 研报撰稿人","⏳ 进行中...")]
        for i, (name, desc) in enumerate(stages):
            with cols[i]: st.markdown(f"**{name}**\n\n{desc}")

    with st.spinner("正在获取数据并进行分析..."):
        company_data = get_company_data(ticker, use_mock=use_mock)
        detective_result = run_detective(company_data)
        announcements_raw = get_mock_announcements(ticker) if use_mock else []
        announcements = build_event_timeline(announcements_raw)

    with wf.container():
        st.markdown("### ✅ Agent 工作流 - 完成")
        cols = st.columns(4)
        statuses = [
            ("📡 数据采集员","✅ 数据已获取"),
            ("🔍 财务侦探",f"✅ {detective_result['red_flags']}项红灯/{detective_result['yellow_flags']}项黄灯"),
            ("📢 公告分析师",f"✅ {len(announcements)}条公告"),
            ("✍️ 研报撰稿人","✅ 研报已生成"),
        ]
        for i, (name, status) in enumerate(statuses):
            with cols[i]: st.markdown(f"**{name}**\n\n{status}")

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
                c = "green" if score >= 70 else ("yellow" if score >= 55 else "red")
                st.markdown(f'<div style="font-size:1.5rem;font-weight:bold;">🟢 财务健康评分：{score}/100</div>' if c=="green" else f'<div style="font-size:1.5rem;font-weight:bold;color:orange;">🟡 财务健康评分：{score}/100</div>' if c=="yellow" else f'<div style="font-size:1.5rem;font-weight:bold;color:red;">🔴 财务健康评分：{score}/100</div>', unsafe_allow_html=True)
            st.markdown(f"**公司简介**\n\n{data.get('description', '暂无数据')}")

            st.divider()
            st.subheader("财务分析")
            revenues = data.get("revenue", [])
            years = data.get("revenue_years", [])
            net_profits = data.get("net_profit", [])
            margins = data.get("gross_margin", [])
            if revenues:
                st.dataframe(pd.DataFrame({"年份": years, "营收(亿元)": revenues, "净利润(亿元)": net_profits}), use_container_width=True, hide_index=True)
                fig = go.Figure()
                fig.add_trace(go.Bar(name="营收(亿元)", x=years, y=revenues, marker_color="#3498db"))
                fig.add_trace(go.Bar(name="净利润(亿元)", x=years, y=net_profits, marker_color="#2ecc71"))
                fig.update_layout(title="营收与净利润趋势", barmode="group", height=350)
                st.plotly_chart(fig, use_container_width=True)

            st.divider()
            st.subheader("近期重大事件")
            for ann in anns[:5]:
                icons = {"S": "🔴", "A": "🟠", "B": "🔵", "C": "⚪"}
                st.markdown(f"- {icons.get(ann.get('level','C'),'⚪')} **{ann['date']}** {ann['title']}\n  - {ann.get('summary','')}")

            st.divider()
            st.subheader("风险提示")
            for item in detective.get("items", []):
                if item["status"] == "red":
                    st.warning(f"**{item['name']}**：{item['detail'][:80]}...")
            st.info("免责声明：本报告由 AI 自动生成，仅供参考，不构成投资建议。")

            st.divider()
            report_md = generate_report(data, detective, anns, include_llm=False)
            with st.expander("📝 查看完整 Markdown 研报"):
                st.markdown(report_md)
            st.download_button(label="📥 下载研报 (Markdown)", data=report_md, file_name=f"{data.get('ticker','stock')}_AlphaReport_{datetime.now().strftime('%Y%m%d')}.md", mime="text/markdown", use_container_width=True)

        with tab2:
            st.subheader("🔍 财务侦探 - 健康评分卡")
            st.markdown("AlphaReport 独家财务异常检测引擎，基于7大维度自动识别财务粉饰信号。")
            score = detective.get("overall_score", 0)
            st.markdown(f"### 综合评分：{score}/100")
            st.progress(score / 100)
            c1, c2, c3 = st.columns(3)
            c1.metric("🟢 正常项", detective.get("green_flags", 0))
            c2.metric("🟡 需关注", detective.get("yellow_flags", 0))
            c3.metric("🔴 风险项", detective.get("red_flags", 0))
            st.divider()
            for item in detective.get("items", []):
                border = {"green":"2px solid #00a86b","yellow":"2px solid #e6a817","red":"2px solid #e74c3c"}
                                icon = "🟢" if item["status"]=="green" else ("🟡" if item["status"]=="yellow" else "🔴")
                detail_preview = item["detail"][:150]
                st.markdown(f'<div style="border-left:{border[item["status"]]};padding:0.8rem;margin:0.8rem 0;background:#fafafa;border-radius:4px;"><strong>{icon} {item["name"]}</strong> 评分：{item["score"]:.2f}<br><small>{detail_preview}...</small></div>', unsafe_allow_html=True)

        with tab3:
            st.subheader("📢 公告追踪 - 智能摘要与关联分析")
            summary = get_announcement_summary(anns)
            st.info(summary["summary"])
            c1, c2, c3 = st.columns(3)
            c1.metric("🔴 重大(S级)", summary.get("s_count", 0))
            c2.metric("🟠 重要(A级)", summary.get("a_count", 0))
            c3.metric("🔵 一般(B级)", summary.get("b_count", 0))
            st.divider()
            if anns:
                st.dataframe(pd.DataFrame([{k:a[k] for k in ["date","title","type","level"]} for a in anns]), use_container_width=True, hide_index=True)
                st.divider()
                st.subheader("⏱ 事件时间线")
                sorted_anns = sorted(anns, key=lambda x: x["date"])
                fig = go.Figure()
                colors = {"S":"red","A":"orange","B":"blue","C":"gray"}
                for a in sorted_anns:
                    fig.add_trace(go.Scatter(x=[a["date"]], y=[a.get("type","其他")], mode="markers", marker=dict(size=18 if a.get("level")=="S" else 12, color=colors.get(a.get("level","C"),"gray")), text=a["title"], hoverinfo="text", showlegend=False))
                fig.update_layout(title="公告时间线", height=300)
                st.plotly_chart(fig, use_container_width=True)
                st.divider()
                st.subheader("历史类似事件统计")
                for t in set(a.get("type","其他") for a in anns):
                    hs = analyze_announcement({"type":t,"level":"A","title":"","date":""}).get("historical_stat",{})
                    st.markdown(f"- **{t}**：历史5日平均涨幅{hs.get('avg_return_5d',0):+.1f}%，上涨概率{hs.get('win_rate',0):.0%}")

        with tab4:
            st.subheader("📊 数据看板")
            revenues = data.get("revenue", [])
            years = data.get("revenue_years", [])
            net_profits = data.get("net_profit", [])
            margins = data.get("gross_margin", [])
            roe = data.get("roe", [])
            cols = st.columns(4)
            if margins: cols[0].metric("最新毛利率", f"{margins[-1]:.1%}")
            if roe: cols[1].metric("最新ROE", f"{roe[-1]:.1%}")
            if net_profits and data.get("operating_cashflow"): cols[2].metric("利润含金量", f"{data['operating_cashflow'][-1]/net_profits[-1]:.2f}" if net_profits[-1]>0 else "N/A")
            if data.get("debt_ratio"): cols[3].metric("资产负债率", f"{data['debt_ratio'][-1]:.0%}")
            if revenues and years:
                t1, t2, t3 = st.tabs(["营收与利润", "毛利率与ROE", "现金流分析"])
                with t1:
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=years, y=revenues, mode="lines+markers", name="营收", line=dict(width=3)))
                    fig.add_trace(go.Scatter(x=years, y=net_profits, mode="lines+markers", name="净利润", line=dict(width=3)))
                    fig.update_layout(height=300)
                    st.plotly_chart(fig, use_container_width=True)
                with t2:
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=years, y=[m*100 for m in margins], mode="lines+markers", name="毛利率(%)", line=dict(width=3)))
                    fig.add_trace(go.Scatter(x=years, y=[r*100 for r in roe], mode="lines+markers", name="ROE(%)", line=dict(width=3)))
                    fig.update_layout(height=300)
                    st.plotly_chart(fig, use_container_width=True)
                with t3:
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=years, y=net_profits, mode="lines+markers", name="净利润", line=dict(width=3)))
                    fig.add_trace(go.Scatter(x=years, y=data.get("operating_cashflow", net_profits), mode="lines+markers", name="经营性现金流", line=dict(width=3)))
                    fig.update_layout(height=300)
                    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("👆 输入股票代码后点击「开始分析」")

st.markdown("""
<div class="footer">
AlphaReport — 让每一个投资者都拥有机构级投研能力<br>
数据来源：AKShare / 预置示例数据 | 仅供参考，不构成投资建议
</div>
""", unsafe_allow_html=True)﻿
