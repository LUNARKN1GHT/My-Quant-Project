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

    def update_universe(self, start: str, end: str, force: bool = False):
        """批量同步股票池到本地"""
        print(f"[DataEngine] 开始批量同步 {len(self.symbols)} 只股票...")
        for s in self.symbols:
            self.loader.fetch_and_save(s, start, end, force_download=force)

    def save_processed(self, symbol: str, df: pd.DataFrame):
        """保存加工后的数据, 不再使用时间戳, 采用覆盖写模式"""
        # 推荐使用 parquet 提升后续回测速度
        save_path = os.path.join(self.processed_path, f"{symbol}.parquet")
        df.to_parquet(save_path)
        # 更新缓存
        self._cache[symbol] = df
        print(f"[DataEngine] 已保存加工数据: {save_path}")

    def get_universe_generator(self, start: str = None, end: str = None):
        """
        高级功能: 生成器模式.
        需要跑全市场回测时, 用这个方法可以一只只处理, 不占内存.
        """
        for s in self.symbols:
            df = self.get_symbol_data(s, start, end)
            if df is not None:
                yield s, df
