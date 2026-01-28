import os
import time
from typing import Optional

import pandas as pd
import yfinance as yf


class DataLoader:
    def __init__(self, raw_path: str = None):
        """
        类初始化，设置程序的存储仓库
        :param raw_path: 项目的数据存储仓库，也可以自定义
        """
        # 使用项目根目录作为基准, 避免 ../ 导致的路径混乱
        if raw_path is None:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.base_path = os.path.join(project_root, "storage", "raw")
        else:
            self.base_path = os.path.abspath(raw_path)

        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path, exist_ok=True)

    def fetch_and_save(self, symbol: str, start: str, end: str,
                       force_download=False,
                       use_parquet: bool = True) -> Optional[pd.DataFrame]:
        """
        抓取并保存数据. Parquet 格式更适合量化
        """
        try:
            # 简化文件名, 方便数据管理
            ext = "parquet" if use_parquet else "csv"
            file_name = f"{symbol}.{ext}"
            save_path = os.path.join(self.base_path, file_name)

            # 检查逻辑: 如果不是强制下载且文件存在, 直接加载
            if os.path.exists(save_path) and not force_download:
                print(f"[DataLoader] {symbol} 已存在, 正在从本地加载...")
                return self.load_local(save_path)

            print(f"[DataLoader] 正在从 Yahoo Finance 下载 {symbol}...")
            data = yf.download(symbol, start=start, end=end, auto_adjust=True)

            if data.empty:
                print(f"警告: 未获取到 {symbol} 的数据")
                return None

            # --- 核心清理步骤 ---
            # 1. 强制平刷多层索引
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)

            # 2. 转换类型并出去可能的时区信息
            data = data.astype(float)
            if data.index.tz is not None:
                data.index = data.index.tz_localize(None)

            # 3. 保存
            if use_parquet:
                data.to_parquet(save_path)
            else:
                data.to_csv(save_path)

            print(f"[DataLoader] {symbol} 成功保存至: {save_path}")
            return data

        except Exception as e:
            print(f"[DataLoader] 错误: {symbol} 处理失败 - {e}")
            return None

    @staticmethod
    def load_local(file_path: str):
        """
        读取本地数据并格式化时间索引
        :param file_path: 需要读取的目录位置
        :return: 数据的 df
        """
        df = pd.read_csv(file_path, index_col=0, parse_dates=True)
        return df

    def batch_fetch_and_save(self, symbols: list, start: str, end: str, delay=1):
        """
        批量下载多个股票的数据
        :param symbols: 股票代码列表
        :param start: 开始日期
        :param end: 结束日期
        :param delay: 请求间隔时间（秒），防止请求过于频繁
        :return: 成功下载的股票数据字典
        """
        results = {}
        for symbol in symbols:
            print(f"正在下载 {symbol}...")
            data = self.fetch_and_save(symbol, start, end)
            if data is not None:
                results[symbol] = data
            # 添加延迟以避免API限制
            time.sleep(delay)

        return results

    def get_available_data(self):
        """
        获取本地已有的数据文件列表
        :return: 文件列表及对应的信息
        """
        files = os.listdir(self.base_path)
        csv_files = [f for f in files if f.endswith('.csv')]
        return csv_files
