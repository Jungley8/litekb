"""
SQLAlchemy ORM 数据库存储
"""

import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine, text
from loguru import logger

from app.models import (
    User,
    KnowledgeBase,
    Document,
    DocumentChunk,
    Conversation,
    Message,
    GraphEntity,
    GraphRelation,
    Organization,
    OrganizationMember,
    APIKey,
    RevokedToken,
    KBDocument,
    Plugin,
    UserSetting,
    AuditLog,
    Share,
    ImportJob,
    ExportJob,
    OrgInvitation,
    KBActivity,
)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/litekb.db")


class ORMStore:
    """ORM 数据库存储"""

    def __init__(self, db_url: str = None):
        self.db_url = db_url or DATABASE_URL
        self.engine = create_engine(
            self.db_url,
            connect_args=(
                {"check_same_thread": False} if "sqlite" in self.db_url else {}
            ),
            echo=False,
        )
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )
        self._init_tables()

    def _init_tables(self):
        """初始化表"""
        from app.models import Base

        Base.metadata.create_all(bind=self.engine)
        logger.info(f"ORM tables initialized: {self.db_url}")

    def get_session(self) -> Session:
        """获取会话"""
        return self.SessionLocal()

    def close_session(self, session: Session):
        """关闭会话"""
        session.close()

    # ========== 上下文管理器 ==========

    @property
    def session(self) -> Session:
        """会话上下文"""
        return self

    def __enter__(self) -> Session:
        self._session = self.get_session()
        return self._session

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self._session.rollback()
        self.close_session(self._session)

    # ========== 用户 ==========

    def create_user(self, user_id: str, data: Dict) -> User:
        with self.get_session() as session:
            user = User(
                id=user_id,
                username=data["username"],
                email=data.get("email"),
                hashed_password=data["hashed_password"],
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            return user

    def get_user(self, user_id: str) -> Optional[User]:
        with self.get_session() as session:
            return session.query(User).filter(User.id == user_id).first()

    def get_user_by_username(self, username: str) -> Optional[User]:
        with self.get_session() as session:
            return session.query(User).filter(User.username == username).first()

    def update_user(self, user_id: str, data: Dict) -> bool:
        with self.get_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            for key, value in data.items():
                setattr(user, key, value)
            session.commit()
            return True

    def list_users(self) -> List[User]:
        with self.get_session() as session:
            return session.query(User).all()

    # ========== 组织 ==========

    def create_organization(self, org_id: str, data: Dict) -> Organization:
        with self.get_session() as session:
            org = Organization(
                id=org_id,
                name=data["name"],
                slug=data.get("slug", data["name"].lower().replace(" ", "-")),
                description=data.get("description"),
                owner_id=data["owner_id"],
            )
            session.add(org)
            session.commit()
            session.refresh(org)
            return org

    def get_organization(self, org_id: str) -> Optional[Organization]:
        with self.get_session() as session:
            return session.query(Organization).filter(Organization.id == org_id).first()

    def list_organizations(self) -> List[Organization]:
        with self.get_session() as session:
            return session.query(Organization).all()

    def add_org_member(self, member_id: str, data: Dict) -> OrganizationMember:
        with self.get_session() as session:
            member = OrganizationMember(
                id=member_id,
                org_id=data["org_id"],
                user_id=data["user_id"],
                role=data.get("role", "member"),
            )
            session.add(member)
            session.commit()
            session.refresh(member)
            return member

    def list_org_members(self, org_id: str) -> List[OrganizationMember]:
        with self.get_session() as session:
            return (
                session.query(OrganizationMember)
                .filter(OrganizationMember.org_id == org_id)
                .all()
            )

    # ========== 知识库 ==========

    def create_kb(self, kb_id: str, data: Dict) -> KnowledgeBase:
        with self.get_session() as session:
            kb = KnowledgeBase(
                id=kb_id,
                name=data["name"],
                description=data.get("description"),
                created_by=data["created_by"],
            )
            session.add(kb)
            session.commit()
            session.refresh(kb)
            return kb

    def get_kb(self, kb_id: str) -> Optional[KnowledgeBase]:
        with self.get_session() as session:
            return (
                session.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
            )

    def list_kbs(self, org_id: str = None) -> List[KnowledgeBase]:
        with self.get_session() as session:
            query = session.query(KnowledgeBase)
            if org_id:
                query = query.filter(KnowledgeBase.org_id == org_id)
            return query.all()

    def update_kb(self, kb_id: str, data: Dict) -> bool:
        with self.get_session() as session:
            kb = session.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
            if not kb:
                return False
            for key, value in data.items():
                setattr(kb, key, value)
            session.commit()
            return True

    def delete_kb(self, kb_id: str) -> bool:
        with self.get_session() as session:
            kb = session.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
            if not kb:
                return False
            session.delete(kb)
            session.commit()
            return True

    # ========== 文档 ==========

    def create_doc(self, doc_id: str, data: Dict) -> Document:
        with self.get_session() as session:
            doc = Document(
                id=doc_id,
                title=data["title"],
                content=data.get("content"),
                file_type=data.get("file_type"),
                file_size=data.get("file_size"),
                kb_id=data["kb_id"],
            )
            session.add(doc)
            session.commit()
            session.refresh(doc)
            return doc

    def get_doc(self, doc_id: str) -> Optional[Document]:
        with self.get_session() as session:
            return session.query(Document).filter(Document.id == doc_id).first()

    def list_docs(
        self, kb_id: str = None, skip: int = 0, limit: int = 100
    ) -> List[Document]:
        with self.get_session() as session:
            query = session.query(Document)
            if kb_id:
                query = query.filter(Document.kb_id == kb_id)
            return query.offset(skip).limit(limit).all()

    def update_doc(self, doc_id: str, data: Dict) -> bool:
        with self.get_session() as session:
            doc = session.query(Document).filter(Document.id == doc_id).first()
            if not doc:
                return False
            for key, value in data.items():
                setattr(doc, key, value)
            session.commit()
            return True

    def delete_doc(self, doc_id: str) -> bool:
        with self.get_session() as session:
            doc = session.query(Document).filter(Document.id == doc_id).first()
            if not doc:
                return False
            session.delete(doc)
            session.commit()
            return True

    # ========== 文档块 ==========

    def create_chunk(self, chunk_id: str, data: Dict) -> DocumentChunk:
        with self.get_session() as session:
            chunk = DocumentChunk(
                id=chunk_id,
                doc_id=data["doc_id"],
                kb_id=data["kb_id"],
                content=data["content"],
                chunk_index=data.get("chunk_index"),
            )
            session.add(chunk)
            session.commit()
            session.refresh(chunk)
            return chunk

    def list_chunks(
        self, kb_id: str = None, doc_id: str = None, limit: int = 100
    ) -> List[DocumentChunk]:
        with self.get_session() as session:
            query = session.query(DocumentChunk)
            if kb_id:
                query = query.filter(DocumentChunk.kb_id == kb_id)
            if doc_id:
                query = query.filter(DocumentChunk.doc_id == doc_id)
            return query.limit(limit).all()

    # ========== 对话 ==========

    def create_conversation(self, conv_id: str, data: Dict) -> Conversation:
        with self.get_session() as session:
            conv = Conversation(
                id=conv_id, kb_id=data["kb_id"], title=data.get("title")
            )
            session.add(conv)
            session.commit()
            session.refresh(conv)
            return conv

    def get_conversation(self, conv_id: str) -> Optional[Conversation]:
        with self.get_session() as session:
            return (
                session.query(Conversation).filter(Conversation.id == conv_id).first()
            )

    def list_conversations(
        self, kb_id: str = None, user_id: str = None, limit: int = 50
    ) -> List[Conversation]:
        with self.get_session() as session:
            query = session.query(Conversation)
            if kb_id:
                query = query.filter(Conversation.kb_id == kb_id)
            return query.limit(limit).all()

    def create_message(self, msg_id: str, data: Dict) -> Message:
        with self.get_session() as session:
            msg = Message(
                id=msg_id,
                conversation_id=data["conversation_id"],
                role=data["role"],
                content=data["content"],
                sources=data.get("sources"),
            )
            session.add(msg)
            session.commit()
            session.refresh(msg)
            return msg

    def list_messages(self, conversation_id: str) -> List[Message]:
        with self.get_session() as session:
            return (
                session.query(Message)
                .filter(Message.conversation_id == conversation_id)
                .order_by(Message.created_at)
                .all()
            )

    # ========== 图谱实体 ==========

    def create_entity(self, entity_id: str, data: Dict) -> GraphEntity:
        with self.get_session() as session:
            entity = GraphEntity(
                id=entity_id,
                kb_id=data["kb_id"],
                entity_type=data["entity_type"],
                entity_name=data["entity_name"],
                properties=data.get("properties"),
                doc_id=data.get("doc_id"),
            )
            session.add(entity)
            session.commit()
            session.refresh(entity)
            return entity

    def list_entities(
        self, kb_id: str = None, entity_type: str = None, limit: int = 100
    ) -> List[GraphEntity]:
        with self.get_session() as session:
            query = session.query(GraphEntity)
            if kb_id:
                query = query.filter(GraphEntity.kb_id == kb_id)
            if entity_type:
                query = query.filter(GraphEntity.entity_type == entity_type)
            return query.limit(limit).all()

    # ========== 图谱关系 ==========

    def create_relation(self, rel_id: str, data: Dict) -> GraphRelation:
        with self.get_session() as session:
            rel = GraphRelation(
                id=rel_id,
                kb_id=data["kb_id"],
                source_id=data["source_id"],
                target_id=data["target_id"],
                relation_type=data["relation_type"],
                properties=data.get("properties"),
                confidence=data.get("confidence", 1.0),
            )
            session.add(rel)
            session.commit()
            session.refresh(rel)
            return rel

    def list_relations(
        self, kb_id: str = None, source_id: str = None, limit: int = 100
    ) -> List[GraphRelation]:
        with self.get_session() as session:
            query = session.query(GraphRelation)
            if kb_id:
                query = query.filter(GraphRelation.kb_id == kb_id)
            if source_id:
                query = query.filter(GraphRelation.source_id == source_id)
            return query.limit(limit).all()

    # ========== 分享 ==========

    def create_share(self, share_id: str, data: Dict) -> Share:
        with self.get_session() as session:
            share = Share(
                id=share_id,
                token=data["token"],
                resource_type=data["resource_type"],
                resource_id=data["resource_id"],
                title=data["title"],
                password_hash=data.get("password_hash"),
                created_by=data["created_by"],
            )
            session.add(share)
            session.commit()
            session.refresh(share)
            return share

    def get_share(self, share_id: str) -> Optional[Share]:
        with self.get_session() as session:
            return session.query(Share).filter(Share.id == share_id).first()

    def get_share_by_token(self, token: str) -> Optional[Share]:
        with self.get_session() as session:
            return (
                session.query(Share)
                .filter(Share.token == token, Share.is_active == True)
                .first()
            )

    def increment_share_view(self, share_id: str):
        with self.get_session() as session:
            share = session.query(Share).filter(Share.id == share_id).first()
            if share:
                share.view_count += 1
                session.commit()

    def list_shares(
        self, resource_type: str = None, resource_id: str = None
    ) -> List[Share]:
        with self.get_session() as session:
            query = session.query(Share).filter(Share.is_active == True)
            if resource_type and resource_id:
                query = query.filter(
                    Share.resource_type == resource_type,
                    Share.resource_id == resource_id,
                )
            return query.all()

    # ========== API Keys ==========

    def create_api_key(self, key_id: str, data: Dict) -> APIKey:
        with self.get_session() as session:
            api_key = APIKey(
                id=key_id,
                key_hash=data["key_hash"],
                name=data["name"],
                user_id=data["user_id"],
                org_id=data.get("org_id"),
            )
            session.add(api_key)
            session.commit()
            session.refresh(api_key)
            return api_key

    def get_api_key(self, key_hash: str) -> Optional[APIKey]:
        with self.get_session() as session:
            return (
                session.query(APIKey)
                .filter(APIKey.key_hash == key_hash, APIKey.is_active == True)
                .first()
            )

    # ========== Token 黑名单 ==========

    def revoke_token(
        self, token_hash: str, user_id: str = None, expires_in: int = 86400
    ):
        with self.get_session() as session:
            from datetime import timedelta

            revoked = RevokedToken(
                token_hash=token_hash,
                user_id=user_id,
                expires_at=datetime.utcnow() + timedelta(seconds=expires_in),
            )
            session.add(revoked)
            session.commit()

    def is_token_revoked(self, token_hash: str) -> bool:
        with self.get_session() as session:
            revoked = (
                session.query(RevokedToken)
                .filter(
                    RevokedToken.token_hash == token_hash,
                    RevokedToken.expires_at > datetime.utcnow(),
                )
                .first()
            )
            return revoked is not None

    # ========== 审计日志 ==========

    def log_action(self, data: Dict):
        with self.get_session() as session:
            log = AuditLog(
                user_id=data.get("user_id"),
                action=data["action"],
                resource_type=data.get("resource_type"),
                resource_id=data.get("resource_id"),
                details=data.get("details"),
                ip_address=data.get("ip_address"),
            )
            session.add(log)
            session.commit()

    def list_audit_logs(self, user_id: str = None, limit: int = 100) -> List[AuditLog]:
        with self.get_session() as session:
            query = session.query(AuditLog)
            if user_id:
                query = query.filter(AuditLog.user_id == user_id)
            return query.order_by(AuditLog.created_at.desc()).limit(limit).all()

    # ========== 原生 SQL 查询 ==========

    def execute(self, sql: str, params: Dict = None):
        """执行原生 SQL"""
        with self.get_session() as session:
            if params:
                return session.execute(text(sql), params)
            return session.execute(text(sql))

    def query_raw(self, sql: str, params: Dict = None) -> List[Dict]:
        """查询并返回字典列表"""
        with self.get_session() as session:
            result = session.execute(text(sql), params or {})
            return [dict(row._mapping) for row in result]


# 全局实例
orm_store = ORMStore()
