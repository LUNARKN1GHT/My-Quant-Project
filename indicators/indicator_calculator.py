from typing import List

import pandas as pd
import pandas_ta as ta


class IndicatorCalculator:
    """指标计算器: 支持前缀管理和批量特征生成"""

    def __init__(self, df: pd.DataFrame):
        # 保持原始数据的副本，确保不破坏原数据
        self.df = df.copy()
        # 预检查：确保 Close 列是浮点数，规避 Numba 类型错误
        if 'Close' in self.df.columns:
            self.df['Close'] = self.df['Close'].astype(float)

    def add_sma(self, periods: List[int], prefix: str = "SMA"):
        """批量添加简单移动平均线"""
        for p in periods:
            column_name = f"{prefix}_{p}"
            self.df[column_name] = ta.sma(self.df['Close'], length=p)
        return self  # 支持链式调用

    def add_rsi(self, periods: List[int] = [14], prefix: str = "RSI"):
        """添加 RSI 指标"""
        for p in periods:
            self.df[f"{prefix}_{p}"] = ta.rsi(self.df['Close'], length=p)
        return self

    def add_macd(self, fast=12, slow=26, signal=9, prefix: str = "MACD"):
        """添加 MACD 指标，并自动规范化返回的列名"""
        macd_df = ta.macd(self.df['Close'], fast=fast, slow=slow, signal=signal)
        # 规范化列名，例如 MACD_12_26_9 -> MACD_line, MACDh_12_26_9 -> MACD_hist
        macd_df.columns = [f"{prefix}_line", f"{prefix}_hist", f"{prefix}_signal"]
        self.df = pd.concat([self.df, macd_df], axis=1)
        return self

    def add_bollinger_bands(self, period=20, std=2, prefix: str = "BB"):
        """添加布林带"""
        bb_df = ta.bbands(self.df['Close'], length=period, std=std)
        # 简化布林带列名
        bb_df.columns = [f"{prefix}_L", f"{prefix}_M", f"{prefix}_U", f"{prefix}_Bw", f"{prefix}_Bp"]
        self.df = pd.concat([self.df, bb_df], axis=1)
        return self

    def add_volatility_atr(self, period=14, prefix: str = "ATR"):
        """添加平均真实波幅 (ATR)"""
        self.df[f"{prefix}_{period}"] = ta.atr(self.df['High'], self.df['Low'], self.df['Close'], length=period)
        return self

    def clean_data(self):
        """处理由于指标计算产生的冷启动空值"""
        self.df.dropna(inplace=True)
        return self

    def get_result(self) -> pd.DataFrame:
        """返回计算后的完整的 DataFrame"""
        return self.df

    def add_kdj(self, n=9, m1=3, m2=3, prefix: str = "KDJ"):
        """添加 KDJ 指标"""
        kdj_df = ta.kdj(self.df['High'], self.df['Low'], self.df['Close'], length=n, signal=m1, runoff=m2)
        kdj_df.columns = [f"{prefix}_K", f"{prefix}_D", f"{prefix}_J"]
        self.df = pd.concat([self.df, kdj_df], axis=1)
        return self

    def add_momentum_slope(self, col: str, window: int = 5, prefix: str = "Slope"):
        """计算指定列的斜率（动量变化率）"""
        self.df[f"{prefix}_{col}_{window}"] = self.df[col].diff(window) / window
        return self
