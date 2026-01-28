import numpy as np


class SimpleStrategy:
    @staticmethod
    def generate_signals(df):
        """
        基于 SMA 和 RSI 生成买卖信号
        1 代表买入, -1 代表卖出, 0 代表持有/观望
        """
        # 复制一份数据避免修改原始 df
        df = df.copy()

        # 初始化信号列
        df['Signal'] = 0

        # 计算金叉：今日 SMA20 > SMA60 且 昨日 SMA20 <= SMA60
        gold_cross = (df['SMA_20'] > df['SMA_60']) & (df['SMA_20'].shift(1) <= df['SMA_60'].shift(1))

        # 计算死叉：今日 SMA20 < SMA60 且 昨日 SMA20 >= SMA60
        death_cross = (df['SMA_20'] < df['SMA_60']) & (df['SMA_20'].shift(1) >= df['SMA_60'].shift(1))

        # 结合 RSI 过滤买入信号（防止在高位追涨）
        df.loc[gold_cross & (df['RSI'] < 70), 'Signal'] = 1
        df.loc[death_cross, 'Signal'] = -1

        # 为了方便查看，我们可以记录“持仓状态” (1为持仓，0为不持仓)
        # 使用 ffill() 将信号向下填充，直到遇到下一个信号
        df['Position'] = df['Signal'].replace(0, np.nan).ffill().fillna(0).replace(-1, 0)

        return df
