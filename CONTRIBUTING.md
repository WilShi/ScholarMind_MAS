# 贡献指南 Contributing Guide

感谢您对 ScholarMind 的贡献兴趣！本文档将指导您如何参与项目开发。

Thank you for your interest in contributing to ScholarMind! This guide will help you get started.

## 📋 目录 Table of Contents

- [行为准则](#行为准则-code-of-conduct)
- [开始之前](#开始之前-before-you-begin)
- [开发流程](#开发流程-development-workflow)
- [代码规范](#代码规范-code-standards)
- [提交规范](#提交规范-commit-guidelines)
- [测试要求](#测试要求-testing-requirements)
- [文档要求](#文档要求-documentation-requirements)

## 行为准则 Code of Conduct

我们致力于提供一个友好、安全和受欢迎的环境。请尊重所有贡献者。

We are committed to providing a friendly, safe, and welcoming environment. Please respect all contributors.

## 开始之前 Before You Begin

### 1. Fork 项目

在 GitHub 上 Fork 本项目到您的账号下。

### 2. 克隆仓库

```bash
git clone https://github.com/YOUR_USERNAME/ScholarMind_MAS.git
cd ScholarMind_MAS
```

### 3. 安装开发依赖

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
pip install -r requirements-lock.txt

# 安装开发工具
pip install black flake8 isort mypy pytest pytest-cov pre-commit

# 安装 pre-commit hooks
pre-commit install
```

### 4. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入您的 API 密钥
```

## 开发流程 Development Workflow

### 1. 创建分支

```bash
git checkout -b feature/your-feature-name
# 或
git checkout -b fix/your-bug-fix
```

分支命名规范:
- `feature/` - 新功能
- `fix/` - Bug 修复
- `docs/` - 文档更新
- `refactor/` - 代码重构
- `test/` - 测试相关

### 2. 进行开发

- 编写清晰、可维护的代码
- 遵循项目的代码规范
- 添加必要的测试
- 更新相关文档

### 3. 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest scholarmind/tests/test_specific.py

# 生成覆盖率报告
pytest --cov=scholarmind --cov-report=html
```

### 4. 代码检查

```bash
# 格式化代码
black .
isort .

# 代码检查
flake8 scholarmind/

# 类型检查
mypy scholarmind/
```

### 5. 提交更改

```bash
git add .
git commit -m "feat: add new feature description"
git push origin feature/your-feature-name
```

### 6. 创建 Pull Request

1. 在 GitHub 上创建 Pull Request
2. 填写 PR 模板中的所有必要信息
3. 等待代码审查
4. 根据反馈进行修改

## 代码规范 Code Standards

### Python 代码风格

- 遵循 PEP 8 规范
- 使用 Black 进行代码格式化（行长度 100）
- 使用 isort 整理导入
- 使用类型注解

```python
from typing import Dict, List, Optional

def process_paper(
    paper_input: str,
    input_type: str = "file",
    user_background: Optional[str] = None
) -> Dict[str, Any]:
    """
    处理论文的函数。

    Args:
        paper_input: 论文输入（文件路径、URL或文本）
        input_type: 输入类型（file, url, text）
        user_background: 用户背景级别

    Returns:
        包含处理结果的字典

    Raises:
        ValueError: 当输入类型不支持时
    """
    pass
```

### Docstring 规范

使用 Google 风格的 docstring：

```python
def function_name(param1: str, param2: int) -> bool:
    """
    函数简短描述（一行）。

    更详细的函数描述（如果需要）。

    Args:
        param1: 参数1的描述
        param2: 参数2的描述

    Returns:
        返回值的描述

    Raises:
        ExceptionType: 异常的描述

    Example:
        >>> function_name("test", 42)
        True
    """
    pass
```

### 命名规范

- 类名：`PascalCase`
- 函数/方法：`snake_case`
- 常量：`UPPER_SNAKE_CASE`
- 私有成员：`_leading_underscore`

## 提交规范 Commit Guidelines

使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type 类型

- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式（不影响代码运行的变动）
- `refactor`: 重构（既不是新增功能，也不是修改bug的代码变动）
- `perf`: 性能优化
- `test`: 增加测试
- `chore`: 构建过程或辅助工具的变动

### 示例

```bash
feat(agent): add caching mechanism for methodology analysis

Add LRU cache to methodology agent to improve performance
when analyzing similar papers.

Closes #123
```

## 测试要求 Testing Requirements

### 单元测试

- 所有新功能必须包含单元测试
- 测试覆盖率应≥70%
- 使用 pytest 框架

```python
import pytest
from scholarmind.agents import MethodologyAgent

@pytest.mark.asyncio
async def test_methodology_agent_initialization():
    """测试方法论智能体初始化"""
    agent = MethodologyAgent()
    assert agent.name == "MethodologyAgent"
    assert agent.model is not None

def test_methodology_analysis_structure():
    """测试方法论分析输出结构"""
    result = {
        "architecture_analysis": "test",
        "innovation_points": ["point1"],
        "success": True
    }
    assert "architecture_analysis" in result
    assert isinstance(result["innovation_points"], list)
```

### 集成测试

- 测试多个组件的交互
- 标记为 `@pytest.mark.integration`

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_pipeline():
    """测试完整的5智能体流程"""
    pipeline = ScholarMindEnhancedPipeline()
    result = await pipeline.process_paper(
        paper_input="test_paper.pdf",
        input_type="file"
    )
    assert result["success"] is True
```

## 文档要求 Documentation Requirements

### 代码文档

- 所有公共 API 必须有 docstring
- 复杂逻辑需要内联注释
- 使用中英文双语（可选）

### README 更新

如果您的更改影响到：
- 功能特性
- 安装步骤
- 使用方法
- API 接口

请同步更新 README.md

### 示例文档

在 `docs/` 目录下添加使用示例：

```python
# docs/examples/custom_agent.md

## 创建自定义智能体

本示例展示如何创建自定义智能体...

\`\`\`python
from scholarmind.agents.base_agent import ScholarMindAgentBase

class MyCustomAgent(ScholarMindAgentBase):
    def __init__(self, **kwargs):
        super().__init__(name="MyCustomAgent", **kwargs)

    async def _process_logic(self, input_data):
        # 您的处理逻辑
        pass
\`\`\`
```

## Pull Request 检查清单

提交 PR 前，请确保：

- [ ] 代码通过所有测试
- [ ] 新功能有对应的测试
- [ ] 代码通过 Black、Flake8、isort 检查
- [ ] 更新了相关文档
- [ ] 提交信息符合规范
- [ ] PR 描述清晰，说明了更改的目的和内容
- [ ] 关联了相关的 Issue（如果有）

## 获取帮助

如果您有任何问题：

1. 查看 [文档](./docs/)
2. 搜索现有的 [Issues](https://github.com/WilShi/ScholarMind_MAS/issues)
3. 创建新的 Issue 提问

## 许可证

通过贡献代码，您同意您的贡献将在 MIT 许可证下授权。

---

再次感谢您的贡献！🎉

Thank you for your contribution! 🎉
