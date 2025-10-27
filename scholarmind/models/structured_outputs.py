"""
ScholarMind Structured Output Models
智读ScholarMind结构化输出模型
"""

from typing import Any, Dict, Generic, List, Optional, TypeVar
from enum import Enum

from pydantic import BaseModel, Field


class PaperMetadata(BaseModel):
    """论文元数据"""

    title: str = Field(description="论文标题")
    authors: List[str] = Field(default_factory=list, description="作者列表")
    abstract: str = Field(default="", description="摘要")
    publication_year: Optional[int] = Field(default=None, description="发表年份")
    venue: Optional[str] = Field(default=None, description="发表场所")
    doi: Optional[str] = Field(default=None, description="DOI标识符")
    arxiv_id: Optional[str] = Field(default=None, description="ArXiv ID")
    keywords: List[str] = Field(default_factory=list, description="关键词")
    references: List[str] = Field(default_factory=list, description="参考文献")


class PaperSection(BaseModel):
    """论文章节"""

    title: str = Field(description="章节标题")
    content: str = Field(description="章节内容")
    section_type: str = Field(description="章节类型：introduction, methodology, experiment, conclusion, etc.")


class PaperContent(BaseModel):
    """论文内容结构化表示"""

    metadata: PaperMetadata = Field(description="论文元数据")
    sections: List[PaperSection] = Field(description="论文章节")
    full_text: str = Field(description="完整文本")
    figures: List[Dict[str, Any]] = Field(default_factory=list, description="图表信息")
    tables: List[Dict[str, Any]] = Field(default_factory=list, description="表格信息")


class ResourceRetrievalOutput(BaseModel):
    """资源检索智能体输出"""

    paper_content: Optional[PaperContent] = None
    external_info: Dict[str, Any] = Field(default_factory=dict)
    processing_info: Dict[str, Any] = Field(default_factory=dict)
    success: bool = False
    error_message: Optional[str] = None


class MethodologyAnalysis(BaseModel):
    """方法论解析智能体输出"""

    architecture_analysis: str = Field(description="模型架构分析")
    algorithm_flow: str = Field(description="算法流程解释")
    innovation_points: List[str] = Field(default_factory=list, description="核心创新点")
    related_work_comparison: str = Field(description="相关工作对比")
    technical_details: str = Field(description="技术细节说明")
    complexity_analysis: Optional[str] = Field(default=None, description="复杂度分析")
    mathematical_formulation: Optional[str] = Field(default=None, description="数学公式说明")
    processing_time: float = Field(description="处理时间（秒）")
    success: bool = Field(description="处理是否成功")
    error_message: Optional[str] = Field(default=None, description="错误信息")


class ExperimentEvaluation(BaseModel):
    """实验评估智能体输出"""

    experimental_setup: str = Field(description="实验设置描述")
    baseline_comparison: str = Field(description="基线对比分析")
    key_metrics: List[Dict[str, Any]] = Field(default_factory=list, description="关键指标和结果")
    validity_assessment: str = Field(description="实验有效性评估")
    results_analysis: str = Field(description="结果详细分析")
    limitations: List[str] = Field(default_factory=list, description="实验局限性")
    statistical_significance: Optional[str] = Field(default=None, description="统计显著性分析")
    processing_time: float = Field(description="处理时间（秒）")
    success: bool = Field(description="处理是否成功")
    error_message: Optional[str] = Field(default=None, description="错误信息")


class InsightAnalysis(BaseModel):
    """洞察生成智能体输出"""

    logical_flow: str = Field(description="论文整体逻辑链分析")
    strengths: List[str] = Field(default_factory=list, description="论文优点")
    weaknesses: List[str] = Field(default_factory=list, description="论文缺点和局限性")
    critical_insights: List[str] = Field(default_factory=list, description="批判性洞察")
    future_directions: List[str] = Field(default_factory=list, description="未来研究方向建议")
    novelty_assessment: str = Field(description="创新性评估")
    impact_analysis: str = Field(description="潜在影响分析")
    research_questions: Optional[List[str]] = Field(default=None, description="衍生研究问题")
    processing_time: float = Field(description="处理时间（秒）")
    success: bool = Field(description="处理是否成功")
    error_message: Optional[str] = Field(default=None, description="错误信息")


class ReportSection(BaseModel):
    """报告章节"""

    title: str = Field(description="章节标题")
    content: str = Field(description="章节内容")
    importance_score: float = Field(description="重要性评分 0-1")


class SynthesizerOutput(BaseModel):
    """综合报告智能体输出"""

    title: str = Field(description="报告标题")
    summary: str = Field(description="论文摘要")
    key_contributions: List[str] = Field(description="主要贡献")
    methodology_summary: str = Field(description="方法论概述")
    experiment_summary: str = Field(description="实验概述")
    insights: List[str] = Field(description="洞察和观点")
    sections: List[ReportSection] = Field(description="详细章节")
    user_background_adaptation: str = Field(description="用户背景适配说明")
    processing_time: float = Field(description="处理时间（秒）")
    success: bool = Field(description="处理是否成功")
    error_message: Optional[str] = Field(description="错误信息")


# ==================== 统一 API 响应模型 ====================

class ResponseStatus(str, Enum):
    """响应状态枚举"""
    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"  # 部分成功


DataT = TypeVar("DataT")


class APIResponse(BaseModel, Generic[DataT]):
    """
    统一的 API 响应模型

    使用泛型支持不同类型的数据

    示例:
        >>> response = APIResponse[MethodologyAnalysis](
        ...     status=ResponseStatus.SUCCESS,
        ...     data=methodology_result,
        ...     message="方法论分析完成"
        ... )
    """
    status: ResponseStatus = Field(description="响应状态")
    data: Optional[DataT] = Field(default=None, description="响应数据")
    message: Optional[str] = Field(default=None, description="响应消息")
    error: Optional[str] = Field(default=None, description="错误信息")
    error_code: Optional[str] = Field(default=None, description="错误代码")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据")

    class Config:
        use_enum_values = True


class ErrorDetail(BaseModel):
    """错误详情模型"""
    code: str = Field(description="错误代码")
    message: str = Field(description="错误消息")
    field: Optional[str] = Field(default=None, description="相关字段")
    details: Optional[Dict[str, Any]] = Field(default=None, description="额外详情")


class PaginationMetadata(BaseModel):
    """分页元数据"""
    page: int = Field(description="当前页码", ge=1)
    page_size: int = Field(description="每页大小", ge=1, le=100)
    total_items: int = Field(description="总项目数", ge=0)
    total_pages: int = Field(description="总页数", ge=0)


class PaginatedResponse(BaseModel, Generic[DataT]):
    """分页响应模型"""
    status: ResponseStatus = Field(description="响应状态")
    data: List[DataT] = Field(default_factory=list, description="数据列表")
    pagination: PaginationMetadata = Field(description="分页信息")
    message: Optional[str] = Field(default=None, description="响应消息")


# ==================== 便捷构造函数 ====================

def success_response(
    data: Any = None,
    message: str = "操作成功",
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    创建成功响应

    Args:
        data: 响应数据
        message: 成功消息
        metadata: 额外元数据

    Returns:
        标准化的成功响应字典
    """
    return {
        "status": ResponseStatus.SUCCESS,
        "data": data,
        "message": message,
        "error": None,
        "error_code": None,
        "metadata": metadata or {}
    }


def error_response(
    error: str,
    error_code: Optional[str] = None,
    message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    创建错误响应

    Args:
        error: 错误信息
        error_code: 错误代码
        message: 错误消息
        metadata: 额外元数据

    Returns:
        标准化的错误响应字典
    """
    return {
        "status": ResponseStatus.ERROR,
        "data": None,
        "message": message or "操作失败",
        "error": error,
        "error_code": error_code,
        "metadata": metadata or {}
    }


def partial_response(
    data: Any = None,
    message: str = "部分成功",
    error: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    创建部分成功响应

    Args:
        data: 响应数据（可能不完整）
        message: 响应消息
        error: 错误信息（说明哪些部分失败）
        metadata: 额外元数据

    Returns:
        标准化的部分成功响应字典
    """
    return {
        "status": ResponseStatus.PARTIAL,
        "data": data,
        "message": message,
        "error": error,
        "error_code": None,
        "metadata": metadata or {}
    }
