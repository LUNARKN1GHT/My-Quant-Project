import os
from datetime import datetime

import pandas as pd


class DashboardGenerator:
    def __init__(self, report_path: str = "reports"):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.save_dir = os.path.join(project_root, report_path)
        self.save_path = os.path.join(self.save_dir, "index.html")

    def generate_summary(self, metrics_list: list, config: dict):
        df = pd.DataFrame(metrics_list)

        # 1. 格式化 Symbol 链接
        df["Symbol"] = df["Symbol"].apply(
            lambda x: (
                f'<a href="./{x}/{x}_interactive.html" target="_blank">{x}</a>'
                if x != "PORTFOLIO_TOTAL"
                else f"<b>{x}</b>"
            )
        )

        # 2. 只有单股模式下才显示“详情报告”列
        if "Symbol" in df.columns:
            df["Analysis"] = df.apply(
                lambda row: (
                    f'<a href="./{row["Symbol"]}/{row["Symbol"]}_interactive.html" target="_blank">📈 查看分析</a>'
                    if "PORTFOLIO_TOTAL" not in str(row["Symbol"])
                    else "-"
                ),
                axis=1,
            )

        # 3. 组合模式特有的顶部组件
        portfolio_banner = ""
        if config["backtest"].get("mode") == "portfolio":
            portfolio_banner = f"""
            <div class="card portfolio-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h2 style="color: #00bfff; margin: 0;">📊 组合投资模式已激活</h2>
                        <p style="color: #888; margin: 5px 0 0 0;">资产动态调仓与风险对冲深度分析</p>
                    </div>
                    <a href="portfolio_allocation.html" class="btn-main">打开资产分配堆叠图</a>
                </div>
            </div>
            """

        # 4. 构建高对比度深色 HTML
        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="utf-8">
            <title>Gemini Quant Dashboard</title>
            <style>
                :root {{ --bg: #0f1115; --card: #1a1d23; --text: #e0e0e0; --accent: #00bfff; --border: #2d323a; }}
                body {{ font-family: 'Inter', system-ui, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 40px; }}
                .container {{ max-width: 1200px; margin: auto; }}
                h1 {{ font-size: 28px; font-weight: 700; margin-bottom: 30px; letter-spacing: -0.5px; }}

                /* 配置卡片 */
                .header-grid {{ display: grid; grid-template-columns: 2fr 1fr; gap: 20px; margin-bottom: 30px; }}
                .card {{ background: var(--card); border: 1px solid var(--border); padding: 25px; border-radius: 12px; }}
                .config-item {{ margin-bottom: 12px; font-size: 14px; color: #aaa; }}
                .config-item strong {{ color: var(--accent); font-size: 16px; display: block; margin-bottom: 4px; }}

                /* 组合特有卡片 */
                .portfolio-card {{ border-left: 5px solid var(--accent); background: linear-gradient(90deg, #1a1d23 0%, #15202b 100%); margin-bottom: 30px; }}
                .btn-main {{ background: var(--accent); color: #000; padding: 12px 24px; border-radius: 8px; font-weight: bold; text-decoration: none; transition: 0.3s; }}
                .btn-main:hover {{ transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,191,255,0.4); }}

                /* 数据表格 */
                table {{ width: 100%; border-collapse: collapse; margin-top: 10px; background: var(--card); border-radius: 12px; overflow: hidden; }}
                th {{ background: #242930; color: #888; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; padding: 18px; text-align: left; }}
                td {{ padding: 18px; border-bottom: 1px solid var(--border); font-size: 15px; }}
                tr:last-child td {{ border-bottom: none; }}
                tr:hover {{ background: #242933; }}
                a {{ color: var(--accent); text-decoration: none; }}

                /* 状态标签 */
                .positive {{ color: #00ff88; font-weight: bold; }}
                .negative {{ color: #ff4444; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📈 策略多品种回测看板</h1>

                {portfolio_banner}

                <div class="header-grid">
                    <div class="card">
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                            <div class="config-item">
                                <strong>核心参数</strong>
                                {", ".join([f"{k}: {v}" for k, v in config["strategy"]["params"].items()])}
                            </div>
                            <div class="config-item">
                                <strong>测试周期</strong>
                                {config['backtest']['start_date']} >> {config['backtest']['end_date']}
                            </div>
                        </div>
                    </div>
                    <div class="card">
                        <div class="config-item">
                            <strong>当前执行策略</strong>
                            <span style="font-size: 18px; color: white;">{config["strategy"]["active_strategy"]}</span>
                        </div>
                    </div>
                </div>

                <div class="card" style="padding: 0;">
                    {df.to_html(escape=False, index=False, border=0)}
                </div>

                <div style="text-align: center; margin-top: 40px; color: #555; font-size: 12px;">
                    Report Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Gemini Quant Engine V3.0
                </div>
            </div>
        </body>
        </html>
        """

        with open(self.save_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"🚀 [Dashboard] 深色高对比度看板已生成: {self.save_path}")
