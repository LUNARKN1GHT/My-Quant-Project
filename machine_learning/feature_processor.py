import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


class FeatureProcessor:
    def __init__(self, n_components: float = 0.95):
        """
        :param n_components: 保留多少比例的方差（0.95 表示保留能解释 95% 信息的特征组合）
        """
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=n_components)
        self.feature_cols = []

    def fit_transform(self, df: pd.DataFrame):
        """
        对特征进行标准化和 PCA 降维（已修复 FutureWarning）
        """
        # 1. 自动识别特征列
        exclude = [
            "Open",
            "High",
            "Low",
            "Close",
            "Volume",
            "Signal",
            "Target",
            "Market_Return",
            "Strategy_Return",
        ]
        self.feature_cols = [
            c for c in df.columns if c not in exclude and not c.startswith("Cumulative")
        ]

        # 2. 现代化的缺失值处理：先向前填充，再对剩余的空值填 0
        X = df[self.feature_cols].ffill().fillna(0)

        # 3. 标准化
        X_scaled = self.scaler.fit_transform(X)

        # 4. PCA 正交化
        X_pca = self.pca.fit_transform(X_scaled)

        pca_cols = [f"PCA_{i+1}" for i in range(X_pca.shape[1])]
        pca_df = pd.DataFrame(X_pca, columns=pca_cols, index=df.index)

        return pd.concat([df, pca_df], axis=1), pca_cols
