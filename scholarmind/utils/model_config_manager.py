"""
ScholarMind Enhanced Model Configuration Manager
增强的模型配置管理器，支持缓存、验证和可用性测试
"""

import asyncio
import json
import os
import time
from typing import Dict, Any, Optional

from config import get_model_config, ModelConfig
from ..utils.logger import setup_logger

logger = setup_logger('scholarmind.model_config_manager', level='INFO', log_file=None, console=True)


class ModelConfigManager:
    """模型配置管理器（单例模式）"""
    
    _instance = None
    _config_cache = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._configs = {}  # 初始化配置字典
        return cls._instance
        
    def get_model_config(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """获取模型配置，支持缓存和验证"""
        cache_key = model_name or "default"
        
        if cache_key not in self._config_cache:
            config = get_model_config(model_name)
            self._validate_config(config)
            self._config_cache[cache_key] = config
            # 同时存储到_configs中
            self._configs[cache_key] = config
            
        return self._config_cache[cache_key]
        
    def _validate_config(self, config: Dict[str, Any]):
        """验证模型配置的完整性"""
        required_fields = ["model_name", "api_key", "model_type"]
        for field in required_fields:
            if not config.get(field):
                raise ValueError(f"模型配置缺少必需字段: {field}")
                
    def clear_cache(self):
        """清除配置缓存"""
        self._config_cache.clear()
        
    def get_all_configs(self) -> Dict[str, Any]:
        """获取所有模型配置"""
        return self._configs.copy()


class EnhancedModelConfigManager(ModelConfigManager):
    """增强的模型配置管理器"""
    
    def __init__(self):
        super().__init__()
        self.availability_tester = None
        
    async def check_all_models_availability(self) -> Dict[str, Dict[str, Any]]:
        """
        检查所有模型的可用性
        
        Returns:
            Dict[str, Dict[str, Any]]: 模型名称到可用性状态的映射
        """
        results = {}
        
        # 获取所有模型配置
        configs = self.get_all_configs()
        
        # 并发测试所有模型
        tasks = []
        model_names = []
        
        for model_name, config in configs.items():
            if config.get("availability_test", {}).get("enabled", True):
                tasks.append(self.test_model_availability(model_name))
                model_names.append(model_name)
        
        if tasks:
            availability_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for model_name, result in zip(model_names, availability_results):
                if isinstance(result, Exception):
                    results[model_name] = {
                        "available": False,
                        "error": str(result),
                        "tested_at": time.time()
                    }
                else:
                    results[model_name] = result
        
        return results

    async def get_available_model_config(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """
        获取可用的模型配置，会进行可用性测试
        
        Args:
            model_name: 模型配置名称
            
        Returns:
            可用的模型配置
        """
        # 如果未指定模型名，获取默认配置
        if model_name is None:
            model_name = ModelConfig.DEFAULT_MODEL_CONFIG_NAME
            
        # 获取配置
        config = self.get_model_config(model_name)
        
        # 进行可用性测试
        if self.availability_tester is None:
            from .model_availability import get_model_tester
            self.availability_tester = get_model_tester()
        
        test_result = await self.availability_tester.test_model_availability(model_name)
        
        if not test_result.get("available", False):
            # 如果默认模型不可用，尝试备用模型
            if model_name == ModelConfig.DEFAULT_MODEL_CONFIG_NAME:
                logger.warning(f"默认模型 {model_name} 不可用，尝试备用模型")
                backup_config = self.get_model_config(ModelConfig.BACKUP_MODEL_CONFIG_NAME)
                backup_test_result = await self.availability_tester.test_model_availability(ModelConfig.BACKUP_MODEL_CONFIG_NAME)
                
                if backup_test_result.get("available", False):
                    logger.info(f"使用备用模型 {ModelConfig.BACKUP_MODEL_CONFIG_NAME}")
                    return backup_config
                else:
                    raise RuntimeError(f"默认模型和备用模型都不可用")
            else:
                raise RuntimeError(f"模型 {model_name} 不可用: {test_result.get('message')}")
        
        return config
    
    async def initialize_with_availability_check(self):
        """初始化并进行可用性检查"""
        logger.info("正在检查模型可用性...")
        
        # 测试默认模型
        try:
            await self.get_available_model_config(ModelConfig.DEFAULT_MODEL_CONFIG_NAME)
            logger.info(f"默认模型 {ModelConfig.DEFAULT_MODEL_CONFIG_NAME} 可用")
        except Exception as e:
            logger.warning(f"默认模型检查失败: {e}")
            
        # 测试备用模型
        try:
            await self.get_available_model_config(ModelConfig.BACKUP_MODEL_CONFIG_NAME)
            logger.info(f"备用模型 {ModelConfig.BACKUP_MODEL_CONFIG_NAME} 可用")
        except Exception as e:
            logger.warning(f"备用模型检查失败: {e}")
            
        # 如果启用，测试所有模型
        if os.getenv("ENABLE_MODEL_AVAILABILITY_TEST", "true").lower() == "true":
            logger.info("正在测试所有配置的模型...")
            all_results = await self.availability_tester.test_all_models()
            
            available_count = sum(1 for result in all_results.values() if result.get("available", False))
            total_count = len(all_results)
            
            logger.info(f"模型可用性测试完成: {available_count}/{total_count} 个模型可用")
            
            # 列出不可用的模型
            for config_name, result in all_results.items():
                if not result.get("available", False):
                    logger.warning(f"模型 {config_name} 不可用: {result.get('message')}")


# 全局增强配置管理器实例
_enhanced_config_manager = None


def get_enhanced_model_config_manager() -> EnhancedModelConfigManager:
    """获取增强的模型配置管理器实例"""
    global _enhanced_config_manager
    if _enhanced_config_manager is None:
        _enhanced_config_manager = EnhancedModelConfigManager()
    return _enhanced_config_manager