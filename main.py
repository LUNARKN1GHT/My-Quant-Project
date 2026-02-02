import os
import sys

from utils.dashboard import DashboardGenerator

# 确保项目根目录在系统路径中，防止导入失败
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.helpers import load_config
from core.data_engine import DataEngine
from indicators.indicator_calculator import IndicatorCalculator
from strategies.simple_strategy import MaRsiStrategy
from core.backtest_engine import BacktestEngine
from utils.visualizer import Visualizer
from strategies.mean_reversion import BollingerMeanReversion
from utils.html_report import HTMLVisualizer


def run_pipeline():
    print("🚀 量化系统启动...")

    # 1. 加载配置
    try:
        cfg = load_config()
    except FileNotFoundError:
        print("❌ 错误：找不到 config/settings.yaml 文件，请先创建！")
        return

    # 2. 初始化引擎与同步数据
    engine = DataEngine(symbols=cfg["backtest"]["symbols"])
    print(f"\n[Step 1] 正在同步数据池: {cfg['backtest']['symbols']}...")
    engine.update_universe(
        start=cfg["backtest"]["start_date"], end=cfg["backtest"]["end_date"]
    )

    # 3. 特征工程 (计算指标)
    print("\n[Step 2] 正在进行特征工程 (Indicator Calculation)...")
    for s in cfg["backtest"]["symbols"]:
        raw_df = engine.get_symbol_data(s)
        if raw_df is not None:
            calc = IndicatorCalculator(raw_df)
            processed_df = (
                calc.add_sma(
                    [
                        cfg["strategy"]["params"]["sma_short"],
                        cfg["strategy"]["params"]["sma_long"],
                    ]
                )
                .add_rsi([14])
                .add_macd()
                .add_bollinger_bands()
                .clean_data()
                .get_result()
            )
            engine.save_processed(s, processed_df)

    # 4. 生成策略信号
    print("\n[Step 3] 正在生成交易信号...")
    strategy = None
    if cfg["strategy"]["active_strategy"] == "MaRsiStrategy":
        strategy = MaRsiStrategy(symbols=cfg["backtest"]["symbols"])
    elif cfg["strategy"]["active_strategy"] == "BollingerMeanReversion":
        strategy = BollingerMeanReversion(symbols=cfg["backtest"]["symbols"])
    signals_dict = strategy.generate_all_signals(engine)

    # 5. 回测与可视化
    print("\n[Step 4] 正在运行回测并生成可视化报告...")
    backtester = BacktestEngine(
        initial_capital=cfg["backtest"]["initial_capital"],
        commission=cfg["backtest"]["commission"],
    )
    viz = Visualizer(report_path=cfg["paths"]["reports"])
    html_viz = HTMLVisualizer(report_path=cfg["paths"]["reports"])
    dashboard = DashboardGenerator()

    all_metrics = []

    for symbol, df_sig in signals_dict.items():
        # 执行回测计算
        results = backtester.run(symbol, df_sig)

        # 终端打印性能指标
        m = backtester.calculate_advanced_metrics(symbol, results)
        all_metrics.append(m)

        # 保存图片报告
        viz.plot_backtest(symbol, results)
        html_viz.generate_interactive_report(symbol, results)

    dashboard.generate_summary(all_metrics, cfg)

    print("\n✅ 整个流程运行完毕！请查阅 reports 文件夹中的报告图片。")


if __name__ == "__main__":
    run_pipeline()
