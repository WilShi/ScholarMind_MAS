"""
ScholarMind Report Generator
智读ScholarMind报告生成工具
"""

import os
from datetime import datetime
from typing import Dict, List

from agentscope.tool import Toolkit

from ..models.structured_outputs import PaperContent, ReportSection, SynthesizerOutput


class ReportGenerator:
    """报告生成器"""

    def __init__(self):

        self.templates = self._load_templates()

    def _load_templates(self) -> Dict[str, str]:
        """加载报告模板"""

        return {
            "executive_summary": """

# 论文解读报告



## 基本信息

- **标题**: {title}

- **作者**: {authors}

- **发表年份**: {year}

- **关键词**: {keywords}



## 核心摘要

{summary}



## 主要贡献

{contributions}



## 方法概述

{methodology}



## 实验结果

{experiments}



## 关键洞察

{insights}

""",
            "detailed_report": """

# 详细解读报告：{title}



## 作者信息

{authors}



## 摘要

{abstract}



## 1. 研究背景与动机

{background}



## 2. 核心方法论

{methodology_detailed}



## 3. 实验设计与结果

{experiments_detailed}



## 4. 主要贡献与创新

{contributions_detailed}



## 5. 局限性与未来方向

{limitations}



## 6. 总结与评价

{conclusion}

""",
            "beginner_friendly": """

# 论文通俗解读：{title}



### 这篇论文讲了什么？

{simple_summary}



### 为什么重要？

{importance}



### 用了什么方法？

{simple_methodology}



### 发现了什么？

{simple_results}



### 对我们有什么启发？

{practical_insights}

""",
        }

    def generate_summary_report(
        self, paper_content: PaperContent, user_background: str = "general"
    ) -> str:
        """

        生成摘要报告



        Args:

            paper_content: 结构化的论文内容

            user_background: 用户背景（beginner, intermediate, advanced）



        Returns:

            str: 生成的摘要报告文本

        """

        metadata = paper_content.metadata

        # 提取关键信息

        title = metadata.title

        authors = ", ".join(metadata.authors[:3])  # 最多显示3个作者

        if len(metadata.authors) > 3:

            authors += f" 等 {len(metadata.authors)} 位作者"

        year = metadata.publication_year or "未知"

        keywords = ", ".join(metadata.keywords[:5]) if metadata.keywords else "无"

        # 生成摘要

        summary = metadata.abstract

        if len(summary) > 500:

            summary = summary[:500] + "..."

        # 提取主要贡献

        contributions = self._extract_contributions(paper_content)

        # 提取方法论概述

        methodology = self._extract_methodology_summary(paper_content)

        # 提取实验概述

        experiments = self._extract_experiments_summary(paper_content)

        # 生成洞察

        insights = self._generate_insights(paper_content, user_background)

        # 根据用户背景调整模板

        template = self._select_template(user_background)

        return template.format(
            title=title,
            authors=authors,
            year=year,
            keywords=keywords,
            summary=summary,
            contributions=contributions,
            methodology=methodology,
            experiments=experiments,
            insights=insights,
        )

    def generate_detailed_report(
        self, paper_content: PaperContent, user_background: str = "general"
    ) -> str:
        """生成详细报告"""

        metadata = paper_content.metadata

        # 提取各部分内容

        title = metadata.title

        authors = self._format_authors(metadata.authors)

        abstract = metadata.abstract

        # 提取各章节内容

        background = self._extract_section_content(paper_content, "introduction")

        methodology_detailed = self._extract_section_content(paper_content, "methodology")

        experiments_detailed = self._extract_section_content(paper_content, "experiment")

        contributions_detailed = self._extract_contributions(paper_content)

        limitations = self._extract_limitations(paper_content)

        conclusion = self._extract_section_content(paper_content, "conclusion")

        result = self.templates["detailed_report"].format(
            title=title,
            authors=authors,
            abstract=abstract,
            background=background,
            methodology_detailed=methodology_detailed,
            experiments_detailed=experiments_detailed,
            contributions_detailed=contributions_detailed,
            limitations=limitations,
            conclusion=conclusion,
        )
        return result

    def _extract_contributions(self, paper_content: PaperContent) -> str:
        """提取主要贡献"""

        contributions = []

        # 从摘要中提取贡献

        paper_content.metadata.abstract.lower()

        contribution_keywords = [
            "contribution",
            "propose",
            "present",
            "introduce",
            "develop",
            "achieve",
        ]

        sentences = paper_content.metadata.abstract.split(". ")

        for sentence in sentences:

            if any(keyword in sentence.lower() for keyword in contribution_keywords):

                contributions.append(f"- {sentence.strip()}")

        # 从方法论中提取贡献

        for section in paper_content.sections:

            if section.section_type == "methodology":

                sentences = section.content.split(". ")

                for sentence in sentences[:3]:  # 只取前3句

                    if len(sentence.strip()) > 20:

                        contributions.append(f"- {sentence.strip()}")

                break

        return (
            "\n".join(contributions[:5])
            if contributions
            else "- 论文提出了新的方法或技术\n- 在相关任务上取得了改进\n- 为该领域提供了新的见解"
        )

    def _extract_methodology_summary(self, paper_content: PaperContent) -> str:
        """提取方法论概述"""

        for section in paper_content.sections:

            if section.section_type == "methodology":

                # 提取前200个字符作为概述

                content = section.content.replace("\n", " ").strip()

                if len(content) > 200:

                    content = content[:200] + "..."

                return content

        return "论文采用了先进的技术方法来解决相关问题。"

    def _extract_experiments_summary(self, paper_content: PaperContent) -> str:
        """提取实验概述"""

        for section in paper_content.sections:

            if section.section_type == "experiment":

                # 提取关键实验信息

                content = section.content.replace("\n", " ").strip()

                if len(content) > 200:

                    content = content[:200] + "..."

                return content

        return "论文通过实验验证了所提出方法的有效性。"

    def _extract_section_content(self, paper_content: PaperContent, section_type: str) -> str:
        """提取特定章节内容"""

        for section in paper_content.sections:

            if section.section_type == section_type:

                return section.content

        return f"未找到{section_type}章节内容。"

    def _generate_insights(self, paper_content: PaperContent, user_background: str) -> str:
        """生成洞察"""

        insights = []

        # 基础洞察

        insights.append("- 该研究为相关领域提供了新的思路和方法")

        # 根据用户背景调整洞察

        if user_background == "beginner":

            insights.append("- 对于初学者来说，这篇论文提供了很好的入门参考")

            insights.append("- 建议先了解相关的基础知识再深入阅读")

        elif user_background == "researcher":

            insights.append("- 研究人员可以关注其方法的技术细节")

            insights.append("- 值得进一步探索其在其他领域的应用")

        elif user_background == "engineer":

            insights.append("- 工程师可以关注其实现细节和实用性")

            insights.append("- 考虑如何将该方法应用到实际项目中")

        return "\n".join(insights)

    def _select_template(self, user_background: str) -> str:
        """根据用户背景选择模板"""

        if user_background == "beginner":

            result = self.templates["beginner_friendly"]
            return result

        elif user_background == "researcher":

            result = self.templates["detailed_report"]
            return result

        else:

            result = self.templates["executive_summary"]
            return result

    def _format_authors(self, authors: List[str]) -> str:
        """格式化作者列表"""

        if not authors:

            return "未知作者"

        if len(authors) <= 3:

            return ", ".join(authors)

        else:

            return f"{', '.join(authors[:3])} 等 {len(authors)} 位作者"

    def _extract_limitations(self, paper_content: PaperContent) -> str:
        """提取局限性"""

        limitations = []

        # 在结论中查找局限性

        for section in paper_content.sections:

            if section.section_type == "conclusion":

                section.content.lower()

                limitation_keywords = ["limitation", "future", "challenge", "drawback", "weakness"]

                sentences = section.content.split(". ")

                for sentence in sentences:

                    if any(keyword in sentence.lower() for keyword in limitation_keywords):

                        limitations.append(f"- {sentence.strip()}")

                break

        return (
            "\n".join(limitations[:3])
            if limitations
            else "- 论文未明确提及局限性\n- 未来工作可以进一步改进和扩展"
        )

    def save_report(self, content: str, filename: str, output_dir: str = "outputs") -> str:
        """保存报告到文件"""

        os.makedirs(output_dir, exist_ok=True)

        filepath = os.path.join(output_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:

            f.write(content)

        return filepath

    def generate_synthesizer_output(
        self, paper_content: PaperContent, user_background: str = "general"
    ) -> SynthesizerOutput:
        """生成综合报告智能体输出"""

        start_time = datetime.now()

        # 生成报告内容

        self.generate_summary_report(paper_content, user_background)

        # 提取关键信息

        metadata = paper_content.metadata

        key_contributions = [
            contrib.strip("- ")
            for contrib in self._extract_contributions(paper_content).split("\n")
            if contrib.strip()
        ]

        methodology_summary = self._extract_methodology_summary(paper_content)

        experiment_summary = self._extract_experiments_summary(paper_content)

        insights = [
            insight.strip("- ")
            for insight in self._generate_insights(paper_content, user_background).split("\n")
            if insight.strip()
        ]

        # 创建报告章节

        sections = [
            ReportSection(
                title="基本信息",
                content=f"标题: {metadata.title}\n作者: {', '.join(metadata.authors)}\n年份: {metadata.publication_year}",
                importance_score=0.8,
            ),
            ReportSection(title="摘要", content=metadata.abstract, importance_score=0.9),
            ReportSection(title="方法论", content=methodology_summary, importance_score=0.8),
            ReportSection(title="实验结果", content=experiment_summary, importance_score=0.7),
        ]

        end_time = datetime.now()

        processing_time = (end_time - start_time).total_seconds()

        return SynthesizerOutput(
            title=f"论文解读报告: {metadata.title}",
            summary=metadata.abstract,
            key_contributions=key_contributions,
            methodology_summary=methodology_summary,
            experiment_summary=experiment_summary,
            insights=insights,
            sections=sections,
            user_background_adaptation=f"报告已根据{user_background}背景进行优化",
            processing_time=processing_time,
            success=True,
            error_message=None,
        )


# Create a global instance of ReportGenerator

_report_generator_instance = ReportGenerator()


def generate_report_tool(
    paper_content: PaperContent, user_background: str = "general"
) -> SynthesizerOutput:
    """

    使用ScholarMind报告生成器生成综合报告。



    Args:

        paper_content (PaperContent): 包含论文结构化内容的对象。

        user_background (str, optional): 用户的背景（例如 "beginner", "intermediate", "advanced"）。默认为 "general"。



    Returns:

        SynthesizerOutput: 包含报告标题、摘要、主要贡献、方法论、实验、洞察等信息的结构化对象。

    """

    return _report_generator_instance.generate_synthesizer_output(paper_content, user_background)


# Create a toolkit and register the tool

report_generator_toolkit = Toolkit()

report_generator_toolkit.register_tool_function(generate_report_tool)
