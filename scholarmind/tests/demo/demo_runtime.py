#!/usr/bin/env python3
"""
ScholarMind Runtime 演示脚本
"""

import asyncio
import json
import time
import requests
from pathlib import Path

# 服务配置
SERVICE_URL = "http://localhost:8080"


def test_health_check():
    """测试健康检查端点"""
    print("🔍 测试健康检查...")
    try:
        response = requests.get(f"{SERVICE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 服务状态: {data['status']}")
            print(f"📋 服务名称: {data['service']}")
            print(f"🔢 版本: {data['version']}")
            return True
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 连接服务失败: {str(e)}")
        return False


def test_pipeline_status():
    """测试工作流状态端点"""
    print("\n🔍 测试工作流状态...")
    try:
        response = requests.get(f"{SERVICE_URL}/pipeline_status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            pipeline_info = data['data']
            print(f"✅ 工作流名称: {pipeline_info['name']}")
            print(f"🤖 智能体数量: {len(pipeline_info['agents'])}")
            print(f"📊 管道类型: {pipeline_info['pipeline_type']}")
            print(f"🔄 并行智能体: {', '.join(pipeline_info['parallel_agents'])}")
            return True
        else:
            print(f"❌ 获取工作流状态失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {str(e)}")
        return False


def test_input_validation():
    """测试输入验证端点"""
    print("\n🔍 测试输入验证...")
    
    # 测试有效输入
    print("测试有效输入...")
    try:
        response = requests.post(
            f"{SERVICE_URL}/validate_inputs",
            json={
                "paper_input": "example.pdf",
                "input_type": "file",
                "user_background": "intermediate"
            },
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            validation_result = data['data']
            if validation_result['valid']:
                print("✅ 有效输入验证通过")
            else:
                print(f"⚠️  输入验证失败: {validation_result['errors']}")
        else:
            print(f"❌ 验证请求失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 验证请求异常: {str(e)}")
    
    # 测试无效输入
    print("测试无效输入...")
    try:
        response = requests.post(
            f"{SERVICE_URL}/validate_inputs",
            json={
                "paper_input": "",
                "input_type": "file",
                "user_background": "invalid"
            },
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            validation_result = data['data']
            if not validation_result['valid']:
                print("✅ 无效输入正确被拒绝")
                print(f"   错误信息: {validation_result['errors']}")
            else:
                print("⚠️  无效输入未被正确识别")
        else:
            print(f"❌ 验证请求失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 验证请求异常: {str(e)}")


def test_paper_processing():
    """测试论文处理端点"""
    print("\n🔍 测试论文处理...")
    
    # 测试缺少参数的请求
    print("测试缺少参数的请求...")
    try:
        response = requests.post(
            f"{SERVICE_URL}/process_paper",
            json={"paper_input": "test.pdf"},
            timeout=5
        )
        if response.status_code == 400:
            print("✅ 缺少参数的请求被正确拒绝")
        else:
            print(f"⚠️  意外的状态码: {response.status_code}")
    except Exception as e:
        print(f"❌ 请求异常: {str(e)}")
    
    # 测试完整请求（文件不存在）
    print("测试完整请求（文件不存在）...")
    try:
        response = requests.post(
            f"{SERVICE_URL}/process_paper",
            json={
                "paper_input": "nonexistent.pdf",
                "input_type": "file",
                "user_background": "intermediate",
                "output_format": "markdown",
                "output_language": "zh",
                "save_report": False
            },
            timeout=10
        )
        if response.status_code == 500:
            data = response.json()
            if "File not found" in data.get('detail', ''):
                print("✅ 文件不存在的错误被正确处理")
            else:
                print(f"⚠️  意外的错误: {data.get('detail', '未知错误')}")
        else:
            print(f"⚠️  意外的状态码: {response.status_code}")
    except Exception as e:
        print(f"❌ 请求异常: {str(e)}")


def main():
    """主函数"""
    print("🚀 ScholarMind Runtime 功能演示")
    print("=" * 50)
    
    # 检查服务是否可用
    if not test_health_check():
        print("\n❌ 服务不可用，请确保Runtime服务正在运行:")
        print("   python main_runtime.py --mode runtime")
        return
    
    # 运行各项测试
    test_pipeline_status()
    test_input_validation()
    test_paper_processing()
    
    print("\n" + "=" * 50)
    print("✨ 演示完成！")
    print("\n💡 使用提示:")
    print("1. 启动服务: python main_runtime.py --mode runtime")
    print("2. 交互模式: python main_runtime.py --mode interactive")
    print("3. 直接处理: python main_runtime.py --mode direct paper.pdf")
    print("4. 查看帮助: python main_runtime.py --help")


if __name__ == "__main__":
    main()