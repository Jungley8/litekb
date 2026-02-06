"""
混合检索服务 - 结合向量、关键词和图检索
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from loguru import logger

from app.config import settings
from app.services.vector import vector_store


@dataclass
class SearchResult:
    """搜索结果"""
    id: str
    content: str
    score: float
    source_type: str  # vector, keyword, graph
    metadata: Dict[str, Any]


class KeywordSearch:
    """关键词搜索 (BM25)"""
    
    def __init__(self):
        self.index = None
        self.documents = {}
    
    def build_index(self, docs: List[Dict[str, Any]]):
        """构建 BM25 索引"""
        try:
            from bm25s import BM25
            import stemmer
            import re
            
            # 预处理文本
            texts = []
            for doc in docs:
                text = doc.get("content", "")
                # 简单分词
                words = re.findall(r"\w+", text.lower())
                texts.append(" ".join(words))
                self.documents[doc["id"]] = doc
            
            # 创建索引
            self.index = BM25(corpus=texts, stemmer=stemmer.stemmer)
            logger.info(f"BM25 索引构建完成，包含 {len(texts)} 篇文档")
            
        except ImportError:
            logger.warning("bm25s 未安装，使用简单关键词匹配")
            self.documents = {d["id"]: d for d in docs}
    
    def search(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """搜索"""
        import re
        
        if self.index is None:
            # 简单匹配
            query_words = set(re.findall(r"\w+", query.lower()))
            results = []
            for doc in self.documents.values():
                content_lower = doc.get("content", "").lower()
                score = sum(1 for w in query_words if w in content_lower)
                if score > 0:
                    results.append(SearchResult(
                        id=doc["id"],
                        content=doc.get("content", "")[:500],
                        score=score / len(query_words),
                        source_type="keyword",
                        metadata=doc.get("metadata", {})
                    ))
            return sorted(results, key=lambda x: x.score, reverse=True)[:top_k]
        
        # BM25 搜索
        query_tokens = " ".join(re.findall(r"\w+", query.lower()))
        scores, ids = self.index.search(query_tokens, k=top_k)
        
        results = []
        for score, idx in zip(scores, ids):
            doc_id = list(self.documents.keys())[idx]
            doc = self.documents[doc_id]
            results.append(SearchResult(
                id=doc_id,
                content=doc.get("content", "")[:500],
                score=float(score),
                source_type="keyword",
                metadata=doc.get("metadata", {})
            ))
        
        return results


class HybridSearchEngine:
    """混合检索引擎"""
    
    def __init__(self):
        self.vector_store = vector_store
        self.keyword_search = KeywordSearch()
    
    async def index_documents(self, kb_id: str, documents: List[Dict[str, Any]]):
        """索引文档"""
        # 构建关键词索引
        self.keyword_search.build_index(documents)
        
        # 索引到向量库
        # TODO: 创建 DocumentChunk 并添加到向量库
    
    async def search(
        self,
        query: str,
        kb_id: str,
        strategy: str = "hybrid",
        top_k: int = 10,
        filters: Optional[Dict] = None
    ) -> List[SearchResult]:
        """混合搜索"""
        
        if strategy == "vector":
            # 仅向量检索
            vector_results = await self.vector_store.search(query, kb_id, top_k, filters)
            return [
                SearchResult(
                    id=r["id"],
                    content=r["payload"].get("content", ""),
                    score=r["score"],
                    source_type="vector",
                    metadata=r["payload"].get("metadata", {})
                )
                for r in vector_results
            ]
        
        elif strategy == "keyword":
            # 仅关键词检索
            return self.keyword_search.search(query, top_k)
        
        elif strategy == "hybrid":
            # 并行检索 + RRF 融合
            vector_results = await self.vector_store.search(query, kb_id, top_k, filters)
            keyword_results = self.keyword_search.search(query, top_k)
            
            # RRF 融合
            return self.rrf_fuse(vector_results, keyword_results, top_k)
        
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
    
    def rrf_fuse(
        self,
        vector_results: List[Dict],
        keyword_results: List[SearchResult],
        top_k: int = 10,
        k: float = 60.0
    ) -> List[SearchResult]:
        """
        RRF (Reciprocal Rank Fusion) 融合
        
        RRF(d) = Σ(1 / (k + r(d)))
        其中 r(d) 是文档 d 在各个检索结果中的排名
        """
        # 合并所有结果
        all_results = {}
        
        # 向量结果排名
        for rank, r in enumerate(vector_results):
            doc_id = r["id"]
            score = 1.0 / (k + rank + 1)
            all_results[doc_id] = {
                "content": r["payload"].get("content", ""),
                "score": score,
                "rrf_score": score,
                "sources": [("vector", r["score"])]
            }
        
        # 关键词结果排名
        for rank, r in enumerate(keyword_results):
            doc_id = r.id
            if doc_id in all_results:
                all_results[doc_id]["rrf_score"] += 1.0 / (k + rank + 1)
                all_results[doc_id]["sources"].append(("keyword", r.score))
            else:
                all_results[doc_id] = {
                    "content": r.content,
                    "score": 1.0 / (k + rank + 1),
                    "rrf_score": 1.0 / (k + rank + 1),
                    "sources": [("keyword", r.score)]
                }
        
        # 按 RRF 分数排序
        sorted_results = sorted(
            all_results.items(),
            key=lambda x: x[1]["rrf_score"],
            reverse=True
        )[:top_k]
        
        return [
            SearchResult(
                id=doc_id,
                content=info["content"],
                score=info["rrf_score"],
                source_type="hybrid",
                metadata={"sources": info["sources"]}
            )
            for doc_id, info in sorted_results
        ]


# 全局实例
hybrid_search = HybridSearchEngine()
