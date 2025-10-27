# ScholarMind 日志配置指南

## 📋 日志目录结构

所有日志文件统一存放在 `logs/` 目录下：

```
logs/
├── scholarmind.log          # 主应用日志
├── access.log               # HTTP 访问日志（Runtime模式）
├── app.log                  # 应用级别日志
├── error.log.{PID}          # AgentScope Runtime 错误日志
└── info.log.{PID}           # AgentScope Runtime 信息日志
```

---

## ⚙️ 配置方式

### 1. 环境变量配置

在 `.env` 文件中配置：

```bash
# 日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
LOG_LEVEL=INFO

# 日志目录
LOG_DIR=logs

# 主日志文件路径
LOG_FILE=logs/scholarmind.log
```

### 2. 代码中使用

#### 基础日志使用

```python
from scholarmind.utils.logger import setup_logger

# 创建logger
logger = setup_logger('my_module', log_file='logs/my_module.log')

# 记录日志
logger.info("信息日志")
logger.warning("警告日志")
logger.error("错误日志")
logger.debug("调试日志")
```

#### 使用预定义的Logger

```python
from scholarmind.utils.logger import agent_logger, pipeline_logger, tool_logger

# Agent日志
agent_logger.info("智能体执行中...")

# Pipeline日志
pipeline_logger.info("流程开始执行")

# Tool日志
tool_logger.info("工具调用成功")
```

#### 中文路径日志（ScholarMindLogger）

```python
from scholarmind.utils.logger import ScholarMindLogger

logger = ScholarMindLogger('my_module')

# 记录带中文路径的操作
logger.info_path("读取文件", "/路径/到/中文文件.pdf")
logger.error_path("文件不存在", "/不存在的/文件.txt", message="请检查路径")
```

---

## 📊 日志级别说明

| 级别 | 用途 | 示例 |
|------|------|------|
| **DEBUG** | 详细的调试信息 | 变量值、函数调用栈 |
| **INFO** | 一般信息性消息 | 程序启动、任务完成 |
| **WARNING** | 警告信息，不影响运行 | 参数使用默认值、性能问题 |
| **ERROR** | 错误信息，功能受影响 | 文件读取失败、API调用失败 |
| **CRITICAL** | 严重错误，程序可能崩溃 | 数据库连接失败、内存溢出 |

---

## 🔧 日志格式

默认日志格式：
```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

输出示例：
```
2025-01-27 10:30:45 - scholarmind.agent - INFO - 论文解析完成
2025-01-27 10:30:46 - scholarmind.pipeline - WARNING - 模型响应较慢
2025-01-27 10:30:47 - scholarmind.tool - ERROR - ArXiv API 调用失败
```

自定义格式（通过环境变量）：
```bash
LOG_FORMAT="%(levelname)s | %(name)s | %(message)s"
```

---

## 🧹 日志管理

### 1. 手动清理

```bash
# 清理空日志文件
find logs/ -type f -size 0 -delete

# 清理所有日志
rm -rf logs/*

# 使用清理脚本
bash scripts/clean_logs.sh
```

### 2. 日志轮转（推荐用于生产环境）

```python
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    'logs/scholarmind.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5            # 保留5个备份
)
```

### 3. 按日期归档

```python
from logging.handlers import TimedRotatingFileHandler

handler = TimedRotatingFileHandler(
    'logs/scholarmind.log',
    when='midnight',  # 每天午夜轮转
    interval=1,       # 间隔1天
    backupCount=7     # 保留7天
)
```

---

## 🎯 不同模式的日志

### CLI 模式
```bash
python main.py paper.pdf
# 日志输出到: logs/scholarmind.log
```

### Runtime API 模式
```bash
python main_runtime.py --mode runtime
# 日志输出到:
# - logs/scholarmind.log (应用日志)
# - logs/error.log.{PID} (错误日志)
# - logs/info.log.{PID} (信息日志)
# - logs/access.log (HTTP访问日志)
```

### Interactive 模式
```bash
python main_runtime.py --mode interactive
# 日志输出到: logs/scholarmind.log
```

---

## 📝 最佳实践

### 1. 日志级别使用建议

```python
# ✅ 好的做法
logger.debug(f"函数参数: {params}")  # 调试信息
logger.info("任务开始执行")           # 一般信息
logger.warning("使用默认配置")        # 警告
logger.error(f"处理失败: {error}")   # 错误

# ❌ 不好的做法
logger.info("变量x的值是123")        # 应该用debug
logger.error("用户输入了错误参数")    # 应该用warning
```

### 2. 日志消息编写

```python
# ✅ 清晰明确
logger.info(f"论文解析完成: {paper_title}, 用时 {elapsed:.2f}秒")

# ❌ 信息不足
logger.info("完成")
```

### 3. 异常日志

```python
# ✅ 包含完整堆栈
try:
    process_paper(file_path)
except Exception as e:
    logger.error(f"论文处理失败: {e}", exc_info=True)

# ❌ 丢失堆栈信息
try:
    process_paper(file_path)
except Exception as e:
    logger.error(f"失败: {e}")
```

### 4. 敏感信息保护

```python
# ✅ 不记录敏感信息
logger.info(f"API调用成功, 用户: {user_id[:4]}****")

# ❌ 记录了完整API密钥
logger.debug(f"API Key: {api_key}")  # 危险！
```

---

## 🔍 日志分析

### 查看错误日志
```bash
grep "ERROR" logs/scholarmind.log
```

### 统计不同级别日志数量
```bash
awk '{print $5}' logs/scholarmind.log | sort | uniq -c
```

### 查看最近的日志
```bash
tail -f logs/scholarmind.log
```

### 搜索特定模块的日志
```bash
grep "scholarmind.agent" logs/scholarmind.log
```

---

## ⚠️ 注意事项

1. **日志目录已添加到 .gitignore**，不会被提交到版本控制
2. **定期清理日志**，防止占用过多磁盘空间
3. **生产环境建议使用日志轮转**，避免单个文件过大
4. **不要在日志中记录敏感信息**（API密钥、密码等）
5. **合理使用日志级别**，避免日志过多或过少

---

## 🆘 故障排查

### 问题：日志文件不生成

**解决方法**：
```bash
# 检查logs目录是否存在
ls -la logs/

# 手动创建logs目录
mkdir -p logs/

# 检查权限
chmod 755 logs/
```

### 问题：日志中文乱码

**解决方法**：
```python
# 确保使用UTF-8编码
logger = setup_logger('my_module')  # 已默认使用UTF-8
```

### 问题：日志文件过大

**解决方法**：
```bash
# 使用日志轮转
# 或清理旧日志
find logs/ -name "*.log" -mtime +7 -delete  # 删除7天前的日志
```

---

*最后更新: 2025-01-27*
