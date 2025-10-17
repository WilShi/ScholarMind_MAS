import json
import time

from agentscope.agent import AgentBase
from agentscope.message import Msg
from agentscope.model import OpenAIChatModel

from config import get_model_config
from ..utils.logger import agent_logger


class SynthesizerAgent(AgentBase):
    def __init__(self, **kwargs):
        # Initialize parent class first
        super().__init__(**kwargs)
        # Set agent name
        self.name = "synthesizer_agent"

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
            agent_logger.info(f"LLM模型已初始化: {model_config.get('model_name')}")
        except Exception as e:
            agent_logger.warning(f"Failed to initialize model: {e}")
            agent_logger.info("Will use fallback mode extracting from paper content")
            self.model = None

        # Initialize any required attributes
        self.sys_prompt = "You are a helpful assistant that generates academic paper summary reports."

    async def reply(self, msg: Msg) -> Msg:
        """
        Process the input message and generate a report using LLM
        """
        start_time = time.time()

        try:
            # 解析输入数据 - 支持字典或JSON字符串以保证兼容性
            if isinstance(msg.content, dict):
                input_data = msg.content
            else:
                input_data = json.loads(msg.content)
            paper_content = input_data.get("paper_content", {})
            user_background = input_data.get("user_background", "intermediate")
            output_language = input_data.get("output_language", "zh")

            # Get analysis from all agents
            methodology_analysis = input_data.get("methodology_analysis")
            experiment_evaluation = input_data.get("experiment_evaluation")
            insight_analysis = input_data.get("insight_analysis")  # NEW: Phase 3 addition

            metadata = paper_content.get("metadata", {})
            sections = paper_content.get("sections", [])

            # Use LLM to generate real insights
            if self.model:
                # Build context for LLM (including all analysis results)
                paper_context = self._build_paper_context(
                    metadata, sections, user_background,
                    methodology_analysis, experiment_evaluation, insight_analysis
                )

                # Generate analysis using LLM (now async)
                analysis = await self._generate_analysis_with_llm(
                    paper_context, user_background, output_language,
                    methodology_analysis, experiment_evaluation, insight_analysis
                )

                response_data = {
                    "title": f"Analysis of: {metadata.get('title', 'Unknown Title')}",
                    "summary": analysis.get("summary", ""),
                    "key_contributions": analysis.get("key_contributions", []),
                    "methodology_summary": analysis.get("methodology_summary", ""),
                    "experiment_summary": analysis.get("experiment_summary", ""),
                    "insights": analysis.get("insights", []),
                    "user_background_adaptation": user_background,
                    "processing_time": time.time() - start_time,
                    "success": True,
                }
            else:
                # Fallback: Extract information from paper content directly
                response_data = self._generate_fallback_analysis(metadata, sections, user_background)
                response_data["processing_time"] = time.time() - start_time
                response_data["success"] = True

            response_content = {
                "status": "success",
                "data": response_data,
                "message": "Report generated successfully",
            }

            # Create response message - 直接传递字典
            response_msg = Msg(name=self.name, content=response_content, role="assistant")

            return response_msg
        except Exception as e:
            error_response = {"status": "error", "error": str(e), "data": {"success": False, "error_message": str(e)}}

            return Msg(name=self.name, content=error_response, role="assistant")

    def _build_paper_context(
        self,
        metadata: dict,
        sections: list,
        user_background: str,
        methodology_analysis: dict = None,
        experiment_evaluation: dict = None,
        insight_analysis: dict = None  # NEW: Phase 3 addition
    ) -> str:
        """Build context string for LLM from paper content and all analysis results"""
        context_parts = []

        # Add title
        if metadata.get("title"):
            context_parts.append(f"Title: {metadata['title']}\n")

        # Add authors
        if metadata.get("authors"):
            authors_str = ", ".join(metadata["authors"])
            context_parts.append(f"Authors: {authors_str}\n")

        # Add abstract
        if metadata.get("abstract"):
            context_parts.append(f"\nAbstract:\n{metadata['abstract']}\n")

        # Add methodology analysis if available
        if methodology_analysis:
            context_parts.append("\n--- Methodology Analysis (from MethodologyAgent) ---\n")
            if methodology_analysis.get("architecture_analysis"):
                context_parts.append(f"Architecture: {methodology_analysis['architecture_analysis'][:300]}...\n")
            if methodology_analysis.get("innovation_points"):
                context_parts.append(f"Innovation Points: {', '.join(methodology_analysis['innovation_points'][:3])}\n")

        # Add experiment evaluation if available
        if experiment_evaluation:
            context_parts.append("\n--- Experiment Evaluation (from ExperimentEvaluatorAgent) ---\n")
            if experiment_evaluation.get("experimental_setup"):
                context_parts.append(f"Setup: {experiment_evaluation['experimental_setup'][:300]}...\n")
            if experiment_evaluation.get("results_analysis"):
                context_parts.append(f"Results: {experiment_evaluation['results_analysis'][:300]}...\n")

        # NEW: Add insight analysis if available
        if insight_analysis:
            context_parts.append("\n--- Critical Insights (from InsightGenerationAgent) ---\n")
            if insight_analysis.get("strengths"):
                context_parts.append(f"Strengths: {', '.join(insight_analysis['strengths'][:3])}\n")
            if insight_analysis.get("weaknesses"):
                context_parts.append(f"Weaknesses: {', '.join(insight_analysis['weaknesses'][:3])}\n")
            if insight_analysis.get("future_directions"):
                context_parts.append(f"Future Directions: {', '.join(insight_analysis['future_directions'][:3])}\n")
            if insight_analysis.get("novelty_assessment"):
                context_parts.append(f"Novelty: {insight_analysis['novelty_assessment'][:300]}...\n")

        # Add key sections (limit to avoid token limits)
        context_parts.append("\n--- Key Sections from Paper ---\n")
        for section in sections[:10]:  # Limit to first 10 sections
            section_title = section.get("title", "Untitled")
            section_content = section.get("content", "")
            # Truncate long sections
            if len(section_content) > 500:
                section_content = section_content[:500] + "..."
            context_parts.append(f"\n## {section_title}\n{section_content}\n")

        return "".join(context_parts)

    async def _generate_analysis_with_llm(
        self,
        paper_context: str,
        user_background: str,
        output_language: str = "zh",
        methodology_analysis: dict = None,
        experiment_evaluation: dict = None,
        insight_analysis: dict = None  # NEW: Phase 3 addition
    ) -> dict:
        """Use LLM to generate paper analysis with integrated insights from all agents"""
        # Define background-specific instructions
        background_instructions = {
            "beginner": "Explain concepts in simple terms, avoid jargon, and provide context for technical terms.",
            "intermediate": "Use moderate technical language and assume basic familiarity with the field.",
            "advanced": "Use technical terminology freely and focus on novel contributions and technical details."
        }

        instruction = background_instructions.get(user_background, background_instructions["intermediate"])

        # Language requirement
        language_instruction = {
            "zh": "Chinese (中文)",
            "en": "English"
        }[output_language]

        # Build additional context string for all agent outputs
        additional_context = ""
        if methodology_analysis or experiment_evaluation or insight_analysis:
            additional_context = "\n\nYou have access to comprehensive analysis from multiple specialized agents:\n"
            if methodology_analysis:
                additional_context += "- Methodology Agent has deeply analyzed the technical approach, architecture, and innovations\n"
            if experiment_evaluation:
                additional_context += "- Experiment Evaluator Agent has analyzed the experimental setup, results, and validity\n"
            if insight_analysis:
                additional_context += "- Insight Generation Agent has provided critical insights, strengths, weaknesses, and future directions\n"
            additional_context += "\nPlease synthesize all these perspectives into a cohesive, comprehensive report.\n"

        # Create prompt for LLM
        prompt = f"""You are synthesizing a comprehensive report for an academic paper. {instruction}{additional_context}

{paper_context}

Please provide a comprehensive analysis in JSON format with the following structure:
{{
    "summary": "A 2-3 paragraph summary integrating all agent insights (methodology, experiments, and critical analysis)",
    "key_contributions": ["contribution 1 (from methodology innovations)", "contribution 2", "contribution 3"],
    "methodology_summary": "A paragraph summarizing the methodology (use MethodologyAgent's analysis if available)",
    "experiment_summary": "A paragraph summarizing the experiments and results (use ExperimentEvaluatorAgent's analysis if available)",
    "insights": ["insight 1 (can reference methodology innovations)", "insight 2 (can reference experimental findings)", "insight 3 (can reference critical analysis and future directions)"]
}}

**Important**: Respond ONLY with valid JSON, no additional text. Please write all content in {language_instruction}."""

        try:
            # Call LLM - OpenAIChatModel expects messages list
            messages = [
                {"role": "system", "content": self.sys_prompt},
                {"role": "user", "content": prompt}
            ]

            agent_logger.debug("正在调用LLM分析论文...")

            # Await the async model call
            response = await self.model(messages)

            # Handle async generator (streaming response)
            # In streaming mode, each chunk contains cumulative text from start to current position
            # So we only need the last chunk which contains the complete response
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
            agent_logger.info("LLM分析成功生成")
            return analysis

        except json.JSONDecodeError as e:
            agent_logger.warning(f"Failed to parse JSON from LLM response: {e}")
            # Return structured fallback
            return {
                "summary": "Failed to parse LLM response.",
                "key_contributions": ["LLM response parsing failed"],
                "methodology_summary": "LLM response parsing failed",
                "experiment_summary": "LLM response parsing failed",
                "insights": ["Please check logs for details"]
            }
        except Exception as e:
            agent_logger.error(f"LLM generation failed: {e}")
            agent_logger.debug(f"Error type: {type(e).__name__}")
            # Return structured fallback
            return {
                "summary": "Failed to generate LLM-based summary.",
                "key_contributions": ["LLM analysis unavailable"],
                "methodology_summary": "LLM analysis unavailable",
                "experiment_summary": "LLM analysis unavailable",
                "insights": ["Please check logs for details"]
            }

    def _generate_fallback_analysis(self, metadata: dict, sections: list, user_background: str) -> dict:
        """Generate basic analysis without LLM by extracting from content"""
        # Extract abstract as summary
        summary = metadata.get("abstract", "No abstract available.")

        # Try to identify key sections
        key_contributions = []
        methodology_summary = "Not found"
        experiment_summary = "Not found"

        for section in sections:
            section_title = section.get("title", "").lower()
            section_content = section.get("content", "")
            section_type = section.get("section_type", "")

            # Extract contributions from conclusion or introduction
            if section_type in ["conclusion", "introduction"] and len(key_contributions) < 3:
                # Simple extraction: first 3 sentences
                sentences = section_content.split(". ")[:3]
                key_contributions.extend([s.strip() + "." for s in sentences if len(s.strip()) > 20])

            # Extract methodology
            if section_type == "methodology" and methodology_summary == "Not found":
                methodology_summary = section_content[:500] + ("..." if len(section_content) > 500 else "")

            # Extract experiments
            if section_type == "experiment" and experiment_summary == "Not found":
                experiment_summary = section_content[:500] + ("..." if len(section_content) > 500 else "")

        # Generate basic insights
        insights = [
            f"This paper is titled '{metadata.get('title', 'Unknown')}'",
            f"Authored by: {', '.join(metadata.get('authors', ['Unknown authors']))}",
            f"Contains {len(sections)} sections"
        ]

        if metadata.get("keywords"):
            insights.append(f"Key topics: {', '.join(metadata['keywords'][:5])}")

        return {
            "title": f"Basic Analysis of: {metadata.get('title', 'Unknown Title')}",
            "summary": summary,
            "key_contributions": key_contributions[:5] if key_contributions else ["No contributions extracted"],
            "methodology_summary": methodology_summary,
            "experiment_summary": experiment_summary,
            "insights": insights,
            "user_background_adaptation": user_background,
        }

    def validate_user_background(self, background: str) -> bool:
        """Validate user background value"""
        return background in ["beginner", "intermediate", "advanced"]
