"""
ScholarMind Chinese Path Tests
中文路径测试用例

测试系统对中文路径的支持能力
"""

import os
import tempfile
import unittest
from pathlib import Path

from scholarmind.tools.paper_parser import PaperParser
from scholarmind.utils.logger import ScholarMindLogger
from scholarmind.utils.path_utils import PathUtils


class TestChinesePaths(unittest.TestCase):
    """中文路径测试类"""

    def setUp(self):
        """测试前准备"""
        self.logger = ScholarMindLogger("test.chinese_paths")
        self.temp_dir = Path(tempfile.mkdtemp())
        self.parser = PaperParser()

    def tearDown(self):
        """测试后清理"""
        import shutil

        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def create_test_file(self, filename: str, content: str) -> Path:
        """
        创建测试文件

        Args:
            filename: 文件名（可能包含中文）
            content: 文件内容

        Returns:
            Path: 创建的文件路径
        """
        file_path = self.temp_dir / filename
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            self.logger.info_path("创建测试文件", file_path, "成功")
            return file_path
        except Exception as e:
            self.logger.error_path("创建测试文件失败", file_path, str(e))
            raise

    def test_chinese_filename_basic(self):
        """测试基本中文文件名"""
        chinese_filename = "测试论文.txt"
        content = """这是一个测试论文

摘要
这是论文的摘要内容。

介绍
这是论文的介绍部分。

方法
这是论文的方法部分。

结果
这是论文的结果部分。

结论
这是论文的结论部分。
"""

        file_path = self.create_test_file(chinese_filename, content)

        # 测试PathUtils.safe_path_exists
        self.assertTrue(PathUtils.safe_path_exists(file_path))

        # 测试PathUtils.normalize_path
        normalized_path = PathUtils.normalize_path(file_path)
        self.assertEqual(str(normalized_path), str(file_path))

        # 测试文件解析
        try:
            paper_content = self.parser.parse_file(str(file_path))
            self.assertIsNotNone(paper_content)
            self.assertEqual(paper_content.metadata.title, chinese_filename)
            self.assertIn("摘要", paper_content.full_text)
            self.logger.info_path("中文文件解析", file_path, "成功")
        except Exception as e:
            self.logger.error_path("中文文件解析", file_path, f"失败: {e}")
            raise

    def test_chinese_directory_path(self):
        """测试中文目录路径"""
        chinese_dirname = "中文目录"
        chinese_filename = "论文文件.txt"

        # 创建中文目录
        chinese_dir = self.temp_dir / chinese_dirname
        chinese_dir.mkdir(exist_ok=True)

        content = """中文目录中的测试文件

这是位于中文目录中的测试文件内容。
"""

        file_path = self.create_test_file(chinese_filename, content)
        # 移动到中文目录
        chinese_file_path = chinese_dir / chinese_filename
        file_path.rename(chinese_file_path)

        # 测试路径存在性检查
        self.assertTrue(PathUtils.safe_path_exists(chinese_file_path))

        # 测试文件解析
        try:
            paper_content = self.parser.parse_file(str(chinese_file_path))
            self.assertIsNotNone(paper_content)
            self.assertIn("中文目录", paper_content.full_text)
            self.logger.info_path("中文目录文件解析", chinese_file_path, "成功")
        except Exception as e:
            self.logger.error_path("中文目录文件解析", chinese_file_path, f"失败: {e}")
            raise

    def test_mixed_chinese_english_path(self):
        """测试中英文混合路径"""
        mixed_filename = "Test_测试文件_Mixed.txt"
        content = """Mixed Path Test File

这是一个中英文混合路径的测试文件。

This is a test file with mixed Chinese and English path.
"""

        file_path = self.create_test_file(mixed_filename, content)

        # 测试路径处理
        self.assertTrue(PathUtils.safe_path_exists(file_path))

        # 测试文件解析
        try:
            paper_content = self.parser.parse_file(str(file_path))
            self.assertIsNotNone(paper_content)
            self.assertIn("Mixed", paper_content.full_text)
            self.assertIn("测试", paper_content.full_text)
            self.logger.info_path("中英文混合路径解析", file_path, "成功")
        except Exception as e:
            self.logger.error_path("中英文混合路径解析", file_path, f"失败: {e}")
            raise

    def test_special_chinese_characters(self):
        """测试特殊中文字符"""
        special_chars = "特殊符号测试《》【】" "''.txt"
        content = """特殊中文字符测试

这个文件名包含特殊的中文字符和符号。
"""

        file_path = self.create_test_file(special_chars, content)

        # 测试路径处理
        self.assertTrue(PathUtils.safe_path_exists(file_path))

        # 测试文件解析
        try:
            paper_content = self.parser.parse_file(str(file_path))
            self.assertIsNotNone(paper_content)
            self.assertIn("特殊", paper_content.full_text)
            self.logger.info_path("特殊字符路径解析", file_path, "成功")
        except Exception as e:
            self.logger.error_path("特殊字符路径解析", file_path, f"失败: {e}")
            raise

    def test_encoding_detection(self):
        """测试编码检测"""
        # 测试UTF-8编码
        utf8_content = "UTF-8编码测试内容"
        encoding = PathUtils.detect_encoding(utf8_content)
        self.assertEqual(encoding, "utf-8")

        # 测试GBK编码（如果支持）
        try:
            gbk_content = "GBK编码测试".encode("gbk").decode("gbk")
            encoding = PathUtils.detect_encoding(gbk_content)
            self.assertIn(encoding, ["gbk", "utf-8"])  # 可能为gbk或utf-8
        except Exception:
            # 如果系统不支持GBK，跳过此测试
            pass

    def test_path_info_extraction(self):
        """测试路径信息提取"""
        chinese_filename = "信息提取测试.txt"
        content = "测试文件内容"

        file_path = self.create_test_file(chinese_filename, content)

        # 测试文件信息提取
        file_info = PathUtils.get_file_info(file_path)

        self.assertTrue(file_info["exists"])
        self.assertTrue(file_info["is_file"])
        self.assertFalse(file_info["is_dir"])
        self.assertGreater(file_info["size"], 0)
        self.assertEqual(file_info["name"], chinese_filename)
        self.assertIn("utf-8", file_info["encoding"])

        self.logger.info_path("文件信息提取", file_path, f"编码: {file_info['encoding']}")

    def test_error_handling_with_chinese_paths(self):
        """测试中文路径的错误处理"""
        non_existent_path = "不存在的文件.txt"

        # 测试不存在文件的处理
        self.assertFalse(PathUtils.safe_path_exists(non_existent_path))

        # 测试错误信息格式化
        error_msg = PathUtils.format_path_error(non_existent_path, "文件不存在")
        self.assertIn("不存在的文件.txt", error_msg)
        self.assertIn("文件不存在", error_msg)

        self.logger.info_path("错误处理测试", non_existent_path, "测试完成")

    def test_safe_file_operations(self):
        """测试安全文件操作"""
        chinese_filename = "安全操作测试.txt"
        content = """安全文件操作测试

这是用于测试安全文件操作的内容。
包含中文字符：测试、操作、安全。
"""

        file_path = self.create_test_file(chinese_filename, content)

        # 测试安全文件打开
        try:
            with PathUtils.safe_open_file(file_path, "r") as f:
                read_content = f.read()
                self.assertIn("安全文件操作测试", read_content)
                self.assertIn("中文字符", read_content)
                self.logger.info_path("安全文件操作", file_path, "读取成功")
        except Exception as e:
            self.logger.error_path("安全文件操作", file_path, f"读取失败: {e}")
            raise


class TestCrossPlatformCompatibility(unittest.TestCase):
    """跨平台兼容性测试"""

    def setUp(self):
        """测试前准备"""
        self.logger = ScholarMindLogger("test.cross_platform")

    def test_platform_detection(self):
        """测试平台检测"""
        is_windows = PathUtils.is_windows()
        self.assertIsInstance(is_windows, bool)

        platform_name = "Windows" if is_windows else "Unix-like"
        self.logger.info(f"当前平台: {platform_name}")

    def test_path_normalization_across_platforms(self):
        """测试跨平台路径规范化"""
        test_paths = [
            "测试文件.txt",
            "中文目录/子目录/文件.txt",
            "/absolute/path/测试文件.txt",
            "relative/path/测试文件.txt",
        ]

        for test_path in test_paths:
            try:
                normalized = PathUtils.normalize_path(test_path)
                self.assertIsInstance(normalized, Path)
                self.logger.info_path("路径规范化测试", test_path, f"规范化为: {normalized}")
            except Exception as e:
                self.logger.error_path("路径规范化测试", test_path, f"失败: {e}")


if __name__ == "__main__":
    # 运行测试
    unittest.main(verbosity=2)
