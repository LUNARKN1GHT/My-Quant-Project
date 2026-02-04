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
        """第二步：特征工程，支持链式调用"""
        print("🧬 构建特征矩阵与因子合成...")
        processor = FeatureProcessor(n_components=0.95)

        for s in self.cfg["backtest"]["symbols"]:
            df = self.engine.get_symbol_data(s)
            if df is not None:
                # 1. 计算基础指标
                calc = IndicatorCalculator(df)
                # 这里的参数可以未来也写进 YAML
                processed_df = (
                    calc.add_sma([20, 60, 120])
                    .add_rsi([14])
                    .add_macd()
                    .add_bollinger_bands()
                    .clean_data()
                    .get_result()
                )
                # 2. 因子合成：将多个相关指标合成独立的 PCA 特征
                df_synthesized, pca_features = processor.fit_transform(processed_df)

                # 3. 存储带合成特征的数据
                self.engine.save_processed(s, df_synthesized)

    def run_backtest(self, strategy_instance):
        """第三步：执行指定策略的回测"""
        print(f"⚔️ 执行策略: {strategy_instance.name}")
        pos_mgr = PositionManager(max_cap=0.25)  # 设定单股最高 25% 仓位
        signals_dict = strategy_instance.generate_all_signals(self.engine)

        for symbol, df_sig in signals_dict.items():
            # 1. 运行回测
            initial_results = self.backtester.run(symbol, df_sig)

            temp_m = self.backtester.calculate_advanced_metrics(symbol, initial_results)

            win_rate = float(temp_m["Win Rate"].strip("%")) / 100
            profit_factor = (
                float(temp_m["Profit Factor"])
                if temp_m["Profit Factor"] != "inf"
                else 2.0
            )

            suggested_size = pos_mgr.calculate_kelly_size(win_rate, profit_factor)
            print(f"💰 [{symbol}] 凯利仓位应用: {suggested_size:.2%}")

            # --- 使用建议仓位跑真正的最终回测 ---
            final_results = self.backtester.run(symbol, df_sig)

            # 2. AI 洞察 (可选)
            top_drivers = self.ai_engine.analyze(symbol, initial_results)
            top_drivers_str = ", ".join(list(top_drivers.keys())[::-1][:3])

            # 3. 收集指标
            m = self.backtester.calculate_advanced_metrics(symbol, initial_results)
            m["Top Drivers (AI)"] = top_drivers_str
            m["Position Size"] = f"{suggested_size:.2%}"
            self.all_metrics.append(m)

            # 4. 生成单独报告
            self.html_viz.generate_interactive_report(symbol, initial_results)

    def finalize(self):
        """第四步：生成总看板"""
        self.dashboard.generate_summary(self.all_metrics, self.cfg)
        print("✅ 任务流运行结束")
