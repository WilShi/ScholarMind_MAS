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
  <a href="#开发指南">开发指南</a>
</p>

## 项目简介

ScholarMind（智读）是一个先进的多智能体协作系统，旨在将复杂的计算机学术论文自动转化为结构清晰、深入浅出的解读报告。通过模拟专家团队的研讨过程，ScholarMind 能够深度解析论文的方法论、评估其实验设计，并提供批判性洞察，赋能科研与学习。

## 功能特性

- **智能体协作架构**：采用5个专业角色智能体协同工作，包括资源检索、方法论解析、实验评估、洞察生成和综合报告生成
- **并行处理能力**：支持方法论分析与实验评估的并行处理，大幅提升处理效率
- **多种输入方式**：
  - 交互式对话模式（智能识别论文标题、ArXiv URL/ID、本地PDF文件）
  - 命令行参数指定论文文件、URL或文本内容
- **智能输入识别**：自动识别并处理多种论文输入格式
- **学术API集成**：集成ArXiv API，支持通过论文标题搜索论文
- **多语言支持**：支持中英文双语输出
- **个性化报告**：根据用户技术背景（初级/中级/高级）调整报告深度
- **零LLM参数收集**：在交互模式下，参数收集阶段不调用LLM，节省API资源
- **结构化输出**：生成包含标题、摘要、关键贡献、洞察等结构化内容的报告

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

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 配置环境变量：
```bash
cp .env.example .env
# 编辑 .env 文件，填入您的 API 密钥
```

4. 运行测试（可选）：
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

## 开发指南

### 项目结构

```
scholarmind/
├── agents/                    # 智能体实现
│   ├── resource_retrieval_agent.py      # 资源检索智能体
│   ├── methodology_agent.py             # 方法论解析智能体
│   ├── experiment_evaluator_agent.py    # 实验评估智能体
│   ├── insight_generation_agent.py      # 洞察生成智能体
│   ├── synthesizer_agent.py             # 综合报告智能体
│   └── interactive_agent.py             # 交互式智能体
├── tools/                     # 工具集
│   ├── paper_parser.py                  # 论文解析工具
│   ├── academic_search.py               # 学术搜索工具
│   └── report_generator.py              # 报告生成工具
├── workflows/                 # 工作流
│   └── scholarmind_pipeline.py          # 主工作流
├── models/                    # 数据模型
│   └── structured_outputs.py            # 结构化输出模型
├── tests/                     # 测试
├── main.py                    # 主入口
├── config.py                  # 配置文件
└── requirements.txt           # 依赖包
```

### 核心组件

1. **智能体（Agents）**：每个智能体负责特定的任务，通过继承 AgentScope 的 ReActAgent 实现
2. **工具（Tools）**：提供各种功能函数，如论文解析、学术搜索等
3. **工作流（Workflow）**：使用 AgentScope 的 Pipeline 编排智能体协作流程
4. **数据模型（Models）**：定义结构化输出格式，确保数据一致性

### 开发流程

1. 实现新的智能体功能
2. 编写对应的测试用例
3. 集成到工作流中
4. 运行测试验证功能

## 测试

项目包含全面的测试套件，确保系统稳定性和功能正确性：

```bash
# 运行所有测试
python -m pytest

# 运行特定测试文件
python -m pytest scholarmind/tests/test_basic_functionality.py
```

## 许可证

本项目采用 MIT 许可证。详情请见 [LICENSE](LICENSE) 文件。

## 贡献

欢迎提交 Issue 和 Pull Request 来改进 ScholarMind！

## 致谢

- [AgentScope](https://github.com/modelscope/agentscope) - 多智能体协作框架
- [ArXiv API](https://arxiv.org/help/api) - 学术论文搜索服务