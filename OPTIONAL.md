# LiteKB - 可选优化清单

## ✅ 已完成

### 1. 本地 Embedding 支持
| 文件 | 功能 |
|------|------|
| `backend/app/services/local_embedding.py` | SentenceTransformer 本地嵌入 |

### 2. RAG 摘要生成
| 文件 | 功能 |
|------|------|
| `backend/app/services/summary.py` | 文档摘要、关键要点、实体提取 |

### 3. Graph RAG 增强
| 文件 | 功能 |
|------|------|
| `backend/app/services/graph_rag.py` | 图谱增强检索、推理路径 |

### 4. 分享功能完善
| 文件 | 功能 |
|------|------|
| `backend/app/services/share_v2.py` | 完整分享服务 |
| `backend/app/api/share.py` | 分享 API 端点 |

### 5. 其他服务完善
| 文件 | 功能 |
|------|------|
| `backend/app/services/search.py` | 混合搜索 (RRF 融合) |
| `backend/app/services/export.py` | 导出功能 (MD/JSON/HTML/CSV) |
| `backend/app/services/multimodal.py` | 多模态处理 |
| `backend/app/services/websocket.py` | WebSocket 连接管理 |
| `backend/app/services/plugin.py` | 插件系统 |

### 6. 清理 TODO
- 所有服务中的 TODO 标记已清理
- 替换为实际实现或注释说明

---

## ⏳ 待完成

| 项目 | 状态 | 说明 |
|------|------|------|
| 报告生成 | ⏳ 待完成 | 定时生成使用报告 (周报/月报) |

---

## 📊 最终状态

```
✅ 本地 Embedding: 完成
✅ RAG 摘要: 完成
✅ Graph RAG: 完成
✅ 分享完善: 完成
✅ 其他服务: 完成
⏳ 报告生成: 待完成

可选优化进度: 5/6 完成 (83%)
```

---

## 🚀 使用方式

```bash
# 克隆并启动
git clone https://github.com/Jungley8/litekb.git
cd litekb
docker-compose up -d
```
