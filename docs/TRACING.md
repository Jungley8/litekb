# 🚀 LiteKB Langfuse 提示词管理

## ✅ 集成方式

**所有 RAG/图谱/文档处理使用 Langfuse 提示词**

---

## 🔧 配置

```bash
# .env
LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY=pk-xxx
LANGFUSE_SECRET_KEY=sk-xxx
```

---

## 📁 提示词文件

```
backend/app/services/prompt.py
```

---

## 🎯 支持的提示词

| 名称 | 用途 |
|------|------|
| `rag_naive` | 基础 RAG |
| `rag_contextual` | 上下文 RAG |
| `rag_graph` | 图谱增强 RAG |
| `doc_summarize` | 文档摘要 |
| `entity_extraction` | 实体抽取 |
| `relation_extraction` | 关系抽取 |
| `graph_query` | 图谱查询 |

---

## 📖 使用方式

```python
from app.services.prompt import get_prompt, rag_prompt

# RAG 提示词
prompt = rag_prompt(
    mode="naive",
    question="...",
    context="...",
    history="...",
)

# 实体抽取
prompt = entity_extraction_prompt(text)

# 文档摘要
prompt = summarize_prompt(content, max_length="200")
```

---

## 🔄 自动同步

启动时自动同步默认提示词到 Langfuse：

```python
from app.services.prompt import prompt_manager

# 同步所有
prompt_manager.sync_all_to_langfuse()
```

---

## 📊 Langfuse 面板

访问 https://cloud.langfuse.com 管理：

- 修改提示词 (自动版本)
- 查看使用情况
- 分析 Token 消耗

---

## ✅ 检查清单

- [x] RAG 对话 → Langfuse 提示词
- [x] 图谱查询 → Langfuse 提示词
- [x] 文档摘要 → Langfuse 提示词
- [x] 实体抽取 → Langfuse 提示词
- [x] 自动版本管理
- [x] 无需 API (内部使用)
