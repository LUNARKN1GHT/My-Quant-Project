import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from strategies.base import BaseStrategy


class MLStrategy(BaseStrategy):
    def __init__(
        self, symbols: list, train_size: float = 0.8, prob_threshold: float = 0.6
    ):
        """
        :param train_size: 用于训练的数据比例（前 80% 训练，后 20% 回测预测）
        :param prob_threshold: 买入的概率阈值
        """
        super().__init__("Machine_Learning_Strategy", symbols)
        self.feature_order = None
        self.params = {"train_size": train_size, "prob_threshold": prob_threshold}
        self.models = {}  # 为每只股票存储独立的模型

    @staticmethod
    def _prepare_features(df: pd.DataFrame):
        """提取特征列，剔除价格和元数据"""
        exclude = ["Open", "High", "Low", "Close", "Volume", "Signal", "Target"]
        # 还要排除掉后面计算产生的回测列
        exclude += [
            "Market_Return",
            "Strategy_Return",
            "Position",
            "Trades",
            "Cumulative_Return",
            "Equity_Curve",
            "Peak",
            "Drawdown",
        ]
        features = [col for col in df.columns if col not in exclude]
        return features

    def on_data(self, symbol: str, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["Signal"] = 0

        # 1. 准备目标标签 (未来 5 天是否上涨)
        df["Target"] = (df["Close"].shift(-5) > df["Close"]).astype(int)
        features = self._prepare_features(df)

        # 清理空值
        clean_df = df.dropna(subset=features + ["Target"])

        # 2. 划分训练集和测试集 (按时间顺序)
        split_idx = int(len(clean_df) * self.params["train_size"])
        train_df = clean_df.iloc[:split_idx]
        test_df = clean_df.iloc[split_idx:]

        if len(train_df) < 100:
            print(f"⚠️ {symbol} 数据量太小，无法训练模型")
            return df

        # 3. 训练模型
        print(
            f"🤖 [{symbol}] 正在训练 AI 模型... 样本数: {len(train_df)}, 特征数: {len(features)}"
        )
        X_train = train_df[features]
        y_train = train_df["Target"]

        # 记录训练时的特征顺序，确保预测时完全一致
        self.feature_order = features.copy()

        model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
        model.fit(X_train, y_train)
        self.models[symbol] = model  # 持久化模型

        # 4. 预测 (在整个数据集上生成概率，或仅在测试集生成)
        # 为了回测展示完整性，我们在测试集上应用信号
        X_test = test_df[features]
        # 获取预测为 '1' (涨) 的概率
        probs = model.predict_proba(X_test)[:, 1]

        # 5. 生成信号：概率 > 阈值则买入 (1)，否则观望 (0)
        # 我们暂时不设卖出信号 (-1)，由 BacktestEngine 的持仓逻辑自动处理
        test_signals = (probs > self.params["prob_threshold"]).astype(int)
        print(
            f"📈 [{symbol}] 预测完成，最大上涨概率: {probs.max():.2%}, 产生信号数: {sum(test_signals)}"
        )

        # 将信号填回原 DataFrame (对应测试集位置)
        df.loc[test_df.index, "Signal"] = test_signals

        return df
