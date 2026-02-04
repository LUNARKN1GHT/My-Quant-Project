import numpy as np
import pandas as pd


class RiskManager:
    def __init__(self, stop_loss_mult=2.0, take_profit_mult=3.0):
        """
        :param stop_loss_mult: ATR 的倍数作为止损距离 (常见为 1.5 - 2.5)
        :param take_profit_mult: ATR 的倍数作为止盈距离
        """
        self.stop_loss_mult = stop_loss_mult
        self.take_profit_mult = take_profit_mult

    def calculate_atr_exits(self, df: pd.DataFrame):
        """为每一行计算基于 ATR 的动态止损价和止盈价"""
        df = df.copy()

        # 计算 ATR (通常使用 14 天)
        # 如果 IndicatorCalculator 还没算过 ATR，这里可以补算
        if "ATR" not in df.columns:
            high_low = df["High"] - df["Low"]
            high_cp = np.abs(df["High"] - df["Close"].shift())
            low_cp = np.abs(df["Low"] - df["Close"].shift())
            tr = pd.concat([high_low, high_cp, low_cp], axis=1).max(axis=1)
            df["ATR"] = tr.rolling(window=14).mean()

        # 买入时的初始止损位 = 现价 - (ATR * 倍数)
        df["Initial_SL"] = df["Close"] - (df["ATR"] * self.stop_loss_mult)
        # 买入时的初始止盈位 = 现价 + (ATR * 倍数)
        df["Initial_TP"] = df["Close"] + (df["ATR"] * self.take_profit_mult)

        return df
