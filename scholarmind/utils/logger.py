"""
ScholarMind Logging Utilities
智读ScholarMind日志工具模块

统一的日志配置和管理
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from config import LoggingConfig


def setup_logger(
    name: str,
    level: Optional[str] = None,
    log_file: Optional[str] = None,
    console: bool = True
) -> logging.Logger:
    """
    设置并返回配置好的logger

    Args:
        name: Logger名称
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 日志文件路径（可选）
        console: 是否输出到控制台

    Returns:
        logging.Logger: 配置好的logger实例
    """
    logger = logging.getLogger(name)

    # 避免重复添加handler
    if logger.handlers:
        return logger

    # 设置日志级别
    log_level = level or LoggingConfig.LOG_LEVEL
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # 创建格式化器
    formatter = logging.Formatter(
        LoggingConfig.LOG_FORMAT,
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 控制台处理器
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # 文件处理器
    if log_file or LoggingConfig.LOG_FILE:
        file_path = log_file or LoggingConfig.LOG_FILE
        # 确保日志目录存在
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(file_path, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# 预创建常用的logger实例
agent_logger = setup_logger('scholarmind.agent')
pipeline_logger = setup_logger('scholarmind.pipeline')
tool_logger = setup_logger('scholarmind.tool')
