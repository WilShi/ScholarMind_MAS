"""
ScholarMind Enhanced Pipeline
智读ScholarMind增强工作流 - 统一架构和错误处理
"""

import asyncio
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from agentscope import pipeline
from agentscope.message import Msg

from ..agents.experiment_evaluator_agent import ExperimentEvaluatorAgent
from ..agents.insight_generation_agent import InsightGenerationAgent
from ..agents.methodology_agent import MethodologyAgent
from ..agents.resource_retrieval_agent import ResourceRetrievalAgent
from ..agents.synthesizer_agent import SynthesizerAgent
from ..utils.error_handler import safe_execute, with_error_handling
from ..utils.logger import pipeline_logger
from ..utils.message_utils import MessageUtils


class ScholarMindEnhancedPipeline:
    """ScholarMind增强工作流 - 统一架构和错误处理"""

    def __init__(self):
        """初始化增强工作流"""
        pipeline_logger.info("🚀 初始化ScholarMind增强工作流...")

        # 初始化智能体（使用新的基类架构）
        self.resource_agent = ResourceRetrievalAgent()
        self.methodology_agent = MethodologyAgent()
        self.experiment_agent = ExperimentEvaluatorAgent()
        self.insight_agent = InsightGenerationAgent()
        self.synthesizer_agent = SynthesizerAgent()

        # 工作流状态
        self._pipeline_status = {
            "initialized": True,
            "agents_ready": False,
            "last_run": None,
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
        }

        pipeline_logger.info("✅ 增强工作流初始化完成（5个智能体完整DAG）")

    @with_error_handling(fallback_value={"success": False, "error": "工作流初始化失败"})
    async def initialize_agents(self):
        """异步初始化所有智能体"""
        if self._pipeline_status["agents_ready"]:
            return {"success": True, "message": "智能体已初始化"}

        try:
            # 预热所有智能体模型
            agents = [
                self.resource_agent,
                self.methodology_agent,
                self.experiment_agent,
                self.insight_agent,
                self.synthesizer_agent,
            ]

            for agent in agents:
                if hasattr(agent, "_ensure_model_initialized"):
                    await agent._ensure_model_initialized()
                    pipeline_logger.info(f"✅ {agent.name} 模型初始化完成")

            self._pipeline_status["agents_ready"] = True
            return {"success": True, "message": "所有智能体初始化完成"}

        except Exception as e:
            pipeline_logger.error(f"❌ 智能体初始化失败: {e}")
            return {"success": False, "error": str(e)}

    @with_error_handling(fallback_value={"success": False, "error": "论文处理失败"})
    async def process_paper(
        self,
        paper_input: str,
        input_type: str = "file",
        user_background: str = "intermediate",
        save_report: bool = True,
        output_format: str = "markdown",
        output_language: str = "zh",
        progress_callback: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        增强的论文处理流程（5个智能体完整DAG）

        Args:
            paper_input: 论文输入（文件路径、URL或文本）
            input_type: 输入类型（file、url、text）
            user_background: 用户背景（beginner、intermediate、advanced）
            save_report: 是否保存报告
            output_format: 输出格式（markdown、json）
            output_language: 输出语言（zh、en）
            progress_callback: 进度回调函数

        Returns:
            Dict[str, Any]: 处理结果
        """
        start_time = time.time()

        # 更新工作流状态
        self._pipeline_status["last_run"] = time.time()
        self._pipeline_status["total_runs"] += 1

        try:
            # 初始化智能体
            await self.initialize_agents()

            # 验证输入参数
            validation_result = self.validate_inputs(paper_input, input_type, user_background)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": f"输入验证失败: {'; '.join(validation_result['errors'])}",
                    "stage": "validation",
                }

            # 步骤1：资源检索
            resource_result = await self._execute_stage(
                stage_name="resource_retrieval",
                stage_func=self._process_resource_retrieval,
                progress_callback=progress_callback,
                progress_message="📖 步骤 1/4：正在检索和解析论文...",
                paper_input=paper_input,
                input_type=input_type,
            )

            if not resource_result["success"]:
                self._pipeline_status["failed_runs"] += 1
                return resource_result

            # 步骤2：并行处理（方法论分析 + 实验评估）
            methodology_result, experiment_result = await self._execute_parallel_stage(
                stage_name="parallel_analysis",
                progress_callback=progress_callback,
                progress_message="🔬 步骤 2/4：并行分析论文方法论和实验评估...",
                paper_content=resource_result["data"]["paper_content"],
                output_language=output_language,
            )

            # 步骤3：洞察生成
            insight_result = await self._execute_stage(
                stage_name="insight_generation",
                stage_func=self._process_insight_generation,
                progress_callback=progress_callback,
                progress_message="💡 步骤 3/4：生成批判性洞察和研究建议...",
                paper_content=resource_result["data"]["paper_content"],
                methodology_analysis=(
                    methodology_result.get("data") if methodology_result["success"] else None
                ),
                experiment_evaluation=(
                    experiment_result.get("data") if experiment_result["success"] else None
                ),
                output_language=output_language,
            )

            # 步骤4：综合报告生成
            synthesizer_result = await self._execute_stage(
                stage_name="synthesizer",
                stage_func=self._process_synthesizer,
                progress_callback=progress_callback,
                progress_message="📝 步骤 4/4：综合生成个性化解读报告...",
                resource_data=resource_result["data"],
                methodology_analysis=(
                    methodology_result.get("data") if methodology_result["success"] else None
                ),
                experiment_evaluation=(
                    experiment_result.get("data") if experiment_result["success"] else None
                ),
                insight_analysis=insight_result.get("data") if insight_result["success"] else None,
                user_background=user_background,
                output_language=output_language,
            )

            if not synthesizer_result["success"]:
                self._pipeline_status["failed_runs"] += 1
                return synthesizer_result

            # 保存报告
            report_path = None
            if save_report:
                report_path = await self._save_report_safe(
                    synthesizer_result["data"], output_format, output_language
                )

            # 计算总处理时间
            total_time = time.time() - start_time
            self._pipeline_status["successful_runs"] += 1

            # 发送完成消息
            if progress_callback:
                await progress_callback(f"✨ 论文分析完成！总耗时: {total_time:.1f}秒")

            # 构建最终结果
            result = self._build_final_result(
                total_time=total_time,
                resource_result=resource_result,
                methodology_result=methodology_result,
                experiment_result=experiment_result,
                insight_result=insight_result,
                synthesizer_result=synthesizer_result,
                report_path=report_path,
                user_background=user_background,
                input_type=input_type,
                output_format=output_format,
                output_language=output_language,
            )

            pipeline_logger.info(f"✅ 论文处理完成，总耗时: {total_time:.2f}秒")
            return result

        except Exception as e:
            self._pipeline_status["failed_runs"] += 1
            total_time = time.time() - start_time
            pipeline_logger.error(f"❌ 论文处理失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "processing_time": total_time,
                "stage": "unknown",
            }

    async def _execute_stage(
        self,
        stage_name: str,
        stage_func: Callable,
        progress_callback: Optional[Callable] = None,
        progress_message: str = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """执行单个处理阶段"""
        try:
            if progress_callback and progress_message:
                await progress_callback(progress_message)
            else:
                pipeline_logger.info(f"执行阶段: {stage_name}")

            result = await stage_func(**kwargs)

            if not result.get("success", False):
                pipeline_logger.warning(
                    f"⚠️ {stage_name} 阶段失败: {result.get('error', '未知错误')}"
                )

            return result

        except Exception as e:
            pipeline_logger.error(f"❌ {stage_name} 阶段异常: {e}")
            return {"success": False, "error": str(e), "stage": stage_name}

    async def _execute_parallel_stage(
        self,
        stage_name: str,
        progress_callback: Optional[Callable] = None,
        progress_message: str = None,
        **kwargs,
    ) -> tuple:
        """执行并行处理阶段"""
        try:
            if progress_callback and progress_message:
                await progress_callback(progress_message)
            else:
                pipeline_logger.info(f"执行并行阶段: {stage_name}")

            parallel_start = time.time()

            # 并行执行方法论分析和实验评估
            methodology_task = self._process_methodology_analysis(
                kwargs["paper_content"], kwargs["output_language"]
            )
            experiment_task = self._process_experiment_evaluation(
                kwargs["paper_content"], kwargs["output_language"]
            )

            methodology_result, experiment_result = await asyncio.gather(
                methodology_task, experiment_task, return_exceptions=True
            )

            parallel_time = time.time() - parallel_start

            # 处理异常结果
            if isinstance(methodology_result, Exception):
                methodology_result = {"success": False, "error": str(methodology_result)}
            if isinstance(experiment_result, Exception):
                experiment_result = {"success": False, "error": str(experiment_result)}

            if progress_callback:
                await progress_callback(f"✅ 并行分析完成，耗时: {parallel_time:.1f}秒")

            return methodology_result, experiment_result

        except Exception as e:
            pipeline_logger.error(f"❌ {stage_name} 并行阶段异常: {e}")
            error_result = {"success": False, "error": str(e)}
            return error_result, error_result

    async def _process_parallel_analysis(self, paper_content: dict, output_language: str) -> tuple:
        """并行分析方法（向后兼容接口）"""
        return await self._execute_parallel_stage(
            stage_name="parallel_analysis",
            paper_content=paper_content,
            output_language=output_language,
        )

    def validate_inputs(
        self, paper_input: str, input_type: str, user_background: str
    ) -> Dict[str, Any]:
        """验证输入参数"""
        errors = []

        # 验证论文输入
        if not paper_input or not paper_input.strip():
            errors.append("论文输入不能为空")

        # 验证输入类型
        valid_types = ["file", "url", "text"]
        if input_type not in valid_types:
            errors.append(f"无效的输入类型: {input_type}，支持的类型: {valid_types}")

        # 验证用户背景
        valid_backgrounds = ["beginner", "intermediate", "advanced"]
        if user_background not in valid_backgrounds:
            errors.append(f"无效的用户背景: {user_background}，支持的背景: {valid_backgrounds}")

        # 文件类型特定验证
        if input_type == "file":
            if not Path(paper_input).exists():
                pipeline_logger.error_path("文件验证", paper_input, "文件不存在")
                errors.append(f"文件不存在: {paper_input}")
            elif not paper_input.lower().endswith((".pdf", ".txt")):
                pipeline_logger.warning_path("文件格式验证", paper_input, "不支持的文件格式")
                errors.append(f"不支持的文件格式: {paper_input}，支持的格式: .pdf, .txt")

        return {"valid": len(errors) == 0, "errors": errors}

    async def _process_resource_retrieval(
        self, paper_input: str, input_type: str
    ) -> Dict[str, Any]:
        """处理资源检索阶段"""
        try:
            input_data = {"paper_input": paper_input, "input_type": input_type}
            message = MessageUtils.create_user_message(input_data)

            response = await self.resource_agent.reply(message)
            return MessageUtils.parse_agent_response(response)

        except Exception as e:
            return {"success": False, "error": f"资源检索失败: {str(e)}"}

    async def _process_methodology_analysis(
        self, paper_content: Dict[str, Any], output_language: str
    ) -> Dict[str, Any]:
        """处理方法论分析阶段"""
        try:
            input_data = {"paper_content": paper_content, "output_language": output_language}
            message = MessageUtils.create_user_message(input_data)

            response = await self.methodology_agent.reply(message)
            return MessageUtils.parse_agent_response(response)

        except Exception as e:
            return {"success": False, "error": f"方法论分析失败: {str(e)}"}

    async def _process_experiment_evaluation(
        self, paper_content: Dict[str, Any], output_language: str
    ) -> Dict[str, Any]:
        """处理实验评估阶段"""
        try:
            input_data = {"paper_content": paper_content, "output_language": output_language}
            message = MessageUtils.create_user_message(input_data)

            response = await self.experiment_agent.reply(message)
            return MessageUtils.parse_agent_response(response)

        except Exception as e:
            return {"success": False, "error": f"实验评估失败: {str(e)}"}

    async def _process_insight_generation(
        self,
        paper_content: Dict[str, Any],
        methodology_analysis: Optional[Dict[str, Any]],
        experiment_evaluation: Optional[Dict[str, Any]],
        output_language: str,
    ) -> Dict[str, Any]:
        """处理洞察生成阶段"""
        try:
            input_data = {
                "paper_content": paper_content,
                "methodology_analysis": methodology_analysis,
                "experiment_evaluation": experiment_evaluation,
                "output_language": output_language,
            }
            message = MessageUtils.create_user_message(input_data)

            response = await self.insight_agent.reply(message)
            return MessageUtils.parse_agent_response(response)

        except Exception as e:
            return {"success": False, "error": f"洞察生成失败: {str(e)}"}

    async def _process_synthesizer(
        self,
        resource_data: Dict[str, Any],
        methodology_analysis: Optional[Dict[str, Any]],
        experiment_evaluation: Optional[Dict[str, Any]],
        insight_analysis: Optional[Dict[str, Any]],
        user_background: str,
        output_language: str,
    ) -> Dict[str, Any]:
        """处理综合报告生成阶段"""
        try:
            input_data = {
                "paper_content": resource_data["paper_content"],
                "methodology_analysis": methodology_analysis,
                "experiment_evaluation": experiment_evaluation,
                "insight_analysis": insight_analysis,
                "user_background": user_background,
                "output_language": output_language,
            }
            message = MessageUtils.create_user_message(input_data)

            response = await self.synthesizer_agent.reply(message)
            return MessageUtils.parse_agent_response(response)

        except Exception as e:
            return {"success": False, "error": f"报告生成失败: {str(e)}"}

    async def _save_report_safe(
        self, report_data: Dict[str, Any], output_format: str, output_language: str
    ) -> Optional[str]:
        """安全的报告保存"""
        try:
            return self._save_report(report_data, output_format, output_language)
        except Exception as e:
            pipeline_logger.error(f"❌ 报告保存失败: {e}")
            return None

    def _save_report(
        self, report_data: Dict[str, Any], output_format: str, output_language: str
    ) -> Optional[str]:
        """保存报告到文件"""
        try:
            import json
            import os
            from datetime import datetime

            # 创建输出目录
            output_dir = "outputs"
            os.makedirs(output_dir, exist_ok=True)

            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            title_safe = "".join(
                c
                for c in report_data.get("title", "report")[:50]
                if c.isalnum() or c in (" ", "-", "_")
            ).rstrip()
            filename = f"{title_safe}_{timestamp}.{output_format}"
            filepath = os.path.join(output_dir, filename)

            # 保存报告
            if output_format == "json":
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(report_data, f, ensure_ascii=False, indent=2)
            else:  # markdown
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(f"# {report_data.get('title', '论文分析报告')}\n\n")
                    f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    f.write(f"**语言**: {output_language}\n\n")
                    f.write("---\n\n")

                    if report_data.get("summary"):
                        f.write("## 摘要\n\n")
                        f.write(f"{report_data['summary']}\n\n")

                    if report_data.get("key_contributions"):
                        f.write("## 主要贡献\n\n")
                        for i, contribution in enumerate(report_data["key_contributions"], 1):
                            f.write(f"{i}. {contribution}\n")
                        f.write("\n")

                    if report_data.get("insights"):
                        f.write("## 关键洞察\n\n")
                        for i, insight in enumerate(report_data["insights"], 1):
                            f.write(f"{i}. {insight}\n")
                        f.write("\n")

            pipeline_logger.info(f"✅ 报告已保存至: {filepath}")
            return filepath

        except Exception as e:
            pipeline_logger.error(f"❌ 报告保存失败: {e}")
            return None

    def _build_final_result(
        self,
        total_time: float,
        resource_result: Dict[str, Any],
        methodology_result: Dict[str, Any],
        experiment_result: Dict[str, Any],
        insight_result: Dict[str, Any],
        synthesizer_result: Dict[str, Any],
        report_path: Optional[str],
        user_background: str,
        input_type: str,
        output_format: str,
        output_language: str,
    ) -> Dict[str, Any]:
        """构建最终结果"""

        # 安全地获取各阶段的处理时间
        def safe_get_processing_time(result, default=0):
            if isinstance(result, dict):
                # 尝试多种可能的路径
                if "processing_time" in result:
                    return result["processing_time"]
                elif (
                    "data" in result
                    and isinstance(result["data"], dict)
                    and "processing_time" in result["data"]
                ):
                    return result["data"]["processing_time"]
            return default

        return {
            "success": True,
            "message": "论文处理完成",
            "processing_time": total_time,
            "stages": {
                "resource_retrieval": {
                    "success": True,
                    "processing_time": safe_get_processing_time(resource_result),
                    "paper_title": resource_result.get("data", {})
                    .get("paper_content", {})
                    .get("metadata", {})
                    .get("title", "Unknown"),
                },
                "methodology_analysis": {
                    "success": methodology_result.get("success", False),
                    "processing_time": safe_get_processing_time(methodology_result),
                },
                "experiment_evaluation": {
                    "success": experiment_result.get("success", False),
                    "processing_time": safe_get_processing_time(experiment_result),
                },
                "insight_generation": {
                    "success": insight_result.get("success", False),
                    "processing_time": safe_get_processing_time(insight_result),
                },
                "synthesizer": {
                    "success": synthesizer_result.get("success", True),
                    "processing_time": safe_get_processing_time(synthesizer_result),
                    "report_title": synthesizer_result.get("data", {}).get("title", "Unknown"),
                },
            },
            "outputs": {
                "paper_content": resource_result.get("data", {}).get("paper_content"),
                "methodology_analysis": (
                    methodology_result.get("data") if methodology_result.get("success") else None
                ),
                "experiment_evaluation": (
                    experiment_result.get("data") if experiment_result.get("success") else None
                ),
                "insight_analysis": (
                    insight_result.get("data") if insight_result.get("success") else None
                ),
                "report": synthesizer_result.get("data"),
                "report_path": report_path,
            },
            "metadata": {
                "user_background": user_background,
                "input_type": input_type,
                "output_format": output_format,
                "output_language": output_language,
            },
        }

    def get_pipeline_status(self) -> Dict[str, Any]:
        """获取工作流状态"""
        return {
            **self._pipeline_status,
            "agents": [
                self.resource_agent.name,
                self.methodology_agent.name,
                self.experiment_agent.name,
                self.insight_agent.name,
                self.synthesizer_agent.name,
            ],
            "pipeline_type": "Complete DAG (5 agents)",
            "workflow_stages": [
                "resource_retrieval",
                "parallel_analysis",
                "insight_generation",
                "synthesizer",
            ],
            "success_rate": (
                self._pipeline_status["successful_runs"]
                / max(self._pipeline_status["total_runs"], 1)
                * 100
            ),
        }


# 保持向后兼容的工厂函数
def create_pipeline() -> ScholarMindEnhancedPipeline:
    """创建ScholarMind工作流实例（向后兼容）"""
    return ScholarMindEnhancedPipeline()
