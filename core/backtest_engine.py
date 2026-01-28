import numpy as np
import pandas as pd


class BacktestEngine:
    def __init__(self, initial_capital: float = 100000.0, commission: float = 0.001):
        """
        :param initial_capital: 初始资金
        :param commission: 手续费率（如 0.001 代表 0.1%）
        """
        self.initial_capital = initial_capital
        self.commission = commission

    def run(self, symbol: str, df: pd.DataFrame) -> pd.DataFrame:
        """
        运行回测
        """
        if 'Signal' not in df.columns:
            raise ValueError(f"数据集中缺少 Signal 列，请先运行策略逻辑。")

        results = df.copy()

        # 1. 计算每日收益率
        results['Market_Return'] = results['Close'].pct_change()

        # 2. 计算持仓状态 (Position)
        # 将信号（1, -1, 0）转换为持仓（1代表持仓，0代表空仓）
        # 这里使用 ffill() 模拟：一旦买入信号出现，就一直持仓直到卖出信号出现
        results['Position'] = results['Signal'].replace(0, np.nan).ffill().fillna(0)
        # 限制持仓只能是 1（多头）或 0（空仓），暂不支持做空
        results['Position'] = results['Position'].apply(lambda x: 1 if x == 1 else 0)

        # 3. 计算策略收益 (昨天的持仓决定了今天的收益)
        results['Strategy_Return'] = results['Position'].shift(1) * results['Market_Return']

        # 4. 扣除手续费 (当持仓发生变化时产生交易)
        results['Trades'] = results['Position'].diff().abs()
        results['Strategy_Return'] -= results['Trades'] * self.commission

        # 5. 计算累计收益和资金曲线
        results['Cumulative_Return'] = (1 + results['Strategy_Return'].fillna(0)).cumprod()
        results['Equity_Curve'] = results['Cumulative_Return'] * self.initial_capital

        # 6. 计算回撤 (Drawdown)
        results['Peak'] = results['Equity_Curve'].cummax()
        results['Drawdown'] = (results['Equity_Curve'] - results['Peak']) / results['Peak']

        return results

    def get_performance_summary(self, symbol: str, results: pd.DataFrame):
        """
        计算核心指标：年化收益、夏普比率、最大回撤
        """
        # 基础数据准备
        total_return = results['Cumulative_Return'].iloc[-1] - 1

        # 计算年化收益 (使用更严谨的复利计算方式)
        days = len(results)
        if days > 0:
            annualized_return = (1 + total_return) ** (252 / days) - 1
        else:
            annualized_return = 0

        # 计算波动率和夏普比率
        annualized_vol = results['Strategy_Return'].std() * np.sqrt(252)
        # 假设无风险利率为 2% (0.02)
        risk_free_rate = 0.02
        if annualized_vol > 0:
            sharpe_ratio = (annualized_return - risk_free_rate) / annualized_vol
        else:
            sharpe_ratio = 0

        max_drawdown = results['Drawdown'].min()

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
