# 🚀 LiteKB Langfuse 可观测性集成

## ✅ 已完成功能

### 1. Langfuse 集成

| 文件 | 功能 |
|------|------|
| `tracing/langfuse.py` | Langfuse 客户端 (可回退) |
| `tracing/decorators.py` | LLM 追踪装饰器 |
| `tracing/prompts.py` | 提示词版本管理 |
| `tracing/middleware.py` | 自动追踪中间件 |
| `api/tracing.py` | 追踪 API 端点 |

---

## 🔧 使用配置

### 环境变量

```bash
# .env

# Langfuse (可选，不配置则回退到本地追踪)
LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY=pk-xxx
LANGFUSE_SECRET_KEY=sk-xxx
LANGFUSE_HOST=https://cloud.langfuse.com
```

### 安装依赖

```bash
pip install -r requirements-tracing.txt
```

---

## 📖 功能说明

### 1. 提示词版本管理

```python
from app.tracing.prompts import prompt_manager

# 保存提示词
prompt_manager.save_prompt(
    name="rag_system",
    prompt="你是知识库助手...",
    metadata={"description": "RAG 系统提示词"}
)

# 获取提示词
prompt = prompt_manager.get_prompt("rag_system")
print(prompt["prompt"])

# 渲染提示词
rendered = prompt_manager.render_prompt(
    "rag_system",
    variables={"context": "...", "question": "..."}
)
```

### 2. LLM 调用追踪

```python
from app.tracing.decorators import trace_llm, token_tracker

@trace_llm(provider="openai", model="gpt-4o")
async def call_llm(prompt: str):
    # 自动追踪
    response = await openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content
```

### 3. 自动中间件追踪

```python
from app.tracing.middleware import TracingMiddleware

# 自动追踪所有 API 请求
app.add_middleware(TracingMiddleware)
```

### 4. Token 统计

```python
from app.tracing.decorators import token_tracker

# 获取统计
stats = token_tracker.get_stats()
# {
#     "total_input": 10000,
#     "total_output": 50000,
#     "total_cost": 0.5,
#     "by_model": {...},
#     "by_provider": {...},
# }
```

---

## 🎯 API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/prompts` | GET | 列出所有提示词 |
| `/api/v1/prompts/{name}` | GET | 获取提示词 |
| `/api/v1/prompts` | POST | 创建/更新提示词 |
| `/api/v1/prompts/{name}/versions` | GET | 列出所有版本 |
| `/api/v1/prompts/{name}/compare` | GET | 比较版本 |
| `/api/v1/prompts/{name}/render` | POST | 渲染提示词 |
| `/api/v1/tracing/stats` | GET | 获取追踪统计 |
| `/api/v1/tracing/status` | GET | 获取追踪状态 |

---

## 📊 默认提示词模板

| 名称 | 描述 |
|------|------|
| `rag_system` | RAG 系统提示词 |
| `rag_with_history` | 带历史记录的 RAG |
| `graph_augmented` | 图谱增强 RAG |
| `summarization` | 文档摘要 |
| `entity_extraction` | 实体抽取 |

---

## 🔄 可回退机制

如果没有配置 Langfuse，系统会自动回退到本地追踪：

```python
# Langfuse 禁用时
langfuse.enabled = False

# 自动使用本地追踪
LocalTrace
LocalGeneration
LocalSpan
```

---

## 📈 成本计算

自动计算 LLM 调用成本：

```python
from app.tracing.decorators import calculate_cost

cost = calculate_cost(
    provider="openai",
    model="gpt-4o",
    input_tokens=1000,
    output_tokens=2000,
)
# 自动计算: (1/1M * $5) + (2/1M * $15) = $0.035
```

---

## 📝 文件结构

```
backend/app/
├── tracing/
│   ├── __init__.py          # 导出
│   ├── langfuse.py         # Langfuse 客户端
│   ├── decorators.py        # 追踪装饰器
│   ├── prompts.py          # 提示词管理
│   └── middleware.py       # 自动追踪
├── api/
│   └── tracing.py         # API 端点
└── requirements-tracing.txt  # 可选依赖
```

---

## 🚀 快速开始

```bash
# 1. 配置环境变量
cp .env.example .env
# 添加 LANGFUSE_ 开头的变量

# 2. 安装依赖 (可选)
pip install -r requirements-tracing.txt

# 3. 启动服务
docker-compose up -d

# 4. 访问 Langfuse (如果配置了)
# https://cloud.langfuse.com
```

---

## ✅ 检查清单

- [x] Langfuse 客户端 (可回退)
- [x] 提示词版本管理
- [x] LLM 链路跟踪
- [x] Token 使用统计
- [x] 成本计算
- [x] 自动追踪中间件
- [x] API 端点
- [x] 默认提示词模板
- [x] 本地追踪回退
