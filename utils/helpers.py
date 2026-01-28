import os

import yaml


def load_config(config_name="settings.yaml"):
    """
    从 config 文件夹加载 YAML 配置文件
    :param config_name: 配置文件名称
    :return: 配置数据集
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(project_root, "config", config_name)

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config
