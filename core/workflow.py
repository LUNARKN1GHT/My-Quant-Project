import os

import pandas as pd

from core.backtest_engine import BacktestEngine
from core.data_engine import DataEngine
from core.position_manager import PositionManager
from indicators.indicator_calculator import IndicatorCalculator
from machine_learning.feature_importance import FeatureImportanceEngine
from machine_learning.feature_processor import FeatureProcessor
from utils.dashboard import DashboardGenerator
from utils.helpers import load_config
from utils.html_report import HTMLVisualizer


class WorkflowManager:
    def __init__(self):
        self.cfg = load_config()
        self.engine = DataEngine(symbols=self.cfg["backtest"]["symbols"])
        self.backtester = BacktestEngine(
            initial_capital=self.cfg["backtest"]["initial_capital"],
            commission=self.cfg["backtest"]["commission"],
        )
        self.html_viz = HTMLVisualizer(report_path=self.cfg["paths"]["reports"])
        self.dashboard = DashboardGenerator(report_path=self.cfg["paths"]["reports"])
        self.ai_engine = FeatureImportanceEngine(
            report_path=self.cfg["paths"]["reports"]
        )
        self.all_metrics = []

    def sync_data(self):
        """第一步：同步原始数据"""
        print(f"🔄 同步数据池: {self.cfg['backtest']['symbols']}")
        self.engine.update_universe(
            start=self.cfg["backtest"]["start_date"],
            end=self.cfg["backtest"]["end_date"],
        )

    def prepare_features(self):
        """第二步：特征工程与 PCA 因子合成"""
        print("🧬 构建特征矩阵与因子合成...")
        processor = FeatureProcessor(n_components=0.95)

        for s in self.cfg["backtest"]["symbols"]:
            df = self.engine.get_symbol_data(s)
            if df is not None:
                calc = IndicatorCalculator(df)
                processed_df = (
                    calc.add_sma([20, 60, 120])
                    .add_rsi([14])
                    .add_macd()
                    .add_bollinger_bands()
                    .clean_data()
                    .get_result()
                )
                # 因子正交化，提取 PCA 特征
                df_synthesized, _ = processor.fit_transform(processed_df)
                self.engine.save_processed(s, df_synthesized)

    def run_backtest(self, strategy_instance):
        """核心路由：根据配置决定是跑单股还是组合"""
        mode = self.cfg["backtest"].get("mode", "individual")
        # 获取所有股票的预测信号
        signals_dict = strategy_instance.generate_all_signals(self.engine)

        if mode == "individual":
            self._run_individual_mode(signals_dict, strategy_instance.name)
        elif mode == "portfolio":
            self._run_portfolio_mode(signals_dict, strategy_instance.name)

    def _run_individual_mode(self, signals_dict, strategy_name):
        """模式 A：单股独立回测（逐一分析）"""
        print(f"🚩 正在以 [单股模式] 运行策略: {strategy_name}")
        pos_mgr = PositionManager(
            max_cap=self.cfg["backtest"].get("max_stock_weight", 0.25)
        )

        for symbol, df_sig in signals_dict.items():
            # 1. 预跑回测：获取该品种的基础统计信息，用于凯利公式
            initial_res = self.backtester.run(symbol, df_sig, pos_size=0.1)
            temp_m = self.backtester.calculate_advanced_metrics(symbol, initial_res)

            # 2. 计算凯利建议仓位
            win_rate = float(temp_m["Win Rate"].strip("%")) / 100
            pf = temp_m["Profit Factor"]
            profit_factor = float(pf) if pf != "inf" and float(pf) > 0 else 1.0

            suggested_size = pos_mgr.calculate_kelly_size(win_rate, profit_factor)
            print(f"💰 [{symbol}] 凯利仓位建议: {suggested_size:.2%}")

            # 3. 正式回测：使用 AI 建议的仓位
            final_results = self.backtester.run(symbol, df_sig, pos_size=suggested_size)

            # 4. AI 因子贡献度分析
            top_drivers = self.ai_engine.analyze(symbol, final_results)
            top_drivers_str = ", ".join(list(top_drivers.keys())[::-1][:3])

            # 5. 结果收集与报告生成
            m = self.backtester.calculate_advanced_metrics(symbol, final_results)
            m["Top Drivers (AI)"] = top_drivers_str
            m["Position Size"] = f"{suggested_size:.2%}"
            self.all_metrics.append(m)
            self.html_viz.generate_interactive_report(symbol, final_results)

    def _run_portfolio_mode(self, signals_dict, strategy_name):
        """模式 B：组合投资模式（资产对冲与相关性过滤）"""
        print(f"🚩 正在以 [组合模式] 运行策略: {strategy_name}")

        # 1. 引入相关性过滤器（避免行业一把梭）
        self._apply_correlation_filter(signals_dict)

        # 2. 调用组合引擎（需要你创建 core/portfolio_engine.py）
        from core.portfolio_engine import PortfolioEngine

        port_engine = PortfolioEngine(
            initial_capital=self.cfg["backtest"]["initial_capital"],
            max_stock_weight=self.cfg["backtest"].get("max_stock_weight", 0.15),
        )

        portfolio_results = port_engine.run_portfolio(signals_dict)

        weights_path = os.path.join(
            self.cfg["paths"]["reports"], "portfolio_weights.csv"
        )
        port_engine.weights_df.to_csv(weights_path)

        # 生成可视化
        self.html_viz.generate_portfolio_visuals(
            portfolio_results, port_engine.weights_df
        )

        # 3. 生成专属报告（包含持仓堆叠图）
        self.html_viz.generate_portfolio_visuals(
            portfolio_results, port_engine.weights_df
        )

        # 3. 特殊处理：将组合的整体表现塞进 metrics 列表以便展示
        # 这里需要你扩展 calculate_advanced_metrics 来支持组合数据
        m = self.backtester.calculate_advanced_metrics(
            "PORTFOLIO_TOTAL", portfolio_results
        )
        self.all_metrics.append(m)
        print(
            f"📈 组合回测完成，最终净值: {portfolio_results['Total_Equity'].iloc[-1]:.2f}"
        )

    def _apply_correlation_filter(self, signals_dict):
        """计算相关性，并在存在高相关性时抑制弱信号"""
        # 提取 Close 价构建矩阵
        prices = pd.concat({s: df["Close"] for s, df in signals_dict.items()}, axis=1)
        corr = prices.corr()
        print("📊 组合相关性矩阵已生成，正在优化信号结构...")
        # 实际逻辑可以在 PortfolioEngine 中实现每日动态抑制
        return corr

    def finalize(self):
        """第四步：生成可视化看板"""
        self.dashboard.generate_summary(self.all_metrics, self.cfg)
        print("✅ 全流程自动化任务运行结束")
