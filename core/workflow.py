from core.backtest_engine import BacktestEngine
from core.data_engine import DataEngine
from indicators.indicator_calculator import IndicatorCalculator
from machine_learning.feature_importance import FeatureImportanceEngine
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
        print("🧬 构建特征矩阵...")
        for s in self.cfg["backtest"]["symbols"]:
            df = self.engine.get_symbol_data(s)
            if df is not None:
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
                self.engine.save_processed(s, processed_df)

    def run_backtest(self, strategy_instance):
        """第三步：执行指定策略的回测"""
        print(f"⚔️ 执行策略: {strategy_instance.name}")
        signals_dict = strategy_instance.generate_all_signals(self.engine)

        for symbol, df_sig in signals_dict.items():
            # 1. 运行回测
            results = self.backtester.run(symbol, df_sig)

            # 2. AI 洞察 (可选)
            top_drivers = self.ai_engine.analyze(symbol, results)
            top_drivers_str = ", ".join(list(top_drivers.keys())[::-1][:3])

            # 3. 收集指标
            m = self.backtester.calculate_advanced_metrics(symbol, results)
            m["Top Drivers (AI)"] = top_drivers_str
            self.all_metrics.append(m)

            # 4. 生成单独报告
            self.html_viz.generate_interactive_report(symbol, results)

    def finalize(self):
        """第四步：生成总看板"""
        self.dashboard.generate_summary(self.all_metrics, self.cfg)
        print("✅ 任务流运行结束")
