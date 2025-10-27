"""
ScholarMind Runtime Entry Point
智读ScholarMind Runtime主程序入口 - 完全符合 AgentScope Runtime 官方架构规范
"""

import sys
import argparse
import textwrap
import asyncio
import json
import time
import os
import signal
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, Optional

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).resolve().parent))

import agentscope
from agentscope.message import Msg
from agentscope_runtime.engine import Runner
from agentscope_runtime.engine.deployers import LocalDeployManager
from agentscope_runtime.engine.services.context_manager import ContextManager

from scholarmind.agents.runtime_agent import ScholarMindRuntimeAgent
from scholarmind.agents.interactive_agent import InteractiveScholarAgent
from scholarmind.workflows.scholarmind_pipeline import create_pipeline
from scholarmind.utils.logger import setup_logger
from config import setup_directories, validate_config

# Create CLI logger for user-facing output
cli_logger = setup_logger('scholarmind.runtime', level='INFO', log_file=None, console=True)


class ScholarMindRuntimeService:
    """ScholarMind Runtime服务管理器 - 符合官方架构规范"""
    
    def __init__(self):
        """初始化Runtime服务"""
        self.agent = None
        self.deploy_manager = None
        self.runner = None
        self.service_config = {
            "name": "scholarmind-service",
            "version": "1.0.0",
            "description": "智读ScholarMind多智能体论文解读服务",
            "host": "localhost",
            "port": 8080,
        }
        self.is_running = False
        self._shutdown_event = asyncio.Event()

    async def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """初始化Runtime服务"""
        try:
            cli_logger.info("🚀 正在初始化ScholarMind Runtime服务...")
            
            # 初始化AgentScope
            agentscope.init(
                project="ScholarMind-Runtime",
                name="scholarmind-runtime",
                studio_url="http://localhost:3000"
            )
            
            # 创建符合Runtime规范的智能体
            self.agent = ScholarMindRuntimeAgent(
                name=self.service_config["name"]
            )
            
            # 更新配置
            if config:
                self.service_config.update(config)
            
            cli_logger.info("✅ ScholarMind Runtime服务初始化完成")
            return True
            
        except Exception as e:
            cli_logger.error(f"❌ Runtime服务初始化失败: {str(e)}")
            return False

    @asynccontextmanager
    async def create_runner(self):
        """创建Runner上下文管理器"""
        async with Runner(
            agent=self.agent,
            context_manager=ContextManager(),
        ) as runner:
            cli_logger.info("✅ Runner创建成功")
            yield runner

    async def start(self) -> bool:
        """启动Runtime服务（使用官方部署架构）"""
        try:
            cli_logger.info(f"🌐 启动ScholarMind Runtime服务...")
            
            # 创建部署管理器
            self.deploy_manager = LocalDeployManager(
                host=self.service_config["host"],
                port=self.service_config["port"],
            )
            
            # 使用官方部署架构
            async with self.create_runner() as runner:
                self.runner = runner
                
                # 部署智能体为服务
                deploy_result = await runner.deploy(
                    deploy_manager=self.deploy_manager,
                    endpoint_path="/process_paper",
                    stream=True,  # 启用流式响应
                )
                
                self.is_running = True
                
                cli_logger.info(f"✅ ScholarMind Runtime服务启动成功")
                cli_logger.info(f"🚀 智能体部署在: {deploy_result}")
                cli_logger.info(f"🌐 服务URL: {self.deploy_manager.service_url}")
                cli_logger.info(f"💚 健康检查: {self.deploy_manager.service_url}/health")
                cli_logger.info(f"📋 API端点: {self.deploy_manager.service_url}/process_paper")
                
                # 显示其他可用的健康检查端点
                cli_logger.info(f"🔍 就绪检查: {self.deploy_manager.service_url}/readiness")
                cli_logger.info(f"💓 存活检查: {self.deploy_manager.service_url}/liveness")
                
                cli_logger.info("\n🎯 Runtime服务正在运行，按 Ctrl+C 停止服务")
                
                # 保持服务运行 - 使用事件等待而不是循环
                try:
                    await self._shutdown_event.wait()
                except asyncio.CancelledError:
                    pass
                
            return True
            
        except Exception as e:
            cli_logger.error(f"❌ Runtime服务启动失败: {str(e)}")
            return False

    async def stop(self):
        """停止Runtime服务"""
        try:
            cli_logger.info("🛑 正在停止ScholarMind Runtime服务...")
            self.is_running = False
            # 触发关闭事件，解除等待
            self._shutdown_event.set()
            
            if self.deploy_manager and self.deploy_manager.is_running:
                await self.deploy_manager.stop()
                
            cli_logger.info("✅ Runtime服务已停止")
        except Exception as e:
            cli_logger.error(f"❌ 停止Runtime服务时出错: {str(e)}")

    async def run_interactive_mode(self):
        """运行交互式模式"""
        cli_logger.info("\n🎯 启动交互式对话模式...")
        
        # 创建工作流和交互式智能体
        pipeline = create_pipeline()
        interactive_agent = InteractiveScholarAgent()
        
        await interactive_agent.run_interactive_session(pipeline)

    async def run_direct_mode(self, args):
        """运行直接处理模式（兼容原main.py功能）"""
        cli_logger.info("🔬 运行直接处理模式...")
        
        # 创建工作流
        pipeline = create_pipeline()
        
        # 检查是否提供了论文输入参数
        if not args.input:
            # 如果没有提供输入参数，启动交互式对话智能体
            cli_logger.info("\n启动交互式对话模式...\n")
            interactive_agent = InteractiveScholarAgent()
            await interactive_agent.run_interactive_session(pipeline)
            return

        # 验证输入参数
        cli_logger.info("\n🔍 正在验证输入参数...")
        validation_result = pipeline.validate_inputs(args.input, args.type, args.background)
        if not validation_result["valid"]:
            cli_logger.error(f"❌ 输入参数无效:")
            for error in validation_result["errors"]:
                cli_logger.error(f"  - {error}")
            return
        cli_logger.info("✅ 输入参数验证通过。")

        # 执行论文处理
        cli_logger.info(f"\n🔬 开始处理论文: {args.input}")
        result = await pipeline.process_paper(
            paper_input=args.input,
            input_type=args.type,
            user_background=args.background,
            save_report=args.save_report,
            output_format=args.output_format,
            output_language=args.language
        )

        # 显示结果
        if result and result.get("success"):
            # 多语言标签
            labels = {
                "zh": {
                    "title": "📄 报告标题",
                    "summary": "📝 摘要",
                    "contributions": "🎯 主要贡献",
                    "insights": "💡 关键洞察",
                    "saved": "💾 报告已保存至",
                    "total_time": "⏱️  总耗时",
                    "seconds": "秒"
                },
                "en": {
                    "title": "📄 Report Title",
                    "summary": "📝 Summary",
                    "contributions": "🎯 Key Contributions",
                    "insights": "💡 Key Insights",
                    "saved": "💾 Report saved to",
                    "total_time": "⏱️  Total Time",
                    "seconds": "seconds"
                }
            }[args.language]

            cli_logger.info("\n" + "="*25 + " 处 理 完 成 " + "="*25)
            report = result["outputs"]["report"]

            cli_logger.info(f"\n{labels['title']}: {report['title']}")
            cli_logger.info(f"\n{labels['summary']}:")
            cli_logger.info(textwrap.fill(report['summary'], width=80))

            if report.get('key_contributions'):
                cli_logger.info(f"\n{labels['contributions']}:")
                for i, contribution in enumerate(report['key_contributions'], 1):
                    cli_logger.info(f"  {i}. {contribution}")

            if report.get('insights'):
                cli_logger.info(f"\n{labels['insights']}:")
                for i, insight in enumerate(report['insights'], 1):
                    cli_logger.info(f"  {i}. {insight}")

            if result["outputs"].get("report_path"):
                cli_logger.info(f"\n{labels['saved']}: {result['outputs']['report_path']}")

            cli_logger.info(f"\n{labels['total_time']}: {result['processing_time']:.2f} {labels['seconds']}")
            cli_logger.info("\n" + "="*60)

        else:
            cli_logger.error(f"\n💥 处理失败: {result.get('error', '未知错误')}")


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="智读ScholarMind Runtime - 计算机学术论文多智能体解读系统 (AgentScope Runtime)"
    )
    
    # 运行模式选择
    parser.add_argument(
        "--mode",
        choices=["runtime", "interactive", "direct"],
        default="runtime",
        help="运行模式: runtime(服务模式), interactive(交互模式), direct(直接模式)"
    )
    
    # Runtime配置
    parser.add_argument(
        "--host",
        default="localhost",
        help="Runtime服务主机地址 (默认: localhost)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Runtime服务端口 (默认: 8080)"
    )
    
    # 论文处理参数（用于direct模式）
    parser.add_argument(
        "input",
        nargs="?",
        help="论文输入 (文件路径、URL或文本) - 仅用于direct模式"
    )
    
    parser.add_argument(
        "--type",
        choices=["file", "url", "text"],
        default="file",
        help="输入类型 (默认: file)"
    )
    
    parser.add_argument(
        "--background",
        choices=["beginner", "intermediate", "advanced"],
        default="intermediate",
        help="用户背景 (默认: intermediate)"
    )
    
    parser.add_argument(
        "--output-format",
        choices=["markdown", "json"],
        default="markdown",
        help="报告输出格式 (默认: markdown)"
    )

    parser.add_argument(
        "--language",
        choices=["zh", "en"],
        default="zh",
        help="输出语言 / Output language (默认/default: zh - 中文)"
    )

    parser.add_argument(
        "--save-report",
        action="store_true",
        help="保存报告到文件"
    )
    
    return parser.parse_args()


# 全局服务实例，用于信号处理
_global_service = None
_shutdown_requested = False

def signal_handler(signum, frame):
    """信号处理器"""
    global _shutdown_requested
    if _shutdown_requested:
        # 如果已经在关闭过程中，忽略后续信号
        return
    
    _shutdown_requested = True
    cli_logger.info(f"\n收到信号 {signum}，正在优雅关闭服务...")
    if _global_service:
        # 触发关闭事件，让主事件循环处理停止逻辑
        _global_service._shutdown_event.set()


async def main():
    """主函数：初始化并运行ScholarMind Runtime服务"""
    # 声明全局变量
    global _global_service, _shutdown_requested
    
    # 预备工作：设置目录和解析参数
    setup_directories()
    args = parse_arguments()

    # 设置信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 验证环境配置
    cli_logger.info("正在验证环境配置...")
    if not validate_config():
        cli_logger.error("❌ 配置验证失败! 请检查您的 .env 文件和环境变量设置 (例如 OPENAI_API_KEY)。")
        return
    cli_logger.info("✅ 环境配置验证通过。")

    # 根据模式选择运行方式
    if args.mode == "direct":
        # 直接模式，兼容原main.py功能
        service = ScholarMindRuntimeService()
        await service.run_direct_mode(args)
        return

    # Runtime服务模式
    service = ScholarMindRuntimeService()
    
    # 设置全局服务实例供信号处理使用
    _global_service = service
    
    # 配置Runtime服务
    runtime_config = {
        "host": args.host,
        "port": args.port,
    }
    
    # 初始化服务
    if not await service.initialize(runtime_config):
        cli_logger.error("❌ 服务初始化失败")
        return
    
    try:
        if args.mode == "runtime":
            # 启动Runtime服务
            await service.start()
                    
        elif args.mode == "interactive":
            # 交互式模式
            await service.run_interactive_mode()
            
    except KeyboardInterrupt:
        cli_logger.info("\n⚠️  收到中断信号")
    except Exception as e:
        cli_logger.error(f"❌ 运行时错误: {str(e)}")
    finally:
        # 停止服务
        await service.stop()
        cli_logger.info("👋 ScholarMind Runtime服务已退出")
        # 清理全局引用
        _global_service = None
        _shutdown_requested = False


if __name__ == "__main__":
    asyncio.run(main())
