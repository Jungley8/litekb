"""
多租户数据模型
"""

from sqlalchemy import (
    create_engine,
    Column,
    String,
    Text,
    Integer,
    Float,
    DateTime,
    JSON,
    Boolean,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()


def gen_uuid():
    return str(uuid.uuid4())


class Organization(Base):
    """组织/租户"""

    __tablename__ = "organizations"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    name = Column(String(200), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    logo = Column(String(500))
    settings = Column(JSON, default={})
    plan = Column(String(50), default="free")
    owner_id = Column(String(36))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class User(Base):
    """用户"""

    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    avatar = Column(String(500))

    # 多租户字段
    organization_id = Column(String(36), ForeignKey("organizations.id"))
    role = Column(String(50), default="member")  # owner, admin, member

    # 状态
    is_active = Column(Boolean, default=True)
    last_login_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class OrganizationMember(Base):
    """组织成员关联 (支持一人多组织)"""

    __tablename__ = "organization_members"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    role = Column(String(50), default="member")
    joined_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("organization_id", "user_id", name="uq_org_user"),
    )


class Invitation(Base):
    """邀请"""

    __tablename__ = "invitations"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    email = Column(String(255), nullable=False)
    role = Column(String(50), default="member")
    token = Column(String(100), unique=True, nullable=False)
    expires_at = Column(DateTime)
    status = Column(String(20), default="pending")  # pending, accepted, expired
    created_by = Column(String(36))
    created_at = Column(DateTime, default=datetime.utcnow)


class APIKey(Base):
    """API Key (服务账号)"""

    __tablename__ = "api_keys"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    name = Column(String(200), nullable=False)
    key_hash = Column(String(255), nullable=False)
    key_prefix = Column(String(20), nullable=False)  # 显示用
    scopes = Column(JSON, default=["read"])  # read, write, admin
    last_used_at = Column(DateTime)
    expires_at = Column(DateTime)
    created_by = Column(String(36))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class KnowledgeBase(Base):
    """知识库"""

    __tablename__ = "knowledge_bases"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    config = Column(JSON, default={})
    is_public = Column(Boolean, default=False)  # 公开知识库

    created_by = Column(String(36))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# 原有表添加外键
class Document(Base):
    """文档"""

    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    kb_id = Column(String(36), nullable=False)

    title = Column(String(500), nullable=False)
    file_type = Column(String(50))
    content = Column(Text)
    extra_metadata = Column(JSON, default={})
    status = Column(String(50), default="pending")

    created_by = Column(String(36))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AuditLog(Base):
    """审计日志"""

    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id"))
    user_id = Column(String(36))

    action = Column(String(100), nullable=False)  # kb:create, doc:delete, etc.
    resource_type = Column(String(50))
    resource_id = Column(String(36))
    details = Column(JSON, default={})

    ip_address = Column(String(45))
    user_agent = Column(String(500))

    created_at = Column(DateTime, default=datetime.utcnow)
