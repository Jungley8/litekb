"""
向量存储服务 - Qdrant
"""
from typing import List, Optional, Dict, Any
from loguru import logger
from qdrant_client import QdrantClient
from qdrant_client.models import (
    PointStruct,
    VectorParams,
    Distance,
    Filter,
    FieldCondition,
    MatchValue,
    SearchRequest
)

from app.config import settings
from app.models import get_session, DocumentChunk


class VectorStore:
    """向量存储服务"""
    
    def __init__(self):
        self.client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key
        )
        self.collection_name = settings.qdrant_collection
        self.embedding_dim = settings.embedding_dimensions
    
    def create_collection(self):
        """创建集合"""
        try:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dim,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"创建集合 {self.collection_name} 成功")
        except Exception as e:
            if "already exists" in str(e):
                logger.info(f"集合 {self.collection_name} 已存在")
            else:
                raise e
    
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """获取文本嵌入"""
        # TODO: 实现实际的嵌入计算
        # 使用 OpenAI 或 Sentence Transformers
        provider = settings.embedding_provider
        
        if provider == "openai":
            return await self._openai_embedding(texts)
        elif provider == "sentence-transformers":
            return await self._st_embedding(texts)
        else:
            # 返回随机向量作为占位
            import numpy as np
            return [np.random.randn(self.embedding_dim).tolist() for _ in texts]
    
    async def _openai_embedding(self, texts: List[str]) -> List[List[float]]:
        """OpenAI 嵌入"""
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        
        response = await client.embeddings.create(
            model=settings.embedding_model,
            input=texts
        )
        
        return [data.embedding for data in response.data]
    
    async def _st_embedding(self, texts: List[str]) -> List[List[float]]:
        """Sentence Transformers 嵌入"""
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(settings.embedding_model)
        return model.encode(texts).tolist()
    
    async def add_chunks(self, kb_id: str, chunks: List[DocumentChunk]):
        """添加分块到向量库"""
        if not chunks:
            return
        
        # 获取文本内容
        texts = [chunk.content for chunk in chunks]
        
        # 计算嵌入
        embeddings = await self.get_embeddings(texts)
        
        # 创建点
        points = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            point = PointStruct(
                id=chunk.id,
                vector=embedding,
                payload={
                    "kb_id": kb_id,
                    "doc_id": chunk.doc_id,
                    "chunk_index": chunk.chunk_index,
                    "content": chunk.content,
                    "metadata": chunk.metadata or {}
                }
            )
            points.append(point)
        
        # 批量上传
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        
        logger.info(f"添加 {len(points)} 个向量到 {self.collection_name}")
    
    async def search(
        self,
        query: str,
        kb_id: str,
        top_k: int = 10,
        filters: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """向量搜索"""
        # 计算查询嵌入
        query_embedding = await self.get_embeddings([query])
        
        # 构建过滤条件
        filter_conditions = [FieldCondition(key="kb_id", match=MatchValue(value=kb_id))]
        
        if filters:
            for key, value in filters.items():
                filter_conditions.append(
                    FieldCondition(key=key, match=MatchValue(value=value))
                )
        
        search_filter = Filter(all_of=filter_conditions)
        
        # 搜索
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding[0],
            limit=top_k,
            query_filter=search_filter
        )
        
        return [
            {
                "id": r.id,
                "score": r.score,
                "payload": r.payload
            }
            for r in results
        ]
    
    async def delete_by_kb(self, kb_id: str):
        """删除知识库所有向量"""
        self.client.delete(
            collection_name=self.collection_name,
            filter=Filter(all_of=[FieldCondition(key="kb_id", match=MatchValue(value=kb_id))])
        )


# 全局实例
vector_store = VectorStore()
