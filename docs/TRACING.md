# 🚀 LiteKB Langfuse 可观测性集成

## ✅ 全部使用 Langfuse 原生 API

---

## 🔧 配置

### 环境变量

```bash
# .env

# Langfuse (必需)
LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY=pk-xxx
LANGFUSE_SECRET_KEY=sk-xxx
LANGFUSE_HOST=https://cloud.langfuse.com  # 可选，默认 cloud
```

### 安装依赖

```bash
pip install langfuse>=2.0.0
```

---

## 📖 功能

### 1. 提示词管理 (Langfuse Prompt Management)

Langfuse 自动管理提示词版本。

```python
from app.tracing import create_prompt, get_prompt, list_prompts

# 创建提示词 (自动版本管理)
create_prompt(
    name="rag_system",
    prompt="你是知识库助手...",
    config={"temperature": 0.1}
)

# 获取提示词
prompt = get_prompt("rag_system")  # 最新版本
prompt = get_prompt("rag_system", version=2)  # 指定版本

# 列出所有提示词
prompts = list_prompts()

# 渲染提示词
rendered = render_prompt(
    "rag_system",
    variables={"context": "...", "question": "..."}
)
```

---

### 2. Token & Cost 统计 (Langfuse Tracing)

自动记录 LLM 调用并统计成本。

```python
from app.tracing import get_token_stats, get_generations

# 获取 Token 统计
stats = get_token_stats()
# {
#     "total_input_tokens": 100000,
#     "total_output_tokens": 500000,
#     "total_cost": 5.0,
#     "by_model": {
#         "gpt-4o": {"input": 50000, "output": 200000, "cost": 2.5}
#     }
# }

# 获取详细生成记录
generations = get_generations(name="llm_call", limit=100)
```

---

### 3. LLM 调用追踪

```python
from app.tracing import llm_tracker

@llm_tracker.trace_call(provider="openai", model="gpt-4o")
async def call_llm(prompt: str):
    response = await openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content
```

---

## 📡 API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/prompts` | GET | 列出所有提示词 |
| `/api/v1/prompts/{name}` | GET | 获取提示词 |
| `/api/v1/prompts` | POST | 创建提示词 |
| `/api/v1/prompts/{name}` | PUT | 更新提示词 |
| `/api/v1/prompts/{name}/versions` | GET | 版本历史 |
| `/api/v1/prompts/{name}/render` | POST | 渲染提示词 |
| `/api/v1/tracing/stats` | GET | Token 统计 |
| `/api/v1/tracing/generations` | GET | 生成记录 |
| `/api/v1/tracing/status` | GET | 追踪状态 |

---

## 🎯 使用示例

### 创建提示词

```bash
curl -X POST http://localhost:8000/api/v1/prompts \
  -H "Content-Type: application/json" \
  -d '{
    "name": "rag_system",
    "prompt": "你是知识库助手...",
    "config": {"temperature": 0.1}
  }'
```

### 获取 Token 统计

```bash
curl http://localhost:8000/api/v1/tracing/stats
# {
#     "enabled": true,
#     "stats": {
#         "total_input_tokens": 12345,
#         "total_output_tokens": 67890,
#         "total_cost": 1.23
#     }
# }
```

---

## 📊 Langfuse 面板

访问 https://cloud.langfuse.com 查看：

- **Prompts** - 提示词管理
- **Traces** - 链路追踪
- **Generations** - Token 使用
- **Cost** - 成本分析

---

## 🔄 与本地追踪对比

| 功能 | Langfuse API | 本地追踪 |
|------|-------------|---------|
| 提示词版本 | ✅ 自动管理 | ❌ 需要自己实现 |
| Token 统计 | ✅ 自动计算 | ❌ 需要自己实现 |
| 成本分析 | ✅ 自动计算 | ❌ 需要自己实现 |
| 版本历史 | ✅ 完整记录 | ❌ 需要自己实现 |
| 数据持久化 | ✅ 云端存储 | ❌ 内存/文件 |
| 协作 | ✅ 团队共享 | ❌ 单机 |

---

## ✅ 检查清单

- [x] 提示词管理 (Langfuse Prompt Management)
- [x] Token/Cost 统计 (Langfuse Tracing)
- [x] LLM 链路追踪
- [x] API 端点
- [x] 自动版本管理
- [x] 成本分析

---

## 📁 文件结构

```
backend/app/tracing/
├── __init__.py          # 导出
├── langfuse.py         # Langfuse API
└── decorators.py        # 追踪装饰器
```

---

## 🚀 快速开始

```bash
# 1. 配置 Langfuse
export LANGFUSE_ENABLED=true
export LANGFUSE_PUBLIC_KEY=pk-xxx
export LANGFUSE_SECRET_KEY=sk-xxx

# 2. 启动
docker-compose up -d

# 3. 访问 Langfuse
# https://cloud.langfuse.com
```
