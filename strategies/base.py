from abc import ABC, abstractmethod

import pandas as pd


class BaseStrategy(ABC):
    def __init__(self, name: str, symbols: list):
        """
        :param name: 策略名称
        :param symbols: 该策略运行的股票池
        """
        self.name = name
        self.symbols = symbols
        self.params = {}  # 用于存储策略参数, 方便后续调优

    @abstractmethod
    def on_data(self, symbol: str, df: pd.DataFrame) -> pd.DataFrame:
        """
        核心信号逻辑. 子类必须实现此方法
        :param symbol:
        :param df:
        :return:
        """
        pass

    def generate_all_signals(self, engine) -> dict:
        """通过 DataEngine 批量为股票池生成信号"""
        all_signals = {}
        for symbol in self.symbols:
            # 从 engine 获取 processed 数据
            df = engine.get_symbol_data(symbol, use_processed=True)
            if df is not None:
                # 调用子类实现的逻辑
                df_with_signal = self.on_data(symbol, df)
                all_signals[symbol] = df_with_signal
        return all_signals
