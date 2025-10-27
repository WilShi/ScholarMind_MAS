"""
ScholarMind Model Availability Tester
模型可用性测试模块
"""

import asyncio
import json
import os
import time
from typing import Any, Dict, List, Optional

import aiohttp
from agentscope.model import OpenAIChatModel

from ..utils.logger import setup_logger

logger = setup_logger("scholarmind.model_availability", level="INFO", log_file=None, console=True)


class ModelAvailabilityTester:
    """模型可用性测试器"""

    def __init__(self):
        self.test_results = {}
        self.test_timeout = int(os.getenv("MODEL_TEST_TIMEOUT", "10"))
        self.enable_test = os.getenv("ENABLE_MODEL_AVAILABILITY_TEST", "true").lower() == "true"

    async def test_model_availability(self, config_name: str) -> Dict[str, Any]:
        """
        测试指定模型的可用性

        Args:
            config_name: 模型配置名称

        Returns:
            测试结果字典
        """
        if not self.enable_test:
            return {"available": True, "message": "模型可用性测试已禁用", "test_time": time.time()}

        try:
            # 获取模型配置
            from config import get_model_config

            model_config = get_model_config(config_name)

            # 检查是否配置了可用性测试
            availability_test = model_config.get("availability_test", {})
            if not availability_test.get("enabled", False):
                return {
                    "available": True,
                    "message": "该模型未配置可用性测试",
                    "test_time": time.time(),
                }

            # 执行测试
            start_time = time.time()
            result = await self._execute_model_test(model_config, availability_test)
            result["test_time"] = time.time()
            result["test_duration"] = time.time() - start_time

            # 缓存测试结果
            self.test_results[config_name] = result

            return result

        except Exception as e:
            error_result = {
                "available": False,
                "error": str(e),
                "message": f"模型测试失败: {str(e)}",
                "test_time": time.time(),
            }
            self.test_results[config_name] = error_result
            return error_result

    async def _execute_model_test(
        self, model_config: Dict[str, Any], test_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行具体的模型测试"""
        try:
            # 创建模型实例
            model = OpenAIChatModel(
                model_name=model_config.get("model_name"),
                api_key=model_config.get("api_key"),
                client_args=model_config.get("client_args", {}),
                generate_kwargs={
                    "temperature": model_config.get("temperature", 0.1),
                    "max_tokens": 50,  # 测试时使用较小的token数
                    "top_p": model_config.get("top_p", 0.9),
                },
            )

            # 准备测试消息
            test_message = test_config.get("test_message", "Hello")
            messages = [{"role": "user", "content": test_message}]

            # 执行测试请求
            response = await asyncio.wait_for(model(messages), timeout=self.test_timeout)

            # 解析响应
            response_text = await self._parse_response(response)

            # 验证响应
            expected_min_length = test_config.get("expected_response_length_min", 1)
            is_valid = len(response_text.strip()) >= expected_min_length

            return {
                "available": is_valid,
                "message": "模型测试成功" if is_valid else "模型响应不符合预期",
                "response_text": response_text,
                "response_length": len(response_text),
            }

        except asyncio.TimeoutError:
            return {
                "available": False,
                "message": f"模型测试超时（{self.test_timeout}秒）",
                "error": "timeout",
            }
        except Exception as e:
            return {"available": False, "message": f"模型测试失败: {str(e)}", "error": str(e)}

    async def _parse_response(self, response) -> str:
        """解析模型响应"""
        try:
            if hasattr(response, "__aiter__"):
                # 处理流式响应
                response_text = ""
                async for chunk in response:
                    if hasattr(chunk, "content"):
                        if isinstance(chunk.content, list):
                            response_text += "".join(item.get("text", "") for item in chunk.content)
                        elif isinstance(chunk.content, str):
                            response_text += chunk.content
            elif hasattr(response, "text"):
                response_text = response.text
            elif isinstance(response, dict):
                response_text = response.get("text", response.get("content", str(response)))
            else:
                response_text = str(response)
            return response_text
        except Exception:
            return str(response)

    async def test_all_models(self) -> Dict[str, Dict[str, Any]]:
        """测试所有配置的模型"""
        from config import ModelConfig

        # 获取所有模型配置
        all_configs = []
        try:
            config_path = os.path.join(os.path.dirname(__file__), "../../model_configs.json")
            with open(config_path, "r") as f:
                configs = json.load(f)
                all_configs = [config.get("config_name") for config in configs]
        except Exception as e:
            logger.error(f"读取模型配置失败: {e}")
            return {}

        # 并行测试所有模型
        tasks = [self.test_model_availability(config_name) for config_name in all_configs]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 组装结果
        final_results = {}
        for i, config_name in enumerate(all_configs):
            result = results[i]
            if isinstance(result, Exception):
                final_results[config_name] = {
                    "available": False,
                    "error": str(result),
                    "message": "测试过程中发生异常",
                }
            else:
                final_results[config_name] = result if isinstance(result, dict) else {"result": result}

        return final_results

    def get_test_result(self, config_name: str) -> Optional[Dict[str, Any]]:
        """获取缓存的测试结果"""
        result = self.test_results.get(config_name)
        if result is None:
            return None
        if isinstance(result, dict):
            return result
        else:
            return {"data": result}

    def clear_cache(self):
        """清除测试结果缓存"""
        self.test_results.clear()


# 全局测试器实例
_model_tester = None


def get_model_tester() -> ModelAvailabilityTester:
    """获取模型测试器实例"""
    global _model_tester
    if _model_tester is None:
        _model_tester = ModelAvailabilityTester()
    return _model_tester


async def ensure_model_available(config_name: str) -> bool:
    """确保模型可用，如果不可用则抛出异常"""
    tester = get_model_tester()
    result = await tester.test_model_availability(config_name)

    if not result.get("available", False):
        raise RuntimeError(f"模型 {config_name} 不可用: {result.get('message', '未知错误')}")

    return True
