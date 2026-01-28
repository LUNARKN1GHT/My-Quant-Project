import os

import pandas as pd
import yfinance as yf


class DataLoader:
    def __init__(self, raw_path="storage/raw"):
        """
        类初始化，设置程序的存储仓库
        :param raw_path: 项目的数据存储仓库，也可以自定义
        """
        self.base_path = base_path
        self.base_path = raw_path
        # 确保路径存在
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)

    def fetch_and_save(self, symbol: str, start: str, end: str, force_download=False):
        """
        抓取并以标准格式保存数据
        :param symbol: 股票代码
        :param start: 开始日期
        :param end: 结束日期
        :param force_download: 是否强制重新下载数据, 默认 False
        :return data: 下载的数据
        """
        try:
            print(f"开始同步 {symbol} 数据 （{start} 至 {end}）...")

            # 统一文件名格式：代码_开始日期_结束日期.csv
            file_name = f"{symbol}_{start.replace('-', '')}_{end.replace('-', '')}.csv"
            save_path = os.path.join(self.base_path, file_name)

            # 检查是否已存在文件且不需要强制下载
            if os.path.exists(save_path) and not force_download:
                print(f"文件已存在：{save_path}，跳过下载。如需重新下载，请使用force_download=True")
                return self.load_local(save_path)

            # 1. 下载数据
            data = yf.download(symbol, start=start, end=end, auto_adjust=True)

            # 如果列是多层索引,我们只取一列
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)

            # 2. 检查并转换类型
            data = data.astype(float)

            if data.empty:
                print(f"警告：未获取到 {symbol} 的数据")
                return None

            # 3. 数据验证 - 确保必需的列存在
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            missing_cols = [col for col in required_columns if col not in data.columns]
            if missing_cols:
                print(f"警告: 数据中缺少列: {missing_cols}")

            # 4. 添加数据质量检查
            data.dropna(inplace=True)  # 删除含有 NaN 的行

            # 5. 保存
            data.to_csv(save_path)
            print(f"数据成功保存至：{save_path}")
            return data

        except Exception as e:
            print(f"获取数据时发生错误：{e}")
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
