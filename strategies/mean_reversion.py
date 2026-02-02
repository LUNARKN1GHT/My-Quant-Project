import pandas as pd

from strategies.base import BaseStrategy


class BollingerMeanReversion(BaseStrategy):
    def __init__(self, symbols: list):
        super().__init__("BB_Mean_Reversion", symbols)

    def on_data(self, symbol: str, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df['Signal'] = 0
        # BB_L: 下轨, BB_U: 上轨
        buy_cond = (df['Close'] < df['BB_L'])
        sell_cond = (df['Close'] > df['BB_M'])  # 回归到中轴就平仓

        df.loc[buy_cond, 'Signal'] = 1
        df.loc[sell_cond, 'Signal'] = -1
        return df
