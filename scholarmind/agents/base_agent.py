"""
ScholarMind Base Agent
统一的智能体基类，确保所有智能体遵循相同的初始化和错误处理模式
"""

import asyncio
import json
import time
from typing import Any, Dict, Optional

from agentscope.agent import AgentBase, ReActAgent
from agentscope.formatter import OpenAIChatFormatter
from agentscope.message import Msg
from agentscope.model import OpenAIChatModel

from config import get_model_config

from ..utils.logger import agent_logger


class ScholarMindAgentBase(AgentBase):
    """ScholarMind智能体基类"""

    def __init__(
        self, name: str, sys_prompt: str, model_config_name: Optional[str] = None, **kwargs
    ):
        # 调用父类初始化（无参数）
        super().__init__()

        # 手动设置名称和其他属性
        self.name = name
        self.sys_prompt = sys_prompt
        self.model_config_name = model_config_name
        self.model = None  # 延迟初始化

    async def _ensure_model_initialized(self):
        """确保模型已初始化（包含可用性测试）"""
        if self.model is None:
            try:
                # 获取模型配置
                model_config = get_model_config(self.model_config_name)

                # 初始化模型
                self.model = OpenAIChatModel(
                    model_name=model_config.get("model_name"),
                    api_key=model_config.get("api_key"),
                    client_args=model_config.get("client_args", {}),
                    generate_kwargs={
                        "temperature": model_config.get("temperature", 0.1),
                        "max_tokens": model_config.get("max_tokens", 4000),
                        "top_p": model_config.get("top_p", 0.9),
                    },
                )

                agent_logger.info(
                    f"智能体 {self.name} 模型初始化成功: {model_config.get('model_name')}"
                )

            except Exception as e:
                agent_logger.error(f"智能体 {self.name} 模型初始化失败: {e}")
                raise

    async def _safe_model_call(
        self, messages: list, fallback_response: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """安全的模型调用，包含错误处理和重试机制"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                await self._ensure_model_initialized()
                if self.model is None:
                    raise RuntimeError("Model initialization failed")
                response = await self.model(messages)
                return await self._parse_model_response(response)
            except Exception as e:
                agent_logger.warning(
                    f"模型调用失败 (尝试 {attempt + 1}/{max_retries}) {self.name}: {e}"
                )
                if attempt == max_retries - 1:
                    agent_logger.error(f"模型调用最终失败 {self.name}: {e}")
                    return fallback_response or {"error": str(e), "success": False}
                await asyncio.sleep(2**attempt)  # 指数退避
        return fallback_response or {"error": "All retries failed", "success": False}

    async def _parse_model_response(self, response) -> Dict[str, Any]:
        """统一解析模型响应"""
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

            # 尝试解析JSON
            try:
                parsed = json.loads(response_text)
                if isinstance(parsed, dict):
                    return parsed
                else:
                    return {"content": parsed, "success": True}
            except json.JSONDecodeError:
                return {"content": response_text, "success": True}
        except Exception as e:
            agent_logger.error(f"响应解析失败 {self.name}: {e}")
            return {"error": str(e), "success": False}

    async def reply(self, msg: Msg) -> Msg:
        """标准回复方法，子类需要实现具体的处理逻辑"""
        start_time = time.time()
        try:
            # 解析输入消息
            input_data = self._parse_input_message(msg)

            # 执行具体处理逻辑（子类实现）
            result = await self._process_logic(input_data)

            # 构建响应
            response_data = {
                "status": "success" if result.get("success", True) else "error",
                "data": result,
                "processing_time": time.time() - start_time,
                "agent_name": self.name,
                "model_name": self.model.model_name if self.model else "unknown",
            }

            return Msg(name=self.name, content=response_data, role="assistant")

        except Exception as e:
            agent_logger.error(f"处理失败 {self.name}: {e}")
            error_response = {
                "status": "error",
                "error": str(e),
                "processing_time": time.time() - start_time,
                "agent_name": self.name,
                "model_name": self.model.model_name if self.model else "unknown",
            }
            return Msg(name=self.name, content=error_response, role="assistant")

    def _parse_input_message(self, msg: Msg) -> Dict[str, Any]:
        """统一解析输入消息"""
        if isinstance(msg.content, dict):
            return msg.content
        elif isinstance(msg.content, str):
            try:
                parsed = json.loads(msg.content)
                if isinstance(parsed, dict):
                    return parsed
                else:
                    return {"value": parsed}
            except json.JSONDecodeError:
                return {"text": msg.content}
        else:
            return {"raw_content": str(msg.content)}

    async def _process_logic(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """子类需要实现的具体处理逻辑"""
        raise NotImplementedError("子类必须实现_process_logic方法")


class ScholarMindReActAgent(ReActAgent, ScholarMindAgentBase):
    """ScholarMind ReAct智能体基类"""

    def __init__(
        self,
        name: str,
        sys_prompt: str,
        toolkit=None,
        model_config_name: Optional[str] = None,
        **kwargs,
    ):
        # 获取模型配置
        from config import get_model_config

        model_config = get_model_config(model_config_name)

        # 初始化模型
        model = OpenAIChatModel(
            model_name=model_config.get("model_name"),
            api_key=model_config.get("api_key"),
            client_args=model_config.get("client_args", {}),
            generate_kwargs={
                "temperature": model_config.get("temperature", 0.1),
                "max_tokens": model_config.get("max_tokens", 4000),
                "top_p": model_config.get("top_p", 0.9),
            },
        )

        # 初始化ReActAgent
        ReActAgent.__init__(
            self,
            name=name,
            sys_prompt=sys_prompt,
            model=model,
            formatter=OpenAIChatFormatter(),
            toolkit=toolkit,
            **kwargs,
        )

        # 设置基类属性
        self.name = name
        self.sys_prompt = sys_prompt
        self.model_config_name = model_config_name
        self.model = model
