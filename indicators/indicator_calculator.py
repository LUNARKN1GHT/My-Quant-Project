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


class VolatilityIndicators(BaseIndicator):
    """波动率指标计算器"""

    @staticmethod
    def add_bollinger_bands(df, period=20, std=2):
        """添加布林带"""
        bbands = ta.bbands(df['Close'], length=period, std=std)
        df = pd.concat([df, bbands], axis=1)
        return df

    @staticmethod
    def add_atr(df, period=14):
        """添加平均真实波幅"""
        df[f'ATR_{period}'] = ta.atr(df['High'], df['Low'], df['Close'], length=period)
        return df


class VolumeIndicators(BaseIndicator):
    """成交量指标计算器"""

    @staticmethod
    def add_obv(df):
        """添加能量潮指标"""
        df['OBV'] = ta.obv(df['Close'], df['Volume'])
        return df

    @staticmethod
    def add_vwap(df):
        """添加成交量加权平均价（如果数据中有成交量信息）"""
        if 'Volume' in df.columns:
            typical_price = (df['High'] + df['Low'] + df['Close']) / 3
            df['VWAP'] = (typical_price * df['Volume']).cumsum() / df['Volume'].cumsum()
        return df


class IndicatorCalculator:
    """综合指标计算器, 整合所有指标功能"""

    @staticmethod
    def add_all_indicators(df, config=None):
        """
        一次性添加所有指标
        :param df: 输入数据框
        :param config: 指标配置字典，可选
        :return df: 计算后的结果
        """
        if config is None:
            config = {
                'trend': {'sma_short': 20, 'sma_long': 60, 'ema_period': 20},
                'momentum': {'rsi_period': 14},
                'volatility': {'bb_period': 20, 'atr_period': 14},
                'volume': True
            }

        # 添加趋势指标
        df = TrendIndicators.add_sma(df, config['trend']['sma_short'], config['trend']['sma_long'])
        df = TrendIndicators.add_ema(df, config['trend']['ema_period'])

        # 添加动量指标
        df = MomentumIndicators.add_rsi(df, config['momentum']['rsi_period'])

        # 添加波动率指标
        df = VolatilityIndicators.add_bollinger_bands(df, config['volatility']['bb_period'])
        df = VolatilityIndicators.add_atr(df, config['volatility']['atr_period'])

        # 添加成交量指标（如果数据中有成交量）
        if 'Volume' in df.columns and config['volume']:
            df = VolumeIndicators.add_obv(df)
            df = VolumeIndicators.add_vwap(df)

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
