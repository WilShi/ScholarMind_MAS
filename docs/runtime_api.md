# ScholarMind Runtime API 文档

## 概述

ScholarMind Runtime 基于 AgentScope Runtime 官方架构构建，提供完整的论文分析 RESTful API 服务。支持多智能体协作的计算机学术论文解读，包括资源检索、方法论分析、实验评估、洞察生成和报告综合。

**服务地址**：`http://localhost:8080`（默认）

**API 版本**：v1.0.0

---

## 基础信息

### 认证
当前版本无需认证，所有接口均为公开访问。

### 请求格式
- Content-Type: `application/json`
- 字符编码: UTF-8
- 支持跨域请求（CORS）

### 响应格式
- Content-Type: `application/json`
- 统一响应结构
- 支持流式响应（SSE）

---

## 核心业务接口

### 1. 处理论文

**接口地址**：`POST /process_paper`

**接口描述**：执行完整的论文分析流程，使用 5 个智能体协作生成深度解读报告。

#### 请求参数

| 参数名 | 类型 | 必需 | 说明 | 可选值 |
|--------|------|------|------|--------|
| paper_input | string | 是 | 论文输入内容 | - |
| input_type | string | 是 | 输入类型 | file, url, text |
| user_background | string | 是 | 用户背景水平 | beginner, intermediate, advanced |
| output_format | string | 否 | 报告输出格式 | markdown, json |
| output_language | string | 否 | 输出语言 | zh, en |
| save_report | boolean | 否 | 是否保存报告到文件 | true, false |

#### 请求示例

```json
{
  "paper_input": "https://arxiv.org/pdf/2301.07041.pdf",
  "input_type": "url",
  "user_background": "intermediate",
  "output_format": "markdown",
  "output_language": "zh",
  "save_report": true
}
```

#### 响应示例

**成功响应**：
```json
{
  "status": "success",
  "data": {
    "success": true,
    "message": "论文处理完成",
    "processing_time": 45.2,
    "stages": {
      "resource_retrieval": {
        "success": true,
        "processing_time": 12.3,
        "paper_title": "Attention Is All You Need"
      },
      "methodology_analysis": {
        "success": true,
        "processing_time": 15.1
      },
      "experiment_evaluation": {
        "success": true,
        "processing_time": 8.7
      },
      "parallel_processing_time": 18.2,
      "insight_generation": {
        "success": true,
        "processing_time": 6.8
      },
      "synthesizer": {
        "success": true,
        "processing_time": 2.8,
        "report_title": "Attention Is All You Need - 深度解读"
      }
    },
    "outputs": {
      "paper_content": {
        "metadata": {
          "title": "Attention Is All You Need",
          "authors": ["Ashish Vaswani", "Noam Shazeer"],
          "abstract": "The dominant sequence..."
        }
      },
      "methodology_analysis": {
        "approach": "Transformer架构",
        "key_techniques": ["Self-Attention", "Multi-Head Attention"]
      },
      "experiment_evaluation": {
        "datasets": ["WMT 2014 En-De"],
        "performance_metrics": ["BLEU score: 28.4"]
      },
      "insight_analysis": {
        "key_insights": ["注意力机制的有效性", "并行计算优势"]
      },
      "report": {
        "title": "Attention Is All You Need - 深度解读",
        "summary": "本文提出了Transformer模型...",
        "key_contributions": [
          "创新的Self-Attention机制",
          "完全基于注意力的序列建模",
          "高效的并行计算能力"
        ],
        "insights": [
          "Attention机制在NLP领域的革命性影响",
          "为后续大语言模型奠定基础"
        ]
      },
      "report_path": "/path/to/saved/report.md"
    },
    "metadata": {
      "user_background": "intermediate",
      "input_type": "url",
      "output_format": "markdown",
      "output_language": "zh"
    }
  }
}
```

**错误响应**：
```json
{
  "status": "error",
  "errors": ["文件不存在: /path/to/paper.pdf"],
  "message": "请求处理失败: 文件不存在: /path/to/paper.pdf"
}
```

#### 流式响应

支持服务器发送事件（SSE）进行实时进度反馈：

```bash
curl -X POST http://localhost:8080/process_paper \
  -H "Content-Type: application/json" \
  -d '{...}' \
  --no-buffer
```

---

### 2. 验证输入参数

**接口地址**：`POST /validate_inputs`

**接口描述**：在执行论文处理前验证输入参数的有效性。

#### 请求参数

| 参数名 | 类型 | 必需 | 说明 |
|--------|------|------|------|
| paper_input | string | 是 | 论文输入内容 |
| input_type | string | 是 | 输入类型 |
| user_background | string | 是 | 用户背景水平 |

#### 请求示例

```json
{
  "paper_input": "paper.pdf",
  "input_type": "file",
  "user_background": "advanced"
}
```

#### 响应示例

```json
{
  "status": "success",
  "data": {
    "valid": true,
    "errors": []
  }
}
```

**验证失败示例**：
```json
{
  "status": "success",
  "data": {
    "valid": false,
    "errors": [
      "文件不存在: /path/to/paper.pdf",
      "用户背景必须是 beginner、intermediate 或 advanced"
    ]
  }
}
```

---

### 3. 获取工作流状态

**接口地址**：`GET /pipeline_status`

**接口描述**：获取当前工作流的配置信息和状态。

#### 响应示例

```json
{
  "status": "success",
  "data": {
    "name": "scholarmind_phase3_pipeline",
    "agents": [
      {
        "name": "ResourceRetrievalAgent",
        "type": "ResourceRetrievalAgent"
      },
      {
        "name": "MethodologyAgent",
        "type": "MethodologyAgent"
      },
      {
        "name": "ExperimentEvaluatorAgent",
        "type": "ExperimentEvaluatorAgent"
      },
      {
        "name": "InsightGenerationAgent",
        "type": "InsightGenerationAgent"
      },
      {
        "name": "SynthesizerAgent",
        "type": "SynthesizerAgent"
      }
    ],
    "pipeline_type": "Complete DAG (5 agents)",
    "parallel_agents": ["MethodologyAgent", "ExperimentEvaluatorAgent"],
    "workflow_stages": [
      "1. Resource Retrieval",
      "2. Parallel Analysis (Methodology + Experiment)",
      "3. Insight Generation",
      "4. Report Synthesis"
    ]
  }
}
```

---

## 健康检查接口

### 1. 基本健康检查

**接口地址**：`GET /health`

**接口描述**：检查服务基本运行状态。

#### 响应示例

```json
{
  "status": "healthy",
  "service": "scholarmind-service",
  "version": "1.0.0",
  "timestamp": 1703123456.789
}
```

### 2. 就绪状态检查

**接口地址**：`GET /readiness`

**接口描述**：检查服务是否准备好接收请求（Kubernetes 就绪探针）。

#### 响应示例

```json
{
  "status": "ready",
  "checks": {
    "database": "ok",
    "model_loaded": "ok",
    "dependencies": "ok"
  }
}
```

### 3. 存活状态检查

**接口地址**：`GET /liveness`

**接口描述**：检查服务是否存活（Kubernetes 存活探针）。

#### 响应示例

```json
{
  "status": "alive",
  "uptime": 3600,
  "last_request": 1703123456.789
}
```

---

## 错误码说明

| HTTP 状态码 | 说明 | 示例场景 |
|------------|------|----------|
| 200 | 请求成功 | 正常处理完成 |
| 400 | 请求参数错误 | 缺少必需参数、参数格式错误 |
| 404 | 资源不存在 | 接口地址错误 |
| 500 | 服务器内部错误 | 处理过程中出现异常 |
| 503 | 服务不可用 | 服务正在启动或关闭 |

---

## 使用示例

### cURL 示例

#### 处理论文文件
```bash
curl -X POST http://localhost:8080/process_paper \
  -H "Content-Type: application/json" \
  -d '{
    "paper_input": "/path/to/paper.pdf",
    "input_type": "file",
    "user_background": "intermediate",
    "output_language": "zh",
    "save_report": true
  }'
```

#### 处理 ArXiv 论文
```bash
curl -X POST http://localhost:8080/process_paper \
  -H "Content-Type: application/json" \
  -d '{
    "paper_input": "https://arxiv.org/pdf/2301.07041.pdf",
    "input_type": "url",
    "user_background": "advanced",
    "output_format": "json"
  }'
```

#### 处理论文文本
```bash
curl -X POST http://localhost:8080/process_paper \
  -H "Content-Type: application/json" \
  -d '{
    "paper_input": "Attention Is All You Need\n\nAbstract: The dominant sequence...",
    "input_type": "text",
    "user_background": "beginner"
  }'
```

### Python 示例

```python
import requests
import json

# 服务地址
BASE_URL = "http://localhost:8080"

def process_paper(paper_input, input_type="url", user_background="intermediate"):
    """处理论文"""
    url = f"{BASE_URL}/process_paper"

    payload = {
        "paper_input": paper_input,
        "input_type": input_type,
        "user_background": user_background,
        "output_language": "zh",
        "save_report": True
    }

    response = requests.post(url, json=payload)

    if response.status_code == 200:
        result = response.json()
        if result["status"] == "success":
            report = result["data"]["outputs"]["report"]
            print(f"论文标题: {report['title']}")
            print(f"摘要: {report['summary']}")
            return result
        else:
            print(f"处理失败: {result['message']}")
    else:
        print(f"请求失败: {response.status_code}")

# 使用示例
result = process_paper("https://arxiv.org/pdf/2301.07041.pdf")
```

### JavaScript 示例

```javascript
// 处理论文
async function processPaper(paperInput, inputType = 'url', userBackground = 'intermediate') {
    const response = await fetch('http://localhost:8080/process_paper', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            paper_input: paperInput,
            input_type: inputType,
            user_background: userBackground,
            output_language: 'zh',
            save_report: true
        })
    });

    const result = await response.json();

    if (result.status === 'success') {
        console.log('论文标题:', result.data.outputs.report.title);
        console.log('摘要:', result.data.outputs.report.summary);
        return result;
    } else {
        console.error('处理失败:', result.message);
    }
}

// 使用示例
processPaper('https://arxiv.org/pdf/2301.07041.pdf');
```

---

## 性能说明

### 处理时间
- **资源检索**：10-15 秒
- **并行分析**：15-20 秒
- **洞察生成**：5-10 秒
- **报告综合**：2-5 秒
- **总计**：30-50 秒（取决于论文长度和复杂度）

### 并发支持
- 支持多客户端并发访问
- 建议最大并发数：5-10 个请求
- 超时时间：300 秒（5 分钟）

### 资源要求
- **内存**：建议 4GB 以上
- **CPU**：建议 4 核以上
- **网络**：稳定的互联网连接（用于在线论文获取）

---

## 部署说明

### 启动服务
```bash
# 默认配置启动
python main_runtime.py --mode runtime

# 自定义主机和端口
python main_runtime.py --mode runtime --host 0.0.0.0 --port 9000

# 后台运行
nohup python main_runtime.py --mode runtime > runtime.log 2>&1 &
```

### Docker 部署
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8080

CMD ["python", "main_runtime.py", "--mode", "runtime", "--host", "0.0.0.0"]
```

### 环境变量
```bash
export OPENAI_API_KEY="your_api_key_here"
export DASHSCOPE_API_KEY="your_dashscope_key_here"
```

---

## 更新日志

### v1.0.0
- 基于 AgentScope Runtime 官方架构重构
- 支持 5 智能体协作分析
- 提供完整的 RESTful API
- 支持流式响应和健康检查
- 完善的错误处理和日志记录

---

## 技术支持

如有问题或建议，请通过以下方式联系：

- 项目地址：https://github.com/WilShi/ScholarMind_MAS
- 文档地址：[项目文档目录]
- 问题反馈：GitHub Issues

---

*本文档最后更新时间：2025年10月*
