"""
ScholarMind Logging Utilities
智读ScholarMind日志工具模块

统一的日志配置和管理，支持中文路径显示
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional

# 直接定义日志配置，避免循环导入
class LoggingConfig:
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR = os.getenv("LOG_DIR", "logs")  # 日志目录
    LOG_FILE = os.getenv("LOG_FILE", "logs/scholarmind.log")  # 默认日志文件路径
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def safe_path_str(path) -> str:
    """
    安全地将路径转换为字符串，确保中文字符正确显示
    
    Args:
        path: 路径对象或字符串
        
    Returns:
        str: 安全的路径字符串
    """
    if path is None:
        return ""
    
    try:
        # 如果是Path对象，转换为字符串
        if hasattr(path, '__fspath__'):
            path_str = str(path)
        else:
            path_str = str(path)
            
        # 确保字符串可以正确显示中文
        return path_str.encode('utf-8', errors='replace').decode('utf-8')
    except Exception:
        # 如果转换失败，返回安全的表示
        return repr(path)


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

    # 控制台处理器 - 优化中文显示
    if console:
        # 在Windows上尝试设置控制台编码
        if sys.platform == "win32":
            try:
                # 尝试设置控制台为UTF-8编码
                if hasattr(sys.stdout, 'reconfigure'):
                    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
                if hasattr(sys.stderr, 'reconfigure'):
                    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
            except Exception:
                # 如果设置失败，继续使用默认编码
                pass
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        
        # 设置处理器编码
        if hasattr(console_handler.stream, 'reconfigure'):
            try:
                console_handler.stream.reconfigure(encoding='utf-8', errors='replace')
            except Exception:
                pass
                
        logger.addHandler(console_handler)

    # 文件处理器
    if log_file or LoggingConfig.LOG_FILE:
        file_path = log_file or LoggingConfig.LOG_FILE

        # 确保日志目录存在
        log_dir = Path(file_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(file_path, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


class ScholarMindLogger:
    """ScholarMind专用日志器，增强中文路径支持"""
    
    def __init__(self, name: str):
        self.logger = setup_logger(name)
    
    def log_path_operation(self, level: str, operation: str, path, message: str = "", **kwargs):
        """
        记录路径相关操作，确保中文路径正确显示
        
        Args:
            level: 日志级别 (info, warning, error, debug)
            operation: 操作类型
            path: 路径对象或字符串
            message: 附加消息
            **kwargs: 其他参数
        """
        safe_path = safe_path_str(path)
        log_message = f"{operation}: {safe_path}"
        if message:
            log_message += f" - {message}"
        
        # 添加其他参数
        if kwargs:
            extra_info = ", ".join(f"{k}={v}" for k, v in kwargs.items())
            log_message += f" ({extra_info})"
        
        getattr(self.logger, level.lower())(log_message)
    
    def info_path(self, operation: str, path, message: str = "", **kwargs):
        """记录路径信息"""
        self.log_path_operation("info", operation, path, message, **kwargs)
    
    def warning_path(self, operation: str, path, message: str = "", **kwargs):
        """记录路径警告"""
        self.log_path_operation("warning", operation, path, message, **kwargs)
    
    def error_path(self, operation: str, path, message: str = "", **kwargs):
        """记录路径错误"""
        self.log_path_operation("error", operation, path, message, **kwargs)
    
    def debug_path(self, operation: str, path, message: str = "", **kwargs):
        """记录路径调试信息"""
        self.log_path_operation("debug", operation, path, message, **kwargs)
    
    def __getattr__(self, name):
        """代理其他日志方法到原始logger"""
        return getattr(self.logger, name)


# 预创建常用的logger实例
agent_logger = ScholarMindLogger('scholarmind.agent')
pipeline_logger = ScholarMindLogger('scholarmind.pipeline')
tool_logger = ScholarMindLogger('scholarmind.tool')
