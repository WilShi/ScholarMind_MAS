"""
ScholarMind Academic Search
智读ScholarMind学术搜索工具
"""

import time
from typing import Any, Dict, Optional

import arxiv
import requests
from agentscope.tool import Toolkit
from scholarly import scholarly

from config import AcademicAPIConfig

from ..utils.logger import tool_logger


class AcademicSearcher:
    """学术搜索器"""

    def __init__(self):
        self.semantic_scholar_api_key = AcademicAPIConfig.SEMANTIC_SCHOLAR_API_KEY
        self.semantic_scholar_base_url = AcademicAPIConfig.SEMANTIC_SCHOLAR_BASE_URL
        self.arxiv_base_url = AcademicAPIConfig.ARXIV_BASE_URL

        # 请求限制
        self.request_delay = 1.0  # 秒
        self.max_retries = 3

    def search_paper_by_title(self, title: str) -> Dict[str, Any]:
        """根据标题搜索论文"""
        results = {}

        # Semantic Scholar搜索
        try:
            semantic_results = self._search_semantic_scholar(title)
            results["semantic_scholar"] = semantic_results
        except Exception as e:
            tool_logger.warning(f"Semantic Scholar search failed: {e}")
            results["semantic_scholar"] = {}

        # ArXiv搜索
        try:
            arxiv_results = self._search_arxiv(title)
            results["arxiv"] = arxiv_results
        except Exception as e:
            tool_logger.warning(f"ArXiv search failed: {e}")
            results["arxiv"] = {}

        # Google Scholar搜索
        try:
            scholar_results = self._search_google_scholar(title)
            results["google_scholar"] = scholar_results
        except Exception as e:
            tool_logger.warning(f"Google Scholar search failed: {e}")
            results["google_scholar"] = {}

        return results

    def search_paper_by_doi(self, doi: str) -> Dict[str, Any]:
        """根据DOI搜索论文"""
        results = {}

        # Semantic Scholar DOI查找
        try:
            semantic_results = self._lookup_doi_semantic_scholar(doi)
            results["semantic_scholar"] = semantic_results
        except Exception as e:
            tool_logger.warning(f"Semantic Scholar DOI lookup failed: {e}")
            results["semantic_scholar"] = {}

        return results

    def search_paper_by_arxiv_id(self, arxiv_id: str) -> Dict[str, Any]:
        """根据ArXiv ID搜索论文"""
        results = {}

        try:
            arxiv_results = self._get_arxiv_paper(arxiv_id)
            results["arxiv"] = arxiv_results
        except Exception as e:
            tool_logger.warning(f"ArXiv paper lookup failed: {e}")
            results["arxiv"] = {}

        return results

    def get_citation_info(self, paper_id: str, source: str = "semantic_scholar") -> Dict[str, Any]:
        """获取引用信息"""
        if source == "semantic_scholar":
            return self._get_citations_semantic_scholar(paper_id)
        else:
            return {}

    def get_reference_info(self, paper_id: str, source: str = "semantic_scholar") -> Dict[str, Any]:
        """获取参考文献信息"""
        if source == "semantic_scholar":
            return self._get_references_semantic_scholar(paper_id)
        else:
            return {}

    def _search_semantic_scholar(self, title: str) -> Dict[str, Any]:
        """Semantic Scholar搜索"""
        url = f"{self.semantic_scholar_base_url}/paper/search"
        params = {
            "query": title,
            "limit": 5,
            "fields": "title,authors,abstract,year,venue,citationCount,externalIds,url",
        }

        headers = {}
        if self.semantic_scholar_api_key:
            headers["x-api-key"] = self.semantic_scholar_api_key

        response = self._make_request(url, params=params, headers=headers)

        if response and "data" in response:
            papers = response["data"]
            if papers:
                # 返回第一个最匹配的结果
                return {
                    "paper": papers[0],
                    "total_results": len(papers),
                    "source": "semantic_scholar",
                }

        return {}

    def _lookup_doi_semantic_scholar(self, doi: str) -> Dict[str, Any]:
        """Semantic Scholar DOI查找"""
        url = f"{self.semantic_scholar_base_url}/paper/DOI:{doi}"
        params = {
            "fields": "title,authors,abstract,year,venue,citationCount,externalIds,url,references,citations"
        }

        headers = {}
        if self.semantic_scholar_api_key:
            headers["x-api-key"] = self.semantic_scholar_api_key

        response = self._make_request(url, params=params, headers=headers)

        if response:
            return {"paper": response, "source": "semantic_scholar"}

        return {}

    def _get_citations_semantic_scholar(self, paper_id: str) -> Dict[str, Any]:
        """获取Semantic Scholar引用信息"""
        url = f"{self.semantic_scholar_base_url}/paper/{paper_id}/citations"
        params = {"limit": 20, "fields": "title,authors,year,venue,citationCount"}

        headers = {}
        if self.semantic_scholar_api_key:
            headers["x-api-key"] = self.semantic_scholar_api_key

        response = self._make_request(url, params=params, headers=headers)

        if response and "data" in response:
            return {
                "citations": response["data"],
                "total_citations": len(response["data"]),
                "source": "semantic_scholar",
            }

        return {}

    def _get_references_semantic_scholar(self, paper_id: str) -> Dict[str, Any]:
        """获取Semantic Scholar参考文献信息"""
        url = f"{self.semantic_scholar_base_url}/paper/{paper_id}/references"
        params = {"limit": 20, "fields": "title,authors,year,venue,citationCount"}

        headers = {}
        if self.semantic_scholar_api_key:
            headers["x-api-key"] = self.semantic_scholar_api_key

        response = self._make_request(url, params=params, headers=headers)

        if response and "data" in response:
            return {
                "references": response["data"],
                "total_references": len(response["data"]),
                "source": "semantic_scholar",
            }

        return {}

    def _search_arxiv(self, title: str) -> Dict[str, Any]:
        """ArXiv搜索"""
        try:
            search = arxiv.Search(query=title, max_results=5, sort_by=arxiv.SortCriterion.Relevance)

            papers = list(search.results())

            if papers:
                # 转换所有结果
                paper_list = []
                for paper in papers:
                    paper_list.append(
                        {
                            "title": paper.title,
                            "authors": [author.name for author in paper.authors],
                            "abstract": paper.summary,
                            "published": (
                                paper.published.strftime("%Y-%m-%d") if paper.published else None
                            ),
                            "arxiv_id": paper.get_short_id(),
                            "pdf_url": paper.pdf_url,
                            "primary_category": paper.primary_category,
                        }
                    )

                return {
                    "papers": paper_list,  # 返回所有论文列表
                    "paper": paper_list[0],  # 保持向后兼容，同时提供第一篇
                    "total_results": len(papers),
                    "source": "arxiv",
                }

        except Exception as e:
            tool_logger.warning(f"ArXiv search error: {e}")

        return {}

    def _get_arxiv_paper(self, arxiv_id: str) -> Dict[str, Any]:
        """获取ArXiv论文信息"""
        try:
            search = arxiv.Search(id_list=[arxiv_id])
            paper = next(search.results())

            return {
                "paper": {
                    "title": paper.title,
                    "authors": [author.name for author in paper.authors],
                    "abstract": paper.summary,
                    "published": paper.published.strftime("%Y-%m-%d") if paper.published else None,
                    "arxiv_id": paper.get_short_id(),
                    "pdf_url": paper.pdf_url,
                    "primary_category": paper.primary_category,
                    "categories": paper.categories,
                },
                "source": "arxiv",
            }

        except Exception as e:
            tool_logger.warning(f"ArXiv paper lookup error: {e}")

        return {}

    def _search_google_scholar(self, title: str) -> Dict[str, Any]:
        """Google Scholar搜索"""
        try:
            search_query = scholarly.search_pubs(title)
            papers = []

            for i, paper in enumerate(search_query):
                if i >= 5:  # 限制结果数量
                    break

                papers.append(
                    {
                        "title": paper.get("bib", {}).get("title", ""),
                        "authors": paper.get("bib", {}).get("author", []),
                        "abstract": paper.get("bib", {}).get("abstract", ""),
                        "year": paper.get("bib", {}).get("pub_year", ""),
                        "venue": paper.get("bib", {}).get("venue", ""),
                        "url": paper.get("pub_url", ""),
                        "citation_count": paper.get("num_citations", 0),
                    }
                )

            if papers:
                return {"papers": papers, "total_results": len(papers), "source": "google_scholar"}

        except Exception as e:
            tool_logger.warning(f"Google Scholar search error: {e}")

        return {}

    def _make_request(self, url: str, params: Dict = None, headers: Dict = None) -> Optional[Dict]:
        """发送HTTP请求"""
        for attempt in range(self.max_retries):
            try:
                response = requests.get(url, params=params, headers=headers, timeout=10)
                response.raise_for_status()

                # 添加延迟以避免请求过于频繁
                time.sleep(self.request_delay)

                return response.json()

            except requests.exceptions.RequestException as e:
                tool_logger.debug(f"Request attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2**attempt)  # 指数退避
                else:
                    raise

        return None

    def extract_paper_metrics(self, search_results: Dict[str, Any]) -> Dict[str, Any]:
        """提取论文指标"""
        metrics = {
            "citation_count": 0,
            "reference_count": 0,
            "venue_impact": None,
            "author_h_index": None,
            "publication_age_years": None,
        }

        # 从Semantic Scholar获取引用数
        if "semantic_scholar" in search_results:
            ss_data = search_results["semantic_scholar"]
            if "paper" in ss_data:
                paper = ss_data["paper"]
                metrics["citation_count"] = paper.get("citationCount", 0)

                # 计算发表年限
                if paper.get("year"):
                    import datetime

                    current_year = datetime.datetime.now().year
                    metrics["publication_age_years"] = current_year - paper["year"]

                # 获取参考文献数量
                if "references" in ss_data:
                    metrics["reference_count"] = len(ss_data["references"])

        # 从Google Scholar获取引用数
        if "google_scholar" in search_results:
            gs_data = search_results["google_scholar"]
            if "papers" in gs_data and gs_data["papers"]:
                # 取最高引用数
                max_citations = max(paper.get("citation_count", 0) for paper in gs_data["papers"])
                metrics["citation_count"] = max(metrics["citation_count"], max_citations)

        return metrics


# Create a global instance of AcademicSearcher
_academic_searcher_instance = AcademicSearcher()


def academic_search_by_title_tool(title: str) -> Dict[str, Any]:
    """根据论文标题在多个学术数据库中进行搜索。"""
    return _academic_searcher_instance.search_paper_by_title(title)


def academic_search_by_doi_tool(doi: str) -> Dict[str, Any]:
    """根据论文的DOI进行搜索。"""
    return _academic_searcher_instance.search_paper_by_doi(doi)


def academic_search_by_arxiv_id_tool(arxiv_id: str) -> Dict[str, Any]:
    """根据论文的ArXiv ID进行搜索。"""
    return _academic_searcher_instance.search_paper_by_arxiv_id(arxiv_id)


def academic_get_citation_info_tool(
    paper_id: str, source: str = "semantic_scholar"
) -> Dict[str, Any]:
    """获取给定论文ID的引用信息。"""
    return _academic_searcher_instance.get_citation_info(paper_id, source)


def academic_get_reference_info_tool(
    paper_id: str, source: str = "semantic_scholar"
) -> Dict[str, Any]:
    """获取给定论文ID的参考文献信息。"""
    return _academic_searcher_instance.get_reference_info(paper_id, source)


# Create a toolkit and register all academic search tools
academic_search_toolkit = Toolkit()
academic_search_toolkit.register_tool_function(academic_search_by_title_tool)
academic_search_toolkit.register_tool_function(academic_search_by_doi_tool)
academic_search_toolkit.register_tool_function(academic_search_by_arxiv_id_tool)
academic_search_toolkit.register_tool_function(academic_get_citation_info_tool)
academic_search_toolkit.register_tool_function(academic_get_reference_info_tool)
