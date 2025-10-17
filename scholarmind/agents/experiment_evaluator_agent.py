"""
Experiment Evaluator Agent
实验评估与验证智能体
"""

import json
import time
from typing import Dict, Any

from agentscope.agent import AgentBase
from agentscope.message import Msg
from agentscope.model import OpenAIChatModel

from config import get_model_config
from ..utils.logger import agent_logger


class ExperimentEvaluatorAgent(AgentBase):
    """实验评估与验证智能体"""

    def __init__(self, **kwargs):
        # Initialize parent class first
        super().__init__(**kwargs)
        # Set agent name
        self.name = "experiment_evaluator_agent"

        # Get model configuration and initialize model wrapper
        model_config = get_model_config()

        # Initialize model wrapper using AgentScope's OpenAIChatModel
        try:
            self.model = OpenAIChatModel(
                model_name=model_config.get("model_name"),
                api_key=model_config.get("api_key"),
                client_args=model_config.get("client_args", {}),
                generate_kwargs={
                    "temperature": model_config.get("temperature", 0.1),
                    "max_tokens": model_config.get("max_tokens", 4000),
                    "top_p": model_config.get("top_p", 0.9)
                }
            )
            agent_logger.info(f"ExperimentEvaluatorAgent LLM模型已初始化: {model_config.get('model_name')}")
        except Exception as e:
            agent_logger.warning(f"Failed to initialize model for ExperimentEvaluatorAgent: {e}")
            agent_logger.info("Will use fallback mode")
            self.model = None

        # Initialize system prompt
        self.sys_prompt = "You are an expert in evaluating academic papers' experimental designs, results, and statistical validity."

    async def reply(self, msg: Msg) -> Msg:
        """
        Process the input message and generate experiment evaluation using LLM
        """
        start_time = time.time()

        try:
            # 解析输入数据 - 支持字典或JSON字符串以保证兼容性
            if isinstance(msg.content, dict):
                input_data = msg.content
            else:
                input_data = json.loads(msg.content)
            paper_content = input_data.get("paper_content", {})
            output_language = input_data.get("output_language", "zh")

            metadata = paper_content.get("metadata", {})
            sections = paper_content.get("sections", [])

            # Use LLM to generate experiment evaluation
            if self.model:
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
            else:
                # Fallback: Basic extraction from paper content
                response_data = self._generate_fallback_evaluation(metadata, sections)
                response_data["processing_time"] = time.time() - start_time
                response_data["success"] = True
                response_data["error_message"] = None

            response_content = {
                "status": "success",
                "data": response_data,
                "message": "Experiment evaluation generated successfully",
            }

            # Create response message - 直接传递字典
            response_msg = Msg(name=self.name, content=response_content, role="assistant")

            return response_msg
        except Exception as e:
            error_response = {
                "status": "error",
                "error": str(e),
                "data": {
                    "success": False,
                    "error_message": str(e),
                    "processing_time": time.time() - start_time,
                }
            }

            return Msg(name=self.name, content=error_response, role="assistant")

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
            if section_type in experiment_types or any(kw in section_title for kw in experiment_types):
                # Truncate long sections
                if len(section_content) > 1000:
                    section_content = section_content[:1000] + "..."
                context_parts.append(f"\n## {section.get('title', 'Untitled')}\n{section_content}\n")

        # Also include related work for baseline comparison context
        for section in sections:
            section_type = section.get("section_type", "").lower()
            section_title = section.get("title", "").lower()
            section_content = section.get("content", "")

            if section_type == "related_work" or "related work" in section_title or "baseline" in section_title:
                if len(section_content) > 500:
                    section_content = section_content[:500] + "..."
                context_parts.append(f"\n## Baselines and Comparisons\n{section_content}\n")
                break

        return "".join(context_parts)

    async def _generate_experiment_evaluation(self, paper_context: str, output_language: str = "zh") -> dict:
        """Use LLM to generate experiment evaluation"""
        # Language requirement
        language_instruction = {
            "zh": "Chinese (中文)",
            "en": "English"
        }[output_language]

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
            # Call LLM - OpenAIChatModel expects messages list
            messages = [
                {"role": "system", "content": self.sys_prompt},
                {"role": "user", "content": prompt}
            ]

            agent_logger.debug("ExperimentEvaluatorAgent正在调用LLM分析实验...")

            # Await the async model call
            response = await self.model(messages)

            # Handle async generator (streaming response)
            response_text = ""
            if hasattr(response, '__aiter__'):
                # It's an async generator - collect all chunks
                last_chunk_text = ""
                async for chunk in response:
                    # ChatResponse object has a 'content' field which is a list of dicts
                    if hasattr(chunk, 'content'):
                        content = chunk.content
                        if isinstance(content, list):
                            current_text = ""
                            for item in content:
                                if isinstance(item, dict) and 'text' in item:
                                    current_text += item['text']
                            last_chunk_text = current_text  # Keep only the last chunk
                        elif isinstance(content, str):
                            last_chunk_text = content
                    elif isinstance(chunk, dict):
                        last_chunk_text = chunk.get('text', chunk.get('content', ''))
                    elif isinstance(chunk, str):
                        last_chunk_text = chunk

                # Use the last chunk which contains the complete response
                response_text = last_chunk_text
            elif hasattr(response, 'text'):
                response_text = response.text
            elif isinstance(response, dict):
                response_text = response.get('text', response.get('content', str(response)))
            elif isinstance(response, str):
                response_text = response
            else:
                response_text = str(response)

            # Try to extract JSON from response
            # Sometimes LLM adds markdown code blocks
            import re
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)

            # Parse JSON response
            evaluation = json.loads(response_text)
            agent_logger.info("ExperimentEvaluatorAgent评估成功生成")
            return evaluation

        except json.JSONDecodeError as e:
            agent_logger.warning(f"Failed to parse JSON from LLM response: {e}")
            # Return structured fallback
            return {
                "experimental_setup": "Failed to parse LLM response.",
                "baseline_comparison": "LLM response parsing failed",
                "key_metrics": [{"metric": "Parsing failed", "value": "N/A", "significance": "LLM response parsing failed"}],
                "validity_assessment": "LLM response parsing failed",
                "results_analysis": "LLM response parsing failed",
                "limitations": ["LLM response parsing failed"],
            }
        except Exception as e:
            agent_logger.error(f"LLM generation failed: {e}")
            agent_logger.debug(f"Error type: {type(e).__name__}")
            # Return structured fallback
            return {
                "experimental_setup": "Failed to generate LLM-based evaluation.",
                "baseline_comparison": "LLM analysis unavailable",
                "key_metrics": [{"metric": "Analysis unavailable", "value": "N/A", "significance": "LLM analysis unavailable"}],
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
            "experimental_setup": experiment_content[0] if experiment_content else "Not found in paper",
            "baseline_comparison": "Fallback mode - LLM required for detailed comparison",
            "key_metrics": [{"metric": "Not extracted", "value": "N/A", "significance": "Fallback mode"}],
            "validity_assessment": "Fallback mode - LLM required for validity assessment",
            "results_analysis": results_content[0] if results_content else "Not found in paper",
            "limitations": limitations[:3] if limitations else ["Not extracted"],
            "statistical_significance": None,
        }
