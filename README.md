# AlphaReport - 智能投研工作台

面向长期价值投资者的 AI 投研工具。让每一个散户投资者都拥有机构级研究能力。

## 核心功能

### 📄 智能研报生成
输入股票代码，一键生成结构化的投资研究报告，包含公司概况、财务分析、行业展望和估值总结。

### 🔍 财务侦探（独家）
基于 7 大维度的财务异常检测引擎，自动识别财务粉饰信号：
- 利润含金量检测（经营性现金流 vs 净利润）
- 应收账款异常识别
- 存货周转异常检测
- 关联交易排查
- 偿债能力评估
- 现金流画像分析
- 毛利率稳定性检测

输出红黄绿评分卡，让财务风险一目了然。

### 📢 公告追踪
智能公告分级（S/A/B/C 四级），构建事件时间线，提供历史类似事件统计参考。

## 快速开始

### 安装

```bash
git clone https://github.com/your-team/AlphaReport.git
cd AlphaReport
pip install -r requirements.txt
```

### 运行

```bash
streamlit run src/app.py
```

### 演示模式
默认启用模拟数据模式，无需网络连接即可体验全部功能。
支持三种演示股票：
- 贵州茅台 (600519) - 财务健康
- 宁德时代 (300750) - 成长型
- 万科A (000002) - 高风险提示

## 技术架构

```
用户输入股票代码
        ↓
   并行启动 Agent
   ├── 数据采集层 → 财务数据
   ├── 财务侦探 → 健康检查
   └── 公告分析 → 事件时间线
        ↓
   汇总生成完整研报
```

### 技术栈
- **前端界面**: Streamlit
- **数据源**: AKShare (实时) / 预置模拟数据 (演示)
- **可视化**: Plotly, Matplotlib
- **后端**: Python 3.10+
- **可选增强**: OpenAI / DeepSeek API

## 目录结构

```
AlphaReport/
├── src/
│   ├── app.py                  # Streamlit 主入口
│   ├── data_fetcher.py         # 数据采集模块
│   ├── financial_detective.py  # 财务侦探引擎
│   ├── announcement_analyzer.py# 公告分析模块
│   ├── report_generator.py     # 研报生成器
│   └── config.py               # 配置文件
├── business_plan/
│   └── BUSINESS_PLAN.md        # 商业计划书
├── examples/
│   └── sample_report.md        # 示例报告
├── requirements.txt
└── README.md
```

## 竞品对比

| 维度 | FinSight (人大) | AlphaReport (我们) |
|:---|:---|:---|
| 研报生成 | ✅ 强 | ✅ 轻量 |
| 财务异常检测 | ❌ 无 | ✅ **独家** |
| 公告智能分析 | ❌ 无 | ✅ **独家** |
| 开源 | ✅ | ✅ |
| 部署成本 | 较高 | 轻量可部署 |

## 免责声明

本工具生成的研报内容仅供参考，不构成任何投资建议。所有数据来源于公开信息，投资者应独立做出投资决策。

## License

MIT
