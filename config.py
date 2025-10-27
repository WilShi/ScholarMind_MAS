"""
ScholarMind Configuration File
智读ScholarMind系统配置文件
"""

import json
import os
from typing import Any, Dict, Optional

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ModelConfig:
    """LLM模型配置"""

    # 默认模型配置名称（对应 model_configs.json 中的 config_name）
    DEFAULT_MODEL_CONFIG_NAME = "qwen-235b"

    # 备用模型配置名称
    BACKUP_MODEL_CONFIG_NAME = "qwen-80b"


class AcademicAPIConfig:
    """学术API配置"""

    # Semantic Scholar API
    SEMANTIC_SCHOLAR_API_KEY = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
    SEMANTIC_SCHOLAR_BASE_URL = "https://api.semanticscholar.org/graph/v1"

    # ArXiv API
    ARXIV_BASE_URL = "http://export.arxiv.org/api/query"


class ProcessingConfig:
    """处理配置"""

    # PDF解析配置 - 支持环境变量覆盖
    MAX_PDF_SIZE = int(os.getenv("MAX_PDF_SIZE", str(50 * 1024 * 1024)))  # 默认50MB
    PDF_PARSE_TIMEOUT = int(os.getenv("PDF_PARSE_TIMEOUT", "30"))  # 默认30秒

    # 文本处理配置 - 支持环境变量覆盖
    MAX_TEXT_LENGTH = int(os.getenv("MAX_TEXT_LENGTH", "100000"))  # 默认100000字符
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "5000"))  # 默认5000字符

    # 并行处理配置 - 支持环境变量覆盖
    MAX_WORKERS = int(os.getenv("MAX_WORKERS", "4"))  # 默认4个worker
    PARALLEL_TIMEOUT = int(os.getenv("PARALLEL_TIMEOUT", "300"))  # 默认300秒


class OutputConfig:
    """输出配置"""

    # 报告生成配置 - 支持环境变量覆盖
    REPORT_TEMPLATE_DIR = os.getenv("REPORT_TEMPLATE_DIR", "prompts/templates")
    OUTPUT_DIR = os.getenv("OUTPUT_DIR", "outputs")

    # 报告格式配置
    REPORT_FORMATS = ["markdown", "html", "pdf"]
    DEFAULT_REPORT_FORMAT = os.getenv("DEFAULT_REPORT_FORMAT", "markdown")

    # 输出语言配置
    OUTPUT_LANGUAGES = ["zh", "en"]  # zh=中文, en=英文
    DEFAULT_OUTPUT_LANGUAGE = os.getenv("DEFAULT_OUTPUT_LANGUAGE", "zh")  # 默认中文


class LoggingConfig:
    """日志配置"""

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR = os.getenv("LOG_DIR", "logs")  # 日志目录
    LOG_FILE = os.getenv("LOG_FILE", "logs/scholarmind.log")  # 主日志文件
    LOG_FORMAT = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")


class CacheConfig:
    """缓存配置"""

    ENABLE_CACHE = os.getenv("ENABLE_CACHE", "true").lower() == "true"  # 支持环境变量
    CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))  # 默认1小时
    CACHE_DIR = os.getenv("CACHE_DIR", ".cache")
    MAX_CACHE_SIZE = int(os.getenv("MAX_CACHE_SIZE", "1000"))  # 默认1000MB


def get_model_config(model_name: Optional[str] = None) -> Dict[str, Any]:
    """
    获取模型配置

    Args:
        model_name: 模型配置名称（对应model_configs.json中的config_name），
                   如果为None，则返回默认模型配置

    Returns:
        模型配置字典
    """
    # 读取model_configs.json
    config_path = os.path.join(os.path.dirname(__file__), "model_configs.json")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            model_configs = json.load(f)

        # 如果没有指定model_name，使用默认配置
        if model_name is None:
            model_name = ModelConfig.DEFAULT_MODEL_CONFIG_NAME
        elif model_name == "backup":
            model_name = ModelConfig.BACKUP_MODEL_CONFIG_NAME

        # 查找指定的配置
        for config in model_configs:
            if config.get("config_name") == model_name:
                # 替换环境变量占位符
                result_config = {}
                for key, value in config.items():
                    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                        env_var = value[2:-1]
                        result_config[key] = os.getenv(env_var, "")
                    else:
                        result_config[key] = value

                return result_config

        # 如果没找到，返回默认配置
        return model_configs[0] if model_configs else {}

    except (FileNotFoundError, json.JSONDecodeError):
        # 如果配置文件读取失败，返回一个基本的备用配置
        return {
            "config_name": "fallback",
            "model_type": "openai_chat",
            "model_name": "gpt-3.5-turbo",
            "api_key": os.getenv("OPENAI_API_KEY", ""),
            "temperature": 0.1,
            "max_tokens": 4000,
        }


def validate_config() -> bool:
    """验证配置是否完整"""
    # 检查是否至少配置了其中一个API密钥
    openai_key = os.getenv("OPENAI_API_KEY")
    modelscope_key = os.getenv("MODELSCOPE_API_KEY")

    if not openai_key and not modelscope_key:
        print(
            "Missing required environment variable: "
            "Please set either OPENAI_API_KEY or MODELSCOPE_API_KEY"
        )
        return False

    return True


def setup_directories():
    """创建必要的目录"""
    directories = [
        OutputConfig.OUTPUT_DIR,
        CacheConfig.CACHE_DIR,
        OutputConfig.REPORT_TEMPLATE_DIR,
        LoggingConfig.LOG_DIR,  # 添加日志目录
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)


if __name__ == "__main__":
    # 验证配置
    if validate_config():
        print("Configuration validation passed!")
        setup_directories()
        print("Directories setup completed!")
    else:
        print("Configuration validation failed!")
