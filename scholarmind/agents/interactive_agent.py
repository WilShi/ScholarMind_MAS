"""
Interactive Agent for ScholarMind
智读ScholarMind交互式智能体
"""

from typing import Dict, Any, Optional
import re

from agentscope.agent import AgentBase, UserAgent
from agentscope.message import Msg

from config import get_model_config


class InteractiveScholarAgent(AgentBase):
    """交互式论文助手智能体（简化版本，不使用 LLM）"""

    def __init__(self, **kwargs: Any) -> None:
        """初始化交互式智能体"""
        super().__init__()
        self.name = "ScholarMind助手"
        self.user_agent = UserAgent(name="User")

    async def run_interactive_session(self, pipeline):
        """
        运行交互式会话

        Args:
            pipeline: ScholarMind处理流水线
        """
        # 导入搜索工具
        from scholarmind.tools.academic_search import academic_search_by_title_tool

        # 欢迎消息
        welcome_msg = """╔═══════════════════════════════════════════════════════════╗
║                  ScholarMind 智能论文助手                    ║
╚═══════════════════════════════════════════════════════════╝

您好！我是 ScholarMind 论文解读助手。

我可以帮您：
📚 搜索 ArXiv 论文（输入论文名称或关键词）
🔗 分析论文链接（输入 ArXiv URL 或 ID）
📄 分析本地论文（输入 PDF 文件路径）

请告诉我您想分析哪篇论文？（输入 'exit' 或 'quit' 退出）"""

        await self.print(Msg(
            name=self.name,
            content=welcome_msg,
            role="assistant"
        ))

        while True:
            # 获取用户输入
            user_msg = await self.user_agent()
            user_input = user_msg.content.strip()

            # 退出命令
            if user_input.lower() in ['exit', 'quit', '退出', 'q']:
                await self.print(Msg(
                    name=self.name,
                    content="\n感谢使用 ScholarMind！再见！",
                    role="assistant"
                ))
                break

            if not user_input:
                await self.print(Msg(
                    name=self.name,
                    content="请输入论文名称、链接或文件路径。",
                    role="assistant"
                ))
                continue

            try:
                # 分析用户输入类型
                paper_info = self._analyze_input(user_input)

                if paper_info['type'] == 'search':
                    # 需要搜索论文
                    await self.print(Msg(
                        name=self.name,
                        content=f"\n正在 ArXiv 搜索 \"{user_input}\"...\n",
                        role="assistant"
                    ))

                    search_results = academic_search_by_title_tool(user_input)

                    # 检查是否找到结果
                    if search_results.get('arxiv') and search_results['arxiv'].get('total_results', 0) > 0:
                        # 获取所有论文
                        papers = search_results['arxiv'].get('papers', [])
                        total = len(papers)

                        # 显示所有搜索结果
                        result_text = f"找到 {total} 篇相关论文：\n"
                        for i, paper_data in enumerate(papers, 1):
                            result_text += f"\n【{i}】{paper_data['title']}\n"
                            result_text += f"    作者: {', '.join(paper_data['authors'][:3])}"
                            if len(paper_data['authors']) > 3:
                                result_text += f" 等 {len(paper_data['authors'])} 位作者"
                            result_text += f"\n    发表: {paper_data.get('published', 'N/A')}"
                            result_text += f"\n    ArXiv ID: {paper_data['arxiv_id']}"
                            result_text += f"\n    分类: {paper_data.get('primary_category', 'N/A')}"
                            result_text += f"\n    摘要: {paper_data['abstract'][:150]}..."
                            result_text += "\n"

                        await self.print(Msg(
                            name=self.name,
                            content=result_text,
                            role="assistant"
                        ))

                        # 让用户选择
                        await self.print(Msg(
                            name=self.name,
                            content=f"\n请选择要分析的论文（输入序号 1-{total}，或输入 'cancel' 取消）：",
                            role="assistant"
                        ))
                        choice_msg = await self.user_agent()
                        choice = choice_msg.content.strip()

                        # 检查是否取消
                        if choice.lower() in ['cancel', '取消', 'c', 'n', 'no']:
                            await self.print(Msg(
                                name=self.name,
                                content="已取消。请继续输入其他论文。\n",
                                role="assistant"
                            ))
                            continue

                        # 验证用户选择
                        try:
                            choice_idx = int(choice) - 1
                            if 0 <= choice_idx < total:
                                selected_paper = papers[choice_idx]
                                # 使用选中的论文
                                paper_info = {
                                    'input': selected_paper['pdf_url'],
                                    'input_type': 'url',
                                    'title': selected_paper['title']
                                }
                                await self._process_paper(paper_info, pipeline)
                            else:
                                await self.print(Msg(
                                    name=self.name,
                                    content=f"无效的选择。请输入 1-{total} 之间的数字。\n",
                                    role="assistant"
                                ))
                        except ValueError:
                            await self.print(Msg(
                                name=self.name,
                                content="无效的输入。请输入数字或 'cancel'。\n",
                                role="assistant"
                            ))
                    else:
                        not_found_text = """未找到相关论文。请尝试：
  - 使用更精确的论文标题
  - 提供 ArXiv URL 或 ID
  - 提供本地 PDF 文件路径"""

                        await self.print(Msg(
                            name=self.name,
                            content=not_found_text,
                            role="assistant"
                        ))

                elif paper_info['type'] == 'direct':
                    # 直接处理（URL 或文件路径）
                    await self._process_paper(paper_info, pipeline)

            except Exception as e:
                await self.print(Msg(
                    name=self.name,
                    content=f"\n❌ 处理时出错: {str(e)}\n请重试或提供其他论文。\n",
                    role="assistant"
                ))

    def _analyze_input(self, user_input: str) -> Dict[str, Any]:
        """
        分析用户输入类型

        Args:
            user_input: 用户输入

        Returns:
            论文信息字典 {'type': 'search'|'direct', 'input': ..., 'input_type': ..., 'title': ...}
        """
        # 去除首尾的单引号或双引号（用户可能在终端输入带引号的路径）
        user_input = user_input.strip().strip("'\"")

        # 1. 检查是否是本地文件路径
        if user_input.endswith('.pdf') or ('/' in user_input and not user_input.startswith('http')):
            return {
                'type': 'direct',
                'input': user_input,
                'input_type': 'file',
                'title': user_input.split('/')[-1]
            }

        # 2. 检查是否是 ArXiv URL
        if 'arxiv.org' in user_input.lower():
            # 提取 ArXiv ID
            arxiv_id_match = re.search(r'(\d+\.\d+)', user_input)
            if arxiv_id_match:
                arxiv_id = arxiv_id_match.group(1)
                return {
                    'type': 'direct',
                    'input': f'https://arxiv.org/pdf/{arxiv_id}.pdf',
                    'input_type': 'url',
                    'arxiv_id': arxiv_id,
                    'title': f'ArXiv:{arxiv_id}'
                }

        # 3. 检查是否是纯 ArXiv ID (如 1706.03762)
        arxiv_id_match = re.match(r'^\d{4}\.\d{4,5}$', user_input)
        if arxiv_id_match:
            arxiv_id = user_input
            return {
                'type': 'direct',
                'input': f'https://arxiv.org/pdf/{arxiv_id}.pdf',
                'input_type': 'url',
                'arxiv_id': arxiv_id,
                'title': f'ArXiv:{arxiv_id}'
            }

        # 4. 其他情况，当作论文标题/关键词搜索
        return {
            'type': 'search',
            'input': user_input
        }

    async def _process_paper(self, paper_info: Dict[str, Any], pipeline):
        """
        处理论文

        Args:
            paper_info: 论文信息
            pipeline: 处理流水线
        """
        try:
            # 定义进度回调函数
            async def progress_callback(message: str):
                """进度回调函数，用于显示处理进度"""
                await self.print(Msg(
                    name=self.name,
                    content=message,
                    role="assistant"
                ))

            # 使用默认配置，并传入进度回调
            result = await pipeline.process_paper(
                paper_input=paper_info['input'],
                input_type=paper_info.get('input_type', 'url'),
                user_background='intermediate',
                save_report=True,
                output_format='markdown',
                output_language='zh',
                progress_callback=progress_callback  # 传入回调函数
            )

            # 显示结果
            if result and result.get("success"):
                report = result["outputs"]["report"]

                success_text = f"""
{"="*60}
📄 分析完成！
{"="*60}

标题: {report['title']}

摘要:
{report['summary']}"""

                if report.get('key_contributions'):
                    success_text += "\n\n主要贡献:"
                    for i, contribution in enumerate(report['key_contributions'], 1):
                        success_text += f"\n  {i}. {contribution}"

                if report.get('insights'):
                    success_text += "\n\n关键洞察:"
                    for i, insight in enumerate(report['insights'], 1):
                        success_text += f"\n  {i}. {insight}"

                if result["outputs"].get("report_path"):
                    success_text += f"\n\n报告已保存至: {result['outputs']['report_path']}"

                success_text += f"\n\n总耗时: {result['processing_time']:.2f} 秒"
                success_text += f"\n{"="*60}\n"

                await self.print(Msg(
                    name=self.name,
                    content=success_text,
                    role="assistant"
                ))
            else:
                await self.print(Msg(
                    name=self.name,
                    content=f"\n❌ 分析失败: {result.get('error', '未知错误')}\n",
                    role="assistant"
                ))

        except Exception as e:
            await self.print(Msg(
                name=self.name,
                content=f"\n❌ 处理论文时出错: {str(e)}\n",
                role="assistant"
            ))
