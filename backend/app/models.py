"""
数据库模型
"""
from sqlalchemy import create_engine, Column, String, Text, Integer, Float, DateTime, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import uuid

Base = declarative_base()


def gen_uuid():
    return str(uuid.uuid4())


class User(Base):
    """用户"""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=gen_uuid)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255))
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class KnowledgeBase(Base):
    """知识库"""
    __tablename__ = "knowledge_bases"
    
    id = Column(String(36), primary_key=True, default=gen_uuid)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    config = Column(JSON, default={})
    created_by = Column(String(36))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Document(Base):
    """文档"""
    __tablename__ = "documents"
    
    id = Column(String(36), primary_key=True, default=gen_uuid)
    title = Column(String(500), nullable=False)
    file_type = Column(String(50))  # txt, md, pdf, docx
    file_path = Column(String(1000))
    file_size = Column(Integer)
    content = Column(Text)
    metadata = Column(JSON, default={})
    status = Column(String(50), default="pending")  # pending, processing, indexed, failed
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class KBDocument(Base):
    """知识库-文档关联"""
    __tablename__ = "kb_documents"
    
    id = Column(String(36), primary_key=True, default=gen_uuid)
    kb_id = Column(String(36), nullable=False)
    doc_id = Column(String(36), nullable=False)
    chunk_count = Column(Integer, default=0)
    added_at = Column(DateTime, default=datetime.utcnow)


class DocumentChunk(Base):
    """文档分块"""
    __tablename__ = "document_chunks"
    
    id = Column(String(36), primary_key=True, default=gen_uuid)
    doc_id = Column(String(36), nullable=False)
    kb_id = Column(String(36), nullable=False)
    chunk_index = Column(Integer)
    content = Column(Text, nullable=False)
    metadata = Column(JSON, default={})
    embedding_id = Column(String(100))  # Qdrant 中的 point ID
    created_at = Column(DateTime, default=datetime.utcnow)


class Conversation(Base):
    """对话"""
    __tablename__ = "conversations"
    
    id = Column(String(36), primary_key=True, default=gen_uuid)
    kb_id = Column(String(36), nullable=False)
    title = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Message(Base):
    """对话消息"""
    __tablename__ = "messages"
    
    id = Column(String(36), primary_key=True, default=gen_uuid)
    conversation_id = Column(String(36), nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant
    content = Column(Text, nullable=False)
    sources = Column(JSON)  # 引用来源
    created_at = Column(DateTime, default=datetime.utcnow)


class GraphEntity(Base):
    """知识图谱实体"""
    __tablename__ = "graph_entities"
    
    id = Column(String(36), primary_key=True, default=gen_uuid)
    kb_id = Column(String(36), nullable=False)
    doc_id = Column(String(36))
    entity_type = Column(String(100), nullable=False)
    entity_name = Column(String(500), nullable=False)
    properties = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)


class GraphRelation(Base):
    """知识图谱关系"""
    __tablename__ = "graph_relations"
    
    id = Column(String(36), primary_key=True, default=gen_uuid)
    kb_id = Column(String(36), nullable=False)
    source_id = Column(String(36), nullable=False)
    target_id = Column(String(36), nullable=False)
    relation_type = Column(String(100), nullable=False)
    properties = Column(JSON, default={})
    confidence = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)


# 数据库初始化
_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        from app.config import settings
        _engine = create_engine(
            settings.database_url,
            connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
        )
    return _engine


def get_session():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal()


def init_db():
    """初始化数据库"""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
