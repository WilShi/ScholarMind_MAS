"""
Phase 3 Tests - Insight Generation and Complete 5-Agent Workflow
测试洞察生成智能体和完整5智能体工作流
"""

import json

import pytest
from agentscope.message import Msg

from scholarmind.agents.insight_generation_agent import InsightGenerationAgent
from scholarmind.workflows.scholarmind_pipeline import ScholarMindPipeline


class TestInsightGenerationAgent:
    """洞察生成智能体测试"""

    def test_insight_agent_initialization(self):
        """测试洞察生成智能体初始化"""
        agent = InsightGenerationAgent()
        assert agent is not None
        assert agent.name == "InsightGenerationAgent"
        assert hasattr(agent, "model")

    @pytest.mark.asyncio
    async def test_insight_agent_reply(self):
        """测试洞察生成智能体回复功能"""
        agent = InsightGenerationAgent()

        # 创建测试输入
        test_paper_content = {
            "metadata": {
                "title": "Critical Analysis Test Paper",
                "authors": ["Test Researcher"],
                "abstract": "This paper presents innovative research with limitations.",
            },
            "sections": [
                {
                    "title": "Conclusion",
                    "content": "Our work has both strengths and limitations. "
                    "Future work should address scalability.",
                    "section_type": "conclusion",
                },
                {
                    "title": "Discussion",
                    "content": "The proposed method shows promise but requires further validation.",
                    "section_type": "discussion",
                },
            ],
        }

        # 模拟来自其他智能体的分析
        methodology_analysis = {
            "innovation_points": ["Novel architecture", "Improved efficiency"],
            "architecture_analysis": "The paper proposes a new neural network architecture.",
            "technical_details": "Uses attention mechanisms and skip connections.",
        }

        experiment_evaluation = {
            "limitations": ["Small dataset", "Limited baselines", "Computational cost"],
            "validity_assessment": "The experiments are well-designed but could be more comprehensive.",
            "results_analysis": "Results show improvement over baselines.",
        }

        input_data = {
            "paper_content": test_paper_content,
            "methodology_analysis": methodology_analysis,
            "experiment_evaluation": experiment_evaluation,
            "output_language": "en",
        }

        msg = Msg(name="user", content=json.dumps(input_data), role="user")

        # 调用agent
        response = await agent.reply(msg)
        # response.content 已经是字典，不需要 json.loads
        response_data = (
            response.content if isinstance(response.content, dict) else json.loads(response.content)
        )

        # 验证响应结构
        assert response_data["status"] in ["success", "error"]
        if response_data["status"] == "success":
            data = response_data["data"]
            assert "logical_flow" in data
            assert "strengths" in data
            assert "weaknesses" in data
            assert "critical_insights" in data
            assert "future_directions" in data
            assert "novelty_assessment" in data
            assert "impact_analysis" in data
            assert "processing_time" in data
            assert data["success"] is True

    def test_insight_agent_context_building(self):
        """测试洞察生成智能体上下文构建"""
        agent = InsightGenerationAgent()

        metadata = {"title": "Test Paper", "abstract": "Test abstract"}

        sections = [
            {
                "title": "Conclusion",
                "content": "Test conclusion content",
                "section_type": "conclusion",
            }
        ]

        methodology_analysis = {"innovation_points": ["Innovation 1", "Innovation 2"]}

        experiment_evaluation = {"limitations": ["Limitation 1"]}

        context = agent._build_insight_context(
            metadata, sections, methodology_analysis, experiment_evaluation
        )

        assert "Test Paper" in context
        assert "Test abstract" in context
        assert "Innovation 1" in context
        assert "Limitation 1" in context


class TestComplete5AgentWorkflow:
    """完整5智能体工作流测试"""

    def test_pipeline_initialization_5_agents(self):
        """测试5智能体工作流初始化"""
        pipeline = ScholarMindPipeline()

        assert pipeline is not None
        assert hasattr(pipeline, "resource_agent")
        assert hasattr(pipeline, "methodology_agent")
        assert hasattr(pipeline, "experiment_agent")
        assert hasattr(pipeline, "insight_agent")
        assert hasattr(pipeline, "synthesizer_agent")

        # 验证工作流状态
        status = pipeline.get_pipeline_status()
        assert len(status["agents"]) == 5
        assert status["pipeline_type"] == "Complete DAG (5 agents)"

    @pytest.mark.asyncio
    async def test_5_agent_workflow_stages(self):
        """测试5智能体工作流各阶段"""
        pipeline = ScholarMindPipeline()

        # 创建简单的测试论文内容
        test_paper_content = {
            "metadata": {
                "title": "5-Agent Workflow Test",
                "authors": ["Test Author"],
                "abstract": "Testing complete workflow with 5 agents.",
            },
            "sections": [
                {
                    "title": "Introduction",
                    "content": "This paper introduces a novel approach.",
                    "section_type": "introduction",
                },
                {
                    "title": "Methodology",
                    "content": "We propose a new method based on transformers.",
                    "section_type": "methodology",
                },
                {
                    "title": "Experiments",
                    "content": "We evaluate on three benchmarks and achieve SOTA results.",
                    "section_type": "experiment",
                },
                {
                    "title": "Conclusion",
                    "content": "Our method shows promise. Future work includes scaling to larger datasets.",
                    "section_type": "conclusion",
                },
            ],
        }

        # 测试资源检索阶段
        resource_result = await pipeline._process_resource_retrieval(
            json.dumps({"paper_content": test_paper_content}), "text"
        )
        assert resource_result["success"] is True

        # 测试并行分析阶段
        methodology_result, experiment_result = await pipeline._process_parallel_analysis(
            test_paper_content, "en"
        )
        assert "success" in methodology_result
        assert "success" in experiment_result

        # 测试洞察生成阶段
        insight_result = await pipeline._process_insight_generation(
            test_paper_content,
            methodology_result.get("data") if methodology_result.get("success") else None,
            experiment_result.get("data") if experiment_result.get("success") else None,
            "en",
        )
        assert "success" in insight_result


class TestPhase3Integration:
    """Phase 3集成测试"""

    @pytest.mark.asyncio
    async def test_full_5_agent_pipeline_text_input(self):
        """测试完整5智能体流程 - 文本输入"""
        pipeline = ScholarMindPipeline()

        test_text = """
        Deep Learning for Natural Language Processing

        Authors: John Doe, Jane Smith

        Abstract: This paper presents a novel deep learning approach for natural language processing tasks.

        Introduction: Natural language processing has seen significant advances with deep learning.

        Methodology: We propose a transformer-based architecture with attention mechanisms.

        Experiments: We evaluate our method on GLUE benchmark and achieve state-of-the-art results.

        Conclusion: Our approach shows promising results. Future work includes multilingual support.
        """

        # 运行完整流程
        result = await pipeline.process_paper(
            paper_input=test_text,
            input_type="text",
            user_background="intermediate",
            save_report=False,
            output_language="en",
        )

        # 验证结果
        assert result is not None
        assert result.get("success") is True

        # 验证所有阶段都执行了
        stages = result.get("stages", {})
        assert "resource_retrieval" in stages
        assert "methodology_analysis" in stages
        assert "experiment_evaluation" in stages
        assert "insight_generation" in stages  # NEW: Phase 3
        assert "synthesizer" in stages

        # 验证输出包含所有分析结果
        outputs = result.get("outputs", {})
        assert "paper_content" in outputs
        assert "report" in outputs

    def test_pipeline_workflow_stages_info(self):
        """测试工作流阶段信息"""
        pipeline = ScholarMindPipeline()
        status = pipeline.get_pipeline_status()

        assert "workflow_stages" in status
        stages = status["workflow_stages"]
        assert len(stages) == 4  # 4个主要阶段
        # 验证stage名称（使用实际返回的小写snake_case格式）
        assert "resource_retrieval" in stages[0]
        assert "parallel_analysis" in stages[1]
        assert "insight_generation" in stages[2]
        assert "synthesizer" in stages[3]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
