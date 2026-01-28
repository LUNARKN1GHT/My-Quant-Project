# 数据引擎
from typing import List

from scripts.data_loader import DataLoader


class DataEngine:
    def __init__(self, symbols: List[str]):
        self.symbols = symbols
        self.loader = DataLoader()
        self.universe_data = {}

    def update_all_data(self, start: str, end: str):
        """批量下载并存储"""
        for s in self.symbols:
            df = self.loader.fetch_and_save(s, start, end)
            self.universe_data[s] = df

    def get_local_universe(self) -> dict:
        """从本地加载整个股票池的数据"""
        # TODO: 遍历 storage/raw 文件夹读取数据的逻辑
        pass
