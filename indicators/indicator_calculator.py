import pandas as pd
import pandas_ta as ta


class BaseIndicator:
    """指标基类, 定义通用接口"""

    def __init__(self):
        pass

    def calculate(self, df):
        """计算指标的方法, 子类必须实现"""
        raise NotImplementedError("子类必须实现calculate方法")


class IndicatorAppender:
    @staticmethod
    def add_trend_indicators(df):
        """添加趋势指标: 移动平均线"""
        # 计算 20日 和 60日 均线
        close_prices = df['Close'].astype(float)

        df['SMA_20'] = ta.sma(close_prices, length=20)
        df['SMA_60'] = ta.sma(close_prices, length=60)
        return df

    @staticmethod
    def add_momentum_indicators(df):
        """添加动量指标: RSI, MACD"""
        # RSI (相对强弱指数)
        df['RSI'] = ta.rsi(df['Close'], length=14)

        # MACD
        macd = ta.macd(df['Close'])
        df = pd.concat([df, macd], axis=1)
        return df

    @staticmethod
    def add_volatility_indicators(df):
        """添加波动率指标: 布林带"""
        bbands = ta.bbands(df['Close'], length=20, std=2)
        df = pd.concat([df, bbands], axis=1)
        return df
