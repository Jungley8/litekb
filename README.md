# LiteKB - 轻量级开源知识库系统

> **目标**：最容易上手、支持 RAG + 混合检索 + 知识图谱的开源知识库

---

## 一、技术架构

### 后端 (Python + FastAPI)

| 组件 | 选择 | 理由 |
|------|------|------|
| **框架** | FastAPI | 异步高性能、自动文档、类型安全 |
| **数据库** | SQLite + PostgreSQL (可选) | SQLite 零配置，PostgreSQL 生产级 |
| **向量库** | Qdrant | 轻量、Rust 写、支持混合检索 |
| **图数据库** | Neo4j (可选) / NetworkX (内存) | 知识图谱构建 |
| **LLM 集成** | LangChain (轻量使用) | 避免过度抽象 |
| **文档解析** | Apache Tika + python-docx | 支持多种格式 |

### 前端 (Node.js + Vue 3)

| 组件 | 选择 | 理由 |
|------|------|------|
| **框架** | Vue 3 + Vite | 开发快、类型友好 |
| **UI 库** | Naive UI | Vue 生态、主题友好 |
| **状态管理** | Pinia | Vue 官方推荐 |
| **图表** | D3.js / Vue Flow | 知识图谱可视化 |
| **搜索UI** | Algolia InstantSearch (自托管) | 混合检索体验 |

### 部署

| 方式 | 说明 |
|------|------|
| **Docker Compose** | 本地开发一键启动 |
| **Kubernetes** | 生产环境 |
| ** Railway / Vercel** | 前端托管 |
| **Render / Fly.io** | 后端托管 |

---

## 二、系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         LiteKB 整体架构                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Frontend (Vue 3)                       │   │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────────────────┐  │   │
│  │  │ 知识库    │ │ 文档管理  │ │    知识图谱可视化      │  │   │
│  │  │ 管理界面  │ │ 界面      │ │    (D3/Vue Flow)      │  │   │
│  │  └───────────┘ └───────────┘ └───────────────────────┘  │   │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────────────────┐  │   │
│  │  │ RAG 对话  │ │ 搜索中心  │ │    系统设置           │  │   │
│  │  │ 界面      │ │ (混合检索)│ │                       │  │   │
│  │  └───────────┘ └───────────┘ └───────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                    REST API / WebSocket                        │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  Backend API (FastAPI)                   │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌───────────────────┐  │   │
│  │  │ Auth        │ │ Documents   │ │ Knowledge Graph   │  │   │
│  │  │ (JWT)       │ │ Service     │ │ Service           │  │   │
│  │  └─────────────┘ └─────────────┘ └───────────────────┘  │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌───────────────────┐  │   │
│  │  │ RAG         │ │ Search      │ │ Agent             │  │   │
│  │  │ Engine      │ │ (Hybrid)    │ │ Service           │  │   │
│  │  └─────────────┘ └─────────────┘ └───────────────────┘  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│            ┌────────────────┼────────────────┐                 │
│            ▼                ▼                ▼                 │
│  ┌──────────────────┐ ┌──────────────┐ ┌──────────────────┐    │
│  │ Qdrant           │ │ PostgreSQL   │ │ Neo4j / NetworkX │    │
│  │ (向量存储)        │ │ (元数据/关系) │ │ (知识图谱)        │    │
│  └──────────────────┘ └──────────────┘ └──────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    LLM Services                          │   │
│  │  OpenAI / Anthropic / Ollama (本地) / HuggingFace       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 三、核心功能模块

### 1. 文档处理流水线

```
文档上传 → 格式检测 → 文本提取 → 分块 → 向量化 → 存储
                                    │
                                    ▼
                              知识图谱构建
                              (实体/关系抽取)
```

### 2. 混合检索引擎

```python
class HybridSearchEngine:
    """混合检索：关键词 + 向量 + 图关系"""

    async def search(
        self,
        query: str,
        strategy: SearchStrategy = "hybrid",  # vector | keyword | graph | hybrid
        top_k: int = 10,
        filters: dict = None
    ) -> SearchResult:
        """混合检索"""

        # 1. 向量检索
        vector_results = await self.vector_search(query, top_k)

        # 2. BM25 关键词检索
        keyword_results = await self.keyword_search(query, top_k)

        # 3. 图检索 (实体链接)
        graph_results = await self.graph_search(query, top_k)

        # 4. RRF 融合排序 (Reciprocal Rank Fusion)
        fused_results = self.rrf_fuse(
            vector_results,
            keyword_results,
            graph_results
        )

        return fused_results
```

### 3. RAG 引擎

```python
class RAGEngine:
    def __init__(self, search_engine, llm_client):
        self.search = search_engine
        self.llm = llm_client

    async def query(
        self,
        question: str,
        mode: str = "naive",  # naive | contextual | graph-augmented
        system_prompt: str = None
    ) -> RAGResponse:
        """RAG 查询"""

        if mode == "naive":
            # 标准 RAG
            chunks = await self.search.search(question)
            context = self.build_context(chunks)

        elif mode == "contextual":
            # 上下文增强 RAG
            chunks = await self.search.search(question)
            context = self.build_context_with_summary(chunks)

        elif mode == "graph-augmented":
            # 图增强 RAG
            graph_context = await self.get_graph_context(question)
            chunks = await self.search.search(question)
            context = self.combine_context(graph_context, chunks)

        # 调用 LLM
        answer = await self.llm.generate(
            context + question,
            system_prompt=system_prompt
        )

        # 来源追溯
        sources = self.extract_sources(chunks)

        return RAGResponse(answer, sources)
```

### 4. 知识图谱服务

```python
class KnowledgeGraphService:
    """知识图谱构建与查询"""

    async def build_from_document(self, doc_id: str) -> Graph:
        """从文档构建知识图谱"""

        # 1. 提取实体 (使用 LLM 或 NER)
        entities = await self.extract_entities(doc_id)

        # 2. 提取关系
        relations = await self.extract_relations(doc_id, entities)

        # 3. 构建图
        graph = self.create_graph(entities, relations)

        # 4. 存储到 Neo4j 或 NetworkX
        await self.save_graph(graph)

        return graph

    async def query_graph(self, query: str) -> GraphResult:
        """图查询 - 探索相关实体"""
        # Cypher 查询或自然语言查询
        pass

    def visualize_graph(self, graph_id: str) -> GraphViz:
        """生成图可视化数据"""
        pass
```

---

## 四、数据模型

### 核心 Schema

```python
# documents.sql (PostgreSQL)

CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    file_type VARCHAR(50),
    file_path TEXT,
    file_size BIGINT,
    metadata JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'pending',  -- pending, processing, indexed, failed
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE knowledge_bases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    config JSONB DEFAULT '{}',  -- embedding模型、检索策略等
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE kb_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kb_id UUID REFERENCES knowledge_bases(id) ON DELETE CASCADE,
    doc_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_count INT DEFAULT 0,
    added_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(kb_id, doc_id)
);

-- 知识图谱表 (Neo4j 或 NetworkX 导出)
CREATE TABLE graph_entities (
    id UUID PRIMARY KEY,
    doc_id UUID REFERENCES documents(id),
    entity_type VARCHAR(100),
    entity_name VARCHAR(500),
    properties JSONB DEFAULT '{}',
    embedding VECTOR(384)  -- 可选，用于语义搜索
);

CREATE TABLE graph_relations (
    id UUID PRIMARY KEY,
    source_entity_id UUID REFERENCES graph_entities(id),
    target_entity_id UUID REFERENCES graph_entities(id),
    relation_type VARCHAR(100),
    properties JSONB DEFAULT '{}',
    confidence FLOAT DEFAULT 1.0
);
```

---

## 五、API 设计

### 核心 Endpoints

```yaml
# OpenAPI Spec

paths:
  /api/v1/documents:
    post:
      summary: 上传文档
      requestBody:
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                file: { type: string, format: binary }
                kb_id: { type: string, format: uuid }
      responses:
        201:
          description: 文档创建成功

  /api/v1/kb/{kb_id}/search:
    post:
      summary: 混合检索
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                query: { type: string }
                strategy: { type: string, enum: [hybrid, vector, keyword, graph] }
                top_k: { type: integer, default: 10 }
                filters: { type: object }
      responses:
        200:
          description: 检索结果

  /api/v1/kb/{kb_id}/rag:
    post:
      summary: RAG 对话
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                question: { type: string }
                mode: { type: string, enum: [naive, contextual, graph-augmented] }
                history: { type: array }
      responses:
        200:
          description: RAG 回答 + 来源

  /api/v1/kb/{kb_id}/graph:
    get:
      summary: 获取知识图谱
    post:
      summary: 构建/更新图谱
```

---

## 六、前端页面规划

```
src/
├── views/
│   ├── Home.vue                 # 仪表盘
│   ├── KnowledgeBases.vue       # 知识库列表/创建
│   ├── KBDetail.vue            # 知识库详情
│   │   ├── components/
│   │   │   ├── DocumentList.vue
│   │   │   ├── GraphView.vue    # 知识图谱可视化
│   │   │   └── Settings.vue
│   │   └── tabs/
│   │       ├── Chat.vue         # RAG 对话
│   │       ├── Search.vue       # 混合搜索
│   │       ├── Documents.vue   # 文档管理
│   │       └── Graph.vue       # 图谱浏览
│   └── Admin.vue               # 系统管理
├── components/
│   ├── common/
│   │   ├── FileUploader.vue
│   │   └── MarkdownViewer.vue
│   ├── graph/
│   │   ├── GraphCanvas.vue     # D3 可画布
│   │   ├── EntityNode.vue
│   │   └── RelationEdge.vue
│   └── search/
│       ├── SearchBar.vue
│       └── ResultCard.vue
├── stores/
│   ├── kb.ts                    # 知识库状态
│   ├── doc.ts                   # 文档状态
│   └── graph.ts                 # 图谱状态
└── api/
    ├── kb.ts
    ├── doc.ts
    └── graph.ts
```

### 知识图谱可视化 (D3.js)

```vue
<!-- GraphCanvas.vue -->
<template>
  <div ref="container" class="graph-canvas">
    <svg ref="svg"></svg>
  </div>
</template>

<script setup>
import * as d3 from 'd3'
import { onMounted, watch } from 'vue'

const props = defineProps({
  graphData: {
    type: Object,
    required: true
  }
})

function renderGraph() {
  // D3 力导向图布局
  const simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(links).id(d => d.id))
    .force('charge', d3.forceManyBody().strength(-300))
    .force('center', d3.forceCenter(width / 2, height / 2))

  // 绘制节点和边
  // ...
}
</script>
```

---

## 七、开发路线图

### Phase 1: 基础架构 (2-3 周)

- [ ] 项目脚手架 (Monorepo: backend + frontend)
- [ ] Docker Compose 配置
- [ ] FastAPI 后端 + SQLite
- [ ] Vue 3 前端 + Naive UI
- [ ] JWT 认证
- [ ] 文档上传 (TXT/Markdown)

### Phase 2: RAG 基础 (3-4 周)

- [ ] Qdrant 集成
- [ ] 嵌入模型 (Sentence Transformers)
- [ ] 文本分块策略
- [ ] 向量检索 API
- [ ] RAG 对话界面
- [ ] OpenAI / Ollama 集成

### Phase 3: 混合检索 (2-3 周)

- [ ] BM25 关键词检索
- [ ] RRF 融合排序
- [ ] 高级搜索 UI
- [ ] 过滤器和元数据搜索

### Phase 4: 知识图谱 (4-5 周)

- [ ] 实体抽取 (LLM-based)
- [ ] 关系抽取
- [ ] Neo4j 集成
- [ ] 图数据库 CRUD
- [ ] D3.js 可视化
- [ ] 图增强 RAG

### Phase 5: 完善与开源 (2-3 周)

- [ ] 文档解析增强 (PDF/Word)
- [ ] 批量导入
- [ ] 性能优化
- [ ] README 和文档
- [ ] CI/CD
- [ ] 发布到 GitHub

---

## 八、AI Code Agent 开发提示词

```
你将帮我开发一个开源知识库系统 LiteKB。

技术栈：
- 后端: Python + FastAPI + Qdrant + SQLite
- 前端: Vue 3 + TypeScript + Naive UI + D3.js
- 部署: Docker Compose

核心功能：
1. 文档管理和上传
2. RAG 对话 (OpenAI/Ollama)
3. 混合检索 (向量 + 关键词)
4. 知识图谱 (实体/关系抽取 + 可视化)

请遵循：
1. 代码清晰，注释详细 (这是开源项目)
2. 类型完整 (TypeScript + Pydantic)
3. 错误处理完善
4. 单一职责原则
5. 先完成后完美

当前任务：[在此描述具体任务]
```

---

## 九、GitHub 开源准备

### 必备文件

```
litekb/
├── README.md              # 亮眼的首屏
├── LICENSE                # MIT / Apache 2.0
├── CONTRIBUTING.md        # 贡献指南
├── CODE_OF_CONDUCT.md     # 社区准则
├── docs/                  # 详细文档
│   ├── getting-started.md
│   ├── architecture.md
│   └── api.md
├── .github/
│   ├── workflows/
│   │   └── ci.yml
│   └── ISSUE_TEMPLATE/
├── docker-compose.yml
└── .gitignore
```

### README 结构

```markdown
# LiteKB 🦊

<p align="center">
  <img src="docs/images/demo.png" width="800"/>
</p>

<p align="center">
  <strong>轻量级开源知识库系统 | RAG + 混合检索 + 知识图谱</strong>
</p>

<p align="center">
  <a href="#快速开始">快速开始</a> •
  <a href="#特性">特性</a> •
  <a href="#截图">截图</a> •
  <a href="#贡献">贡献</a> •
  <a href="#许可">许可</a>
</p>

## ✨ 特性

- 🚀 **开箱即用** - 一键 Docker 启动
- 🔍 **混合检索** - 向量 + 关键词 + 图关系
- 🧠 **RAG 对话** - 基于知识库的智能问答
- 🔗 **知识图谱** - 实体关系可视化
- 🎨 **精美 UI** - Vue 3 + Naive UI

## 🚀 快速开始

```bash
git clone https://github.com/yourname/litekb.git
cd litekb
docker-compose up -d
# 访问 http://localhost:3000
```

## 📚 文档

- [Getting Started](docs/getting-started.md)
- [Architecture](docs/architecture.md)
- [API Reference](docs/api.md)

## 🤝 贡献

欢迎贡献！请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)

## 📄 许可

MIT License
```

---

## 十、下一步

1. **确认启动** - 我可以开始生成项目脚手架代码吗？
2. **技术细节** - 是否需要我先产出某个具体模块的详细设计？
3. **优先级** - 是否同意这个开发顺序？或者想先做知识图谱？

你确认后我就开始写代码！
