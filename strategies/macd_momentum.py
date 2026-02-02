import pandas as pd

from strategies.base import BaseStrategy


class MacdMomentumStrategy(BaseStrategy):
    def __init__(self, symbols: list):
        super().__init__("MACD_Momentum", symbols)

    def on_data(self, symbol: str, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df['Signal'] = 0
        # MACD_hist > 0 且 比昨天更高
        buy_cond = (df['MACD_hist'] > 0) & (df['MACD_hist'] > df['MACD_hist'].shift(1))
        sell_cond = (df['MACD_hist'] < 0)

        df.loc[buy_cond, 'Signal'] = 1
        df.loc[sell_cond, 'Signal'] = -1
        return df
