"""
基础功能测试
"""

import os
import tempfile

import pytest

from scholarmind.tools.paper_parser import PaperParser


class TestBasicFunctionality:
    """基础功能测试"""

    def test_paper_parser_basic(self):
        """测试论文解析器基础功能"""
        parser = PaperParser()

        sample_text = """
        Test Paper Title

        Authors: Test Author

        Abstract
        This is a test abstract for the paper.

        1. Introduction
        This is the introduction section.

        2. Methodology
        This is the methodology section.

        3. Conclusion
        This is the conclusion section.
        """

        result = parser.parse_text(sample_text)

        assert result.metadata.title is not None
        assert result.metadata.abstract is not None
        assert len(result.sections) > 0
        assert result.full_text == sample_text

    def test_file_parsing(self):
        """测试文件解析"""
        parser = PaperParser()

        sample_text = """
        File Test Paper

        Abstract
        This is a test paper from file.

        Introduction
        Testing file parsing functionality.
        """

        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write(sample_text)
            temp_file = f.name

        try:
            result = parser.parse_file(temp_file)

            assert result.metadata.title is not None
            assert len(result.sections) > 0
        finally:
            os.unlink(temp_file)

    def test_metadata_extraction(self):
        """测试元数据提取"""
        parser = PaperParser()

        text = """
        Advanced Machine Learning Techniques

        Authors: John Doe, Jane Smith

        Abstract
        This paper presents advanced machine learning techniques for data analysis.

        Keywords: machine learning, data analysis, artificial intelligence

        2023
        """

        metadata = parser._extract_metadata_from_text(text, "test.txt")

        assert metadata.title == "Advanced Machine Learning Techniques"
        assert len(metadata.authors) == 2
        assert "machine learning" in metadata.abstract.lower()
        assert len(metadata.keywords) > 0

    def test_section_parsing(self):
        """测试章节解析"""
        parser = PaperParser()

        text = """
        Introduction
        This is the introduction section with some content.

        Methodology
        This is the methodology section describing our approach.

        Experiments
        This section describes our experimental setup.

        Conclusion
        This is the conclusion section summarizing our findings.
        """

        sections = parser._parse_sections(text)

        assert len(sections) >= 4

        section_titles = [section.title for section in sections]
        assert any("Introduction" in title for title in section_titles)
        assert any("Methodology" in title for title in section_titles)
        assert any("Experiments" in title for title in section_titles)
        assert any("Conclusion" in title for title in section_titles)


if __name__ == "__main__":
    pytest.main([__file__])
