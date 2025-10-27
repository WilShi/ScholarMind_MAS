"""
Input Validation and Sanitization Utilities
输入验证和清理工具模块
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from ..utils.logger import setup_logger

logger = setup_logger('scholarmind.validation', level='INFO', log_file=None, console=True)


class ValidationError(Exception):
    """输入验证错误"""
    pass


class InputValidator:
    """输入验证器"""

    # 允许的文件扩展名
    ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.txt', '.md'}

    # 最大文件大小 (50MB)
    MAX_FILE_SIZE = 50 * 1024 * 1024

    # 最大文本长度
    MAX_TEXT_LENGTH = 100000

    # ArXiv ID 正则
    ARXIV_ID_PATTERN = re.compile(r'^\d{4}\.\d{4,5}(v\d+)?$')

    # DOI 正则
    DOI_PATTERN = re.compile(r'^10\.\d{4,9}/[-._;()/:A-Z0-9]+$', re.IGNORECASE)

    # 危险字符模式
    DANGEROUS_PATTERNS = [
        r'\.\./',  # 路径遍历
        r'<script',  # XSS
        r'javascript:',  # JS injection
        r'on\w+\s*=',  # Event handlers
        r'<iframe',  # iframe injection
    ]

    @staticmethod
    def validate_file_path(file_path: str) -> Tuple[bool, Optional[str]]:
        """
        验证文件路径

        Args:
            file_path: 文件路径字符串

        Returns:
            (是否有效, 错误消息)
        """
        try:
            path = Path(file_path)

            # 检查文件是否存在
            if not path.exists():
                return False, f"文件不存在: {file_path}"

            # 检查是否是文件
            if not path.is_file():
                return False, f"路径不是文件: {file_path}"

            # 检查文件扩展名
            if path.suffix.lower() not in InputValidator.ALLOWED_EXTENSIONS:
                return False, f"不支持的文件类型: {path.suffix}. 支持的类型: {', '.join(InputValidator.ALLOWED_EXTENSIONS)}"

            # 检查文件大小
            file_size = path.stat().st_size
            if file_size > InputValidator.MAX_FILE_SIZE:
                return False, f"文件过大: {file_size / (1024*1024):.2f}MB (最大 {InputValidator.MAX_FILE_SIZE / (1024*1024):.0f}MB)"

            # 检查文件是否可读
            if not path.is_file() or not path.exists():
                return False, f"文件不可读: {file_path}"

            return True, None

        except Exception as e:
            return False, f"文件路径验证失败: {str(e)}"

    @staticmethod
    def validate_url(url: str) -> Tuple[bool, Optional[str]]:
        """
        验证URL

        Args:
            url: URL字符串

        Returns:
            (是否有效, 错误消息)
        """
        try:
            parsed = urlparse(url)

            # 检查scheme
            if parsed.scheme not in ['http', 'https']:
                return False, f"不支持的URL协议: {parsed.scheme}. 仅支持 http 和 https"

            # 检查是否有host
            if not parsed.netloc:
                return False, "URL缺少主机名"

            # 检查是否是支持的域名
            supported_domains = ['arxiv.org', 'semanticscholar.org', 'doi.org']
            if not any(domain in parsed.netloc for domain in supported_domains):
                logger.warning(f"URL域名不在支持列表中: {parsed.netloc}")

            return True, None

        except Exception as e:
            return False, f"URL验证失败: {str(e)}"

    @staticmethod
    def validate_arxiv_id(arxiv_id: str) -> Tuple[bool, Optional[str]]:
        """
        验证ArXiv ID

        Args:
            arxiv_id: ArXiv ID字符串

        Returns:
            (是否有效, 错误消息)
        """
        # 清理输入
        arxiv_id = arxiv_id.strip()

        # 从URL中提取ID
        if 'arxiv.org' in arxiv_id:
            match = re.search(r'(\d{4}\.\d{4,5}(?:v\d+)?)', arxiv_id)
            if match:
                arxiv_id = match.group(1)
            else:
                return False, "无法从URL中提取ArXiv ID"

        # 验证格式
        if not InputValidator.ARXIV_ID_PATTERN.match(arxiv_id):
            return False, f"无效的ArXiv ID格式: {arxiv_id}. 期望格式: YYMM.NNNNN"

        return True, None

    @staticmethod
    def validate_text(text: str) -> Tuple[bool, Optional[str]]:
        """
        验证文本输入

        Args:
            text: 文本字符串

        Returns:
            (是否有效, 错误消息)
        """
        if not text or not text.strip():
            return False, "文本不能为空"

        if len(text) > InputValidator.MAX_TEXT_LENGTH:
            return False, f"文本过长: {len(text)} 字符 (最大 {InputValidator.MAX_TEXT_LENGTH} 字符)"

        return True, None

    @staticmethod
    def sanitize_text(text: str) -> str:
        """
        清理文本输入，移除危险字符

        Args:
            text: 原始文本

        Returns:
            清理后的文本
        """
        # 移除危险模式
        cleaned_text = text
        for pattern in InputValidator.DANGEROUS_PATTERNS:
            cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE)

        # 移除非打印字符（保留常见空白字符）
        cleaned_text = re.sub(r'[^\x20-\x7E\n\r\t\u4e00-\u9fff]', '', cleaned_text)

        return cleaned_text.strip()

    @staticmethod
    def validate_user_background(background: str) -> Tuple[bool, Optional[str]]:
        """
        验证用户背景级别

        Args:
            background: 背景级别字符串

        Returns:
            (是否有效, 错误消息)
        """
        valid_backgrounds = ['beginner', 'intermediate', 'advanced']

        if background.lower() not in valid_backgrounds:
            return False, f"无效的用户背景: {background}. 有效值: {', '.join(valid_backgrounds)}"

        return True, None

    @staticmethod
    def validate_language(language: str) -> Tuple[bool, Optional[str]]:
        """
        验证语言设置

        Args:
            language: 语言代码

        Returns:
            (是否有效, 错误消息)
        """
        valid_languages = ['zh', 'en']

        if language.lower() not in valid_languages:
            return False, f"不支持的语言: {language}. 有效值: {', '.join(valid_languages)}"

        return True, None

    @classmethod
    def validate_paper_input(cls, paper_input: str, input_type: str) -> Tuple[bool, Optional[str], str]:
        """
        综合验证论文输入

        Args:
            paper_input: 论文输入字符串
            input_type: 输入类型 (file, url, text, arxiv)

        Returns:
            (是否有效, 错误消息, 规范化后的输入)
        """
        # 清理输入
        paper_input = paper_input.strip()

        if input_type == 'file':
            is_valid, error = cls.validate_file_path(paper_input)
            return is_valid, error, paper_input

        elif input_type == 'url':
            is_valid, error = cls.validate_url(paper_input)
            return is_valid, error, paper_input

        elif input_type == 'arxiv':
            is_valid, error = cls.validate_arxiv_id(paper_input)
            # 规范化ArXiv ID
            if is_valid:
                if 'arxiv.org' in paper_input:
                    match = re.search(r'(\d{4}\.\d{4,5}(?:v\d+)?)', paper_input)
                    paper_input = match.group(1) if match else paper_input
            return is_valid, error, paper_input

        elif input_type == 'text':
            is_valid, error = cls.validate_text(paper_input)
            # 清理文本
            cleaned_text = cls.sanitize_text(paper_input)
            return is_valid, error, cleaned_text

        else:
            return False, f"未知的输入类型: {input_type}", paper_input


def validate_pipeline_inputs(
    paper_input: str,
    input_type: str,
    user_background: str = "intermediate",
    output_language: str = "zh"
) -> Dict[str, Any]:
    """
    验证Pipeline输入参数

    Args:
        paper_input: 论文输入
        input_type: 输入类型
        user_background: 用户背景
        output_language: 输出语言

    Returns:
        验证结果字典，包含 success, errors, cleaned_inputs
    """
    errors = []
    validator = InputValidator()

    # 验证论文输入
    is_valid, error, cleaned_input = validator.validate_paper_input(paper_input, input_type)
    if not is_valid:
        errors.append(f"论文输入验证失败: {error}")

    # 验证用户背景
    is_valid, error = validator.validate_user_background(user_background)
    if not is_valid:
        errors.append(f"用户背景验证失败: {error}")

    # 验证输出语言
    is_valid, error = validator.validate_language(output_language)
    if not is_valid:
        errors.append(f"输出语言验证失败: {error}")

    return {
        "success": len(errors) == 0,
        "errors": errors,
        "cleaned_inputs": {
            "paper_input": cleaned_input,
            "input_type": input_type,
            "user_background": user_background.lower(),
            "output_language": output_language.lower()
        }
    }
