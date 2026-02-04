import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


class HTMLVisualizer:
    def __init__(self, report_path: str = "reports"):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.save_dir = os.path.join(project_root, report_path)
        self.report_path = os.path.join(report_path)
        os.makedirs(self.save_dir, exist_ok=True)

    def generate_interactive_report(self, symbol: str, results: pd.DataFrame):
        """
        创建一个交互式的 HTML 报告
        """
        # 1. 创建子图：行1是价格/信号，行2是资产曲线
        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.1,
            subplot_titles=(f"{symbol} 信号与指标", "资金价值与回撤"),
            row_heights=[0.7, 0.3],
        )

        # --- 图表 A: K线或收盘价 ---
        fig.add_trace(
            go.Scatter(
                x=results.index,
                y=results["Close"],
                name="收盘价",
                line=dict(color="rgba(100, 100, 100, 0.5)"),
            ),
            row=1,
            col=1,
        )

        # 动态添加 SMA 指标
        sma_cols = [c for c in results.columns if "SMA" in c]
        for col in sma_cols:
            fig.add_trace(
                go.Scatter(x=results.index, y=results[col], name=col), row=1, col=1
            )

        # 绘制买入信号
        buys = results[results["Signal"] == 1]
        fig.add_trace(
            go.Scatter(
                x=buys.index,
                y=buys["Close"],
                mode="markers",
                name="买入信号",
                marker=dict(symbol="triangle-up", size=12, color="red"),
            ),
            row=1,
            col=1,
        )

        # 绘制卖出信号
        sells = results[results["Signal"] == -1]
        fig.add_trace(
            go.Scatter(
                x=sells.index,
                y=sells["Close"],
                mode="markers",
                name="卖出信号",
                marker=dict(symbol="triangle-down", size=12, color="green"),
            ),
            row=1,
            col=1,
        )

        # --- 图表 B: 资金曲线 ---
        fig.add_trace(
            go.Scatter(
                x=results.index,
                y=results["Equity_Curve"],
                name="资产净值",
                line=dict(color="royalblue", width=2),
            ),
            row=2,
            col=1,
        )

        # 填充回撤
        if "Peak" in results.columns:
            fig.add_trace(
                go.Scatter(
                    x=results.index,
                    y=results["Peak"],
                    name="净值高点",
                    line=dict(dash="dash", color="rgba(200, 0, 0, 0.3)"),
                ),
                row=2,
                col=1,
            )

        # 设置交互布局
        fig.update_layout(
            title=f"{symbol} 交互式回测分析报告",
            hovermode="x unified",
            height=800,
            template="plotly_white",
            showlegend=True,
        )

        # 保存为 HTML 文件
        symbol_dir = os.path.join(self.save_dir, symbol)
        os.makedirs(symbol_dir, exist_ok=True)
        save_path = os.path.join(symbol_dir, f"{symbol}_interactive.html")
        fig.write_html(save_path)
        print(f"[HTMLVisualizer] 交互式报告已生成: {save_path}")

    def generate_portfolio_visuals(self, results, weights_df):
        """生成组合投资专属的 HTML 报告"""
        # 1. 绘制资产分配堆叠图
        fig = px.area(
            weights_df,
            title="组合资产分配动态 (Daily Weights Allocation)",
            labels={"value": "权重 (%)", "variable": "资产"},
            template="plotly_dark",
        )

        # 2. 导出为 HTML
        save_path = os.path.join(self.report_path, "portfolio_allocation.html")
        fig.write_html(save_path)
        print(f"📊 组合持仓报告已生成: {save_path}")
