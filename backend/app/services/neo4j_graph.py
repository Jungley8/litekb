"""
Neo4j 知识图谱集成
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger
from dataclasses import dataclass


@dataclass
class GraphNode:
    """图节点"""

    id: str
    label: str
    properties: Dict[str, Any]


@dataclass
class GraphRelationship:
    """图关系"""

    source: str
    target: str
    type: str
    properties: Dict[str, Any]


class Neo4jGraphService:
    """Neo4j 知识图谱服务"""

    def __init__(self):
        self.enabled = False
        self._init_connection()

    def _init_connection(self):
        """初始化连接"""
        try:
            from neo4j import GraphDatabase

            # 从配置获取连接信息
            from app.config import settings

            uri = settings.neo4j_url
            user = settings.neo4j_user
            password = settings.neo4j_password

            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            self.enabled = True
            logger.info(f"Neo4j connected: {uri}")

            # 创建索引
            self._create_indexes()

        except Exception as e:
            logger.warning(f"Neo4j not available: {e}")
            self.enabled = False

    def _create_indexes(self):
        """创建索引"""
        if not self.enabled:
            return

        try:
            with self.driver.session() as session:
                # 实体索引
                session.run("""
                    CREATE INDEX entity_id IF NOT EXISTS
                    FOR (e:Entity) ON (e.id)
                """)

                # 知识库索引
                session.run("""
                    CREATE INDEX kb_entity IF NOT EXISTS
                    FOR (e:Entity) ON (e.kb_id)
                """)

                logger.info("Neo4j indexes created")

        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")

    def close(self):
        """关闭连接"""
        if self.enabled and self.driver:
            self.driver.close()

    async def create_entity(
        self,
        kb_id: str,
        entity_id: str,
        entity_type: str,
        name: str,
        properties: Dict[str, Any] = None,
    ) -> bool:
        """创建实体"""
        if not self.enabled:
            return False

        try:
            with self.driver.session() as session:
                session.run(
                    """
                    MERGE (e:Entity {id: $id})
                    SET e.kb_id = $kb_id,
                        e.type = $type,
                        e.name = $name,
                        e.properties = $properties,
                        e.updated_at = datetime()
                    RETURN e
                """,
                    {
                        "id": entity_id,
                        "kb_id": kb_id,
                        "type": entity_type,
                        "name": name,
                        "properties": properties or {},
                    },
                )

            return True

        except Exception as e:
            logger.error(f"Create entity failed: {e}")
            return False

    async def create_relationship(
        self,
        kb_id: str,
        source_id: str,
        target_id: str,
        rel_type: str,
        properties: Dict[str, Any] = None,
    ) -> bool:
        """创建关系"""
        if not self.enabled:
            return False

        try:
            with self.driver.session() as session:
                session.run(
                    """
                    MATCH (s:Entity {id: $source_id})
                    MATCH (t:Entity {id: $target_id})
                    MERGE (s)-[r:RELATIONSHIP {type: $type}]->(t)
                    SET r.kb_id = $kb_id,
                        r.properties = $properties,
                        r.updated_at = datetime()
                """,
                    {
                        "kb_id": kb_id,
                        "source_id": source_id,
                        "target_id": target_id,
                        "type": rel_type,
                        "properties": properties or {},
                    },
                )

            return True

        except Exception as e:
            logger.error(f"Create relationship failed: {e}")
            return False

    async def get_graph(self, kb_id: str) -> Dict[str, Any]:
        """获取知识图谱"""
        if not self.enabled:
            return {"nodes": [], "links": [], "error": "Neo4j not available"}

        try:
            with self.driver.session() as session:
                # 获取节点
                nodes_result = session.run(
                    """
                    MATCH (e:Entity {kb_id: $kb_id})
                    RETURN e.id as id, e.type as type, e.name as label, e.properties as properties
                """,
                    {"kb_id": kb_id},
                )

                nodes = []
                for record in nodes_result:
                    nodes.append(
                        {
                            "id": record["id"],
                            "label": record["label"],
                            "type": record["type"],
                            "properties": (
                                dict(record["properties"])
                                if record["properties"]
                                else {}
                            ),
                        }
                    )

                # 获取关系
                rels_result = session.run(
                    """
                    MATCH (s:Entity)-[r:RELATIONSHIP]->(t:Entity)
                    WHERE s.kb_id = $kb_id AND t.kb_id = $kb_id
                    RETURN s.id as source, t.id as target, r.type as type
                """,
                    {"kb_id": kb_id},
                )

                links = []
                for record in rels_result:
                    links.append(
                        {
                            "source": record["source"],
                            "target": record["target"],
                            "type": record["type"],
                        }
                    )

                return {"nodes": nodes, "links": links}

        except Exception as e:
            logger.error(f"Get graph failed: {e}")
            return {"nodes": [], "links": [], "error": str(e)}

    async def search_entities(
        self, kb_id: str, query: str, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """搜索实体"""
        if not self.enabled:
            return []

        try:
            with self.driver.session() as session:
                result = session.run(
                    """
                    MATCH (e:Entity {kb_id: $kb_id})
                    WHERE e.name CONTAINS $query OR e.type CONTAINS $query
                    RETURN e.id as id, e.name as name, e.type as type
                    LIMIT $limit
                """,
                    {"kb_id": kb_id, "query": query, "limit": limit},
                )

                return [
                    {"id": record["id"], "name": record["name"], "type": record["type"]}
                    for record in result
                ]

        except Exception as e:
            logger.error(f"Search entities failed: {e}")
            return []

    async def get_entity_relations(self, kb_id: str, entity_id: str) -> Dict[str, Any]:
        """获取实体的关系"""
        if not self.enabled:
            return {}

        try:
            with self.driver.session() as session:
                # 出边
                outgoing = session.run(
                    """
                    MATCH (s:Entity {id: $entity_id})-[r:RELATIONSHIP]->(t:Entity)
                    WHERE s.kb_id = $kb_id
                    RETURN t.id as id, t.name as name, r.type as relation
                """,
                    {"kb_id": kb_id, "entity_id": entity_id},
                )

                # 入边
                incoming = session.run(
                    """
                    MATCH (s:Entity)-[r:RELATIONSHIP]->(t:Entity {id: $entity_id})
                    WHERE t.kb_id = $kb_id
                    RETURN s.id as id, s.name as name, r.type as relation
                """,
                    {"kb_id": kb_id, "entity_id": entity_id},
                )

                return {
                    "entity": entity_id,
                    "outgoing": [
                        {"id": r["id"], "name": r["name"], "relation": r["relation"]}
                        for r in outgoing
                    ],
                    "incoming": [
                        {"id": r["id"], "name": r["name"], "relation": r["relation"]}
                        for r in incoming
                    ],
                }

        except Exception as e:
            logger.error(f"Get entity relations failed: {e}")
            return {}

    async def find_path(
        self, kb_id: str, source_name: str, target_name: str
    ) -> List[Dict[str, Any]]:
        """查找两个实体之间的路径"""
        if not self.enabled:
            return []

        try:
            with self.driver.session() as session:
                result = session.run(
                    """
                    MATCH path = shortestPath(
                        (s:Entity)-[*..10]-(t:Entity)
                    )
                    WHERE s.kb_id = $kb_id 
                      AND t.kb_id = $kb_id
                      AND s.name = $source_name
                      AND t.name = $target_name
                    RETURN path
                    LIMIT 1
                """,
                    {
                        "kb_id": kb_id,
                        "source_name": source_name,
                        "target_name": target_name,
                    },
                )

                paths = []
                for record in result:
                    path = record["path"]
                    paths.append(
                        {
                            "nodes": [n.get("name") for n in path.nodes],
                            "relationships": [r.type for r in path.relationships],
                            "length": len(path.relationships),
                        }
                    )

                return paths

        except Exception as e:
            logger.error(f"Find path failed: {e}")
            return []

    async def delete_kb_graph(self, kb_id: str) -> bool:
        """删除知识库图谱"""
        if not self.enabled:
            return False

        try:
            with self.driver.session() as session:
                session.run(
                    """
                    MATCH (e:Entity {kb_id: $kb_id})
                    DETACH DELETE e
                """,
                    {"kb_id": kb_id},
                )

            return True

        except Exception as e:
            logger.error(f"Delete graph failed: {e}")
            return False


# 全局实例
neo4j_service = Neo4jGraphService()
