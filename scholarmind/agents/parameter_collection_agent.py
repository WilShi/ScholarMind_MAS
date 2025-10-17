"""
Parameter Collection Agent for ScholarMind
智读ScholarMind参数收集智能体
"""

import json
import os
from typing import Dict, Any, Optional

from agentscope.agent import ReActAgent
from agentscope.message import Msg
from agentscope.model import OpenAIChatModel
from agentscope.formatter import OpenAIChatFormatter

from config import get_model_config

# 暂时注释掉这行，避免导入错误
# from ..models.structured_outputs import PaperInput, ProcessingParameters


class ParameterCollectionAgent(ReActAgent):
    """参数收集智能体，用于在没有提供命令行参数时与用户交互收集必要信息"""

    def __init__(self, **kwargs: Any) -> None:
        """初始化参数收集智能体"""
        # 系统提示词，指导智能体如何收集参数
        sys_prompt = """
        你是一个学术论文解读系统的参数收集助手。你的任务是与用户对话，收集运行系统所需的参数。
        
        需要收集的参数包括：
        1. 论文输入 (paper_input)：可以是文件路径、URL或文本内容
        2. 输入类型 (input_type)：file/url/text，默认为file
        3. 用户背景 (user_background)：beginner/intermediate/advanced，默认为intermediate
        4. 输出格式 (output_format)：markdown/json，默认为markdown
        5. 输出语言 (output_language)：zh/en，默认为zh
        
        请遵循以下步骤：
        1. 首先问候用户并简要说明你的作用
        2. 逐项询问用户需要的参数，提供合理的默认值
        3. 验证用户输入的有效性
        4. 最后总结收集到的参数并确认
        
        重要规则：
        - 如果用户没有明确指定某项参数，使用上述默认值
        - 对于论文输入，需要验证文件是否存在（如果是文件路径）或URL是否有效
        - 确保所有参数都符合系统要求的选项范围
        - 保持友好、专业的对话风格
        """

        # 获取模型配置
        model_config = get_model_config()
        
        # 初始化模型
        model = OpenAIChatModel(
            model_name=model_config.get("model_name"),
            api_key=model_config.get("api_key"),
            client_args=model_config.get("client_args", {}),
            generate_kwargs={
                "temperature": model_config.get("temperature", 0.1),
                "max_tokens": model_config.get("max_tokens", 4000),
                "top_p": model_config.get("top_p", 0.9)
            }
        )

        super().__init__(
            name="ParameterCollectionAgent",
            sys_prompt=sys_prompt,
            model=model,
            formatter=OpenAIChatFormatter(),
            **kwargs
        )

    async def collect_parameters(self) -> Dict[str, Any]:
        """
        与用户交互收集参数

        Returns:
            Dict[str, Any]: 收集到的参数字典
        """
        # 问候用户并说明任务
        greeting_msg = Msg(
            name="system",
            content="您好！我是ScholarMind参数收集助手。我将帮助您设置论文解读系统的运行参数。",
            role="system"
        )
        await self.memory.add(greeting_msg)
        
        # 收集参数
        parameters = self._get_default_parameters()
        
        # 询问论文输入
        paper_input_msg = Msg(
            name="user",
            content="请提供论文输入（文件路径、URL或文本内容）：",
            role="user"
        )
        paper_input_response = await self.reply(paper_input_msg)
        if paper_input_response.content.strip():
            parameters["paper_input"] = paper_input_response.content.strip()
        
        # 询问输入类型
        input_type_msg = Msg(
            name="user",
            content=f"请指定输入类型（file/url/text）[默认: {parameters['input_type']}]: ",
            role="user"
        )
        input_type_response = await self.reply(input_type_msg)
        if input_type_response.content.strip() in ["file", "url", "text"]:
            parameters["input_type"] = input_type_response.content.strip()
        
        # 询问用户背景
        background_msg = Msg(
            name="user",
            content=f"请指定您的背景（beginner/intermediate/advanced）[默认: {parameters['user_background']}]: ",
            role="user"
        )
        background_response = await self.reply(background_msg)
        if background_response.content.strip() in ["beginner", "intermediate", "advanced"]:
            parameters["user_background"] = background_response.content.strip()
        
        # 询问输出格式
        format_msg = Msg(
            name="user",
            content=f"请指定报告输出格式（markdown/json）[默认: {parameters['output_format']}]: ",
            role="user"
        )
        format_response = await self.reply(format_msg)
        if format_response.content.strip() in ["markdown", "json"]:
            parameters["output_format"] = format_response.content.strip()
        
        # 询问输出语言
        language_msg = Msg(
            name="user",
            content=f"请指定输出语言（zh/en）[默认: {parameters['output_language']}]: ",
            role="user"
        )
        language_response = await self.reply(language_msg)
        if language_response.content.strip() in ["zh", "en"]:
            parameters["output_language"] = language_response.content.strip()
        
        # 验证收集到的参数
        if not self.validate_parameters(parameters):
            # 如果验证失败，返回默认参数
            return self._get_default_parameters()
        
        return parameters

    def _get_default_parameters(self) -> Dict[str, Any]:
        """获取默认参数"""
        return {
            "paper_input": "",
            "input_type": "file",
            "user_background": "intermediate",
            "output_format": "markdown",
            "output_language": "zh",
            "save_report": True
        }

    def validate_paper_input(self, paper_input: str, input_type: str) -> bool:
        """
        验证论文输入
        
        Args:
            paper_input: 论文输入
            input_type: 输入类型
            
        Returns:
            bool: 验证是否通过
        """
        if not paper_input:
            return False
            
        if input_type == "file":
            return os.path.exists(paper_input)
        elif input_type == "url":
            # 简单的URL格式验证
            return paper_input.startswith(("http://", "https://"))
        elif input_type == "text":
            return len(paper_input.strip()) > 0
        return False

    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """
        验证参数有效性
        
        Args:
            parameters: 参数字典
            
        Returns:
            bool: 验证是否通过
        """
        # 验证输入类型
        if parameters["input_type"] not in ["file", "url", "text"]:
            return False
            
        # 验证用户背景
        if parameters["user_background"] not in ["beginner", "intermediate", "advanced"]:
            return False
            
        # 验证输出格式
        if parameters["output_format"] not in ["markdown", "json"]:
            return False
            
        # 验证输出语言
        if parameters["output_language"] not in ["zh", "en"]:
            return False
            
        # 验证论文输入
        if not self.validate_paper_input(parameters["paper_input"], parameters["input_type"]):
            return False
            
        return True