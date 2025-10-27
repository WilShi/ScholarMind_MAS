"""
ScholarMind Paper Parser
智读ScholarMind论文解析工具
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, List

import arxiv
import pdfplumber
from pypdf import PdfReader
import requests
from agentscope.tool import Toolkit
from docx import Document

from ..models.structured_outputs import PaperContent, PaperMetadata, PaperSection
from ..utils.logger import tool_logger
from ..utils.path_utils import PathUtils


class PaperParser:
    """论文解析器"""

    def __init__(self):
        self.supported_formats = [".pdf", ".docx", ".txt"]
        self.section_patterns = {
            "introduction": r"(?i)(introduction|intro|background|motivation)",
            "methodology": r"(?i)(method|methodology|approach|technique|algorithm|model)",
            "experiment": r"(?i)(experiment|evaluation|result|performance|test|study)",
            "conclusion": r"(?i)(conclusion|discussion|future|summary)",
            "related": r"(?i)(related\s+work|literature\s+review|background)",
            "abstract": r"(?i)(abstract)",
            "references": r"(?i)(references|bibliography)",
        }

    def parse_paper(self, paper_input: str, input_type: str = "file") -> PaperContent:
        """
        解析论文

        Args:
            paper_input: 论文输入（文件路径或URL）
            input_type: 输入类型（file, url, text）

        Returns:
            PaperContent: 解析后的论文内容
        """
        try:
            if input_type == "file":
                return self.parse_file(paper_input)
            elif input_type == "url":
                return self._parse_url(paper_input)
            elif input_type == "text":
                return self.parse_text(paper_input)
            else:
                raise ValueError(f"Unsupported input type: {input_type}")
        except Exception as e:
            raise RuntimeError(f"Failed to parse paper: {str(e)}")

    def parse_file(self, file_path: str) -> PaperContent:
        """解析文件"""
        try:
            # 使用Path对象处理中文路径
            p_file_path = Path(file_path)
            if not p_file_path.exists():
                raise FileNotFoundError(f"File not found: {p_file_path}")

            file_ext = p_file_path.suffix.lower()
            if file_ext not in self.supported_formats:
                raise ValueError(f"Unsupported file format: {file_ext}")

            if file_ext == ".pdf":
                return self.parse_pdf(p_file_path)
            elif file_ext == ".docx":
                return self.parse_docx(p_file_path)
            elif file_ext == ".txt":
                return self.parse_txt(p_file_path)
            return None  # Should not happen
        except Exception as e:
            # 如果Path处理失败，回退到字符串处理
            tool_logger.warning_path("Path处理失败", file_path, f"回退到字符串处理: {e}")
            return self._parse_file_fallback(file_path)

    def parse_pdf(self, file_path: Path) -> PaperContent:
        """解析PDF文件"""
        text_content = ""
        sections = []

        # 使用pdfplumber提取文本（保持布局）
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content += page_text + "\n"
        except Exception as e:
            tool_logger.warning_path("PDF解析", file_path, f"pdfplumber失败，尝试pypdf: {e}")
            # 备用方案：使用pypdf
            try:
                with PathUtils.safe_open_file(file_path, 'rb') as file:
                    pdf_reader = PdfReader(file)
                    for page in pdf_reader.pages:
                        text_content += page.extract_text() + "\n"
            except Exception as e2:
                raise RuntimeError(f"Failed to parse PDF: {str(e2)}")

        # 提取元数据
        metadata = self._extract_metadata_from_text(text_content, file_path.name)

        # 解析章节
        sections = self._parse_sections(text_content)

        return PaperContent(
            metadata=metadata,
            sections=sections,
            full_text=text_content,
            figures=self._extract_figures_info(text_content),
            tables=self._extract_tables_info(text_content),
        )
    
    def _parse_file_fallback(self, file_path: str) -> PaperContent:
        """回退的文件解析方法，处理编码问题"""
        try:
            # 尝试多种编码打开文件
            for encoding in ['utf-8', 'gbk', 'gb2312', 'latin1']:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        text_content = file.read()
                        
                    # 提取元数据
                    metadata = self._extract_metadata_from_text(text_content, Path(file_path).name)
                    
                    # 解析章节
                    sections = self._parse_sections(text_content)
                    
                    return PaperContent(
                        metadata=metadata,
                        sections=sections,
                        full_text=text_content,
                        figures=[],
                        tables=[]
                    )
                except UnicodeDecodeError:
                    continue
            
            raise RuntimeError(f"无法读取文件: {file_path}（尝试了多种编码）")
            
        except Exception as e:
            raise RuntimeError(f"文件解析失败: {str(e)}")

    def parse_docx(self, file_path: Path) -> PaperContent:
        """解析DOCX文件"""
        doc = Document(file_path)
        text_content = ""

        for paragraph in doc.paragraphs:
            text_content += paragraph.text + "\n"

        metadata = self._extract_metadata_from_text(text_content, file_path.name)
        sections = self._parse_sections(text_content)

        return PaperContent(
            metadata=metadata,
            sections=sections,
            full_text=text_content,
            figures=self._extract_figures_info(text_content),
            tables=self._extract_tables_info(text_content),
        )

    def parse_txt(self, file_path: Path) -> PaperContent:
        """解析TXT文件"""
        try:
            with PathUtils.safe_open_file(file_path, 'r') as file:
                text_content = file.read()
        except Exception as e:
            tool_logger.error_path("TXT文件读取", file_path, f"读取失败: {e}")
            raise RuntimeError(f"Failed to parse TXT file: {str(e)}")

        metadata = self._extract_metadata_from_text(text_content, file_path.name)
        sections = self._parse_sections(text_content)

        return PaperContent(
            metadata=metadata,
            sections=sections,
            full_text=text_content,
            figures=[],
            tables=[]
        )

    def _parse_url(self, url: str) -> PaperContent:
        """解析URL"""
        # 检查是否是ArXiv URL
        if "arxiv.org" in url:
            return self._parse_arxiv_url(url)
        else:
            # 尝试下载并解析
            return self._download_and_parse_url(url)

    def _parse_arxiv_url(self, url: str) -> PaperContent:
        """解析ArXiv URL"""
        # 提取ArXiv ID，支持 /abs/ 和 /pdf/ 格式，支持版本号
        arxiv_id_match = re.search(r"arxiv\.org/(?:abs|pdf)/(\d+\.\d+(?:v\d+)?)", url)
        if not arxiv_id_match:
            raise ValueError("Invalid ArXiv URL format")

        arxiv_id = arxiv_id_match.group(1)

        # 使用ArXiv API获取论文信息
        search = arxiv.Search(id_list=[arxiv_id])
        paper = next(search.results())

        # 下载PDF
        paper_path = f"temp_{arxiv_id}.pdf"
        paper.download_pdf(dirpath=".", filename=paper_path)

        try:
            # 解析PDF
            content = self.parse_pdf(Path(paper_path))

            # 更新元数据
            content.metadata.title = paper.title
            content.metadata.authors = [author.name for author in paper.authors]
            content.metadata.abstract = paper.summary
            content.metadata.arxiv_id = arxiv_id

            return content
        finally:
            # 清理临时文件
            if os.path.exists(paper_path):
                os.remove(paper_path)

    def _download_and_parse_url(self, url: str) -> PaperContent:
        """下载并解析URL"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # 根据Content-Type决定如何处理
            content_type = response.headers.get("content-type", "").lower()

            if "pdf" in content_type:
                # 保存为临时PDF文件
                temp_path = "temp_download.pdf"
                with open(temp_path, "wb") as f:
                    f.write(response.content)
                try:
                    return self.parse_pdf(Path(temp_path))
                finally:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
            else:
                # 当作文本处理
                return self.parse_text(response.text)

        except Exception as e:
            raise RuntimeError(f"Failed to download and parse URL: {str(e)}")

    def parse_text(self, text: str) -> PaperContent:
        """解析纯文本"""
        metadata = self._extract_metadata_from_text(text, "text_input")
        sections = self._parse_sections(text)

        return PaperContent(
            metadata=metadata,
            sections=sections,
            full_text=text,
            figures=self._extract_figures_info(text),
            tables=self._extract_tables_info(text),
        )

    def _extract_metadata_from_text(self, text: str, filename: str) -> PaperMetadata:
        """从文本中提取元数据"""
        # 简单的元数据提取逻辑
        lines = text.split("\n")

        # 尝试提取标题（通常在前几行）
        title = ""
        for i, line in enumerate(lines[:10]):
            line = line.strip()
            if len(line) > 10 and len(line) < 200 and not line.startswith("Abstract"):
                title = line
                break

        # 提取摘要
        abstract = ""
        abstract_match = re.search(
            r"(?i)abstract[:\s]*\n?(.*?)(?=\n\s*\n|\n[introduction|keywords|i\.])", text, re.DOTALL
        )
        if abstract_match:
            abstract = abstract_match.group(1).strip()

        # 提取作者（简单模式）
        authors = []
        # 改进的作者提取模式
        author_lines = text.split("\n")[:50]  # 查看前50行
        author_text = "\n".join(author_lines)

        # 查找包含"Authors:"或"Author:"的行
        author_line_match = re.search(r"(?i)(?:Authors?|By)[:\s]*(.*?)(?=\n)", author_text)
        if author_line_match:
            authors_str = author_line_match.group(1).strip()
            # 分割作者（支持逗号和分号分隔）
            authors = [author.strip() for author in re.split(r"[,;]", authors_str) if author.strip()]
        else:
            # 备用方案：查找常见的作者格式
            author_pattern = r"(?:^|\n)([A-Z][a-z]+ [A-Z][a-z]+(?:,?\s+[A-Z][a-z]+ [A-Z][a-z]+)*)"
            author_matches = re.findall(author_pattern, text[:2000])  # 只在前2000字符中查找
            if author_matches:
                authors = [author.strip() for author in author_matches[:5]]  # 最多取5个作者

        # 提取关键词
        keywords = []
        keyword_match = re.search(r"(?i)keywords?[:\s]*\n?(.*?)(?=\n)", text)
        if keyword_match:
            keywords_str = keyword_match.group(1).strip()
            keywords = [kw.strip() for kw in re.split(r"[,;]", keywords_str) if kw.strip()]

        # 尝试提取年份
        year = None
        year_match = re.search(r"\b(19|20)\d{2}\b", text)
        if year_match:
            year = int(year_match.group(0))

        return PaperMetadata(
            title=title or filename, authors=authors, abstract=abstract, publication_year=year, keywords=keywords
        )

    def _parse_sections(self, text: str) -> List[PaperSection]:
        """解析论文章节"""
        sections = []

        # 尝试多种章节标题模式

        # 模式1: 数字编号的章节 (如 "1. Introduction" 或 "1 Introduction")
        section_pattern_numbered = r"(?:^|\n)\s*(\d+\.?\s+[A-Z][A-Za-z\s]+?)\s*\n"
        matches_numbered = list(re.finditer(section_pattern_numbered, text, re.MULTILINE))

        if matches_numbered and len(matches_numbered) >= 3:
            # 处理每个章节
            for i, match in enumerate(matches_numbered):
                section_title = match.group(1).strip()
                # 过滤掉太短或太长的标题
                if len(section_title) < 3 or len(section_title) > 100:
                    continue

                start_pos = match.end()
                end_pos = matches_numbered[i + 1].start() if i + 1 < len(matches_numbered) else len(text)

                section_content = text[start_pos:end_pos].strip()

                # 确定章节类型
                section_type = "other"
                for sec_type, pattern in self.section_patterns.items():
                    if re.search(pattern, section_title):
                        section_type = sec_type
                        break

                sections.append(PaperSection(title=section_title, content=section_content, section_type=section_type))

            return sections

        # 模式2: 简单标题后跟内容（测试用例的格式）
        section_pattern_simple = r"(?:^|\n)\s*([A-Z][a-z]+)\s*\n\s*([^\n]+(?:\n(?![A-Z][a-z]+\s*\n)[^\n]+)*)"
        matches_simple = list(re.finditer(section_pattern_simple, text, re.MULTILINE | re.DOTALL))

        if len(matches_simple) >= 3:  # 如果找到至少3个章节
            # 处理每个章节
            for match in matches_simple:
                section_title = match.group(1).strip()
                section_content = match.group(2).strip()

                # 过滤掉太短的标题
                if len(section_title) < 2:
                    continue

                # 确定章节类型
                section_type = "other"
                for sec_type, pattern in self.section_patterns.items():
                    if re.search(pattern, section_title):
                        section_type = sec_type
                        break

                sections.append(PaperSection(title=section_title, content=section_content, section_type=section_type))

            return sections

        # 模式3: 标题后有分隔线或空行
        section_pattern_alt = r"(?:^|\n)\s*([A-Z][A-Za-z\s]*?)\s*\n\s*[—–-]*\s*\n"
        matches_alt = list(re.finditer(section_pattern_alt, text, re.MULTILINE))

        if matches_alt and len(matches_alt) >= 2:
            # 处理每个章节
            for i, match in enumerate(matches_alt):
                section_title = match.group(1).strip()
                # 过滤掉太短或太长的标题
                if len(section_title) < 2 or len(section_title) > 100:
                    continue

                start_pos = match.end()
                end_pos = matches_alt[i + 1].start() if i + 1 < len(matches_alt) else len(text)

                section_content = text[start_pos:end_pos].strip()

                # 确定章节类型
                section_type = "other"
                for sec_type, pattern in self.section_patterns.items():
                    if re.search(pattern, section_title):
                        section_type = sec_type
                        break

                sections.append(PaperSection(title=section_title, content=section_content, section_type=section_type))

            return sections

        # 如果仍然没有找到足够的章节，创建一个包含全文的章节
        if len(sections) == 0:
            sections.append(PaperSection(title="Full Text", content=text, section_type="full_text"))

        return sections

    def _extract_figures_info(self, text: str) -> List[Dict[str, Any]]:
        """提取图表信息"""
        figures = []

        # 改进的图表提取模式 - 支持跨行匹配
        figure_pattern = r"(?i)figure\s+(\d+)[.:]?\s*([^\n]+(?:\n(?!figure\s+\d+|table\s+\d+)[^\n]+)*)"
        matches = re.finditer(figure_pattern, text, re.MULTILINE)

        for match in matches:
            caption = match.group(2).strip()
            # 清理多余的空白字符
            caption = re.sub(r'\s+', ' ', caption)
            figures.append(
                {"figure_id": match.group(1), "caption": caption[:200], "type": "figure"}  # 限制长度
            )

        return figures

    def _extract_tables_info(self, text: str) -> List[Dict[str, Any]]:
        """提取表格信息"""
        tables = []

        # 改进的表格提取模式 - 支持跨行匹配
        table_pattern = r"(?i)table\s+(\d+)[.:]?\s*([^\n]+(?:\n(?!table\s+\d+|figure\s+\d+)[^\n]+)*)"
        matches = re.finditer(table_pattern, text, re.MULTILINE)

        for match in matches:
            caption = match.group(2).strip()
            # 清理多余的空白字符
            caption = re.sub(r'\s+', ' ', caption)
            tables.append(
                {"table_id": match.group(1), "caption": caption[:200], "type": "table"}  # 限制长度
            )

        return tables


# Create a global instance of PaperParser
_paper_parser_instance = PaperParser()


def parse_paper_tool(paper_input: str, input_type: str = "file") -> PaperContent:
    """
    使用ScholarMind论文解析器解析论文。
    支持从文件路径、URL或直接文本内容解析论文，并提取其结构化内容。

    Args:
        paper_input (str): 论文的输入，可以是文件路径、URL或论文的纯文本内容。
        input_type (str, optional): 输入的类型，可以是 "file" (文件路径), "url" (URL), 或 "text" (纯文本)。默认为 "file"。

    Returns:
        PaperContent: 包含论文元数据、章节、全文、图表和表格信息的结构化对象。
                      如果解析失败，将抛出 RuntimeError。
    """
    return _paper_parser_instance.parse_paper(paper_input, input_type)


# Create a toolkit and register the tool
paper_parser_toolkit = Toolkit()
paper_parser_toolkit.register_tool_function(parse_paper_tool)
