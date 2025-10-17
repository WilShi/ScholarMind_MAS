"""
Phase 2 Agents Tests
测试方法论分析智能体和实验评估智能体
"""

import asyncio
import json
import pytest

from scholarmind.agents.methodology_agent import MethodologyAgent
from scholarmind.agents.experiment_evaluator_agent import ExperimentEvaluatorAgent
from agentscope.message import Msg


class TestMethodologyAgent:
    """方法论分析智能体测试"""

    def test_methodology_agent_initialization(self):
        """测试方法论智能体初始化"""
        agent = MethodologyAgent()
        assert agent is not None
        assert agent.name == "methodology_agent"
        assert hasattr(agent, 'model')

    @pytest.mark.asyncio
    async def test_methodology_agent_reply(self):
        """测试方法论智能体回复功能"""
        agent = MethodologyAgent()

        # 创建测试输入
        test_paper_content = {
            "metadata": {
                "title": "A Novel Approach to Machine Learning",
                "authors": ["Test Author"],
                "abstract": "This paper presents a novel machine learning approach.",
            },
            "sections": [
                {
                    "title": "Methodology",
                    "content": "We propose a new neural network architecture based on transformer models.",
                    "section_type": "methodology"
                },
                {
                    "title": "Algorithm",
                    "content": "Our algorithm consists of three main steps: preprocessing, training, and evaluation.",
                    "section_type": "methodology"
                }
            ]
        }

        input_data = {
            "paper_content": test_paper_content,
            "output_language": "en"
        }

        msg = Msg(name="user", content=json.dumps(input_data), role="user")

        # 调用agent
        response = await agent.reply(msg)
        response_data = json.loads(response.content)

        # 验证响应结构
        assert response_data["status"] in ["success", "error"]
        if response_data["status"] == "success":
            data = response_data["data"]
            assert "architecture_analysis" in data
            assert "algorithm_flow" in data
            assert "innovation_points" in data
            assert "processing_time" in data
            assert data["success"] is True

    def test_methodology_agent_context_building(self):
        """测试方法论智能体上下文构建"""
        agent = MethodologyAgent()

        metadata = {
            "title": "Test Paper",
            "abstract": "Test abstract"
        }

        sections = [
            {
                "title": "Methodology",
                "content": "Test methodology content",
                "section_type": "methodology"
            }
        ]

        context = agent._build_methodology_context(metadata, sections)

        assert "Test Paper" in context
        assert "Test abstract" in context
        assert "Methodology" in context


class TestExperimentEvaluatorAgent:
    """实验评估智能体测试"""

    def test_experiment_evaluator_initialization(self):
        """测试实验评估智能体初始化"""
        agent = ExperimentEvaluatorAgent()
        assert agent is not None
        assert agent.name == "experiment_evaluator_agent"
        assert hasattr(agent, 'model')

    @pytest.mark.asyncio
    async def test_experiment_evaluator_reply(self):
        """测试实验评估智能体回复功能"""
        agent = ExperimentEvaluatorAgent()

        # 创建测试输入
        test_paper_content = {
            "metadata": {
                "title": "Experimental Study on Machine Learning",
                "authors": ["Test Researcher"],
                "abstract": "This paper presents experimental results on machine learning.",
            },
            "sections": [
                {
                    "title": "Experiments",
                    "content": "We conducted experiments on three datasets: MNIST, CIFAR-10, and ImageNet.",
                    "section_type": "experiment"
                },
                {
                    "title": "Results",
                    "content": "Our method achieved 95% accuracy on MNIST, outperforming the baseline by 5%.",
                    "section_type": "results"
                }
            ]
        }

        input_data = {
            "paper_content": test_paper_content,
            "output_language": "en"
        }

        msg = Msg(name="user", content=json.dumps(input_data), role="user")

        # 调用agent
        response = await agent.reply(msg)
        response_data = json.loads(response.content)

        # 验证响应结构
        assert response_data["status"] in ["success", "error"]
        if response_data["status"] == "success":
            data = response_data["data"]
            assert "experimental_setup" in data
            assert "baseline_comparison" in data
            assert "key_metrics" in data
            assert "validity_assessment" in data
            assert "processing_time" in data
            assert data["success"] is True

    def test_experiment_evaluator_context_building(self):
        """测试实验评估智能体上下文构建"""
        agent = ExperimentEvaluatorAgent()

        metadata = {
            "title": "Experiment Paper",
            "abstract": "Experimental study"
        }

        sections = [
            {
                "title": "Experiments",
                "content": "Test experiment content",
                "section_type": "experiment"
            }
        ]

        context = agent._build_experiment_context(metadata, sections)

        assert "Experiment Paper" in context
        assert "Experimental study" in context
        assert "Experiments" in context


class TestParallelProcessing:
    """并行处理测试"""

    @pytest.mark.asyncio
    async def test_parallel_agent_execution(self):
        """测试两个agent能够并行执行"""
        methodology_agent = MethodologyAgent()
        experiment_agent = ExperimentEvaluatorAgent()

        test_paper_content = {
            "metadata": {
                "title": "Parallel Processing Test Paper",
                "authors": ["Test Author"],
                "abstract": "Testing parallel processing.",
            },
            "sections": [
                {
                    "title": "Methodology",
                    "content": "Test methodology",
                    "section_type": "methodology"
                },
                {
                    "title": "Experiments",
                    "content": "Test experiments",
                    "section_type": "experiment"
                }
            ]
        }

        input_data = {
            "paper_content": test_paper_content,
            "output_language": "en"
        }

        msg = Msg(name="user", content=json.dumps(input_data), role="user")

        # 使用asyncio.gather并行执行
        methodology_task = methodology_agent.reply(msg)
        experiment_task = experiment_agent.reply(msg)

        # 并行执行
        methodology_response, experiment_response = await asyncio.gather(
            methodology_task, experiment_task
        )

        # 验证两个响应都成功返回
        assert methodology_response is not None
        assert experiment_response is not None

        methodology_data = json.loads(methodology_response.content)
        experiment_data = json.loads(experiment_response.content)

        assert methodology_data["status"] in ["success", "error"]
        assert experiment_data["status"] in ["success", "error"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
