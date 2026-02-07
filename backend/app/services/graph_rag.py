"""
Graph RAG 检索增强服务 - Langfuse 提示词
"""

from typing import List, Dict, Set, Tuple, Optional
from loguru import logger
from collections import defaultdict

from app.services.prompt import (
    get_prompt,
    entity_extraction_prompt,
    graph_query_prompt,
)


class GraphRAGRetriever:
    """图谱增强检索器"""

    def __init__(self, neo4j_service=None):
        self.neo4j = neo4j_service

    async def retrieve_with_graph(
        self,
        query: str,
        vector_results: List[Dict],
        top_k: int = 5,
        depth: int = 2,
    ) -> Dict:
        """
        结合向量检索和知识图谱的混合检索

        Returns:
            {
                "chunks": [...],       # 原始检索结果
                "entities": [...],    # 相关实体
                "relations": [...],   # 相关关系
                "expanded_context": "", # 扩展上下文
                "reasoning_path": [...] # 推理路径
            }
        """

        # 1. 提取查询中的实体
        query_entities = await self._extract_entities(query)

        # 2. 从图谱检索相关实体
        graph_entities = await self._retrieve_entities(
            query_entities,
            depth=depth,
            limit=top_k * 2,
        )

        # 3. 获取实体的邻居信息
        expanded_info = await self._expand_entities(graph_entities)

        # 4. 构建推理路径
        reasoning_path = await self._build_reasoning_path(
            query_entities,
            graph_entities,
            vector_results,
        )

        # 5. 生成扩展上下文
        expanded_context = self._generate_context(
            vector_results,
            expanded_info,
            reasoning_path,
        )

        return {
            "chunks": vector_results[:top_k],
            "entities": graph_entities,
            "relations": self._extract_relations(graph_entities),
            "expanded_context": expanded_context,
            "reasoning_path": reasoning_path,
        }

    async def _extract_entities(self, query: str) -> List[str]:
        """从查询中提取实体 - 使用 Langfuse 提示词"""

        # 使用 Langfuse 提示词
        prompt_text = entity_extraction_prompt(query)

        # 这里可以调用 LLM 进行实体抽取
        # 例如：entities = await llm_extract(prompt_text)

        # 简单回退：提取关键词
        words = query.replace("?", "").split()
        return [w for w in words if len(w) > 1][:5]

    async def _retrieve_entities(
        self,
        query_entities: List[str],
        depth: int,
        limit: int,
    ) -> List[Dict]:
        """从图谱检索实体"""

        if not self.neo4j:
            # 返回模拟数据
            return [
                {"name": e, "type": "Concept", "score": 0.9} for e in query_entities
            ]

        try:
            entities = []
            for entity in query_entities:
                # 查询实体及其邻居
                result = await self.neo4j.query(
                    """MATCH (e:Entity {name: $name})
                    OPTIONAL MATCH (e)-[r]->(n)
                    OPTIONAL MATCH (n)-[r2]->(m)
                    RETURN e, r, n, m
                    LIMIT $limit""",
                    {"name": entity, "limit": limit},
                )
                entities.extend(result)

            return entities

        except Exception as e:
            logger.error(f"Graph retrieval failed: {e}")
            return []

    async def _expand_entities(self, entities: List[Dict]) -> Dict:
        """扩展实体信息"""
        expanded = {
            "entity_info": {},  # 实体详情
            "neighbors": {},  # 邻居节点
            "related_docs": {},  # 相关文档
        }

        for entity in entities:
            name = entity.get("name", "")
            if name:
                expanded["entity_info"][name] = entity
                expanded["neighbors"][name] = entity.get("neighbors", [])

        return expanded

    async def _build_reasoning_path(
        self,
        query_entities: List[str],
        graph_entities: List[Dict],
        vector_results: List[Dict],
    ) -> List[Dict]:
        """构建推理路径"""

        paths = []

        # 从向量结果构建路径
        for result in vector_results[:3]:
            path = {
                "type": "vector",
                "doc_id": result.get("id"),
                "score": result.get("score", 0),
                "reasoning": f"向量相似度: {result.get('score', 0):.3f}",
            }
            paths.append(path)

        # 从图谱构建路径
        for entity in graph_entities[:3]:
            path = {
                "type": "graph",
                "entity": entity.get("name"),
                "reasoning": f"图谱关联: {entity.get('type', 'Concept')}",
            }
            paths.append(path)

        return paths

    def _extract_relations(self, entities: List[Dict]) -> List[Dict]:
        """提取关系"""
        relations = []

        for entity in entities:
            if entity.get("relations"):
                relations.extend(entity["relations"])

        return relations[:10]  # 最多返回 10 个关系

    def _generate_context(
        self,
        vector_results: List[Dict],
        expanded_info: Dict,
        reasoning_path: List[Dict],
    ) -> str:
        """生成扩展上下文"""

        context_parts = []

        # 文档内容
        for result in vector_results[:3]:
            content = result.get("content", "")[:500]
            context_parts.append(f"文档: {content}")

        # 实体信息
        entity_info = expanded_info.get("entity_info", {})
        for name, info in entity_info.items():
            context_parts.append(f"实体 {name}: {info}")

        return "\n\n".join(context_parts)


# 全局实例
graph_rag_retriever = GraphRAGRetriever()


async def retrieve_with_graph_rag(
    query: str,
    vector_results: List[Dict],
    top_k: int = 5,
    neo4j_service=None,
) -> Dict:
    """使用 Graph RAG 检索"""
    retriever = GraphRAGRetriever(neo4j_service)
    return await retriever.retrieve_with_graph(
        query=query,
        vector_results=vector_results,
        top_k=top_k,
    )
