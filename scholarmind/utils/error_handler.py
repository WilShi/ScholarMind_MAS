"""
ScholarMind Error Handler
统一的错误处理、重试和降级策略
"""

import asyncio
import functools
import traceback
from typing import Any, Callable, Dict, Optional, Type, Union

from ..utils.logger import setup_logger

logger = setup_logger('scholarmind.error_handler', level='INFO', log_file=None, console=True)


def with_error_handling(fallback_value=None, reraise=False):
    """
    错误处理装饰器
    
    Args:
        fallback_value: 出错时的返回值
        reraise: 是否重新抛出异常
    """
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"函数 {func.__name__} 执行失败: {e}")
                if reraise:
                    raise
                return fallback_value or {"success": False, "error": str(e)}
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"函数 {func.__name__} 执行失败: {e}")
                if reraise:
                    raise
                return fallback_value or {"success": False, "error": str(e)}
        
        # 根据函数类型返回对应的包装器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


async def async_safe_execute(func: Callable, *args, fallback_value=None, **kwargs):
    """
    安全执行异步函数
    
    Args:
        func: 要执行的异步函数
        *args: 位置参数
        fallback_value: 出错时的返回值
        **kwargs: 关键字参数
    
    Returns:
        函数执行结果或fallback_value
    """
    try:
        return await func(*args, **kwargs)
    except Exception as e:
        logger.error(f"安全执行异步函数 {func.__name__} 失败: {e}")
        return fallback_value


class ScholarMindError(Exception):
    """ScholarMind基础异常类"""
    def __init__(self, message: str, error_code: str = None, context: Dict[str, Any] = None):
        super().__init__(message)
        self.error_code = error_code
        self.context = context or {}


class ModelError(ScholarMindError):
    """模型相关错误"""
    pass


class PipelineError(ScholarMindError):
    """Pipeline相关错误"""
    pass


class ValidationError(ScholarMindError):
    """验证相关错误"""
    pass


class ConfigurationError(ScholarMindError):
    """配置相关错误"""
    pass


def retry_with_exponential_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple = (Exception,)
):
    """指数退避重试装饰器"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries - 1:
                        break
                        
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    logger.warning(f"重试 {attempt + 1}/{max_retries} {func.__name__}: {e}")
                    await asyncio.sleep(delay)
                    
            # 所有重试都失败
            logger.error(f"重试失败 {func.__name__}: {last_exception}")
            raise last_exception
            
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries - 1:
                        break
                        
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    logger.warning(f"重试 {attempt + 1}/{max_retries} {func.__name__}: {e}")
                    asyncio.sleep(delay)
                    
            raise last_exception
            
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
            
    return decorator


def safe_execute(
    fallback_value: Any = None,
    error_message: str = "操作失败",
    exceptions: tuple = (Exception,)
):
    """安全执行装饰器，提供降级机制"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except exceptions as e:
                logger.error(f"{error_message}: {e}")
                logger.debug(f"错误详情: {traceback.format_exc()}")
                return fallback_value
                
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                logger.error(f"{error_message}: {e}")
                logger.debug(f"错误详情: {traceback.format_exc()}")
                return fallback_value
                
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
            
    return decorator


class ErrorHandler:
    """错误处理器"""
    
    @staticmethod
    def handle_model_error(error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """处理模型错误"""
        error_msg = f"模型推理失败: {str(error)}"
        logger.error(error_msg)
        
        return {
            "success": False,
            "error": error_msg,
            "error_type": "model_error",
            "context": context,
            "fallback_response": "模型服务暂时不可用，请稍后重试"
        }
    
    @staticmethod
    def handle_pipeline_error(error: Exception, stage: str = None) -> Dict[str, Any]:
        """处理Pipeline错误"""
        error_msg = f"Pipeline执行失败{f' (阶段: {stage})' if stage else ''}: {str(error)}"
        logger.error(error_msg)
        
        return {
            "success": False,
            "error": error_msg,
            "error_type": "pipeline_error",
            "stage": stage,
            "suggestion": "请检查输入参数或联系技术支持"
        }
    
    @staticmethod
    def handle_validation_error(error: Exception, field: str = None) -> Dict[str, Any]:
        """处理验证错误"""
        error_msg = f"参数验证失败{f' (字段: {field})' if field else ''}: {str(error)}"
        logger.warning(error_msg)
        
        return {
            "success": False,
            "error": error_msg,
            "error_type": "validation_error",
            "field": field,
            "suggestion": "请检查输入参数的格式和完整性"
        }
    
    @staticmethod
    def handle_configuration_error(error: Exception, config_type: str = None) -> Dict[str, Any]:
        """处理配置错误"""
        error_msg = f"配置错误{f' (类型: {config_type})' if config_type else ''}: {str(error)}"
        logger.error(error_msg)
        
        return {
            "success": False,
            "error": error_msg,
            "error_type": "configuration_error",
            "config_type": config_type,
            "suggestion": "请检查配置文件或环境变量设置"
        }
    
    @staticmethod
    def handle_timeout_error(error: Exception, operation: str = None, timeout: float = None) -> Dict[str, Any]:
        """处理超时错误"""
        timeout_str = f"({timeout}秒)" if timeout else ""
        error_msg = f"操作超时{f' ({operation})' if operation else ''}{timeout_str}: {str(error)}"
        logger.warning(error_msg)
        
        return {
            "success": False,
            "error": error_msg,
            "error_type": "timeout_error",
            "operation": operation,
            "timeout": timeout,
            "suggestion": "请检查网络连接或增加超时时间"
        }


# 全局错误处理实例
error_handler = ErrorHandler()