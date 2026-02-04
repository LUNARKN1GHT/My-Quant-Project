import numpy as np
import pandas as pd

from core.risk_manager import RiskManager


class BacktestEngine:
    def __init__(self, initial_capital: float = 100000.0, commission: float = 0.001):
        """
        :param initial_capital: 初始资金
        :param commission: 手续费率（如 0.001 代表 0.1%）
        """
        self.initial_capital = initial_capital
        self.commission = commission

    def run(self, symbol: str, df: pd.DataFrame, pos_size: float = 1.0) -> pd.DataFrame:
        """
        运行回测
        """
        # 0. 加入风险管理
        risk_mgr = RiskManager()
        df = risk_mgr.calculate_atr_exits(df)

        position = 0
        entry_price = 0
        stop_loss_price = 0
        take_profit_price = 0

        if "Signal" not in df.columns:
            raise ValueError(f"数据集中缺少 Signal 列，请先运行策略逻辑。")

        signals = df["Signal"].values
        close_prices = df["Close"].values
        sl_prices = df["Initial_SL"].values
        tp_prices = df["Initial_TP"].values

        exit_signals = np.zeros(len(df))
        for i in range(1, len(df)):
            # --- 场景 A: 当前持仓，检查是否需要止损或止盈 ---
            if position == 1:
                if (
                    close_prices[i] <= stop_loss_price
                    or close_prices[i] >= take_profit_price
                ):
                    position = 0
                    exit_signals[i] = -1  # 强制平仓信号
                    continue

            # --- 场景 B: 当前空仓，检查 AI 买入信号 ---
            if position == 0 and signals[i] == 1:
                position = 1
                entry_price = close_prices[i]
                stop_loss_price = sl_prices[i]
                take_profit_price = tp_prices[i]

        df.loc[exit_signals == -1, "Signal"] = -1

        results = df.copy()

        # 1. 计算每日收益率
        results["Market_Return"] = results["Close"].pct_change()

        # 2. 计算持仓状态 (Position)
        # 将信号（1, -1, 0）转换为持仓（1代表持仓，0代表空仓）
        # 这里使用 ffill() 模拟：一旦买入信号出现，就一直持仓直到卖出信号出现
        results["Position"] = results["Signal"].replace(0, np.nan).ffill().fillna(0)
        # 限制持仓只能是 1（多头）或 0（空仓），暂不支持做空
        results["Position"] = results["Position"].apply(lambda x: 1 if x == 1 else 0)

        # 3. 计算策略收益 (昨天的持仓决定了今天的收益)
        results["Strategy_Return"] = (
            results["Position"].shift(1) * results["Market_Return"] * pos_size
        )

        # 4. 扣除手续费 (当持仓发生变化时产生交易)
        results["Trades"] = results["Position"].diff().abs()
        results["Strategy_Return"] -= results["Trades"] * self.commission

        # 5. 计算累计收益和资金曲线
        results["Cumulative_Return"] = (
            1 + results["Strategy_Return"].fillna(0)
        ).cumprod()
        results["Equity_Curve"] = results["Cumulative_Return"] * self.initial_capital

        # 6. 计算回撤 (Drawdown)
        results["Peak"] = results["Equity_Curve"].cummax()
        results["Drawdown"] = (results["Equity_Curve"] - results["Peak"]) / results[
            "Peak"
        ]

        return results

    @staticmethod
    def get_performance_summary(symbol: str, results: pd.DataFrame):
        """
        计算核心指标：年化收益、夏普比率、最大回撤
        """
        # 基础数据准备
        total_return = results["Cumulative_Return"].iloc[-1] - 1

        # 计算年化收益 (使用更严谨的复利计算方式)
        days = len(results)
        if days > 0:
            annualized_return = (1 + total_return) ** (252 / days) - 1
        else:
            annualized_return = 0

        # 计算波动率和夏普比率
        annualized_vol = results["Strategy_Return"].std() * np.sqrt(252)
        # 假设无风险利率为 2% (0.02)
        risk_free_rate = 0.02
        if annualized_vol > 0:
            sharpe_ratio = (annualized_return - risk_free_rate) / annualized_vol
        else:
            sharpe_ratio = 0

        max_drawdown = results["Drawdown"].min()

        print(f"\n" + "=" * 30)
        print(f"      回测报告: {symbol}")
        print(f"博弈天数: {days} 天")
        print("-" * 30)
        print(f"总 收益 率: {total_return:>10.2%}")
        print(f"年化收益率: {annualized_return:>10.2%}")
        print(f"最大回撤比: {max_drawdown:>10.2%}")
        print(f"夏普比率  : {sharpe_ratio:>10.2f}")
        print(f"最终净资产: {results['Equity_Curve'].iloc[-1]:>10.2f}")
        print("=" * 30)

    def calculate_advanced_metrics(self, symbol: str, results: pd.DataFrame) -> dict:
        """
        计算高级统计指标
        """
        # 获取每笔交易的收益 (基于 Position 变化的差值)
        # 我们寻找 Position 从 0 变 1 (买入) 到从 1 变 0 (卖出) 的区间收益
        trades = results[results["Trades"] > 0].copy()
        trade_returns = []

        # 简单逻辑：提取所有卖出点的累计收益变化
        # 这是一种向量化模拟每笔交易收益的方法
        if len(trades) >= 2:
            # 简化计算：取持仓期间的净值变化
            equity_at_trades = results.loc[trades.index, "Equity_Curve"]
            trade_returns = equity_at_trades.pct_change().iloc[1::2]  # 取卖出点的变化

        win_rate = (
            len([r for r in trade_returns if r > 0]) / len(trade_returns)
            if len(trade_returns) > 0
            else 0
        )

        gross_profit = sum([r for r in trade_returns if r > 0])
        gross_loss = abs(sum([r for r in trade_returns if r < 0]))
        profit_factor = gross_profit / gross_loss if gross_loss != 0 else float("inf")

        # 封装指标
        metrics = {
            "Symbol": symbol,
            "Total Return": f"{results['Cumulative_Return'].iloc[-1]-1:.2%}",
            "Annual Return": f"{(results['Cumulative_Return'].iloc[-1]**(252/len(results))-1):.2%}",
            "Max Drawdown": f"{results['Drawdown'].min():.2%}",
            "Sharpe Ratio": f"{self.calculate_sharpe(results):.2f}",
            "Win Rate": f"{win_rate:.2%}",
            "Profit Factor": f"{profit_factor:.2f}",
            "Trade Count": len(trade_returns),
        }
        return metrics

    def calculate_sharpe(self, results):
        # 内部调用逻辑
        ret = results["Strategy_Return"]
        if ret.std() == 0:
            return 0
        return (ret.mean() / ret.std()) * np.sqrt(252)
