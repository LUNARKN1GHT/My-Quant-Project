import pandas as pd


class PortfolioEngine:
    def __init__(self, initial_capital=100000, max_stock_weight=0.2):
        self.initial_capital = initial_capital
        self.max_stock_weight = max_stock_weight
        self.weights_df = pd.DataFrame()

    def run_portfolio(self, all_signals_dict: dict):
        # 1. 修复：取所有股票日期的【并集】，解决冷启动空白
        all_dates = pd.DatetimeIndex([])
        for df in all_signals_dict.values():
            all_dates = all_dates.union(df.index)
        all_dates = all_dates.sort_values()

        # 2. 初始化账户
        cash = self.initial_capital
        holdings = {s: 0 for s in all_signals_dict.keys()}
        history = []
        weights_history = []

        # 3. 逐日滚动回测
        for date in all_dates:
            # A. 统计今日所有可用股票的价格 (向前填充，解决停牌/未上市问题)
            current_prices = {}
            for s in all_signals_dict.keys():
                try:
                    # 获取该日期或之前的最后一条有效价格
                    price_series = all_signals_dict[s].loc[:date, "Close"]
                    current_prices[s] = (
                        price_series.iloc[-1] if not price_series.empty else 0
                    )
                except:
                    current_prices[s] = 0

            # B. 计算今日开盘前的总资产 (前日收盘市值 + 剩余现金)
            total_equity = cash + sum(holdings[s] * current_prices[s] for s in holdings)
            prev_equity = total_equity  # 用于计算今日回报率

            # C. 收集今日产生的买入信号
            active_signals = []
            for s, df in all_signals_dict.items():
                if date in df.index and df.loc[date, "Signal"] == 1:
                    if current_prices[s] > 0:  # 确保价格有效
                        active_signals.append(s)

            # D. 【动态调仓逻辑】
            # 先卖出：不在今日信号列表中的，或者信号消失的，全部转为现金
            for s in list(holdings.keys()):
                if s not in active_signals and holdings[s] > 0:
                    cash += holdings[s] * current_prices[s]
                    holdings[s] = 0

            # 再买入：平均分配现金到所有活跃信号
            if len(active_signals) > 0:
                # 每只股票的目标金额 (不超过设定的最大权重)
                target_weight = min(1.0 / len(active_signals), self.max_stock_weight)

                for s in active_signals:
                    target_val = total_equity * target_weight
                    # 只有当目前持仓市值与目标不符时才调整 (简单逻辑：不足则补，多了则卖)
                    current_val = holdings[s] * current_prices[s]

                    if target_val > current_val:
                        can_buy_val = target_val - current_val
                        if cash >= can_buy_val:
                            shares_to_buy = can_buy_val // current_prices[s]
                            holdings[s] += shares_to_buy
                            cash -= shares_to_buy * current_prices[s]

            # E. 记录今日持仓分布 (用于生成那张堆叠图)
            daily_weights = {
                s: (holdings[s] * current_prices[s] / total_equity) for s in holdings
            }
            daily_weights["Cash"] = cash / total_equity
            daily_weights["Date"] = date
            weights_history.append(daily_weights)

            # F. 记录总账
            history.append(
                {
                    "Date": date,
                    "Total_Equity": total_equity,
                    "Cash": cash,
                    "Trades": len(active_signals),  # 简化统计：当日活跃信号数
                    "Strategy_Return": (
                        (total_equity / prev_equity - 1) if prev_equity > 0 else 0
                    ),
                }
            )

        # 4. 结果包装
        res_df = pd.DataFrame(history).set_index("Date")
        res_df["Cumulative_Return"] = res_df["Total_Equity"] / self.initial_capital
        res_df["Drawdown"] = (
            res_df["Total_Equity"] / res_df["Total_Equity"].cummax()
        ) - 1
        res_df["Equity_Curve"] = res_df["Total_Equity"]

        self.weights_df = pd.DataFrame(weights_history).set_index("Date")

        return res_df
