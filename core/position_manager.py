import numpy as np


class PositionManager:
    def __init__(self, max_cap=0.2):
        """
        :param max_cap: 单只股票最高允许占用总资金的比例 (防范单点风险)
        """
        self.max_cap = max_cap

    def calculate_kelly_size(self, win_rate, profit_factor):
        """
        利用凯利公式计算最佳仓位
        """
        if profit_factor <= 1:
            return 0.05  # 如果盈利因子很低，强制轻仓

        p = win_rate
        q = 1 - p
        b = profit_factor  # 简化使用盈利因子作为盈亏比参考

        kelly_f = (p * b - q) / b

        # 实际应用中，通常使用“半凯利”以保持稳健，并受限于最大持仓限制
        position_size = np.clip(kelly_f * 0.5, 0.01, self.max_cap)
        return position_size
