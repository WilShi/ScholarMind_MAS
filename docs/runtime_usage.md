# ScholarMind Runtime 使用指南

## 概述

`main_runtime.py` 是基于 FastAPI 和 AgentScope 的多智能体服务版本，提供了三种运行模式：

1. **Runtime 模式** - 作为 HTTP API 服务运行（基于 FastAPI）
2. **Interactive 模式** - 交互式对话模式  
3. **Direct 模式** - 直接处理模式（兼容原 main.py）

## 安装依赖

确保已安装所需依赖：

```bash
pip install -r requirements.txt
pip install agentscope-runtime  # 包含 FastAPI 和 uvicorn
```

## 使用方法

### 1. Runtime 服务模式

启动 HTTP API 服务：

```bash
# 默认配置启动
python main_runtime.py --mode runtime

# 自定义主机和端口
python main_runtime.py --mode runtime --host 0.0.0.0 --port 9000

# 设置最大并发请求数
python main_runtime.py --mode runtime --max-concurrent 10
```

服务启动后，可通过以下 API 端点访问：

- `POST /process_paper` - 处理论文
- `POST /validate_inputs` - 验证输入参数
- `GET /pipeline_status` - 获取工作流状态
- `GET /health` - 健康检查

**特性**：
- 基于 FastAPI 的 RESTful API
- 完整的请求验证和错误处理
- 支持所有原有的论文处理功能
- 实时健康检查和状态监控

#### API 使用示例

**处理论文：**
```bash
curl -X POST http://localhost:8080/process_paper \
  -H "Content-Type: application/json" \
  -d '{
    "paper_input": "path/to/paper.pdf",
    "input_type": "file",
    "user_background": "intermediate",
    "output_format": "markdown",
    "output_language": "zh",
    "save_report": true
  }'
```

**验证输入：**
```bash
curl -X POST http://localhost:8080/validate_inputs \
  -H "Content-Type: application/json" \
  -d '{
    "paper_input": "path/to/paper.pdf",
    "input_type": "file",
    "user_background": "intermediate"
  }'
```

**获取工作流状态：**
```bash
curl http://localhost:8080/pipeline_status
```

**健康检查：**
```bash
curl http://localhost:8080/health
```

**响应示例：**
```json
{
  "status": "success",
  "data": {
    "success": true,
    "processing_time": 45.2,
    "outputs": {
      "report": {
        "title": "论文标题",
        "summary": "论文摘要...",
        "key_contributions": ["贡献1", "贡献2"],
        "insights": ["洞察1", "洞察2"]
      }
    }
  }
}
```

### 2. 交互式模式

启动交互式对话：

```bash
python main_runtime.py --mode interactive
```

### 3. 直接处理模式

与原 main.py 功能相同：

```bash
# 处理本地文件
python main_runtime.py --mode direct path/to/paper.pdf

# 处理在线论文
python main_runtime.py --mode direct https://arxiv.org/abs/2301.07041 --type url

# 自定义参数
python main_runtime.py --mode direct paper.pdf \
  --background advanced \
  --output-format json \
  --language en \
  --save-report
```

## 命令行参数

### 通用参数

- `--mode`: 运行模式 (`runtime`, `interactive`, `direct`)
- `--host`: 服务主机地址 (默认: localhost)
- `--port`: 服务端口 (默认: 8080)
- `--max-concurrent`: 最大并发请求数 (默认: 5)

### Direct 模式专用参数

- `input`: 论文输入（文件路径、URL或文本）
- `--type`: 输入类型 (`file`, `url`, `text`)
- `--background`: 用户背景 (`beginner`, `intermediate`, `advanced`)
- `--output-format`: 输出格式 (`markdown`, `json`)
- `--language`: 输出语言 (`zh`, `en`)
- `--save-report`: 保存报告到文件

## 服务配置

Runtime 服务可以通过代码配置或环境变量进行自定义：

```python
# 在 ScholarMindRuntimeService 中修改配置
self.service_config = {
    "name": "scholarmind-service",
    "version": "1.0.0",
    "description": "智读ScholarMind多智能体论文解读服务",
    "host": "localhost",
    "port": 8080,
    "max_concurrent_requests": 5
}
```

## 错误处理

Runtime 服务提供完善的错误处理机制：

- API 请求验证
- 参数格式检查
- 服务异常捕获
- 详细错误日志

## 监控和日志

- 使用 `scholarmind.runtime` logger 记录服务日志
- 支持健康检查端点监控服务状态
- 提供工作流状态查询接口

## 与原 main.py 的区别

| 特性 | main.py | main_runtime.py |
|------|---------|-----------------|
| 运行模式 | 单次处理/交互 | 服务/API/交互/直接 |
| 并发处理 | 不支持 | 支持多并发请求 |
| API 接口 | 无 | RESTful API |
| 服务管理 | 无 | 完整的服务生命周期 |
| 监控能力 | 基础日志 | 健康检查、状态查询 |

## 故障排除

1. **端口占用错误**：更换端口或停止占用端口的进程
2. **依赖缺失**：确保安装所有必需依赖
3. **权限问题**：检查文件读取权限和目录写入权限
4. **API 错误**：检查请求参数格式和必需字段

## 开发和扩展

可以通过以下方式扩展 runtime 服务：

1. 添加新的 API 端点
2. 自定义服务配置
3. 集成外部监控系统
4. 添加认证和授权机制

参考 `ScholarMindRuntimeService` 类的实现进行扩展。