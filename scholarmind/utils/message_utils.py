"""
ScholarMind Message Utils
统一消息格式和传递规范
"""

import json
import time
from typing import Any, Dict, List, Union

from agentscope.message import Msg

from ..utils.logger import setup_logger

logger = setup_logger("scholarmind.message_utils", level="INFO", log_file=None, console=True)


class MessageUtils:
    """消息工具类"""

    @staticmethod
    def create_input_message(sender: str, content: Dict[str, Any], role: str = "user") -> Msg:
        """创建标准输入消息"""
        return Msg(name=sender, content=content, role=role)

    @staticmethod
    def create_user_message(content: Union[str, Dict[str, Any]]) -> Msg:
        """创建用户消息"""
        return Msg(name="user", content=content, role="user")

    @staticmethod
    def create_response_message(
        agent_name: str, data: Dict[str, Any], status: str = "success", processing_time: float = 0.0
    ) -> Msg:
        """创建标准响应消息"""
        response_content = {
            "status": status,
            "data": data,
            "agent_name": agent_name,
            "processing_time": processing_time,
            "timestamp": time.time(),
        }

        return Msg(name=agent_name, content=response_content, role="assistant")

    @staticmethod
    def create_error_message(
        agent_name: str,
        error: str,
        error_type: str = "general_error",
        context: Dict[str, Any] = None,
    ) -> Msg:
        """创建错误消息"""
        error_content = {
            "status": "error",
            "error": error,
            "error_type": error_type,
            "agent_name": agent_name,
            "context": context or {},
            "timestamp": time.time(),
        }

        return Msg(name=agent_name, content=error_content, role="assistant")

    @staticmethod
    def parse_message_content(msg: Msg) -> Dict[str, Any]:
        """统一解析消息内容"""
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

    @staticmethod
    def parse_agent_response(response: Msg) -> Dict[str, Any]:
        """解析智能体响应消息"""
        try:
            content = MessageUtils.parse_message_content(response)

            # 如果已经是标准格式，直接返回
            # 检查多种可能的成功标识符
            if isinstance(content, dict) and any(
                key in content for key in ["success", "status", "data"]
            ):
                # 统一格式：确保有success字段
                if "success" not in content:
                    if "status" in content:
                        content["success"] = content["status"] == "success"
                    else:
                        content["success"] = True

                # 确保有data字段
                if "data" not in content and "paper_content" in content:
                    # 如果直接包含paper_content，重构为嵌套结构
                    content["data"] = {
                        "paper_content": content.get("paper_content"),
                        "external_info": content.get("external_info"),
                        "processing_info": content.get("processing_info"),
                    }

                return content

            # 否则包装为标准格式
            return {
                "success": True,
                "data": content,
                "agent_name": response.name,
                "timestamp": time.time(),
            }

        except Exception as e:
            logger.error(f"解析智能体响应失败: {e}")
            return {
                "success": False,
                "error": f"响应解析失败: {str(e)}",
                "agent_name": response.name,
            }

    @staticmethod
    def validate_message_structure(msg: Msg, required_fields: List[str] = None) -> bool:
        """验证消息结构"""
        content = MessageUtils.parse_message_content(msg)

        if not isinstance(content, dict):
            return False

        if required_fields:
            return all(field in content for field in required_fields)

        return True

    @staticmethod
    def extract_paper_input(msg: Msg) -> Dict[str, Any]:
        """从消息中提取论文输入信息"""
        content = MessageUtils.parse_message_content(msg)

        return {
            "paper_input": content.get("paper_input"),
            "input_type": content.get("input_type", "file"),
            "user_background": content.get("user_background", "intermediate"),
            "output_language": content.get("output_language", "zh"),
            "output_format": content.get("output_format", "markdown"),
        }

    @staticmethod
    def create_progress_message(
        agent_name: str, stage: str, message: str, progress: float = None
    ) -> Msg:
        """创建进度消息"""
        progress_content = {
            "status": "progress",
            "stage": stage,
            "message": message,
            "agent_name": agent_name,
            "progress": progress,
            "timestamp": time.time(),
        }

        return Msg(name=agent_name, content=progress_content, role="system")

    @staticmethod
    def create_success_message(agent_name: str, message: str, data: Dict[str, Any] = None) -> Msg:
        """创建成功消息"""
        success_content = {
            "status": "success",
            "message": message,
            "agent_name": agent_name,
            "data": data or {},
            "timestamp": time.time(),
        }

        return Msg(name=agent_name, content=success_content, role="assistant")

    @staticmethod
    def create_pipeline_status_message(
        pipeline_name: str, stage: str, agent_status: Dict[str, Any]
    ) -> Msg:
        """创建Pipeline状态消息"""
        status_content = {
            "status": "pipeline_status",
            "pipeline_name": pipeline_name,
            "stage": stage,
            "agent_status": agent_status,
            "timestamp": time.time(),
        }

        return Msg(name="pipeline_monitor", content=status_content, role="system")
