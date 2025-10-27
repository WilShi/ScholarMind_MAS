"""
ScholarMind Cross-Platform Chinese Path Integration Test
跨平台中文路径集成测试

测试完整的ScholarMind工作流对中文路径的支持
"""

import asyncio
import tempfile
import unittest
from pathlib import Path

from scholarmind.workflows.scholarmind_enhanced_pipeline import ScholarMindEnhancedPipeline
from scholarmind.utils.logger import ScholarMindLogger


class TestChinesePathIntegration(unittest.TestCase):
    """中文路径集成测试"""
    
    def setUp(self):
        """测试前准备"""
        self.logger = ScholarMindLogger('test.integration')
        self.temp_dir = Path(tempfile.mkdtemp())
        self.pipeline = ScholarMindEnhancedPipeline()
        
    def tearDown(self):
        """测试后清理"""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def create_test_paper_file(self, filename: str) -> Path:
        """
       创建测试论文文件
        
        Args:
            filename: 文件名（可能包含中文）
            
        Returns:
            Path: 创建的文件路径
        """
        paper_content = """# 深度学习在自然语言处理中的应用研究

## 摘要
本研究探讨了深度学习技术在自然语言处理领域的应用。我们提出了一种新的神经网络架构，在多个基准测试中取得了优异的性能表现。

## 1. 引言
自然语言处理(NLP)是人工智能领域的重要分支。近年来，深度学习技术的发展为NLP带来了新的机遇。

## 2. 相关工作
Smith等人(2020)提出了基于Transformer的模型，在机器翻译任务中取得了突破性进展。
Johnson等人(2021)研究了预训练语言模型在文本理解中的应用。

## 3. 方法
我们提出了一种新的多尺度注意力机制，结合了局部和全局上下文信息。

### 3.1 模型架构
模型包含编码器和解码器两个主要部分。编码器使用多头注意力机制，解码器采用自回归生成方式。

### 3.2 训练策略
我们使用了预训练+微调的两阶段训练策略。首先在大规模无标注数据上进行预训练，然后在特定任务数据上进行微调。

## 4. 实验
我们在GLUE、SuperGLUE等多个基准数据集上进行了实验。

### 4.1 实验设置
- 学习率：1e-4
- 批次大小：32
- 训练轮数：10

### 4.2 实验结果
我们的模型在GLUE基准测试上达到了89.5%的平均准确率，超过了之前的最佳结果。

## 5. 结论
本研究提出的深度学习模型在自然语言处理任务中表现出色。未来的工作将探索模型的可解释性和效率优化。

## 参考文献
1. Smith, J., et al. (2020). "Transformer-based Models for Machine Translation."
2. Johnson, M., et al. (2021). "Pre-trained Language Models for Text Understanding."
"""
        
        file_path = self.temp_dir / filename
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(paper_content)
            self.logger.info_path("创建测试论文", file_path, "成功")
            return file_path
        except Exception as e:
            self.logger.error_path("创建测试论文失败", file_path, str(e))
            raise
    
    async def test_chinese_filename_workflow(self):
        """测试中文文件名的完整工作流"""
        chinese_filename = "深度学习研究论文.txt"
        file_path = self.create_test_paper_file(chinese_filename)
        
        try:
            # 测试输入验证
            validation_result = self.pipeline.validate_inputs(
                str(file_path), "file", "intermediate"
            )
            self.assertTrue(validation_result["valid"], f"输入验证失败: {validation_result['errors']}")
            self.logger.info_path("输入验证", file_path, "通过")
            
            # 测试资源检索阶段
            resource_result = await self.pipeline._process_resource_retrieval(
                str(file_path), "file"
            )
            self.assertTrue(resource_result.get("success", False), "资源检索失败")
            
            paper_content = resource_result.get("data", {}).get("paper_content")
            self.assertIsNotNone(paper_content)
            self.assertIn("深度学习", paper_content.get("full_text", ""))
            self.logger.info_path("资源检索", file_path, "成功")
            
        except Exception as e:
            self.logger.error_path("中文文件名工作流测试", file_path, f"失败: {e}")
            raise
    
    async def test_mixed_language_path_workflow(self):
        """测试中英文混合路径的工作流"""
        mixed_filename = "Deep_Learning_深度学习_Research.txt"
        file_path = self.create_test_paper_file(mixed_filename)
        
        try:
            # 测试输入验证
            validation_result = self.pipeline.validate_inputs(
                str(file_path), "file", "advanced"
            )
            self.assertTrue(validation_result["valid"], f"输入验证失败: {validation_result['errors']}")
            self.logger.info_path("混合路径输入验证", file_path, "通过")
            
            # 测试资源检索阶段
            resource_result = await self.pipeline._process_resource_retrieval(
                str(file_path), "file"
            )
            self.assertTrue(resource_result.get("success", False), "资源检索失败")
            
            paper_content = resource_result.get("data", {}).get("paper_content")
            self.assertIsNotNone(paper_content)
            self.assertIn("深度学习", paper_content.get("full_text", ""))
            self.assertIn("Deep Learning", paper_content.get("metadata", {}).get("title", ""))
            self.logger.info_path("混合路径资源检索", file_path, "成功")
            
        except Exception as e:
            self.logger.error_path("混合路径工作流测试", file_path, f"失败: {e}")
            raise
    
    async def test_chinese_directory_workflow(self):
        """测试中文目录的工作流"""
        chinese_dirname = "学术论文目录"
        chinese_dir = self.temp_dir / chinese_dirname
        chinese_dir.mkdir(exist_ok=True)
        
        filename = "论文分析.txt"
        file_path = chinese_dir / filename
        file_path.write_text("""# 论文分析

这是一篇关于人工智能的论文分析。

## 主要贡献
1. 提出了新的算法
2. 取得了更好的性能
3. 开源了代码实现

## 实验结果
在标准测试集上达到了95%的准确率。
""", encoding='utf-8')
        
        try:
            # 测试输入验证
            validation_result = self.pipeline.validate_inputs(
                str(file_path), "file", "beginner"
            )
            self.assertTrue(validation_result["valid"], f"输入验证失败: {validation_result['errors']}")
            self.logger.info_path("中文目录输入验证", file_path, "通过")
            
            # 测试资源检索阶段
            resource_result = await self.pipeline._process_resource_retrieval(
                str(file_path), "file"
            )
            self.assertTrue(resource_result.get("success", False), "资源检索失败")
            
            paper_content = resource_result.get("data", {}).get("paper_content")
            self.assertIsNotNone(paper_content)
            self.assertIn("人工智能", paper_content.get("full_text", ""))
            self.logger.info_path("中文目录资源检索", file_path, "成功")
            
        except Exception as e:
            self.logger.error_path("中文目录工作流测试", file_path, f"失败: {e}")
            raise
    
    def test_error_handling_with_chinese_paths(self):
        """测试中文路径的错误处理"""
        non_existent_chinese_file = "不存在的论文文件.txt"
        
        # 测试输入验证的错误处理
        validation_result = self.pipeline.validate_inputs(
            non_existent_chinese_file, "file", "intermediate"
        )
        self.assertFalse(validation_result["valid"])
        self.assertIn("文件不存在", validation_result["errors"][0])
        self.logger.info_path("错误处理测试", non_existent_chinese_file, "正确识别文件不存在")
    
    async def test_pipeline_status_with_chinese_paths(self):
        """测试工作流状态与中文路径"""
        # 获取初始状态
        initial_status = self.pipeline.get_pipeline_status()
        self.assertIsInstance(initial_status, dict)
        self.assertTrue(initial_status.get("initialized", False))
        
        # 测试中文文件处理
        chinese_filename = "状态测试论文.txt"
        file_path = self.create_test_paper_file(chinese_filename)
        
        try:
            # 执行资源检索
            resource_result = await self.pipeline._process_resource_retrieval(
                str(file_path), "file"
            )
            
            # 检查状态更新
            updated_status = self.pipeline.get_pipeline_status()
            self.assertIsInstance(updated_status, dict)
            
            self.logger.info_path("工作流状态测试", file_path, "状态正常")
            
        except Exception as e:
            self.logger.error_path("工作流状态测试", file_path, f"失败: {e}")
            raise


class TestChinesePathPerformance(unittest.TestCase):
    """中文路径性能测试"""
    
    def setUp(self):
        """测试前准备"""
        self.logger = ScholarMindLogger('test.performance')
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        """测试后清理"""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_path_operation_performance(self):
        """测试路径操作性能"""
        import time
        from scholarmind.utils.path_utils import PathUtils
        
        # 创建测试文件
        test_files = [
            f"测试文件_{i}.txt" for i in range(10)
        ]
        
        file_paths = []
        for i, filename in enumerate(test_files):
            file_path = self.temp_dir / filename
            file_path.write_text(f"测试内容 {i}", encoding='utf-8')
            file_paths.append(file_path)
        
        # 测试路径存在性检查性能
        start_time = time.time()
        for file_path in file_paths:
            PathUtils.safe_path_exists(file_path)
        end_time = time.time()
        
        existence_check_time = end_time - start_time
        self.logger.info(f"路径存在性检查性能: {len(file_paths)}个文件耗时 {existence_check_time:.3f}秒")
        
        # 测试路径规范化性能
        start_time = time.time()
        for file_path in file_paths:
            PathUtils.normalize_path(file_path)
        end_time = time.time()
        
        normalization_time = end_time - start_time
        self.logger.info(f"路径规范化性能: {len(file_paths)}个文件耗时 {normalization_time:.3f}秒")
        
        # 测试文件信息获取性能
        start_time = time.time()
        for file_path in file_paths:
            PathUtils.get_file_info(file_path)
        end_time = time.time()
        
        info_extraction_time = end_time - start_time
        self.logger.info(f"文件信息获取性能: {len(file_paths)}个文件耗时 {info_extraction_time:.3f}秒")
        
        # 性能应该在合理范围内
        self.assertLess(existence_check_time, 1.0, "路径存在性检查性能过慢")
        self.assertLess(normalization_time, 1.0, "路径规范化性能过慢")
        self.assertLess(info_extraction_time, 2.0, "文件信息获取性能过慢")


async def run_async_tests():
    """运行异步测试"""
    suite = unittest.TestSuite()
    
    # 添加异步测试用例
    test_cases = [
        TestChinesePathIntegration('test_chinese_filename_workflow'),
        TestChinesePathIntegration('test_mixed_language_path_workflow'),
        TestChinesePathIntegration('test_chinese_directory_workflow'),
        TestChinesePathIntegration('test_pipeline_status_with_chinese_paths'),
    ]
    
    for test_case in test_cases:
        suite.addTest(test_case)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    # 运行同步测试
    print("=== 运行同步测试 ===")
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # 运行异步测试
    print("\n=== 运行异步测试 ===")
    success = asyncio.run(run_async_tests())
    
    if success:
        print("\n✅ 所有测试通过！")
    else:
        print("\n❌ 部分测试失败！")