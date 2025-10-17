"""
ScholarMind Pipeline
智读ScholarMind工作流
"""

import asyncio
import time
from typing import Any, Dict, List, Optional

from agentscope import pipeline
from agentscope.message import Msg

from ..agents.resource_retrieval_agent import ResourceRetrievalAgent
from ..agents.methodology_agent import MethodologyAgent
from ..agents.experiment_evaluator_agent import ExperimentEvaluatorAgent
from ..agents.insight_generation_agent import InsightGenerationAgent
from ..agents.synthesizer_agent import SynthesizerAgent
from ..utils.logger import pipeline_logger


class ScholarMindPipeline:
    """ScholarMind工作流"""

    def __init__(self):
        """初始化工作流"""
        pipeline_logger.info("初始化ScholarMind工作流...")

        # 初始化智能体
        self.resource_agent = ResourceRetrievalAgent()
        self.methodology_agent = MethodologyAgent()
        self.experiment_agent = ExperimentEvaluatorAgent()
        self.insight_agent = InsightGenerationAgent()
        self.synthesizer_agent = SynthesizerAgent()

        # 创建完整DAG工作流（5个智能体）
        # Stage 1: Resource Retrieval (sequential)
        # Stage 2: Methodology + Experiment (parallel)
        # Stage 3: Insight Generation (sequential, uses results from Stage 2)
        # Stage 4: Synthesizer (sequential, integrates all results)
        self.pipeline = pipeline.SequentialPipeline(
            agents=[
                self.resource_agent,
                # Parallel and insight agents will be handled in process_paper method
                self.synthesizer_agent
            ]
        )
        self.pipeline.name = "scholarmind_phase3_pipeline"

        pipeline_logger.info("工作流初始化完成（5个智能体完整DAG）")

    async def process_paper(
        self,
        paper_input: str,
        input_type: str = "file",
        user_background: str = "intermediate",
        save_report: bool = True,
        output_format: str = "markdown",
        output_language: str = "zh",
        progress_callback: Optional[callable] = None,
    ) -> Dict[str, Any]:
        """
        处理论文的完整流程（5个智能体完整DAG）

        Args:
            paper_input: 论文输入（文件路径、URL或文本）
            input_type: 输入类型（file、url、text）
            user_background: 用户背景（beginner、intermediate、advanced）
            save_report: 是否保存报告
            output_format: 输出格式（markdown、json）
            output_language: 输出语言（zh、en）
            progress_callback: 进度回调函数，用于更新进度信息

        Returns:
            Dict[str, Any]: 处理结果
        """
        start_time = time.time()

        try:
            # 发送进度：开始处理
            if progress_callback:
                await progress_callback(f"📥 开始处理论文（输入类型: {input_type}）...")
            else:
                pipeline_logger.info(f"开始处理论文，输入类型: {input_type}")

            # 步骤1：资源检索
            if progress_callback:
                await progress_callback("📖 步骤 1/4：正在检索和解析论文...")
            else:
                pipeline_logger.info("步骤1：资源检索...")
            resource_result = await self._process_resource_retrieval(paper_input, input_type)

            if not resource_result["success"]:
                if progress_callback:
                    await progress_callback(f"❌ 资源检索失败: {resource_result['error']}")
                return {
                    "success": False,
                    "error": f"资源检索失败: {resource_result['error']}",
                    "stage": "resource_retrieval",
                }

            # 步骤2：并行处理（方法论分析 + 实验评估）
            if progress_callback:
                await progress_callback("🔬 步骤 2/4：并行分析论文方法论和实验评估...")
            else:
                pipeline_logger.info("步骤2：并行分析（方法论 + 实验评估）...")
            parallel_start = time.time()

            methodology_result, experiment_result = await self._process_parallel_analysis(
                resource_result["data"]["paper_content"], output_language
            )

            parallel_time = time.time() - parallel_start
            if progress_callback:
                await progress_callback(f"✅ 并行分析完成，耗时: {parallel_time:.1f}秒")
            else:
                pipeline_logger.info(f"并行分析完成，耗时: {parallel_time:.2f}秒")

            # 检查并行处理结果
            if not methodology_result["success"]:
                if progress_callback:
                    await progress_callback(f"⚠️  方法论分析失败: {methodology_result.get('error', '未知错误')}")
                else:
                    pipeline_logger.warning(f"方法论分析失败: {methodology_result.get('error', '未知错误')}")

            if not experiment_result["success"]:
                if progress_callback:
                    await progress_callback(f"⚠️  实验评估失败: {experiment_result.get('error', '未知错误')}")
                else:
                    pipeline_logger.warning(f"实验评估失败: {experiment_result.get('error', '未知错误')}")

            # 步骤3：洞察生成（基于前面的分析结果）
            if progress_callback:
                await progress_callback("💡 步骤 3/4：生成批判性洞察和研究建议...")
            else:
                pipeline_logger.info("步骤3：洞察生成...")
            insight_result = await self._process_insight_generation(
                resource_result["data"]["paper_content"],
                methodology_result.get("data") if methodology_result["success"] else None,
                experiment_result.get("data") if experiment_result["success"] else None,
                output_language
            )

            if not insight_result["success"]:
                if progress_callback:
                    await progress_callback(f"⚠️  洞察生成失败: {insight_result.get('error', '未知错误')}")
                else:
                    pipeline_logger.warning(f"洞察生成失败: {insight_result.get('error', '未知错误')}")

            # 步骤4：综合报告生成
            if progress_callback:
                await progress_callback("📝 步骤 4/4：综合生成个性化解读报告...")
            else:
                pipeline_logger.info("步骤4：综合报告生成...")
            synthesizer_result = await self._process_synthesizer(
                resource_result["data"],
                methodology_result.get("data") if methodology_result["success"] else None,
                experiment_result.get("data") if experiment_result["success"] else None,
                insight_result.get("data") if insight_result["success"] else None,
                user_background,
                output_language
            )

            if not synthesizer_result["success"]:
                if progress_callback:
                    await progress_callback(f"❌ 报告生成失败: {synthesizer_result['error']}")
                return {
                    "success": False,
                    "error": f"报告生成失败: {synthesizer_result['error']}",
                    "stage": "synthesizer",
                }

            # 步骤5：保存报告（如果需要）
            report_path = None
            if save_report:
                if progress_callback:
                    await progress_callback("💾 正在保存报告...")
                report_path = self._save_report(synthesizer_result["data"], output_format, output_language)

            # 计算总处理时间
            total_time = time.time() - start_time

            # 发送完成消息
            if progress_callback:
                await progress_callback(f"✨ 论文分析完成！总耗时: {total_time:.1f}秒")

            # 构建最终结果
            result = {
                "success": True,
                "message": "论文处理完成",
                "processing_time": total_time,
                "stages": {
                    "resource_retrieval": {
                        "success": True,
                        "processing_time": resource_result["processing_time"],
                        "paper_title": resource_result["data"]["paper_content"]["metadata"]["title"],
                    },
                    "methodology_analysis": {
                        "success": methodology_result["success"],
                        "processing_time": methodology_result.get("processing_time", 0),
                    },
                    "experiment_evaluation": {
                        "success": experiment_result["success"],
                        "processing_time": experiment_result.get("processing_time", 0),
                    },
                    "parallel_processing_time": parallel_time,
                    "insight_generation": {
                        "success": insight_result["success"],
                        "processing_time": insight_result.get("processing_time", 0),
                    },
                    "synthesizer": {
                        "success": True,
                        "processing_time": synthesizer_result["processing_time"],
                        "report_title": synthesizer_result["data"]["title"],
                    },
                },
                "outputs": {
                    "paper_content": resource_result["data"]["paper_content"],
                    "methodology_analysis": methodology_result.get("data") if methodology_result["success"] else None,
                    "experiment_evaluation": experiment_result.get("data") if experiment_result["success"] else None,
                    "insight_analysis": insight_result.get("data") if insight_result["success"] else None,
                    "report": synthesizer_result["data"],
                    "report_path": report_path,
                },
                "metadata": {
                    "user_background": user_background,
                    "input_type": input_type,
                    "output_format": output_format,
                    "output_language": output_language,
                },
            }

            pipeline_logger.info(f"论文处理完成，总耗时: {total_time:.2f}秒")
            return result

        except Exception as e:
            total_time = time.time() - start_time
            if progress_callback:
                await progress_callback(f"❌ 处理失败: {str(e)}")
            else:
                pipeline_logger.error(f"论文处理失败: {str(e)}")

            return {"success": False, "error": str(e), "processing_time": total_time, "stage": "unknown"}

    async def _process_resource_retrieval(self, paper_input: str, input_type: str) -> Dict[str, Any]:
        """处理资源检索阶段"""
        try:
            # 创建输入消息 - 直接传递字典
            input_data = {"paper_input": paper_input, "input_type": input_type}

            message = Msg(name="user", content=input_data, role="user")

            # 执行资源检索
            response = await self.resource_agent.reply(message)
            response_data = response.content  # 直接访问字典，无需json.loads

            if response_data["status"] == "success":
                return {
                    "success": True,
                    "data": response_data["data"],
                    "processing_time": response_data["data"]["processing_info"]["processing_time"],
                }
            else:
                return {"success": False, "error": response_data.get("error", "未知错误"), "processing_time": 0}

        except Exception as e:
            return {"success": False, "error": str(e), "processing_time": 0}

    async def _process_parallel_analysis(
        self, paper_content: Dict[str, Any], output_language: str
    ) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """
        并行处理方法论分析和实验评估

        Args:
            paper_content: 论文内容
            output_language: 输出语言

        Returns:
            tuple[Dict[str, Any], Dict[str, Any]]: (方法论分析结果, 实验评估结果)
        """
        # 创建两个并行任务
        methodology_task = self._process_methodology(paper_content, output_language)
        experiment_task = self._process_experiment_evaluation(paper_content, output_language)

        # 使用asyncio.gather并行执行
        methodology_result, experiment_result = await asyncio.gather(
            methodology_task,
            experiment_task,
            return_exceptions=True
        )

        # 处理可能的异常
        if isinstance(methodology_result, Exception):
            methodology_result = {
                "success": False,
                "error": str(methodology_result),
                "processing_time": 0
            }

        if isinstance(experiment_result, Exception):
            experiment_result = {
                "success": False,
                "error": str(experiment_result),
                "processing_time": 0
            }

        return methodology_result, experiment_result

    async def _process_methodology(self, paper_content: Dict[str, Any], output_language: str) -> Dict[str, Any]:
        """处理方法论分析阶段"""
        try:
            # 创建输入消息 - 直接传递字典
            input_data = {
                "paper_content": paper_content,
                "output_language": output_language,
            }

            message = Msg(name="user", content=input_data, role="user")

            # 执行方法论分析
            response = await self.methodology_agent.reply(message)
            response_data = response.content  # 直接访问字典

            if response_data["status"] == "success":
                return {
                    "success": True,
                    "data": response_data["data"],
                    "processing_time": response_data["data"]["processing_time"],
                }
            else:
                return {"success": False, "error": response_data.get("error", "未知错误"), "processing_time": 0}

        except Exception as e:
            return {"success": False, "error": str(e), "processing_time": 0}

    async def _process_experiment_evaluation(self, paper_content: Dict[str, Any], output_language: str) -> Dict[str, Any]:
        """处理实验评估阶段"""
        try:
            # 创建输入消息 - 直接传递字典
            input_data = {
                "paper_content": paper_content,
                "output_language": output_language,
            }

            message = Msg(name="user", content=input_data, role="user")

            # 执行实验评估
            response = await self.experiment_agent.reply(message)
            response_data = response.content  # 直接访问字典

            if response_data["status"] == "success":
                return {
                    "success": True,
                    "data": response_data["data"],
                    "processing_time": response_data["data"]["processing_time"],
                }
            else:
                return {"success": False, "error": response_data.get("error", "未知错误"), "processing_time": 0}

        except Exception as e:
            return {"success": False, "error": str(e), "processing_time": 0}

    async def _process_insight_generation(
        self,
        paper_content: Dict[str, Any],
        methodology_data: Optional[Dict[str, Any]],
        experiment_data: Optional[Dict[str, Any]],
        output_language: str
    ) -> Dict[str, Any]:
        """处理洞察生成阶段"""
        try:
            # 创建输入消息 - 直接传递字典
            input_data = {
                "paper_content": paper_content,
                "methodology_analysis": methodology_data,
                "experiment_evaluation": experiment_data,
                "output_language": output_language,
            }

            message = Msg(name="user", content=input_data, role="user")

            # 执行洞察生成
            response = await self.insight_agent.reply(message)
            response_data = response.content  # 直接访问字典

            if response_data["status"] == "success":
                return {
                    "success": True,
                    "data": response_data["data"],
                    "processing_time": response_data["data"]["processing_time"],
                }
            else:
                return {"success": False, "error": response_data.get("error", "未知错误"), "processing_time": 0}

        except Exception as e:
            return {"success": False, "error": str(e), "processing_time": 0}

    async def _process_synthesizer(
        self,
        paper_content_data: Dict[str, Any],
        methodology_data: Optional[Dict[str, Any]],
        experiment_data: Optional[Dict[str, Any]],
        insight_data: Optional[Dict[str, Any]],
        user_background: str,
        output_language: str
    ) -> Dict[str, Any]:
        """处理综合报告生成阶段"""
        try:
            # 创建输入消息（包含所有分析结果）- 直接传递字典
            input_data = {
                "paper_content": paper_content_data["paper_content"],
                "user_background": user_background,
                "output_language": output_language,
                "external_info": paper_content_data.get("external_info", {}),
                "methodology_analysis": methodology_data,
                "experiment_evaluation": experiment_data,
                "insight_analysis": insight_data,
            }

            message = Msg(name="user", content=input_data, role="user")

            # 执行报告生成
            response = await self.synthesizer_agent.reply(message)
            response_data = response.content  # 直接访问字典

            if response_data["status"] == "success":
                return {
                    "success": True,
                    "data": response_data["data"],
                    "processing_time": response_data["data"]["processing_time"],
                }
            else:
                return {"success": False, "error": response_data.get("error", "未知错误"), "processing_time": 0}

        except Exception as e:
            return {"success": False, "error": str(e), "processing_time": 0}

    def _save_report(self, report_data: Dict[str, Any], output_format: str, output_language: str = "zh") -> Optional[str]:
        """保存报告到文件"""
        try:
            import os
            from datetime import datetime

            # 多语言章节标题
            section_titles = {
                "zh": {
                    "processing_time": "处理时间",
                    "user_background": "用户背景适配",
                    "summary": "摘要",
                    "contributions": "主要贡献",
                    "methodology": "方法论概述",
                    "experiments": "实验概述",
                    "insights": "关键洞察"
                },
                "en": {
                    "processing_time": "Processing Time",
                    "user_background": "User Background",
                    "summary": "Summary",
                    "contributions": "Key Contributions",
                    "methodology": "Methodology Overview",
                    "experiments": "Experiment Overview",
                    "insights": "Key Insights"
                }
            }
            titles = section_titles.get(output_language, section_titles["zh"])

            # 创建输出目录
            os.makedirs("outputs", exist_ok=True)

            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_title = "".join(c for c in report_data["title"][:50] if c.isalnum() or c in (" ", "-", "_")).rstrip()
            filename = f"{safe_title}_{timestamp}"

            if output_format == "json":
                filepath = f"outputs/{filename}.json"
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(report_data, f, ensure_ascii=False, indent=2)
            else:
                # 默认保存为markdown
                filepath = f"outputs/{filename}.md"
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(f"# {report_data['title']}\n\n")
                    f.write(f"**{titles['processing_time']}**: {report_data['processing_time']:.2f}s\n\n")
                    f.write(f"**{titles['user_background']}**: {report_data['user_background_adaptation']}\n\n")
                    f.write(f"## {titles['summary']}\n\n")
                    f.write(f"{report_data['summary']}\n\n")
                    f.write(f"## {titles['contributions']}\n\n")
                    for contribution in report_data["key_contributions"]:
                        f.write(f"- {contribution}\n")
                    f.write(f"\n## {titles['methodology']}\n\n")
                    f.write(f"{report_data['methodology_summary']}\n\n")
                    f.write(f"## {titles['experiments']}\n\n")
                    f.write(f"{report_data['experiment_summary']}\n\n")
                    f.write(f"## {titles['insights']}\n\n")
                    for insight in report_data["insights"]:
                        f.write(f"- {insight}\n")

            pipeline_logger.info(f"报告已保存到: {filepath}")
            return filepath

        except Exception as e:
            pipeline_logger.error(f"保存报告失败: {str(e)}")
            return None

    def get_pipeline_status(self) -> Dict[str, Any]:
        """获取工作流状态"""
        return {
            "name": self.pipeline.name,
            "agents": [
                {"name": self.resource_agent.name, "type": "ResourceRetrievalAgent"},
                {"name": self.methodology_agent.name, "type": "MethodologyAgent"},
                {"name": self.experiment_agent.name, "type": "ExperimentEvaluatorAgent"},
                {"name": self.insight_agent.name, "type": "InsightGenerationAgent"},
                {"name": self.synthesizer_agent.name, "type": "SynthesizerAgent"},
            ],
            "pipeline_type": "Complete DAG (5 agents)",
            "parallel_agents": ["MethodologyAgent", "ExperimentEvaluatorAgent"],
            "workflow_stages": [
                "1. Resource Retrieval",
                "2. Parallel Analysis (Methodology + Experiment)",
                "3. Insight Generation",
                "4. Report Synthesis"
            ]
        }

    def validate_inputs(self, paper_input: str, input_type: str, user_background: str) -> Dict[str, Any]:
        """验证输入参数"""
        errors = []

        # 验证论文输入
        if not paper_input:
            errors.append("论文输入不能为空")
        elif input_type == "file":
            import os

            if not os.path.exists(paper_input):
                errors.append(f"文件不存在: {paper_input}")
        elif input_type == "url":
            import re

            url_pattern = re.compile(
                r"^https?://"  # http:// or https://
                r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain...
                r"localhost|"  # localhost...
                r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
                r"(?::\d+)?"  # optional port
                r"(?:/?|[/?]\S+)$",
                re.IGNORECASE,
            )
            if not url_pattern.match(paper_input):
                errors.append("无效的URL格式")

        # 验证输入类型
        if input_type not in ["file", "url", "text"]:
            errors.append("输入类型必须是 file、url 或 text")

        # 验证用户背景
        if not self.synthesizer_agent.validate_user_background(user_background):
            errors.append("用户背景必须是 beginner、intermediate 或 advanced")

        return {"valid": len(errors) == 0, "errors": errors}

    def get_supported_formats(self) -> Dict[str, List[str]]:
        """获取支持的格式"""
        return {
            "input_types": ["file", "url", "text"],
            "file_formats": [".pdf", ".docx", ".txt"],
            "user_backgrounds": ["beginner", "intermediate", "advanced"],
            "output_formats": ["markdown", "json"],
        }


def create_pipeline(config: Optional[Dict[str, Any]] = None) -> ScholarMindPipeline:
    """
    创建ScholarMind工作流实例

    Args:
        config: 可选配置参数

    Returns:
        ScholarMindPipeline: 工作流实例
    """
    # 目前忽略配置，直接创建默认实例
    # 未来可以根据配置自定义工作流
    return ScholarMindPipeline()
