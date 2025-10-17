"""
Methodology Agent
方法论解析智能体
"""

import json
import time
from typing import Dict, Any

from agentscope.agent import AgentBase
from agentscope.message import Msg
from agentscope.model import OpenAIChatModel

from config import get_model_config
from ..utils.logger import agent_logger


class MethodologyAgent(AgentBase):
    """方法论深度解析智能体"""

    def __init__(self, **kwargs):
        # Initialize parent class first
        super().__init__(**kwargs)
        # Set agent name
        self.name = "methodology_agent"

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
            agent_logger.info(f"MethodologyAgent LLM模型已初始化: {model_config.get('model_name')}")
        except Exception as e:
            agent_logger.warning(f"Failed to initialize model for MethodologyAgent: {e}")
            agent_logger.info("Will use fallback mode")
            self.model = None

        # Initialize system prompt
        self.sys_prompt = "You are an expert in analyzing academic papers' methodologies, algorithms, and technical innovations."

    async def reply(self, msg: Msg) -> Msg:
        """
        Process the input message and generate methodology analysis using LLM
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

            # Use LLM to generate deep methodology analysis
            if self.model:
                # Build context for LLM
                paper_context = self._build_methodology_context(metadata, sections)

                # Generate analysis using LLM
                analysis = await self._generate_methodology_analysis(paper_context, output_language)

                response_data = {
                    "architecture_analysis": analysis.get("architecture_analysis", ""),
                    "algorithm_flow": analysis.get("algorithm_flow", ""),
                    "innovation_points": analysis.get("innovation_points", []),
                    "related_work_comparison": analysis.get("related_work_comparison", ""),
                    "technical_details": analysis.get("technical_details", ""),
                    "complexity_analysis": analysis.get("complexity_analysis"),
                    "mathematical_formulation": analysis.get("mathematical_formulation"),
                    "processing_time": time.time() - start_time,
                    "success": True,
                    "error_message": None,
                }
            else:
                # Fallback: Basic extraction from paper content
                response_data = self._generate_fallback_analysis(metadata, sections)
                response_data["processing_time"] = time.time() - start_time
                response_data["success"] = True
                response_data["error_message"] = None

            response_content = {
                "status": "success",
                "data": response_data,
                "message": "Methodology analysis generated successfully",
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

    def _build_methodology_context(self, metadata: dict, sections: list) -> str:
        """Build context string for LLM from paper methodology sections"""
        context_parts = []

        # Add title and abstract
        if metadata.get("title"):
            context_parts.append(f"Title: {metadata['title']}\n")

        if metadata.get("abstract"):
            context_parts.append(f"\nAbstract:\n{metadata['abstract']}\n")

        # Focus on methodology-related sections
        context_parts.append("\nMethodology Sections:\n")
        methodology_types = ["methodology", "method", "approach", "model", "algorithm", "architecture"]

        for section in sections:
            section_title = section.get("title", "").lower()
            section_type = section.get("section_type", "").lower()
            section_content = section.get("content", "")

            # Check if this is a methodology-related section
            if section_type in methodology_types or any(kw in section_title for kw in methodology_types):
                # Truncate long sections
                if len(section_content) > 1000:
                    section_content = section_content[:1000] + "..."
                context_parts.append(f"\n## {section.get('title', 'Untitled')}\n{section_content}\n")

        # Also include related work sections for comparison
        for section in sections:
            section_type = section.get("section_type", "").lower()
            section_title = section.get("title", "").lower()
            section_content = section.get("content", "")

            if section_type == "related_work" or "related work" in section_title:
                if len(section_content) > 500:
                    section_content = section_content[:500] + "..."
                context_parts.append(f"\n## Related Work\n{section_content}\n")
                break

        return "".join(context_parts)

    async def _generate_methodology_analysis(self, paper_context: str, output_language: str = "zh") -> dict:
        """Use LLM to generate deep methodology analysis"""
        # Language requirement
        language_instruction = {
            "zh": "Chinese (中文)",
            "en": "English"
        }[output_language]

        # Create prompt for LLM
        prompt = f"""You are analyzing the methodology of an academic paper. Please provide a deep technical analysis.

{paper_context}

Please provide a comprehensive methodology analysis in JSON format with the following structure:
{{
    "architecture_analysis": "Detailed breakdown of the model/system architecture (2-3 paragraphs)",
    "algorithm_flow": "Step-by-step explanation of the algorithm flow and key procedures (2-3 paragraphs)",
    "innovation_points": ["innovation 1", "innovation 2", "innovation 3"],
    "related_work_comparison": "Comparison with related work and what makes this approach unique (1-2 paragraphs)",
    "technical_details": "Important technical details, design choices, and rationale (2-3 paragraphs)",
    "complexity_analysis": "Computational and space complexity analysis if applicable (optional)",
    "mathematical_formulation": "Key mathematical formulations or equations explained (optional)"
}}

**Important**: Respond ONLY with valid JSON, no additional text. Please write all content in {language_instruction}."""

        try:
            # Call LLM - OpenAIChatModel expects messages list
            messages = [
                {"role": "system", "content": self.sys_prompt},
                {"role": "user", "content": prompt}
            ]

            agent_logger.debug("MethodologyAgent正在调用LLM分析方法论...")

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
            analysis = json.loads(response_text)
            agent_logger.info("MethodologyAgent分析成功生成")
            return analysis

        except json.JSONDecodeError as e:
            agent_logger.warning(f"Failed to parse JSON from LLM response: {e}")
            # Return structured fallback
            return {
                "architecture_analysis": "Failed to parse LLM response.",
                "algorithm_flow": "LLM response parsing failed",
                "innovation_points": ["LLM response parsing failed"],
                "related_work_comparison": "LLM response parsing failed",
                "technical_details": "LLM response parsing failed",
            }
        except Exception as e:
            agent_logger.error(f"LLM generation failed: {e}")
            agent_logger.debug(f"Error type: {type(e).__name__}")
            # Return structured fallback
            return {
                "architecture_analysis": "Failed to generate LLM-based analysis.",
                "algorithm_flow": "LLM analysis unavailable",
                "innovation_points": ["LLM analysis unavailable"],
                "related_work_comparison": "LLM analysis unavailable",
                "technical_details": "LLM analysis unavailable",
            }

    def _generate_fallback_analysis(self, metadata: dict, sections: list) -> dict:
        """Generate basic analysis without LLM by extracting from content"""
        # Find methodology sections
        methodology_content = []
        innovation_points = []

        for section in sections:
            section_type = section.get("section_type", "").lower()
            section_content = section.get("content", "")

            if section_type in ["methodology", "method", "approach"]:
                methodology_content.append(section_content[:500])

            # Try to extract innovations from introduction or conclusion
            if section_type in ["introduction", "conclusion"]:
                sentences = section_content.split(". ")[:3]
                innovation_points.extend([s.strip() + "." for s in sentences if len(s.strip()) > 20])

        return {
            "architecture_analysis": " ".join(methodology_content[:2]) if methodology_content else "Not found in paper",
            "algorithm_flow": methodology_content[0] if methodology_content else "Not found in paper",
            "innovation_points": innovation_points[:3] if innovation_points else ["Not extracted"],
            "related_work_comparison": "Fallback mode - LLM required for detailed comparison",
            "technical_details": methodology_content[1] if len(methodology_content) > 1 else "Not found in paper",
            "complexity_analysis": None,
            "mathematical_formulation": None,
        }
