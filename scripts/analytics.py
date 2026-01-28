import numpy as np


class StrategyAnalytics:
    @staticmethod
    def calculate_performance(df):
        """
        输入包含 Strategy_Return 的 DataFrame，输出各项性能指标
        """
        # 移除空值（第一行通常是 NaN）
        returns = df['Strategy_Return'].dropna()

        # 1. 累计收益
        total_return = (1 + returns).prod() - 1

        # 2. 年化收益 (假设一年 252 个交易日)
        ann_return = (1 + total_return) ** (252 / len(returns)) - 1

        # 3. 夏普比率 (假设无风险利率为 2%)
        risk_free_rate = 0.02
        excess_returns = returns - risk_free_rate / 252
        sharpe_ratio = np.sqrt(252) * excess_returns.mean() / returns.std()

        # 4. 最大回撤
        cum_returns = (1 + returns).cumprod()
        rolling_max = cum_returns.cummax()
        drawdown = (cum_returns - rolling_max) / rolling_max
        max_drawdown = drawdown.min()

        metrics = {
            "Total Return": f"{total_return:.2%}",
            "Annualized Return": f"{ann_return:.2%}",
            "Sharpe Ratio": f"{sharpe_ratio:.2f}",
            "Max Drawdown": f"{max_drawdown:.2%}"
        }

        return metrics, drawdown
