# 📈 My-Quant-Project: 模块化量化回测与分析系统

这是一个基于 Python 开发的工业级量化交易回测框架。系统采用模块化设计，支持自动化数据抓取、多维度技术指标计算、向量化回测以及可视化报告生成。

## 🌟 核心特性

- **配置驱动 (Config-Driven)**: 所有的路径、股票池、策略参数均通过 config/settings.yaml 统一管理。
- **高效数据引擎**: 支持 Parquet 格式存储，读取速度比传统 CSV 快 10 倍以上；内置内存缓存机制，支持大数据量回测。
- **向量化回测**: 弃用低效的循环模式，采用 Pandas 向量化运算，秒级完成多年历史数据回测。
- **自动化报告**: 自动生成包含价格走势、买卖信号、资金曲线及最大回撤的综合分析图表。
- **机器学习准备**: 标准化的 Processed 特征集存储，无缝对接 Scikit-learn 或 TensorFlow。

# 📂 项目结构

```Plaintext
My-Quant-Project/
├── config/ # 配置文件
│ └── settings.yaml # 全局参数设置
├── core/ # 核心引擎
│ ├── data_engine.py # 数据调度与缓存管理
│ └── backtest_engine.py # 向量化回测引擎
├── data/ # 数据处理
│ └── data_loader.py # 自动下载与清理 (Yahoo Finance)
├── indicators/ # 特征工程
│ └── indicator_calculator.py # 链式指标计算器
├── strategies/ # 交易策略
│ ├── base.py # 策略抽象基类
│ └── simple_strategy.py # 双均线 + RSI 策略实现
├── utils/ # 工具库
│ ├── helpers.py # 配置加载与通用工具
│ └── visualizer.py # Matplotlib 可视化模块
├── storage/ # 数据仓库 (自动创建)
│ ├── raw/ # 原始行情数据
│ └── processed/ # 加工后的特征数据
├── reports/ # 报告中心 (自动创建)
│ └── *.png # 回测分析图表
└── main.py # 项目主入口
```

## 📊 回测报告说明

生成的 reports/*.png 包含两个主要部分：

1. Price Analysis: 展示股价、技术指标（SMA等）以及策略生成的 Buy (红色三角) 与 Sell (绿色三角) 信号点。
2. Portfolio Value: 实时记录账户净值变化，并用淡红色区域标注出历史最大回撤 (Max Drawdown) 的发生阶段。

🛠 未来规划 (Roadmap)

- [ ] 机器学习接入: 引入随机森林 (Random Forest) 预测涨跌概率。
- [ ] 实盘接口: 对接主流 Broker API 实现自动化下单。
- [ ] 多因子分析: 增加宏观经济数据与财务报表因子的对齐。
- [ ] 组合投资: 通过组合投资分配资产
- [ ] 精细化: 量化持股数量