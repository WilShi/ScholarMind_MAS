"""
ScholarMind Main Entry Point
智读ScholarMind主程序入口
"""

import sys
import argparse
import textwrap
from pathlib import Path
import agentscope
import os
import asyncio


# 添加项目根目录到Python路径，确保可以正确导入模块
sys.path.insert(0, str(Path(__file__).resolve().parent))

# 初始化 AgentScope（无需加载model_configs，Agent会直接使用OpenAIChatModel）
agentscope.init(
    project="ScholarMind",
    name="scholarmind-run",
    studio_url="http://localhost:3000"
)

from scholarmind.workflows.scholarmind_pipeline import create_pipeline
from scholarmind.agents.interactive_agent import InteractiveScholarAgent
from scholarmind.utils.logger import setup_logger
from config import setup_directories, validate_config

# Create CLI logger for user-facing output
cli_logger = setup_logger('scholarmind.cli', level='INFO', log_file=None, console=True)

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="智读ScholarMind - 计算机学术论文多智能体解读系统 (AgentScope)"
    )
    
    parser.add_argument(
        "input",
        nargs="?",  # 使参数可选
        help="论文输入 (文件路径、URL或文本)"
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

def main():
    """主函数：初始化并运行ScholarMind工作流"""
    # 预备工作：设置目录和解析参数
    setup_directories()
    args = parse_arguments()

    # 步骤1: 验证环境配置
    cli_logger.info("正在验证环境配置...")
    if not validate_config():
        cli_logger.error("❌ 配置验证失败! 请检查您的 .env 文件和环境变量设置 (例如 OPENAI_API_KEY)。")
        return
    cli_logger.info("✅ 环境配置验证通过。")

    # 步骤2: 初始化工作流
    cli_logger.info("\n🚀 正在初始化 ScholarMind 工作流...")
    pipeline = create_pipeline()
    cli_logger.info("✅ 工作流已准备就绪。")

    # 检查是否提供了论文输入参数
    if not args.input:
        # 如果没有提供输入参数，启动交互式对话智能体
        cli_logger.info("\n启动交互式对话模式...\n")
        interactive_agent = InteractiveScholarAgent()
        asyncio.run(interactive_agent.run_interactive_session(pipeline))
        return

    # 步骤3: 验证输入参数
    cli_logger.info("\n🔍 正在验证输入参数...")
    validation_result = pipeline.validate_inputs(args.input, args.type, args.background)
    if not validation_result["valid"]:
        cli_logger.error(f"❌ 输入参数无效:")
        for error in validation_result["errors"]:
            cli_logger.error(f"  - {error}")
        return
    cli_logger.info("✅ 输入参数验证通过。")

    # 步骤4: 执行论文处理
    cli_logger.info(f"\n🔬 开始处理论文: {args.input}")
    result = asyncio.run(pipeline.process_paper(
        paper_input=args.input,
        input_type=args.type,
        user_background=args.background,
        save_report=args.save_report,
        output_format=args.output_format,
        output_language=args.language
    ))

    # 步骤5: 显示结果
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

if __name__ == "__main__":
    main()