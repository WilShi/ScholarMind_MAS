"""
ScholarMind Path Utils
路径编码检测和转换工具模块，专门处理中文路径问题
"""

import os
import sys
from pathlib import Path
from typing import Optional, Union

from .logger import ScholarMindLogger

logger = ScholarMindLogger('scholarmind.path_utils')


class PathUtils:
    """路径处理工具类"""
    
    @staticmethod
    def is_windows() -> bool:
        """检查是否为Windows系统"""
        return sys.platform.startswith('win')
    
    @staticmethod
    def detect_encoding(text: str) -> str:
        """
        检测文本编码
        
        Args:
            text: 要检测的文本
            
        Returns:
            str: 检测到的编码
        """
        try:
            # 尝试UTF-8编码
            text.encode('utf-8')
            return 'utf-8'
        except UnicodeEncodeError:
            pass
        
        try:
            # 尝试GBK编码
            text.encode('gbk')
            return 'gbk'
        except UnicodeEncodeError:
            pass
        
        try:
            # 尝试GB2312编码
            text.encode('gb2312')
            return 'gb2312'
        except UnicodeEncodeError:
            pass
        
        return 'unknown'
    
    @staticmethod
    def convert_encoding(text: str, from_encoding: str, to_encoding: str = 'utf-8') -> str:
        """
        转换文本编码
        
        Args:
            text: 要转换的文本
            from_encoding: 源编码
            to_encoding: 目标编码
            
        Returns:
            str: 转换后的文本
        """
        try:
            if from_encoding == to_encoding:
                return text
            
            # 先解码为Unicode，再编码为目标编码
            decoded_text = text.decode(from_encoding) if isinstance(text, bytes) else text
            return decoded_text.encode(to_encoding).decode(to_encoding)
        except Exception as e:
            logger.warning_path("编码转换", f"{from_encoding} -> {to_encoding}", str(e))
            return text
    
    @staticmethod
    def safe_path_exists(path: Union[str, Path]) -> bool:
        """
        安全的路径存在性检查，支持中文路径
        
        Args:
            path: 要检查的路径
            
        Returns:
            bool: 路径是否存在
        """
        try:
            # 优先使用pathlib.Path
            path_obj = Path(path) if isinstance(path, str) else path
            return path_obj.exists()
        except Exception:
            # 如果Path处理失败，尝试多种编码
            if isinstance(path, str):
                for encoding in ['utf-8', 'gbk', 'gb2312']:
                    try:
                        encoded_path = path.encode(encoding)
                        decoded_path = encoded_path.decode(encoding)
                        return os.path.exists(decoded_path)
                    except (UnicodeEncodeError, UnicodeDecodeError):
                        continue
            return False
    
    @staticmethod
    def normalize_path(path: Union[str, Path]) -> Path:
        """
        规范化路径，处理中文路径编码问题
        
        Args:
            path: 要规范化的路径
            
        Returns:
            Path: 规范化后的Path对象
        """
        if isinstance(path, Path):
            return path
        
        path_str = str(path)
        
        # 在Windows上，尝试不同的编码
        if PathUtils.is_windows():
            for encoding in ['utf-8', 'gbk', 'gb2312']:
                try:
                    # 编码为bytes再解码，确保正确处理
                    encoded_path = path_str.encode(encoding)
                    decoded_path = encoded_path.decode(encoding)
                    return Path(decoded_path)
                except (UnicodeEncodeError, UnicodeDecodeError):
                    continue
        
        # 默认返回Path对象
        return Path(path_str)
    
    @staticmethod
    def get_file_info(path: Union[str, Path]) -> dict:
        """
        获取文件信息，支持中文路径
        
        Args:
            path: 文件路径
            
        Returns:
            dict: 文件信息
        """
        try:
            path_obj = PathUtils.normalize_path(path)
            
            if not path_obj.exists():
                return {
                    "exists": False,
                    "is_file": False,
                    "is_dir": False,
                    "size": 0,
                    "encoding": "unknown",
                    "error": "文件不存在"
                }
            
            stat_info = path_obj.stat()
            
            # 尝试检测文件编码
            encoding = "unknown"
            if path_obj.is_file():
                try:
                    with open(path_obj, 'rb') as f:
                        # 读取文件前1024字节来检测编码
                        raw_data = f.read(1024)
                        encoding = PathUtils.detect_file_encoding(raw_data)
                except Exception:
                    pass
            
            return {
                "exists": True,
                "is_file": path_obj.is_file(),
                "is_dir": path_obj.is_dir(),
                "size": stat_info.st_size,
                "encoding": encoding,
                "path": str(path_obj),
                "name": path_obj.name,
                "parent": str(path_obj.parent) if path_obj.parent else None
            }
            
        except Exception as e:
            return {
                "exists": False,
                "is_file": False,
                "is_dir": False,
                "size": 0,
                "encoding": "unknown",
                "error": str(e),
                "path": str(path) if isinstance(path, str) else "unknown"
            }
    
    @staticmethod
    def detect_file_encoding(raw_data: bytes) -> str:
        """
        检测文件编码
        
        Args:
            raw_data: 文件原始数据
            
        Returns:
            str: 检测到的编码
        """
        # 尝试UTF-8
        try:
            raw_data.decode('utf-8')
            return 'utf-8'
        except UnicodeDecodeError:
            pass
        
        # 尝试GBK
        try:
            raw_data.decode('gbk')
            return 'gbk'
        except UnicodeDecodeError:
            pass
        
        # 尝试GB2312
        try:
            raw_data.decode('gb2312')
            return 'gb2312'
        except UnicodeDecodeError:
            pass
        
        # 尝试Latin-1
        try:
            raw_data.decode('latin1')
            return 'latin1'
        except UnicodeDecodeError:
            pass
        
        return 'unknown'
    
    @staticmethod
    def safe_open_file(path: Union[str, Path], mode: str = 'r', encoding: Optional[str] = None, **kwargs):
        """
        安全打开文件，自动处理中文路径编码
        
        Args:
            path: 文件路径
            mode: 打开模式
            encoding: 文件编码，如果为None则自动检测
            **kwargs: 其他参数
            
        Returns:
            文件对象
        """
        path_obj = PathUtils.normalize_path(path)
        
        if not path_obj.exists():
            logger.error_path("文件访问", path_obj, "文件不存在")
            raise FileNotFoundError(f"文件不存在: {path_obj}")
        
        # 如果没有指定编码，尝试检测
        if encoding is None and 'b' not in mode:
            try:
                with open(path_obj, 'rb') as f:
                    raw_data = f.read(1024)
                    encoding = PathUtils.detect_file_encoding(raw_data)
            except Exception:
                encoding = 'utf-8'  # 默认使用UTF-8
        
        return open(path_obj, mode, encoding=encoding, **kwargs)
    
    @staticmethod
    def format_path_error(path: Union[str, Path], error: str) -> str:
        """
        格式化路径错误信息，确保中文路径正确显示
        
        Args:
            path: 问题路径
            error: 错误信息
            
        Returns:
            str: 格式化后的错误信息
        """
        try:
            path_obj = PathUtils.normalize_path(path)
            path_str = str(path_obj)
        except Exception:
            path_str = str(path)
        
        return f"{error}: {path_str}"