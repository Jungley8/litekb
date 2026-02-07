"""
知识图谱服务 - Langfuse 提示词
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from loguru import logger
import json

from app.config import settings
from app.models import get_session, GraphEntity, GraphRelation, DocumentChunk
from app.services.prompt import get_prompt, entity_extraction_prompt


@dataclass
class Entity:
    """实体"""

    id: str
    entity_type: str
    entity_name: str
    properties: Dict[str, Any]
    doc_id: Optional[str] = None


@dataclass
class Relation:
    """关系"""

    source_id: str
    target_id: str
    relation_type: str
    confidence: float = 1.0
    properties: Dict[str, Any] = None


class KnowledgeGraphService:
    """知识图谱服务"""

    def __init__(self):
        self.llm_enabled = True  # 使用 LLM 抽取实体关系

    async def extract_entities(
        self, text: str, doc_id: Optional[str] = None
    ) -> List[Entity]:
        """从文本中提取实体 - 使用 Langfuse 提示词"""
        # 获取提示词
        prompt = entity_extraction_prompt(text[:3000])
        system_prompt = get_prompt("entity_extraction_system")

        try:
            from app.services.rag import rag_engine

            response = await rag_engine.llm.chat(
                [{"role": "user", "content": prompt}], system_prompt=system_prompt
            )

            # 解析 JSON
            data = json.loads(response)
            entities = []
            for e in data.get("entities", []):
                entities.append(
                    Entity(
                        id=f"ent_{hash(e['name']) % 100000}",
                        entity_type=e["type"],
                        entity_name=e["name"],
                        properties=e.get("properties", {}),
                        doc_id=doc_id,
                    )
                )
            return entities

        except Exception as e:
            logger.error(f"实体抽取失败: {e}")
            return []

    async def extract_relations(
        self, text: str, entities: List[Entity]
    ) -> List[Relation]:
        """提取实体关系 - 使用 Langfuse 提示词"""
        entity_names = [e.entity_name for e in entities]

        # 使用 Langfuse 提示词
        prompt = get_prompt(
            "relation_extraction",
            {
                "text": text[:3000],
                "entities": ", ".join(entity_names),
            },
        )
        system_prompt = get_prompt("relation_extraction_system")

        try:
            from app.services.rag import rag_engine

            response = await rag_engine.llm.chat(
                [{"role": "user", "content": prompt}], system_prompt=system_prompt
            )

            data = json.loads(response)
            relations = []
            for r in data.get("relations", []):
                relations.append(
                    Relation(
                        source_id=r["source"],
                        target_id=r["target"],
                        relation_type=r["relation"],
                        confidence=r.get("confidence", 1.0),
                    )
                )
            return relations

        except Exception as e:
            logger.error(f"关系抽取失败: {e}")
            return []

    async def build_graph(self, kb_id: str, doc_id: str, text: str) -> Dict[str, Any]:
        """构建知识图谱"""
        # 1. 提取实体
        entities = await self.extract_entities(text, doc_id)

        # 2. 提取关系
        relations = await self.extract_relations(text, entities)

        # 3. 保存到数据库
        session = get_session()
        try:
            # 保存实体
            entity_map = {}
            for entity in entities:
                existing = (
                    session.query(GraphEntity)
                    .filter(
                        GraphEntity.kb_id == kb_id,
                        GraphEntity.entity_name == entity.entity_name,
                    )
                    .first()
                )

                if not existing:
                    db_entity = GraphEntity(
                        id=entity.id,
                        kb_id=kb_id,
                        doc_id=doc_id,
                        entity_type=entity.entity_type,
                        entity_name=entity.entity_name,
                        properties=entity.properties,
                    )
                    session.add(db_entity)
                    entity_map[entity.entity_name] = entity.id
                else:
                    entity_map[entity.entity_name] = existing.id

            # 保存关系
            for relation in relations:
                source_id = entity_map.get(relation.source_id)
                target_id = entity_map.get(relation.target_id)

                if source_id and target_id:
                    existing = (
                        session.query(GraphRelation)
                        .filter(
                            GraphRelation.source_id == source_id,
                            GraphRelation.target_id == target_id,
                            GraphRelation.relation_type == relation.relation_type,
                        )
                        .first()
                    )

                    if not existing:
                        db_rel = GraphRelation(
                            id=f"rel_{hash(relation.source_id + relation.target_id) % 100000}",
                            kb_id=kb_id,
                            source_id=source_id,
                            target_id=target_id,
                            relation_type=relation.relation_type,
                            confidence=relation.confidence,
                        )
                        session.add(db_rel)

            session.commit()

            logger.info(
                f"知识图谱构建完成: {len(entities)} 实体, {len(relations)} 关系"
            )

            return {"entities": len(entities), "relations": len(relations)}

        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_graph(self, kb_id: str) -> Dict[str, Any]:
        """获取知识图谱"""
        session = get_session()
        try:
            entities = (
                session.query(GraphEntity).filter(GraphEntity.kb_id == kb_id).all()
            )

            relations = (
                session.query(GraphRelation).filter(GraphRelation.kb_id == kb_id).all()
            )

            return {
                "nodes": [
                    {"id": e.id, "label": e.entity_name, "type": e.entity_type}
                    for e in entities
                ],
                "links": [
                    {
                        "source": r.source_id,
                        "target": r.target_id,
                        "type": r.relation_type,
                    }
                    for r in relations
                ],
            }
        finally:
            session.close()

    def search_entities(self, kb_id: str, query: str) -> List[Dict[str, Any]]:
        """搜索实体"""
        session = get_session()
        try:
            entities = (
                session.query(GraphEntity)
                .filter(
                    GraphEntity.kb_id == kb_id, GraphEntity.entity_name.contains(query)
                )
                .limit(20)
                .all()
            )

            return [
                {
                    "id": e.id,
                    "label": e.entity_name,
                    "type": e.entity_type,
                    "properties": e.properties,
                }
                for e in entities
            ]
        finally:
            session.close()

    def get_entity_relations(self, kb_id: str, entity_id: str) -> Dict[str, Any]:
        """获取实体的关联"""
        session = get_session()
        try:
            # 获取实体
            entity = session.query(GraphEntity).get(entity_id)
            if not entity:
                return {}

            # 获取出边
            outgoing = (
                session.query(GraphRelation)
                .filter(GraphRelation.source_id == entity_id)
                .all()
            )

            # 获取入边
            incoming = (
                session.query(GraphRelation)
                .filter(GraphRelation.target_id == entity_id)
                .all()
            )

            return {
                "entity": {
                    "id": entity.id,
                    "label": entity.entity_name,
                    "type": entity.entity_type,
                },
                "outgoing": [
                    {
                        "relation": r.relation_type,
                        "target": self._get_entity_name(session, r.target_id),
                    }
                    for r in outgoing
                ],
                "incoming": [
                    {
                        "relation": r.relation_type,
                        "source": self._get_entity_name(session, r.source_id),
                    }
                    for r in incoming
                ],
            }
        finally:
            session.close()

    def _get_entity_name(self, session, entity_id: str) -> str:
        """获取实体名称"""
        entity = session.query(GraphEntity).get(entity_id)
        return entity.entity_name if entity else "Unknown"


# 全局实例
graph_service = KnowledgeGraphService()
