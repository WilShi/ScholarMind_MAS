"""
ScholarMind Runtime Agent
符合 AgentScope Runtime 规范的 ScholarMind 智能体包装器
"""

import asyncio
import json
from typing import Any, Dict, List, Optional

from agentscope.message import Msg
from agentscope_runtime.engine.agents.agentscope_agent import AgentScopeAgent

# 延迟导入，避免循环导入
# from ..workflows.scholarmind_pipeline import create_pipeline
from ..utils.logger import setup_logger

# 创建运行时日志记录器
runtime_logger = setup_logger(
    "scholarmind.runtime_agent", level="INFO", log_file=None, console=True
)


class ScholarMindRuntimeAgent(AgentScopeAgent):
    """
    符合 AgentScope Runtime 规范的 ScholarMind 智能体

    这个类将 ScholarMind 工作流包装为符合 Runtime 规范的智能体，
    可以通过 LocalDeployManager 部署为标准的 FastAPI 服务。
    """

    def __init__(self, name: str = "ScholarMindRuntimeAgent", model=None, **kwargs):
        """
        初始化 ScholarMind Runtime 智能体

        Args:
            name: 智能体名称
            model: 模型实例（对于包装器智能体可以为None）
            **kwargs: 其他参数
        """
        # 对于包装器智能体，我们不需要实际的模型
        # 使用一个简单的占位符模型
        if model is None:
            from agentscope.model import OpenAIChatModel

            model = OpenAIChatModel(
                model_name="gpt-3.5-turbo", api_key="placeholder"  # 这个不会被实际使用
            )

        super().__init__(name=name, model=model, **kwargs)

        # 初始化 ScholarMind 工作流
        self.pipeline = None
        self._model_initialized = False
        runtime_logger.info("🚀 ScholarMind Runtime 智能体初始化完成")

    def build(self, as_context):
        """
        构建 AgentScope 智能体实例

        Args:
            as_context: AgentScope Runtime 上下文

        Returns:
            ScholarMindAgentInstance: 智能体实例
        """
        # 延迟导入避免循环导入
        if self.pipeline is None:
            from ..workflows.scholarmind_pipeline import create_pipeline

            self.pipeline = create_pipeline()

        return ScholarMindAgentInstance(
            name=self.name,
            pipeline=self.pipeline,
            as_context=as_context,
            model=self.model,  # 传递模型实例
        )


class ScholarMindAgentInstance:
    """
    ScholarMind 智能体实例

    这个类实现了 AgentScope Runtime 智能体的具体逻辑，
    处理论文分析请求并返回结构化响应。
    """

    def __init__(
        self,
        name: str,
        pipeline,
        as_context,
        model=None,
    ):
        """
        初始化智能体实例

        Args:
            name: 智能体名称
            pipeline: ScholarMind 工作流
            as_context: AgentScope Runtime 上下文
            model: 模型实例（可选）
        """
        self.name = name
        self.pipeline = pipeline
        self.as_context = as_context
        self.model = model
        runtime_logger.info(f"✅ {self.name} 实例创建完成")

    async def reply(self, message: Msg) -> Msg:
        """
        处理消息并返回回复

        Args:
            message: 输入消息

        Returns:
            Msg: 回复消息
        """
        try:
            # 解析输入消息
            request_data = self._parse_message(message)

            # 验证必需参数
            validation_result = self._validate_request(request_data)
            if not validation_result["valid"]:
                return self._create_error_response(validation_result["errors"])

            # 执行论文处理
            result = await self._process_paper(request_data)

            # 返回结果
            return self._create_response(result)

        except Exception as e:
            runtime_logger.error(f"❌ 处理请求时出错: {str(e)}")
            return self._create_error_response([f"处理请求时出错: {str(e)}"])

    def _parse_message(self, message: Msg) -> Dict[str, Any]:
        """
        解析输入消息

        Args:
            message: 输入消息

        Returns:
            Dict[str, Any]: 解析后的请求数据
        """
        content = message.content

        # 如果内容是字符串，尝试解析为 JSON
        if isinstance(content, str):
            try:
                request_data = json.loads(content)
            except json.JSONDecodeError:
                # 如果不是 JSON，当作简单的论文输入处理
                request_data = {
                    "paper_input": content,
                    "input_type": "text",
                    "user_background": "intermediate",
                    "save_report": True,
                    "output_format": "markdown",
                    "output_language": "zh",
                }
        else:
            # 如果内容已经是字典
            request_data = content

        return request_data

    def _validate_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证请求数据

        Args:
            request_data: 请求数据

        Returns:
            Dict[str, Any]: 验证结果
        """
        errors = []

        # 检查必需字段
        required_fields = ["paper_input", "input_type", "user_background"]
        for field in required_fields:
            if field not in request_data:
                errors.append(f"缺少必需参数: {field}")

        # 验证输入类型
        if "input_type" in request_data:
            valid_types = ["file", "url", "text"]
            if request_data["input_type"] not in valid_types:
                errors.append(
                    f"无效的输入类型: {request_data['input_type']}，支持的类型: {valid_types}"
                )

        # 验证用户背景
        if "user_background" in request_data:
            valid_backgrounds = ["beginner", "intermediate", "advanced"]
            if request_data["user_background"] not in valid_backgrounds:
                errors.append(
                    f"无效的用户背景: {request_data['user_background']}，支持的背景: {valid_backgrounds}"
                )

        # 使用工作流验证输入
        if (
            "paper_input" in request_data
            and "input_type" in request_data
            and "user_background" in request_data
        ):
            pipeline_validation = self.pipeline.validate_inputs(
                request_data["paper_input"],
                request_data["input_type"],
                request_data["user_background"],
            )
            if not pipeline_validation["valid"]:
                errors.extend(pipeline_validation["errors"])

        return {"valid": len(errors) == 0, "errors": errors}

    async def _process_paper(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理论文

        Args:
            request_data: 请求数据

        Returns:
            Dict[str, Any]: 处理结果
        """

        # 定义进度回调函数
        async def progress_callback(message: str):
            """进度回调函数"""
            runtime_logger.info(f"📊 {message}")

        # 执行论文处理
        result = await self.pipeline.process_paper(
            paper_input=request_data["paper_input"],
            input_type=request_data["input_type"],
            user_background=request_data["user_background"],
            save_report=request_data.get("save_report", True),
            output_format=request_data.get("output_format", "markdown"),
            output_language=request_data.get("output_language", "zh"),
            progress_callback=progress_callback,
        )

        return result

    def _create_response(self, result: Dict[str, Any]) -> Msg:
        """
        创建成功响应消息

        Args:
            result: 处理结果

        Returns:
            Msg: 响应消息
        """
        response_data = {"status": "success", "data": result, "message": "论文处理完成"}

        return Msg(name=self.name, content=response_data, role="assistant")

    def _create_error_response(self, errors: List[str]) -> Msg:
        """
        创建错误响应消息

        Args:
            errors: 错误列表

        Returns:
            Msg: 错误响应消息
        """
        response_data = {
            "status": "error",
            "errors": errors,
            "message": f"请求处理失败: {'; '.join(errors)}",
        }

        return Msg(name=self.name, content=response_data, role="assistant")

    def get_pipeline_status(self) -> Dict[str, Any]:
        """
        获取工作流状态

        Returns:
            Dict[str, Any]: 工作流状态
        """
        return self.pipeline.get_pipeline_status()
