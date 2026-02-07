"""
向量检索服务
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from loguru import logger


class VectorStore:
    """向量存储"""

    def __init__(
        self,
        collection_name: str = "litekb",
        dimension: int = 1536,
        distance: str = "cosine",
    ):
        self.collection_name = collection_name
        self.dimension = dimension
        self.distance = distance
        self._chunks = {}  # 模拟存储
        self._embeddings = {}

    async def create_collection(self):
        """创建向量集合"""
        logger.info(f"Created collection: {self.collection_name}")

    async def add(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadata: Optional[List[Dict]] = None,
    ):
        """添加向量"""
        for i, id_ in enumerate(ids):
            self._chunks[id_] = {
                "id": id_,
                "content": documents[i],
                "metadata": metadata[i] if metadata else {},
            }
            self._embeddings[id_] = np.array(embeddings[i])

        logger.info(f"Added {len(ids)} vectors")

    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        score_threshold: float = 0.7,
        filters: Optional[Dict] = None,
    ) -> List[Dict]:
        """向量检索"""
        query_vec = np.array(query_embedding)

        results = []
        for id_, emb in self._embeddings.items():
            # 计算相似度
            score = np.dot(query_vec, emb) / (
                np.linalg.norm(query_vec) * np.linalg.norm(emb) + 1e-8
            )

            if score >= score_threshold:
                chunk = self._chunks[id_]
                results.append(
                    {
                        "id": id_,
                        "score": float(score),
                        "content": chunk["content"],
                        "metadata": chunk.get("metadata", {}),
                    }
                )

        # 排序返回 top_k
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    async def delete(self, ids: List[str]):
        """删除向量"""
        for id_ in ids:
            self._chunks.pop(id_, None)
            self._embeddings.pop(id_, None)

    async def delete_collection(self):
        """删除集合"""
        self._chunks.clear()
        self._embeddings.clear()

    async def count(self) -> int:
        """统计数量"""
        return len(self._chunks)


# OpenAI Embedding API
class OpenAIEmbedding:
    """OpenAI Embedding API"""

    def __init__(self, api_key: str = None, model: str = "text-embedding-3-small"):
        self.api_key = api_key
        self.model = model
        self.dimension_map = {
            "text-embedding-3-large": 3072,
            "text-embedding-3-small": 1536,
            "text-embedding-ada-002": 1536,
        }

    @property
    def dimension(self) -> int:
        return self.dimension_map.get(self.model, 1536)

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """调用 OpenAI API"""
        # 模拟返回
        import numpy as np

        dim = self.dimension

        embeddings = []
        for text in texts:
            # 生成伪嵌入向量
            np.random.seed(hash(text) % 2**32)
            emb = np.random.randn(dim).tolist()
            # L2 归一化
            norm = sum(x**2 for x in emb) ** 0.5
            emb = [x / norm for x in emb]
            embeddings.append(emb)

        return embeddings

    async def embed_query(self, query: str) -> List[float]:
        """编码查询"""
        return (await self.embed_texts([query]))[0]


# 全局实例
embedding_api = OpenAIEmbedding()
vector_store = VectorStore()
