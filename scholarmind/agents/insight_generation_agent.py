"""
Insight Generation Agent
洞察生成智能体
"""

import json
import time
from typing import Any, Dict, Optional

from agentscope.message import Msg

from ..agents.base_agent import ScholarMindAgentBase
from ..utils.logger import agent_logger


class InsightGenerationAgent(ScholarMindAgentBase):
    """洞察生成智能体 - 提供批判性分析和未来方向建议"""

    def __init__(self, **kwargs):
        # Initialize base class with proper name parameter
        super().__init__(
            name="InsightGenerationAgent",
            sys_prompt="You are an expert in generating critical insights and identifying limitations in academic research.",
            **kwargs,
        )

    async def reply(self, msg: Msg) -> Msg:
        """
        使用基类的标准回复方法
        """
        return await super().reply(msg)

    async def _process_logic(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理洞察生成逻辑（符合基类标准）
        """
        start_time = time.time()

        try:
            paper_content = input_data.get("paper_content", {})
            output_language = input_data.get("output_language", "zh")

            # Get analysis from other agents
            methodology_analysis = input_data.get("methodology_analysis")
            experiment_evaluation = input_data.get("experiment_evaluation")

            metadata = paper_content.get("metadata", {})
            sections = paper_content.get("sections", [])

            # Use LLM to generate deep insights
            if self.model:
                # Build comprehensive context for LLM
                paper_context = self._build_insight_context(
                    metadata, sections, methodology_analysis, experiment_evaluation
                )

                # Generate insights using LLM
                insights = await self._generate_insights_with_llm(paper_context, output_language)

                response_data = {
                    "logical_flow": insights.get("logical_flow", ""),
                    "strengths": insights.get("strengths", []),
                    "weaknesses": insights.get("weaknesses", []),
                    "critical_insights": insights.get("critical_insights", []),
                    "future_directions": insights.get("future_directions", []),
                    "novelty_assessment": insights.get("novelty_assessment", ""),
                    "impact_analysis": insights.get("impact_analysis", ""),
                    "research_questions": insights.get("research_questions"),
                    "processing_time": time.time() - start_time,
                    "success": True,
                    "error_message": None,
                }
            else:
                # Fallback: Basic extraction from paper content
                response_data = self._generate_fallback_insights(
                    metadata, sections, methodology_analysis, experiment_evaluation
                )
                response_data["processing_time"] = time.time() - start_time
                response_data["success"] = True
                response_data["error_message"] = None

            return response_data

        except Exception as e:
            agent_logger.error(f"洞察生成失败: {e}")
            return {
                "success": False,
                "error_message": str(e),
                "processing_time": time.time() - start_time if "start_time" in locals() else 0,
            }

    def _build_insight_context(
        self,
        metadata: dict,
        sections: list,
        methodology_analysis: Optional[dict] = None,
        experiment_evaluation: Optional[dict] = None,
    ) -> str:
        """Build comprehensive context string for insight generation"""
        context_parts = []

        # Add title and abstract
        if metadata.get("title"):
            context_parts.append(f"Title: {metadata['title']}\n")

        if metadata.get("abstract"):
            context_parts.append(f"\nAbstract:\n{metadata['abstract']}\n")

        # Add methodology insights if available
        if methodology_analysis:
            context_parts.append("\n--- Methodology Analysis ---\n")
            if methodology_analysis.get("innovation_points"):
                context_parts.append(
                    f"Innovation Points: {', '.join(methodology_analysis['innovation_points'])}\n"
                )
            if methodology_analysis.get("architecture_analysis"):
                context_parts.append(
                    f"Architecture: {methodology_analysis['architecture_analysis'][:400]}...\n"
                )
            if methodology_analysis.get("technical_details"):
                context_parts.append(
                    f"Technical Details: {methodology_analysis['technical_details'][:400]}...\n"
                )

        # Add experiment insights if available
        if experiment_evaluation:
            context_parts.append("\n--- Experiment Evaluation ---\n")
            if experiment_evaluation.get("validity_assessment"):
                context_parts.append(
                    f"Validity: {experiment_evaluation['validity_assessment'][:400]}...\n"
                )
            if experiment_evaluation.get("limitations"):
                context_parts.append(
                    f"Limitations: {', '.join(experiment_evaluation['limitations'][:3])}\n"
                )
            if experiment_evaluation.get("results_analysis"):
                context_parts.append(
                    f"Results: {experiment_evaluation['results_analysis'][:400]}...\n"
                )

        # Add conclusion and discussion sections
        context_parts.append("\n--- Key Sections for Insights ---\n")
        for section in sections:
            section_type = section.get("section_type", "").lower()
            section_title = section.get("title", "").lower()
            section_content = section.get("content", "")

            if section_type in ["conclusion", "discussion", "future_work"] or any(
                kw in section_title for kw in ["conclusion", "discussion", "future", "limitation"]
            ):
                if len(section_content) > 600:
                    section_content = section_content[:600] + "..."
                context_parts.append(
                    f"\n## {section.get('title', 'Untitled')}\n{section_content}\n"
                )

        return "".join(context_parts)

    async def _generate_insights_with_llm(
        self, paper_context: str, output_language: str = "zh"
    ) -> dict:
        """Use LLM to generate deep insights and critical analysis"""
        # Language requirement
        language_instruction = {"zh": "Chinese (中文)", "en": "English"}[output_language]

        # Create prompt for LLM
        prompt = f"""You are performing a critical analysis of an academic paper. Provide deep, thoughtful insights that go beyond surface-level observations.

{paper_context}

Please provide a comprehensive critical analysis in JSON format with the following structure:
{{
    "logical_flow": "Analyze the overall logical structure and argumentation flow of the paper (2-3 paragraphs)",
    "strengths": ["strength 1 (be specific)", "strength 2", "strength 3"],
    "weaknesses": ["weakness 1 (be specific and constructive)", "weakness 2", "weakness 3"],
    "critical_insights": ["critical insight 1 (go beyond obvious observations)", "insight 2", "insight 3"],
    "future_directions": ["future direction 1 (actionable research suggestions)", "direction 2", "direction 3"],
    "novelty_assessment": "Evaluate the novelty and originality of this work (1-2 paragraphs)",
    "impact_analysis": "Analyze the potential impact and significance of this work (1-2 paragraphs)",
    "research_questions": ["Derivative research question 1", "question 2", "question 3"]
}}

**Important**:
- Be critical but constructive
- Provide specific, actionable insights
- Consider both technical and practical implications
- Respond ONLY with valid JSON, no additional text
- Please write all content in {language_instruction}."""

        try:
            # Call LLM - OpenAIChatModel expects messages list
            messages = [
                {"role": "system", "content": self.sys_prompt},
                {"role": "user", "content": prompt},
            ]

            agent_logger.info("InsightGenerationAgent正在调用LLM生成洞察...")

            # Await the async model call
            response = await self.model(messages)

            # Handle async generator (streaming response)
            response_text = ""
            if hasattr(response, "__aiter__"):
                # It's an async generator - collect all chunks
                last_chunk_text = ""
                async for chunk in response:
                    # ChatResponse object has a 'content' field which is a list of dicts
                    if hasattr(chunk, "content"):
                        content = chunk.content
                        if isinstance(content, list):
                            current_text = ""
                            for item in content:
                                if isinstance(item, dict) and "text" in item:
                                    current_text += item["text"]
                            last_chunk_text = current_text  # Keep only the last chunk
                        elif isinstance(content, str):
                            last_chunk_text = content
                    elif isinstance(chunk, dict):
                        last_chunk_text = chunk.get("text", chunk.get("content", ""))
                    elif isinstance(chunk, str):
                        last_chunk_text = chunk

                # Use the last chunk which contains the complete response
                response_text = last_chunk_text
            elif hasattr(response, "text"):
                response_text = response.text
            elif isinstance(response, dict):
                response_text = response.get("text", response.get("content", str(response)))
            elif isinstance(response, str):
                response_text = response
            else:
                response_text = str(response)

            # Try to extract JSON from response
            import re

            json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)

            # Parse JSON response
            insights = json.loads(response_text)
            agent_logger.info("InsightGenerationAgent洞察成功生成")
            return insights

        except json.JSONDecodeError as e:
            agent_logger.warning(f"Failed to parse JSON from LLM response: {e}")
            # Return structured fallback
            return {
                "logical_flow": "Failed to parse LLM response.",
                "strengths": ["LLM response parsing failed"],
                "weaknesses": ["LLM response parsing failed"],
                "critical_insights": ["LLM response parsing failed"],
                "future_directions": ["LLM response parsing failed"],
                "novelty_assessment": "LLM response parsing failed",
                "impact_analysis": "LLM response parsing failed",
            }
        except Exception as e:
            agent_logger.error(f"LLM generation failed: {e}")
            agent_logger.error(f"Error type: {type(e).__name__}")
            # Return structured fallback
            return {
                "logical_flow": "Failed to generate LLM-based insights.",
                "strengths": ["LLM analysis unavailable"],
                "weaknesses": ["LLM analysis unavailable"],
                "critical_insights": ["LLM analysis unavailable"],
                "future_directions": ["LLM analysis unavailable"],
                "novelty_assessment": "LLM analysis unavailable",
                "impact_analysis": "LLM analysis unavailable",
            }

    def _generate_fallback_insights(
        self,
        metadata: dict,
        sections: list,
        methodology_analysis: Optional[dict] = None,
        experiment_evaluation: Optional[dict] = None,
    ) -> dict:
        """Generate basic insights without LLM by extracting from content"""
        # Extract strengths and weaknesses from analysis
        strengths = []
        weaknesses = []

        if methodology_analysis and methodology_analysis.get("innovation_points"):
            strengths.extend(
                [f"Innovation: {ip}" for ip in methodology_analysis["innovation_points"][:2]]
            )

        if experiment_evaluation and experiment_evaluation.get("limitations"):
            weaknesses.extend(experiment_evaluation["limitations"][:3])

        # Find conclusion section
        conclusion_content = ""
        for section in sections:
            section_type = section.get("section_type", "").lower()
            if section_type == "conclusion":
                conclusion_content = section.get("content", "")[:500]
                break

        return {
            "logical_flow": f"This paper titled '{metadata.get('title', 'Unknown')}' presents research findings. "
            + (
                conclusion_content
                if conclusion_content
                else "Detailed logical flow analysis requires LLM."
            ),
            "strengths": (
                strengths if strengths else ["Fallback mode - detailed analysis unavailable"]
            ),
            "weaknesses": (
                weaknesses if weaknesses else ["Fallback mode - detailed analysis unavailable"]
            ),
            "critical_insights": ["Fallback mode - LLM required for critical insights"],
            "future_directions": ["Fallback mode - LLM required for future direction suggestions"],
            "novelty_assessment": "Fallback mode - LLM required for novelty assessment",
            "impact_analysis": "Fallback mode - LLM required for impact analysis",
            "research_questions": None,
        }
