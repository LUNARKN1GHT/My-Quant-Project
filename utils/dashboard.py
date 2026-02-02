import os
from datetime import datetime

import pandas as pd


class DashboardGenerator:
    def __init__(self, report_path: str = "reports"):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.save_dir = os.path.join(project_root, report_path)
        self.save_path = os.path.join(self.save_dir, "index.html")

    def generate_summary(self, metrics_list: list, config: dict):
        """
        生成包含跳转链接、策略参数和高级统计的看板
        """
        df = pd.DataFrame(metrics_list)

        # 1. 核心改进：将 Symbol 列转换为 HTML 链接
        # 假设详细报告的文件名格式为: Symbol_interactive.html
        df["Report"] = df["Symbol"].apply(
            lambda x: f'<a href="./{x}/{x}_interactive.html" target="_blank">🔍 详情报告</a>'
        )

        # 2. 提取配置信息用于展示
        strat_name = config["strategy"]["active_strategy"]
        strat_params = config["strategy"]["params"]
        backtest_range = (
            f"{config['backtest']['start_date']} 至 {config['backtest']['end_date']}"
        )

        # 3. 构建现代感十足的 HTML 模板
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>量化策略回测看板</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; background-color: #f8f9fa; color: #333; }}
                .container {{ max-width: 1200px; margin: auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
                .config-section {{ background: #ecf0f1; padding: 20px; border-radius: 8px; margin-bottom: 30px; display: flex; justify-content: space-between; }}
                .config-item {{ flex: 1; }}
                .config-item strong {{ color: #2980b9; }}
                table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
                th {{ background-color: #34495e; color: white; padding: 15px; text-align: left; }}
                td {{ padding: 12px 15px; border-bottom: 1px solid #eee; }}
                tr:hover {{ background-color: #f1f1f1; }}
                a {{ text-decoration: none; color: #3498db; font-weight: bold; }}
                a:hover {{ color: #2980b9; text-decoration: underline; }}
                .footer {{ margin-top: 30px; font-size: 0.8em; color: #95a5a6; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📈 策略多品种回测总览看板</h1>

                <div class="config-section">
                    <div class="config-item">
                        <strong>当前策略:</strong> {strat_name} <br>
                        <strong>测试周期:</strong> {backtest_range}
                    </div>
                    <div class="config-item">
                        <strong>核心参数:</strong> <br>
                        {", ".join([f"{k}: {v}" for k, v in strat_params.items()])}
                    </div>
                    <div class="config-item">
                        <strong>生成时间:</strong> <br>
                        {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    </div>
                </div>

                {df.to_html(escape=False, index=False, border=0)}

                <div class="footer">
                    * 点击 Symbol 或报告列可跳转至 Plotly 交互式详情页进行深度复盘。
                </div>
            </div>
        </body>
        </html>
        """

        with open(self.save_path, "w", encoding="utf-8") as f:
            f.write(html_template)

        print(f"🚀 [Dashboard] 带有参数展示和跳转功能的看板已生成: {self.save_path}")
