import os

import pandas as pd


class DashboardGenerator:
    def __init__(self, report_path: str = "reports"):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.save_path = os.path.join(project_root, report_path, "index.html")

    def generate_summary(self, metrics_list: list):
        """
        将多个股票的指标列表转为 HTML 表格
        """
        df = pd.DataFrame(metrics_list)

        # 使用 Pandas 自带的 HTML 转换，并加入简单的 CSS 样式
        html_style = """
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background-color: #f4f7f6; }
            table { border-collapse: collapse; width: 100%; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 0 20px rgba(0,0,0,0.1); }
            th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #ddd; }
            th { background-color: #2c3e50; color: white; }
            tr:hover { background-color: #f5f5f5; }
            .positive { color: #27ae60; font-weight: bold; }
            .negative { color: #c0392b; font-weight: bold; }
        </style>
        """

        title = "<h1>Strategy Dashboard</h1>"
        table_html = df.to_html(index=False, classes="table")

        # 增加链接跳转功能 (点击 Symbol 跳转到对应的详细 HTML 报告)
        # 注意：这里需要一些简单的字符串替换

        with open(self.save_path, "w", encoding="utf-8") as f:
            f.write(html_style + title + table_html)

        print(f"[Dashboard] 汇总看板已生成: {self.save_path}")
