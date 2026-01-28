import pandas as pd
import pandas_ta as ta


class BaseIndicator:
    """指标基类, 定义通用接口"""

    def __init__(self):
        pass

    def calculate(self, df):
        """计算指标的方法, 子类必须实现"""
        raise NotImplementedError("子类必须实现calculate方法")


class TrendIndicators(BaseIndicator):
    """趋势指标计算器"""

    @staticmethod
    def add_sma(df, short_period=20, long_period=60):
        """添加移动平均线指标"""
        close_prices = df['Close'].astype(float)
        df[f'SMA_{short_period}'] = ta.sma(close_prices, length=short_period)
        df[f'SMA_{long_period}'] = ta.sma(close_prices, length=long_period)
        return df

    @staticmethod
    def add_ema(df, period=20):
        """添加指数移动平均线"""
        close_prices = df['Close'].astype(float)
        df[f'EMA_{period}'] = ta.ema(close_prices, length=period)
        return df


class MomentumIndicators(BaseIndicator):
    """动量指标计算器"""

    @staticmethod
    def add_rsi(df, period=14):
        """添加相对强弱指数"""
        df[f'RSI_{period}'] = ta.rsi(df['Close'], length=period)
        return df

    @staticmethod
    def add_stochastics(df, k=14, d=3):
        """添加随机指标"""
        stoch = ta.stoch(high=df['High'], low=df['Low'], close=df['Close'], k=k, d=d)
        df = pd.concat([df, stoch], axis=1)
        return df


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
