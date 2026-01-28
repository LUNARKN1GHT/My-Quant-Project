# 数据引擎
import os
from typing import List, Dict, Optional

import pandas as pd

from data.data_loader import DataLoader


class DataEngine:
    def __init__(self, symbols: List[str],
                 raw_path: str = "storage/raw",
                 processed_path: str = "storage/processed",
                 cache_size: int = 50):
        """
        :param symbols: 初始股票池
        :param raw_path:
        :param processed_path:
        :param cache_size: 内存中最多保留多少只股票的数据, 防止溢出
        """
        self.symbols = symbols
        # 使用更稳健的路径获取方式
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.raw_path = os.path.join(project_root, raw_path)
        self.processed_path = os.path.join(project_root, processed_path)

        self.loader = DataLoader(raw_path=self.raw_path)

        # 内存缓存
        self._cache: Dict[str, pd.DataFrame] = {}
        self.cache_size = cache_size

        # 确保目录存在
        os.makedirs(self.processed_path, exist_ok=True)

    def _manage_cache(self, symbol: str, df: pd.DataFrame):
        """简单的缓存淘汰机制"""
        if len(self._cache) >= self.cache_size:
            first_key = next(iter(self._cache))
            del self._cache[first_key]
        self._cache[symbol] = df

    def get_symbol_data(self, symbol: str, start: str = None, end: str = None,
                        use_processed: bool = False) -> Optional[pd.DataFrame]:
        """获取单只股票数据, 并自动按日期切片"""
        df = None

        # 1. 优先看内存缓存
        if symbol in self._cache:
            df = self._cache[symbol]
        else:
            # 2. 尝试加载文件 (优先 processed)
            folder = self.processed_path if use_processed else self.raw_path
            # 兼容 parquet 和 csv
            for ext in ['parquet', 'csv']:
                path = os.path.join(folder, f"{symbol}.{ext}")
                if os.path.exists(path):
                    df = self.loader.load_local(path)
                    self._manage_cache(symbol, df)
                    break

        if df is None:
            print(f"[DataEngine] 错误: 找不到 {symbol} 的本地数据")
            return None

        # 3. 按日期切片 (Slice)
        if start or end:
            # 确保索引是日期类型且排序
            df = df.sort_index()
            return df.loc[start:end].copy()

        return df.copy()

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

    def save_processed_data(self, base_path="../storage/processed"):
        """保存处理后的数据（如带有技术指标的数据）到指定目录"""
        if not os.path.exists(base_path):
            os.makedirs(base_path)

        saved_files = []
        for symbol, df in self.universe_data.items():
            if df is not None:
                # 生成文件名
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                file_name = f"{symbol}_processed_{timestamp}.csv"
                save_path = os.path.join(base_path, file_name)

                # 保存数据
                df.to_csv(save_path)
                saved_files.append(save_path)
                print(f"数据已保存至: {save_path}")

        return saved_files

    def load_processed_data(self, symbol: str, base_path="../storage/processed"):
        """从处理过的数据目录加载特定股票的数据"""
        import glob
        pattern = os.path.join(base_path, f"{symbol}_processed_*.csv")
        files = glob.glob(pattern)

        if not files:
            print(f"未找到 {symbol} 的处理后数据")
            return None

        # 获取最新的文件
        latest_file = max(files, key=os.path.getctime)
        df = self.loader.load_local(latest_file)
        return df
