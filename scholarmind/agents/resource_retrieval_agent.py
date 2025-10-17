import json
import time

from agentscope.agent import ReActAgent
from agentscope.formatter import OpenAIChatFormatter
from agentscope.message import Msg
from agentscope.tool import Toolkit

from config import get_model_config
from ..utils.logger import agent_logger

from ..tools.academic_search import (
    _academic_searcher_instance,
    academic_get_citation_info_tool,
    academic_get_reference_info_tool,
    academic_search_by_arxiv_id_tool,
    academic_search_by_doi_tool,
    academic_search_by_title_tool,
)
from ..tools.paper_parser import parse_paper_tool


class ResourceRetrievalAgent(ReActAgent):
    def __init__(self, **kwargs):
        toolkit = Toolkit()
        toolkit.register_tool_function(parse_paper_tool)
        toolkit.register_tool_function(academic_search_by_title_tool)
        toolkit.register_tool_function(academic_search_by_doi_tool)
        toolkit.register_tool_function(academic_search_by_arxiv_id_tool)
        toolkit.register_tool_function(academic_get_citation_info_tool)
        toolkit.register_tool_function(academic_get_reference_info_tool)

        super().__init__(
            name="resource_retrieval_agent",
            sys_prompt=(
                "You are a helpful assistant specialized in retrieving academic paper "
                "resources. Parse papers, search academic databases for relevant "
                "information, and extract useful metadata."
            ),
            model=get_model_config(),
            formatter=OpenAIChatFormatter(),
            toolkit=toolkit,
            **kwargs,
        )

    async def reply(self, msg: Msg) -> Msg:
        """
        处理输入消息并返回结果
        """
        try:
            agent_logger.debug(f"调试: reply方法开始，msg类型: {type(msg)}")
            agent_logger.debug(f"调试: msg内容: {msg}")
            # 解析输入数据 - 支持字典或JSON字符串以保证兼容性
            if isinstance(msg.content, dict):
                input_data = msg.content
            else:
                input_data = json.loads(msg.content)
            agent_logger.debug(f"调试: 解析后的输入数据: {input_data}")
            paper_input = input_data.get("paper_input", "")
            input_type = input_data.get("input_type", "file")
            agent_logger.debug(f"调试: paper_input: {paper_input}, input_type: {input_type}")

            # 执行论文解析
            start_time = time.time()
            processing_info = {"start_time": start_time, "input_type": input_type, "tools_used": []}

            # 步骤1：解析论文内容
            agent_logger.info(f"开始解析论文，输入类型: {input_type}")

            # 直接调用parse_paper_tool，避免复杂的toolkit异步调用
            from ..tools.paper_parser import parse_paper_tool

            try:
                paper_content = parse_paper_tool(paper_input, input_type)
                agent_logger.debug(f"调试: 直接调用parse_paper_tool成功, 类型: {type(paper_content)}")
            except Exception as e:
                agent_logger.debug(f"调试: parse_paper_tool调用失败: {str(e)}")
                raise

            processing_info["tools_used"].append("parse_paper_tool")
            agent_logger.info(f"论文解析完成，结果类型: {type(paper_content)}")

            # 再次检查并确保paper_content是正确的对象类型，而不是字典
            # 使用更robust的检查方式
            from ..models.structured_outputs import PaperContent

            if not isinstance(paper_content, PaperContent):
                agent_logger.debug(f"调试: paper_content不是PaperContent对象，类型: {type(paper_content)}")
                # 尝试从字典或其他格式转换
                if isinstance(paper_content, dict) or (hasattr(paper_content, '__dict__') and not hasattr(paper_content, 'metadata')):
                    agent_logger.debug(f"调试: 将paper_content转换为PaperContent对象")
                    from ..models.structured_outputs import PaperMetadata, PaperSection

                    # 如果是对象但不是dict，转换为dict
                    if not isinstance(paper_content, dict):
                        if hasattr(paper_content, 'model_dump'):
                            paper_dict = paper_content.model_dump()
                        elif hasattr(paper_content, 'dict'):
                            paper_dict = paper_content.dict()
                        elif hasattr(paper_content, '__dict__'):
                            paper_dict = paper_content.__dict__
                        else:
                            raise TypeError(f"无法转换paper_content类型: {type(paper_content)}")
                    else:
                        paper_dict = paper_content

                    # 从字典构建Paper Content对象
                    metadata_dict = paper_dict.get('metadata', {})
                    if not isinstance(metadata_dict, dict) and hasattr(metadata_dict, '__dict__'):
                        metadata_dict = metadata_dict.__dict__ if not hasattr(metadata_dict, 'model_dump') else metadata_dict.model_dump()

                    metadata = PaperMetadata(
                        title=metadata_dict.get('title', ''),
                        authors=metadata_dict.get('authors', []),
                        abstract=metadata_dict.get('abstract', ''),
                        publication_year=metadata_dict.get('publication_year'),
                        keywords=metadata_dict.get('keywords', []),
                        doi=metadata_dict.get('doi'),
                        arxiv_id=metadata_dict.get('arxiv_id'),
                        references=metadata_dict.get('references', [])
                    )

                    sections_list = []
                    for section_item in paper_dict.get('sections', []):
                        if isinstance(section_item, dict):
                            section_dict = section_item
                        elif hasattr(section_item, 'model_dump'):
                            section_dict = section_item.model_dump()
                        elif hasattr(section_item, '__dict__'):
                            section_dict = section_item.__dict__
                        else:
                            continue

                        section = PaperSection(
                            title=section_dict.get('title', ''),
                            content=section_dict.get('content', ''),
                            section_type=section_dict.get('section_type', 'other')
                        )
                        sections_list.append(section)

                    paper_content = PaperContent(
                        metadata=metadata,
                        sections=sections_list,
                        full_text=paper_dict.get('full_text', ''),
                        figures=paper_dict.get('figures', []),
                        tables=paper_dict.get('tables', [])
                    )
                    agent_logger.debug(f"调试: 转换完成，paper_content类型: {type(paper_content)}")

            if paper_content:
                agent_logger.info(f"论文标题: {paper_content.metadata.title}")
            else:
                agent_logger.warning("paper_content为None")

            # 步骤2：搜索外部学术信息（可选，如果失败不影响整体流程）
            external_info = {}
            try:
                if paper_content.metadata.title:
                    agent_logger.info(f"搜索论文外部信息: {paper_content.metadata.title}")
                    # 直接调用academic_search_by_title_tool函数
                    search_results = academic_search_by_title_tool(paper_content.metadata.title)
                    external_info["search_results"] = search_results
                    # 提取论文指标
                    external_info["metrics"] = _academic_searcher_instance.extract_paper_metrics(search_results)
                    processing_info["tools_used"].append("academic_search_by_title_tool")
                    agent_logger.info("外部信息搜索完成")
            except Exception as e:
                agent_logger.warning(f"外部信息搜索失败（跳过）: {str(e)}")
                # 外部搜索失败不影响整体流程

            # 步骤3：处理参考文献
            if paper_content.metadata.references:
                agent_logger.info("处理参考文献信息")
                # This part might need to use academic_get_reference_info_tool if references are looked up externally
                # For now, assuming it's just counting internal references
                external_info["references_count"] = len(paper_content.metadata.references)

            # 计算处理时间
            end_time = time.time()
            processing_info["end_time"] = end_time
            processing_info["processing_time"] = end_time - start_time

            # 构建输出 - 将Pydantic对象转换为字典以便JSON序列化
            result = {
                "status": "success",
                "data": {
                    "paper_content": paper_content.model_dump() if hasattr(paper_content, 'model_dump') else paper_content,
                    "external_info": external_info,
                    "processing_info": processing_info,
                },
                "message": "Resource retrieval completed successfully",
            }

            agent_logger.info(f"资源检索完成，处理时间: {processing_info['processing_time']:.2f}秒")

            # 创建响应消息 - 直接传递字典，无需JSON序列化
            response_msg = Msg(name=self.name, content=result, role="assistant")

            return response_msg

        except Exception as e:
            # 错误处理
            agent_logger.error(f"资源检索失败: {str(e)}")

            error_result = {"status": "error", "error": str(e), "data": {"success": False, "error_message": str(e)}}

            return Msg(name=self.name, content=error_result, role="assistant")

    def parse_paper(self, paper_input: str, input_type: str):
        """
        解析论文的同步方法，用于测试
        
        Args:
            paper_input: 论文输入
            input_type: 输入类型
            
        Returns:
            解析结果对象
        """
        # 创建模拟结果对象
        class ParseResult:
            def __init__(self, success=True, paper_content=None, error_message=None, processing_info=None):
                self.success = success
                self.paper_content = paper_content
                self.error_message = error_message
                self.processing_info = processing_info or {}

        try:
            # 直接导入并使用paper_parser工具
            from ..tools.paper_parser import PaperParser
            parser = PaperParser()

            if input_type == "text":
                paper_content = parser.parse_text(paper_input)
            elif input_type == "file":
                paper_content = parser.parse_file(paper_input)
            else:
                return ParseResult(success=False, error_message=f"不支持的输入类型: {input_type}")

            if paper_content:
                return ParseResult(
                    success=True,
                    paper_content=paper_content,
                    processing_info={
                        "input_type": input_type,
                        "processing_time": 0.1
                    }
                )
            else:
                return ParseResult(success=False, error_message="解析失败")

        except Exception as e:
            return ParseResult(success=False, error_message=str(e))

    def validate_input(self, paper_input: str, input_type: str) -> bool:
        """验证输入参数"""
        if not paper_input:
            return False

        if input_type not in ["file", "url", "text"]:
            return False

        if input_type == "file":
            import os

            return os.path.exists(paper_input)

        if input_type == "url":
            import re

            url_pattern = re.compile(
                r"^https?://"  # http:// or https://
                r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain...
                r"localhost|"  # localhost...
                r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
                r"(?::\d+)?"  # optional port
                r"(?:/?|[/?]\S+)$",
                re.IGNORECASE,
            )
            return url_pattern.match(paper_input) is not None

        return True

    def get_supported_formats(self) -> dict:
        """获取支持的输入格式"""
        return {
            "file_formats": [".pdf", ".docx", ".txt"],
            "url_types": ["arxiv", "direct_pdf", "webpage"],
            "text_input": ["plain_text", "markdown"],
        }
