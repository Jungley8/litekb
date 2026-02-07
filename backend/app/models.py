"""
数据库模型 - 完整 ORM 定义
"""

from sqlalchemy import (
    create_engine,
    Column,
    String,
    Text,
    Integer,
    Float,
    DateTime,
    Boolean,
    JSON,
    ForeignKey,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()


def gen_uuid():
    return str(uuid.uuid4())


# ========== 用户相关 ==========


class User(Base):
    """用户"""

    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True)
    hashed_password = Column(String(255), nullable=False)
    avatar_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    last_login_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    relationships = relationship("OrganizationMember", back_populates="user")
    api_keys = relationship("APIKey", back_populates="user")


class UserSetting(Base):
    """用户设置"""

    __tablename__ = "user_settings"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False)
    settings = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="settings")


# ========== 组织相关 ==========


class Organization(Base):
    """组织"""

    __tablename__ = "organizations"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    name = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True, nullable=False)
    description = Column(Text)
    logo_url = Column(String(500))
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    plan = Column(String(50), default="free")
    settings = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User")
    members = relationship("OrganizationMember", back_populates="organization")


class OrganizationMember(Base):
    """组织成员"""

    __tablename__ = "organization_members"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    org_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    role = Column(String(50), default="member")  # owner/admin/member/viewer
    invited_by = Column(String(36))
    joined_at = Column(DateTime, default=datetime.utcnow)

    organization = relationship("Organization", back_populates="members")
    user = relationship("User", back_populates="relationships")


class OrgInvitation(Base):
    """组织邀请"""

    __tablename__ = "org_invitations"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    org_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    email = Column(String(255), nullable=False)
    role = Column(String(50), default="member")
    token = Column(String(100), unique=True, nullable=False)
    invited_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    status = Column(String(50), default="pending")  # pending/accepted/expired/revoked
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)


# ========== 认证相关 ==========


class APIKey(Base):
    """API Keys"""

    __tablename__ = "api_keys"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    key_hash = Column(String(64), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    org_id = Column(String(36), ForeignKey("organizations.id"))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    permissions = Column(JSON, default={})
    last_used_at = Column(DateTime)
    expires_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="api_keys")


class RevokedToken(Base):
    """Token 黑名单"""

    __tablename__ = "revoked_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    token_hash = Column(String(64), unique=True, nullable=False)
    user_id = Column(String(36))
    reason = Column(Text)
    revoked_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)


# ========== 知识库相关 ==========


class KnowledgeBase(Base):
    """知识库"""

    __tablename__ = "knowledge_bases"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    org_id = Column(String(36), ForeignKey("organizations.id"))
    name = Column(String(200), nullable=False)
    description = Column(Text)
    embedding_model = Column(String(100), default="text-embedding-3-small")
    chunk_size = Column(Integer, default=512)
    chunk_overlap = Column(Integer, default=50)
    rag_mode = Column(String(50), default="naive")
    is_public = Column(Boolean, default=False)
    settings = Column(JSON, default={})
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    documents = relationship("Document", back_populates="knowledge_base")
    conversations = relationship("Conversation", back_populates="knowledge_base")
    entities = relationship("GraphEntity", back_populates="knowledge_base")


class KBActivity(Base):
    """知识库活动"""

    __tablename__ = "kb_activities"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    kb_id = Column(String(36), ForeignKey("knowledge_bases.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"))
    action = Column(
        String(100), nullable=False
    )  # create_doc/update_doc/delete_doc/chat/search
    resource_type = Column(String(50))
    resource_id = Column(String(36))
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)


# ========== 文档相关 ==========


class Document(Base):
    """文档"""

    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    kb_id = Column(String(36), ForeignKey("knowledge_bases.id"), nullable=False)
    title = Column(String(500), nullable=False)
    content = Column(Text)
    content_type = Column(String(50), default="text/plain")
    file_size = Column(Integer)
    file_hash = Column(String(64))
    status = Column(String(50), default="pending")  # pending/indexing/indexed/error
    error_message = Column(Text)
    metadata = Column(JSON, default={})
    lang = Column(String(10), default="zh")
    char_count = Column(Integer)
    created_by = Column(String(36), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    indexed_at = Column(DateTime)

    knowledge_base = relationship("KnowledgeBase", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document")


class DocumentChunk(Base):
    """文档分块"""

    __tablename__ = "document_chunks"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    doc_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    kb_id = Column(String(36), ForeignKey("knowledge_bases.id"), nullable=False)
    chunk_index = Column(Integer)
    content = Column(Text, nullable=False)
    token_count = Column(Integer)
    metadata = Column(JSON, default={})
    embedding_id = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="chunks")


# ========== 对话相关 ==========


class Conversation(Base):
    """对话"""

    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    kb_id = Column(String(36), ForeignKey("knowledge_bases.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    title = Column(String(500))
    mode = Column(String(50), default="naive")
    temperature = Column(Float, default=0.1)
    token_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    knowledge_base = relationship("KnowledgeBase", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")


class Message(Base):
    """对话消息"""

    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)  # user/assistant/system
    content = Column(Text, nullable=False)
    token_count = Column(Integer)
    sources = Column(JSON)  # 引用的文档来源
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")


# ========== 知识图谱相关 ==========


class GraphEntity(Base):
    """图谱实体"""

    __tablename__ = "graph_entities"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    kb_id = Column(String(36), ForeignKey("knowledge_bases.id"), nullable=False)
    doc_id = Column(String(36), ForeignKey("documents.id"))
    entity_type = Column(String(100), nullable=False)  # PERSON/ORG/LOCATION/etc
    entity_name = Column(String(500), nullable=False)
    description = Column(Text)
    properties = Column(JSON, default={})
    aliases = Column(JSON, default=[])
    confidence = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    knowledge_base = relationship("KnowledgeBase", back_populates="entities")

    outgoing = relationship(
        "GraphRelation", foreign_keys="GraphRelation.source_id", back_populates="source"
    )
    incoming = relationship(
        "GraphRelation", foreign_keys="GraphRelation.target_id", back_populates="target"
    )


class GraphRelation(Base):
    """图谱关系"""

    __tablename__ = "graph_relations"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    kb_id = Column(String(36), ForeignKey("knowledge_bases.id"), nullable=False)
    source_id = Column(String(36), ForeignKey("graph_entities.id"), nullable=False)
    target_id = Column(String(36), ForeignKey("graph_entities.id"), nullable=False)
    relation_type = Column(String(100), nullable=False)  # RELATED_TO/DEPENDS_ON/etc
    description = Column(Text)
    properties = Column(JSON, default={})
    confidence = Column(Float, default=1.0)
    doc_id = Column(String(36), ForeignKey("documents.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    source = relationship(
        "GraphEntity", foreign_keys=[source_id], back_populates="outgoing"
    )
    target = relationship(
        "GraphEntity", foreign_keys=[target_id], back_populates="incoming"
    )


# ========== 分享相关 ==========


class Share(Base):
    """分享链接"""

    __tablename__ = "shares"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    token = Column(String(100), unique=True, nullable=False)
    resource_type = Column(String(50), nullable=False)  # kb/doc/conv/search
    resource_id = Column(String(36), nullable=False)
    title = Column(String(500), nullable=False)
    password_hash = Column(String(255))
    view_password = Column(String(100))
    view_count = Column(Integer, default=0)
    max_views = Column(Integer)
    expires_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# ========== 任务相关 ==========


class ImportJob(Base):
    """导入任务"""

    __tablename__ = "import_jobs"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    kb_id = Column(String(36), ForeignKey("knowledge_bases.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    source_type = Column(String(50), nullable=False)  # file/url/notion
    source_url = Column(String(1000))
    file_name = Column(String(500))
    status = Column(
        String(50), default="pending"
    )  # pending/processing/completed/failed
    progress = Column(Integer, default=0)
    total_items = Column(Integer)
    processed_items = Column(Integer)
    error_message = Column(Text)
    settings = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)


class ExportJob(Base):
    """导出任务"""

    __tablename__ = "export_jobs"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    kb_id = Column(String(36), ForeignKey("knowledge_bases.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    format = Column(String(20), nullable=False)  # markdown/json/html/csv
    status = Column(String(50), default="pending")
    file_path = Column(String(1000))
    file_size = Column(Integer)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    expires_at = Column(DateTime)


# ========== 插件相关 ==========


class Plugin(Base):
    """插件"""

    __tablename__ = "plugins"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    name = Column(String(100), unique=True, nullable=False)
    version = Column(String(20), nullable=False)
    description = Column(Text)
    settings = Column(JSON, default={})
    is_enabled = Column(Boolean, default=True)
    hooks = Column(JSON, default=[])
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ========== 统计相关 ==========


class Stat(Base):
    """统计"""

    __tablename__ = "stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stat_type = Column(String(100), nullable=False)  # api_calls/searches/chats/docs
    stat_key = Column(String(200), nullable=False)
    stat_value = Column(Integer, default=0)
    date = Column(String(10))  # YYYY-MM-DD
    updated_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    """审计日志"""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("users.id"))
    org_id = Column(String(36), ForeignKey("organizations.id"))
    action = Column(String(100), nullable=False)  # create/update/delete/login/logout
    resource_type = Column(String(50))
    resource_id = Column(String(36))
    details = Column(JSON)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


# ========== 数据库初始化 ==========

_engine = None


def get_engine():
    global _engine
    if _engine is None:
        from app.config import settings

        _engine = create_engine(
            settings.database_url,
            connect_args=(
                {"check_same_thread": False}
                if "sqlite" in settings.database_url
                else {}
            ),
        )
    return _engine


def init_db():
    """初始化数据库"""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
