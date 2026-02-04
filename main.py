from core.workflow import WorkflowManager
from strategies.ml_strategy import MLStrategy

# from strategies.simple_strategy import MaRsiStrategy # 也可以按需导入


def main():
    # 实例化指挥官
    flow = WorkflowManager()

    # 执行流水线
    flow.sync_data()
    flow.prepare_features()

    # 动态选择策略
    # 你可以从配置中读取，这里演示直接传入 AI 策略
    ai_strategy = MLStrategy(
        symbols=flow.cfg["backtest"]["symbols"], prob_threshold=0.52
    )

    flow.run_backtest(ai_strategy)

    # 汇总
    flow.finalize()


if __name__ == "__main__":
    main()
