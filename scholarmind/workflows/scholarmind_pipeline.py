"""
ScholarMind Pipeline
智读ScholarMind工作流 - 向后兼容包装器
"""

# 导入增强版本的工作流
from .scholarmind_enhanced_pipeline import (
    ScholarMindEnhancedPipeline,
)
from .scholarmind_enhanced_pipeline import create_pipeline as _create_enhanced_pipeline

# 向后兼容的别名
ScholarMindPipeline = ScholarMindEnhancedPipeline


# 向后兼容的工厂函数
def create_pipeline():
    """创建ScholarMind工作流实例（向后兼容）"""
    return _create_enhanced_pipeline()


# 导出主要类和函数
__all__ = ["ScholarMindPipeline", "create_pipeline", "ScholarMindEnhancedPipeline"]
