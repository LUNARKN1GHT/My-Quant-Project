import pandas as pd


class PortfolioEngine:
    def __init__(self, initial_capital=100000, max_stock_weight=0.15):
        self.initial_capital = initial_capital
        self.max_stock_weight = max_stock_weight

    def run_portfolio(self, all_signals_dict: dict):
        # 1. 自动对齐时间轴
        common_dates = None
        for df in all_signals_dict.values():
            common_dates = (
                df.index
                if common_dates is None
                else common_dates.intersection(df.index)
            )

        cash = self.initial_capital
        holdings = {s: 0 for s in all_signals_dict.keys()}
        history = []
        holdings_history = []  # 新增：专门记录持仓分布

        for date in common_dates:
            daily_holdings_value = {
                s: holdings[s] * all_signals_dict[s].loc[date, "Close"]
                for s in holdings
            }
            total_equity = cash + sum(daily_holdings_value.values())

            # 记录当前权分布 (Weight %)
            weights = {s: val / total_equity for s, val in daily_holdings_value.items()}
            weights["Cash"] = cash / total_equity
            weights["Date"] = date
            holdings_history.append(weights)

            prev_total_equity = cash + sum(
                holdings[s] * all_signals_dict[s].loc[date, "Open"] for s in holdings
            )
            current_trade_count = 0

            # --- 简单的每日再平衡逻辑 ---
            for s, df in all_signals_dict.items():
                price = df.loc[date, "Close"]
                sig = df.loc[date, "Signal"]

                # 买入逻辑
                if sig == 1 and holdings[s] == 0:
                    target_val = prev_total_equity * self.max_stock_weight
                    if cash >= target_val:
                        shares = target_val // price
                        holdings[s] = shares
                        cash -= shares * price
                        current_trade_count += 1

                # 卖出逻辑 (Signal 为 -1 或 0 时视策略而定)
                elif sig == -1 and holdings[s] > 0:
                    cash += holdings[s] * price
                    holdings[s] = 0
                    current_trade_count += 1

            # 计算今日总资产
            total_equity = cash + sum(
                holdings[s] * all_signals_dict[s].loc[date, "Close"] for s in holdings
            )

            history.append(
                {
                    "Date": date,
                    "Total_Equity": total_equity,
                    "Cash": cash,
                    "Trades": current_trade_count,
                    "Strategy_Return": (
                        (total_equity / prev_total_equity - 1)
                        if prev_total_equity != 0
                        else 0
                    ),
                }
            )

        res_df = pd.DataFrame(history).set_index("Date")

        # --- 核心计算补全 ---
        # 1. 累计收益
        res_df["Cumulative_Return"] = res_df["Total_Equity"] / self.initial_capital

        # 2. 计算回撤 (Drawdown) - 修复 KeyError: 'Drawdown' 的关键
        # 公式: (当前价值 / 历史最高价值) - 1
        rolling_max = res_df["Total_Equity"].cummax()
        res_df["Drawdown"] = (res_df["Total_Equity"] / rolling_max) - 1

        # 3. 兼容性对齐
        res_df["Equity_Curve"] = res_df["Total_Equity"]
        res_df["Close"] = res_df["Total_Equity"]  # 这里的 Close 代表组合的“价格”
        # 将持仓历史转为 DataFrame 备用
        self.weights_df = pd.DataFrame(holdings_history).set_index("Date")
        return res_df
