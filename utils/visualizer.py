import os

import matplotlib.pyplot as plt
import pandas as pd


class Visualizer:
    def __init__(self, report_path: str = "reports"):
        """
        :param report_path: 图片存储文件夹
        """
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.save_dir = os.path.join(project_root, report_path)

        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
            print(f"[Visualizer] 创建报告目录: {self.save_dir}")

    def plot_backtest(self, symbol: str, results: pd.DataFrame):
        """
        绘制包含价格、信号和资金曲线的综合图表
        """
        # 设置画布，包含两个子图（上方看价格/信号，下方看资金曲线）
        fig, (ax1, ax2) = plt.subplots(
            2, 1, figsize=(14, 10), sharex=True, gridspec_kw={"height_ratios": [2, 1]}
        )

        # --- 图1: 价格与信号 ---
        ax1.plot(
            results.index,
            results["Close"],
            label="Close Price",
            color="black",
            alpha=0.3,
        )

        # 绘制均线 (假设我们有这两列)
        sma_cols = [c for c in results.columns if "SMA" in c]
        for col in sma_cols:
            ax1.plot(results.index, results[col], label=col, alpha=0.8)

        # 标注买入点 (Signal == 1)
        buys = results[results["Signal"] == 1]
        ax1.scatter(
            buys.index,
            buys["Close"],
            marker="^",
            color="red",
            s=100,
            label="Buy Signal",
            zorder=5,
        )

        # 标注卖出点 (Signal == -1)
        sells = results[results["Signal"] == -1]
        ax1.scatter(
            sells.index,
            sells["Close"],
            marker="v",
            color="green",
            s=100,
            label="Sell Signal",
            zorder=5,
        )

        ax1.set_title(f"{symbol} Strategy Analysis", fontsize=16)
        ax1.set_ylabel("Price")
        ax1.legend(loc="best")
        ax1.grid(True, alpha=0.3)

        # --- 图2: 资金曲线 ---
        ax2.plot(
            results.index,
            results["Equity_Curve"],
            label="Strategy Equity",
            color="blue",
        )

        # 填充回撤区域 (如果你在回测引擎里算好了 Drawdown)
        if "Peak" in results.columns:
            ax2.fill_between(
                results.index,
                results["Equity_Curve"],
                results["Peak"],
                color="red",
                alpha=0.2,
                label="Drawdown",
            )

        ax2.set_ylabel("Portfolio Value")
        ax2.set_xlabel("Date")
        ax2.legend(loc="best")
        ax2.grid(True, alpha=0.3)

        # 调整布局并保存
        plt.tight_layout()

        # 增加子文件夹路径，方便整理
        symbol_dir = os.path.join(self.save_dir, symbol)
        os.makedirs(symbol_dir, exist_ok=True)

        save_path = os.path.join(symbol_dir, f"{symbol}_report.png")
        plt.savefig(save_path, dpi=150)
        plt.close()  # 关闭画布，防止内存溢出
        print(f"[Visualizer] 报告已保存: {save_path}")
