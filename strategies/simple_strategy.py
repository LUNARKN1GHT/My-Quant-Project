import pandas as pd

from strategies.base import BaseStrategy


class MaRsiStrategy(BaseStrategy):
    def __init__(self, symbols: list, sma_s=20, sma_l=60, rsi_limit=70):
        super().__init__("MA_RSI_Strategy", symbols)
        self.params = {
            'sma_short': sma_s,
            'sma_long': sma_l,
            'rsi_limit': rsi_limit
        }

    def on_data(self, symbol: str, df: pd.DataFrame) -> pd.DataFrame:
        df - df.copy()
        # 初始化信号列
        df['Signal'] = 0

        # 定义列名
        s_ma = f"SMA_{self.params['sma_short']}"
        l_ma = f"SMA_{self.params['sma_long']}"
        rsi = "RSI_14"

        # 生成买入信号
        buy_cond = (df[s_ma] > df[l_ma]) & (df[s_ma].shift(1) <= df[l_ma].shift(1)) & (
                df[rsi] < self.params['rsi_limit'])
        # 生成卖出信号
        sell_cond = (df[s_ma] < df[l_ma]) & (df[s_ma].shift(1) >= df[l_ma].shift(1))

        df.loc[buy_cond, 'Signal'] = 1
        df.loc[sell_cond, 'Signal'] = -1

        return df
