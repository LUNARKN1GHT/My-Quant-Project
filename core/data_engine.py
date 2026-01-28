# 数据引擎
import os
from typing import List

from data.data_loader import DataLoader


class DataEngine:
    def __init__(self, symbols: List[str]):
        self.symbols = symbols
        self.loader = DataLoader()
        self.universe_data = {}

    def update_all_data(self, start: str, end: str):
        """批量下载并存储"""
        for s in self.symbols:
            df = self.loader.fetch_and_save(s, start, end)
            if df is not None:  # 只有在成功获取数据时才存储
                self.universe_data[s] = df

    def get_local_universe(self) -> dict:
        """从本地加载整个股票池的数据"""
        local_data = {}
        for filename in os.listdir(self.loader.base_path):
            if filename.endswith('.csv'):
                # 从文件名中提取股票代码（文件名格式：symbol_start_end.csv）
                symbol = filename.split('_')[0]
                if symbol in self.symbols:  # 只加载指定股票池的数据
                    filepath = os.path.join(self.loader.base_path, filename)
                    df = self.loader.load_local(filepath)
                    local_data[symbol] = df
        return local_data

    def refresh_data(self, start: str, end: str, force_download: bool = False):
        """刷新数据，可以选择强制重新下载"""
        for s in self.symbols:
            df = self.loader.fetch_and_save(s, start, end, force_download=force_download)
            if df is not None:
                self.universe_data[s] = df

    def get_data_by_symbol(self, symbol: str) -> object:
        """根据股票代码获取数据"""
        if symbol in self.universe_data:
            return self.universe_data[symbol]
        else:
            # 尝试从本地加载
            local_files = [f for f in os.listdir(self.loader.base_path)
                           if f.startswith(f"{symbol}_") and f.endswith('.csv')]
            if local_files:
                filepath = os.path.join(self.loader.base_path, local_files[0])
                return self.loader.load_local(filepath)
        return None
