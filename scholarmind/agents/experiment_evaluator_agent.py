"""
Experiment Evaluator Agent
实验评估智能体
"""

import json
import time
from typing import Any, Dict

from agentscope.message import Msg

from ..agents.base_agent import ScholarMindAgentBase
from ..utils.logger import agent_logger


class ExperimentEvaluatorAgent(ScholarMindAgentBase):
    """实验评估智能体"""

    def __init__(self, **kwargs):
        # Initialize base class with proper name parameter
        super().__init__(
            name="ExperimentEvaluatorAgent",
            sys_prompt="You are an expert in evaluating experimental designs and results in academic papers.",
            **kwargs,
        )

    async def _process_logic(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理实验评估逻辑"""
        start_time = time.time()

        try:
            paper_content = input_data.get("paper_content", {})
            output_language = input_data.get("output_language", "zh")

            metadata = paper_content.get("metadata", {})
            sections = paper_content.get("sections", [])

            # Build context for LLM
            paper_context = self._build_experiment_context(metadata, sections)

            # Generate evaluation using LLM
            evaluation = await self._generate_experiment_evaluation(paper_context, output_language)

            response_data = {
                "experimental_setup": evaluation.get("experimental_setup", ""),
                "baseline_comparison": evaluation.get("baseline_comparison", ""),
                "key_metrics": evaluation.get("key_metrics", []),
                "validity_assessment": evaluation.get("validity_assessment", ""),
                "results_analysis": evaluation.get("results_analysis", ""),
                "limitations": evaluation.get("limitations", []),
                "statistical_significance": evaluation.get("statistical_significance"),
                "processing_time": time.time() - start_time,
                "success": True,
                "error_message": None,
            }

            return response_data

        except Exception as e:
            return {
                "success": False,
                "error_message": str(e),
                "processing_time": time.time() - start_time,
            }

    def _build_experiment_context(self, metadata: dict, sections: list) -> str:
        """Build context string for LLM from paper experiment sections"""
        context_parts = []

        # Add title and abstract
        if metadata.get("title"):
            context_parts.append(f"Title: {metadata['title']}\n")

        if metadata.get("abstract"):
            context_parts.append(f"\nAbstract:\n{metadata['abstract']}\n")

        # Focus on experiment-related sections
        context_parts.append("\nExperiment Sections:\n")
        experiment_types = ["experiment", "evaluation", "results", "analysis"]

        for section in sections:
            section_title = section.get("title", "").lower()
            section_type = section.get("section_type", "").lower()
            section_content = section.get("content", "")

            # Check if this is an experiment-related section
            if section_type in experiment_types or any(
                kw in section_title for kw in experiment_types
            ):
                # Truncate long sections
                if len(section_content) > 1000:
                    section_content = section_content[:1000] + "..."
                context_parts.append(
                    f"\n## {section.get('title', 'Untitled')}\n{section_content}\n"
                )

        # Also include related work for baseline comparison context
        for section in sections:
            section_type = section.get("section_type", "").lower()
            section_title = section.get("title", "").lower()
            section_content = section.get("content", "")

            if (
                section_type == "related_work"
                or "related work" in section_title
                or "baseline" in section_title
            ):
                if len(section_content) > 500:
                    section_content = section_content[:500] + "..."
                context_parts.append(f"\n## Baselines and Comparisons\n{section_content}\n")
                break

        return "".join(context_parts)

    async def _generate_experiment_evaluation(
        self, paper_context: str, output_language: str = "zh"
    ) -> dict:
        """Use LLM to generate experiment evaluation"""
        # Language requirement
        language_instruction = {"zh": "Chinese (中文)", "en": "English"}[output_language]

        # Create prompt for LLM
        prompt = f"""You are evaluating the experimental design and results of an academic paper. Please provide a comprehensive assessment.

{paper_context}

Please provide a detailed experiment evaluation in JSON format with the following structure:
{{
    "experimental_setup": "Description of the experimental setup, datasets used, and evaluation protocols (2-3 paragraphs)",
    "baseline_comparison": "Analysis of baseline methods compared and how they were selected (1-2 paragraphs)",
    "key_metrics": [
        {{"metric": "Metric name", "value": "Result value", "significance": "Why this metric matters"}},
        {{"metric": "Metric name", "value": "Result value", "significance": "Why this metric matters"}}
    ],
    "validity_assessment": "Assessment of experimental validity, rigor, and reproducibility (2-3 paragraphs)",
    "results_analysis": "Analysis of the results, performance comparisons, and what they demonstrate (2-3 paragraphs)",
    "limitations": ["limitation 1", "limitation 2", "limitation 3"],
    "statistical_significance": "Discussion of statistical significance, error bars, confidence intervals if mentioned (optional)"
}}

**Important**: Respond ONLY with valid JSON, no additional text. Please write all content in {language_instruction}."""

        try:
            # Call LLM using base class safe method
            messages = [
                {"role": "system", "content": self.sys_prompt},
                {"role": "user", "content": prompt},
            ]

            agent_logger.info("ExperimentEvaluatorAgent正在调用LLM分析实验...")

            # Use base class safe model call
            response = await self._safe_model_call(messages)

            if response.get("success", False):
                # Parse JSON response
                response_text = response.get("content", "")

                # Try to extract JSON from response
                import re

                json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group(1)

                evaluation = json.loads(response_text)
                agent_logger.info("ExperimentEvaluatorAgent评估成功生成")
                return evaluation
            else:
                # Return structured fallback
                return {
                    "experimental_setup": "Model call failed",
                    "baseline_comparison": "Model call failed",
                    "key_metrics": [
                        {
                            "metric": "Model call failed",
                            "value": "N/A",
                            "significance": "Model call failed",
                        }
                    ],
                    "validity_assessment": "Model call failed",
                    "results_analysis": "Model call failed",
                    "limitations": ["Model call failed"],
                }

        except json.JSONDecodeError as e:
            agent_logger.warning(f"Failed to parse JSON from LLM response: {e}")
            # Return structured fallback
            return {
                "experimental_setup": "Failed to parse LLM response.",
                "baseline_comparison": "LLM response parsing failed",
                "key_metrics": [
                    {
                        "metric": "Parsing failed",
                        "value": "N/A",
                        "significance": "LLM response parsing failed",
                    }
                ],
                "validity_assessment": "LLM response parsing failed",
                "results_analysis": "LLM response parsing failed",
                "limitations": ["LLM response parsing failed"],
            }
        except Exception as e:
            agent_logger.error(f"LLM generation failed: {e}")
            # Return structured fallback
            return {
                "experimental_setup": "Failed to generate LLM-based evaluation.",
                "baseline_comparison": "LLM analysis unavailable",
                "key_metrics": [
                    {
                        "metric": "Analysis unavailable",
                        "value": "N/A",
                        "significance": "LLM analysis unavailable",
                    }
                ],
                "validity_assessment": "LLM analysis unavailable",
                "results_analysis": "LLM analysis unavailable",
                "limitations": ["LLM analysis unavailable"],
            }

    def _generate_fallback_evaluation(self, metadata: dict, sections: list) -> dict:
        """Generate basic evaluation without LLM by extracting from content"""
        # Find experiment sections
        experiment_content = []
        results_content = []
        limitations = []

        for section in sections:
            section_type = section.get("section_type", "").lower()
            section_content = section.get("content", "")

            if section_type in ["experiment", "evaluation"]:
                experiment_content.append(section_content[:500])

            if section_type == "results":
                results_content.append(section_content[:500])

            # Try to extract limitations
            if section_type == "conclusion" or section_type == "discussion":
                sentences = section_content.split(". ")
                for sentence in sentences:
                    if "limitation" in sentence.lower() or "future work" in sentence.lower():
                        limitations.append(sentence.strip() + ".")
                        if len(limitations) >= 3:
                            break

        return {
            "experimental_setup": (
                experiment_content[0] if experiment_content else "Not found in paper"
            ),
            "baseline_comparison": "Fallback mode - LLM required for detailed comparison",
            "key_metrics": [
                {"metric": "Not extracted", "value": "N/A", "significance": "Fallback mode"}
            ],
            "validity_assessment": "Fallback mode - LLM required for validity assessment",
            "results_analysis": results_content[0] if results_content else "Not found in paper",
            "limitations": limitations[:3] if limitations else ["Not extracted"],
            "statistical_significance": None,
        }
