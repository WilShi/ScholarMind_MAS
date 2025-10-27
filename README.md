# ScholarMind 智读

<p align="center">
  <img src="images/scholarmind_logo_v3.svg" alt="ScholarMind Logo" width="200"/>
</p>

<p align="center">
  <strong>基于 AgentScope 的计算机学术论文多智能体解读系统</strong>
</p>

<p align="center">
<a href="#功能特性">功能特性</a> •
<a href="#系统架构">系统架构</a> •
<a href="#快速开始">快速开始</a> •
<a href="#使用方法">使用方法</a> •
<a href="#开发指南">开发指南</a> •
   <a href="#测试">测试</a>
</p>

## 项目简介

ScholarMind（智读）是一个先进的多智能体协作系统，旨在将复杂的计算机学术论文自动转化为结构清晰、深入浅出的解读报告。通过模拟专家团队的研讨过程，ScholarMind 能够深度解析论文的方法论、评估其实验设计，并提供批判性洞察，赋能科研与学习。

## 功能特性

- **智能体协作架构**：采用5个专业角色智能体协同工作，包括资源检索、方法论解析、实验评估、洞察生成和综合报告生成
- **多运行模式**：
  - 交互式对话模式（智能识别论文标题、ArXiv URL/ID、本地PDF文件）
  - 命令行参数指定论文文件、URL或文本内容
  - Runtime API模式（基于AgentScope Runtime的RESTful API服务）
- **并行处理能力**：支持方法论分析与实验评估的并行处理，大幅提升处理效率
- **智能输入识别**：自动识别并处理多种论文输入格式，包括输入验证和安全过滤
- **学术API集成**：集成ArXiv和Semantic Scholar API，支持通过论文标题搜索论文
- **多语言支持**：支持中英文双语输出
- **个性化报告**：根据用户技术背景（初级/中级/高级）调整报告深度
- **零LLM参数收集**：在交互模式下，参数收集阶段不调用LLM，节省API资源
- **结构化输出**：生成包含标题、摘要、关键贡献、洞察等结构化内容的报告
- **生产就绪**：完整的CI/CD流水线、日志管理系统和错误处理
- **开发友好**：Pre-commit hooks、类型检查、代码覆盖率报告、全面的测试套件

## 系统架构

ScholarMind 采用基于 AgentScope 的多智能体协作架构，核心是一个有向无环图（DAG）的计算流程：

```
用户输入 → [资源检索智能体] → [方法论解析智能体]
                              ↘
                               [洞察生成智能体] → [综合报告智能体] → 解读报告
                              ↗
             [实验评估智能体]
```

### 智能体角色

1. **资源检索智能体**：负责论文解析和结构化信息提取
2. **方法论解析智能体**：深度剖析论文的技术核心和创新点
3. **实验评估智能体**：客观评估实验设计的严谨性和结论可靠性
4. **洞察生成智能体**：提炼宏观逻辑并提供批判性洞察
5. **综合报告智能体**：整合所有分析结果生成最终报告
6. **Runtime智能体**：基于AgentScope Runtime的API服务智能体，支持HTTP请求处理

### 工作流

- **标准工作流**：基础的5智能体DAG流程（`scholarmind_pipeline.py`）
- **增强工作流**：包含输入验证、错误处理和监控的改进版本（`scholarmind_enhanced_pipeline.py`）

## 快速开始

### 环境要求

- Python 3.10+
- AgentScope 框架
- 支持的LLM服务（OpenAI、ModelScope等）

### 安装步骤

1. 克隆项目代码：
```bash
git clone <repository-url>
cd ScholarMind_MAS
```

2. 安装依赖（推荐使用锁定版本）：
```bash
# 使用锁定版本（推荐）
pip install -r requirements-lock.txt

# 或使用标准版本
pip install -r requirements.txt
```

3. 设置开发环境（可选）：
```bash
# 安装pre-commit hooks
pip install pre-commit
pre-commit install
```

4. 配置环境变量：
```bash
cp .env.example .env
# 编辑 .env 文件，填入您的 API 密钥
```

5. 运行测试（可选）：
```bash
python -m pytest
```

## 使用方法

### 交互式模式（推荐）

直接运行程序，系统将引导您完成论文分析：

```bash
python main.py
```

交互式模式支持多种输入方式：
- 论文标题：`attention is all you need`
- ArXiv ID：`1706.03762`
- ArXiv URL：`https://arxiv.org/abs/1706.03762`
- 本地PDF文件：`/path/to/paper.pdf`

### Runtime API模式

启动基于AgentScope Runtime的RESTful API服务：

```bash
# 启动Runtime服务
python main_runtime.py --mode runtime

# 或启动交互式Runtime模式
python main_runtime.py --mode interactive

# 或直接处理模式（兼容main.py功能）
python main_runtime.py --mode direct /path/to/paper.pdf
```

API服务启动后，可通过以下端点访问：
- **论文处理**: `POST http://localhost:8080/process_paper`
- **健康检查**: `GET http://localhost:8080/health`
- **就绪检查**: `GET http://localhost:8080/readiness`
- **存活检查**: `GET http://localhost:8080/liveness`

### 命令行模式

```bash
# 分析本地PDF文件
python main.py /path/to/paper.pdf --type file

# 分析ArXiv论文
python main.py "1706.03762" --type url

# 分析论文文本
python main.py "This is a paper about..." --type text

# 指定用户背景（beginner/intermediate/advanced）
python main.py /path/to/paper.pdf --background advanced

# 指定输出语言（zh/en）
python main.py /path/to/paper.pdf --language en

# 保存报告到文件
python main.py /path/to/paper.pdf --save-report
```

### 配置说明

在 `.env` 文件中配置您的API密钥：

```env
# 选择配置以下任一或多个API密钥
OPENAI_API_KEY=your-openai-api-key
MODELSCOPE_API_KEY=your-modelscope-api-key
SEMANTIC_SCHOLAR_API_KEY=your-semantic-scholar-api-key
```

## 版本信息

当前版本：**0.2.0** (详见 [CHANGELOG.md](CHANGELOG.md))

## 开发指南

### 代码质量工具

项目使用以下工具确保代码质量：

- **Black** - 代码格式化（行长度限制100字符）
- **isort** - 导入语句排序
- **flake8** - 代码风格检查
- **mypy** - 静态类型检查
- **pytest** - 测试框架，支持覆盖率报告
- **pre-commit** - Git提交前检查钩子
- **bandit** - 安全检查

### 项目结构

```
scholarmind/
├── agents/                    # 智能体实现
│   ├── base_agent.py                   # 智能体基类
│   ├── resource_retrieval_agent.py     # 资源检索智能体
│   ├── methodology_agent.py            # 方法论解析智能体
│   ├── experiment_evaluator_agent.py   # 实验评估智能体
│   ├── insight_generation_agent.py     # 洞察生成智能体
│   ├── synthesizer_agent.py            # 综合报告智能体
│   ├── interactive_agent.py            # 交互式智能体
│   └── runtime_agent.py                # Runtime API智能体
├── tools/                     # 工具集
│   └── paper_parser.py                 # 论文解析工具
├── workflows/                 # 工作流
│   ├── scholarmind_pipeline.py         # 标准工作流
│   └── scholarmind_enhanced_pipeline.py # 增强工作流
├── models/                    # 数据模型
│   └── structured_outputs.py           # 结构化输出模型
├── utils/                     # 工具模块
│   ├── logger.py                        # 日志工具
│   ├── error_handler.py                 # 错误处理
│   ├── input_validation.py              # 输入验证
│   ├── message_utils.py                 # 消息工具
│   ├── model_availability.py            # 模型可用性检查
│   ├── model_config_manager.py          # 模型配置管理
│   └── path_utils.py                    # 路径工具
├── tests/                     # 测试
│   ├── demo/                           # 演示脚本
│   ├── test_*.py                       # 测试文件
docs/                          # 文档
├── design.md                            # 设计文档
├── task.md                              # 任务文档
├── logging_guide.md                    # 日志指南
├── runtime_api.md                      # Runtime API文档
├── runtime_usage.md                    # Runtime使用指南
scripts/                       # 脚本工具
├── clean_logs.sh                        # 日志清理脚本
.github/                       # GitHub配置
├── workflows/ci.yml                     # CI/CD流水线
├── main.py                     # CLI主入口
├── main_runtime.py             # Runtime主入口
├── config.py                   # 配置文件
├── pyproject.toml              # 项目配置
├── requirements.txt            # 依赖包
├── requirements-lock.txt       # 锁定版本依赖
└── CONTRIBUTING.md             # 贡献指南
```

### 核心组件

1. **智能体（Agents）**：每个智能体负责特定的任务，通过继承 AgentScope 的 ReActAgent 实现
2. **工具（Tools）**：提供各种功能函数，如论文解析等
3. **工作流（Workflow）**：使用 AgentScope 的 Pipeline 编排智能体协作流程
4. **数据模型（Models）**：定义结构化输出格式，确保数据一致性
5. **工具模块（Utils）**：提供日志、错误处理、输入验证等通用功能
6. **配置系统**：支持环境变量的灵活配置管理

### 开发流程

1. 查看[贡献指南](CONTRIBUTING.md)了解开发规范
2. 实现新的智能体功能或工具模块
3. 编写对应的测试用例
4. 集成到工作流中
5. 运行pre-commit hooks检查代码质量
6. 运行测试验证功能
7. 提交Pull Request

## 测试

项目包含全面的测试套件，确保系统稳定性和功能正确性：

```bash
# 运行所有测试
python -m pytest

# 运行特定测试文件
python -m pytest scholarmind/tests/test_basic_functionality.py

# 生成测试覆盖率报告
python -m pytest --cov=scholarmind --cov-report=html

# 运行代码质量检查
flake8 scholarmind/
mypy scholarmind/
black --check scholarmind/
isort --check-only scholarmind/
```

### 测试覆盖范围

- 基础功能测试（论文解析、元数据提取）
- 智能体单元测试（各智能体核心功能）
- 集成测试（完整工作流测试）
- 错误处理测试
- 输入验证测试

## 许可证

本项目采用 MIT 许可证。详情请见 [LICENSE](LICENSE) 文件。

## 贡献

欢迎提交 Issue 和 Pull Request 来改进 ScholarMind！

详细的贡献指南请见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 版本发布

项目遵循 [Semantic Versioning](https://semver.org/)，详细的变更日志请见 [CHANGELOG.md](CHANGELOG.md)。

## 致谢

- [AgentScope](https://github.com/modelscope/agentscope) - 多智能体协作框架
- [ArXiv API](https://arxiv.org/help/api) - 学术论文搜索服务
