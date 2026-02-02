import json
import os

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.ensemble import RandomForestClassifier


class FeatureImportanceEngine:
    def __init__(self, report_path: str = "reports"):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.save_dir = os.path.join(project_root, report_path)

    def analyze(self, symbol: str, df: pd.DataFrame):
        """
        利用随机森林分析特征对未来涨跌的影响力
        """
        # 1. 准备标签：预测未来 5 天的收盘价是否高于今天 (1为涨, 0为跌)
        df = df.copy()
        df["Target"] = (df["Close"].shift(-5) > df["Close"]).astype(int)

        # 2. 定义特征列 (排除掉非特征列)
        exclude_cols = [
            "Open",
            "High",
            "Low",
            "Close",
            "Volume",
            "Signal",
            "Target",
            "Market_Return",
            "Strategy_Return",
            "Position",
            "Trades",
            "Cumulative_Return",
            "Equity_Curve",
            "Peak",
            "Drawdown",
        ]
        features = [col for col in df.columns if col not in exclude_cols]

        # 清洗数据：移除最后 5 行（因为没有 Target）以及由于指标产生的空行
        data = df.dropna(subset=features + ["Target"])

        X = data[features]
        y = data["Target"]

        # 3. 训练随机森林模型
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X, y)

        # 4. 提取特征重要性
        importances = pd.Series(model.feature_importances_, index=features).sort_values(
            ascending=True
        )

        # 5. 可视化并保存
        plt.figure(figsize=(10, 8))
        importances.plot(kind="barh", color="skyblue")
        plt.title(f"Feature Importance Analysis: {symbol}")
        plt.xlabel("Importance Score")
        plt.tight_layout()

        # --- 增加子文件夹路径 ---
        symbol_dir = os.path.join(self.save_dir, symbol)
        os.makedirs(symbol_dir, exist_ok=True)

        img_path = os.path.join(symbol_dir, f"{symbol}_feature_importance.png")
        plt.savefig(img_path)
        plt.close()

        # --- 保存为 JSON 数据 ---
        json_save_path = os.path.join(symbol_dir, f"{symbol}_feature_importance.json")
        with open(json_save_path, "w", encoding="utf-8") as f:
            # 只取前 5 个最重要的特征存入 JSON，方便摘要显示
            top_features = importances.tail(5).to_dict()
            json.dump(top_features, f, indent=4)

        print(f"🤖 [AI] 特征重要性分析已完成: {img_path}")

        return top_features
