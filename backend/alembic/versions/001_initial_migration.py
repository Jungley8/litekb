"""Initial migration - create all tables

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00

"""
from typing import Union
from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    # 创建组织表
    op.create_table(
        'organizations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('slug', sa.String(100), unique=True, nullable=False),
        sa.Column('logo', sa.String(500)),
        sa.Column('settings', sa.JSON, default={}),
        sa.Column('plan', sa.String(50), default='free'),
        sa.Column('owner_id', sa.String(36)),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # 创建用户表
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('username', sa.String(100), unique=True, nullable=False),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('avatar', sa.String(500)),
        sa.Column('organization_id', sa.String(36), sa.ForeignKey('organizations.id')),
        sa.Column('role', sa.String(50), default='member'),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('last_login_at', sa.DateTime),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # 创建组织成员关联表
    op.create_table(
        'organization_members',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('organization_id', sa.String(36), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('role', sa.String(50), default='member'),
        sa.Column('joined_at', sa.DateTime, default=sa.func.now()),
        sa.UniqueConstraint('organization_id', 'user_id'),
    )
    
    # 创建邀请表
    op.create_table(
        'invitations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('organization_id', sa.String(36), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), default='member'),
        sa.Column('token', sa.String(100), unique=True, nullable=False),
        sa.Column('expires_at', sa.DateTime),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('created_by', sa.String(36)),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
    )
    
    # 创建 API Keys 表
    op.create_table(
        'api_keys',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('organization_id', sa.String(36), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('key_hash', sa.String(255), nullable=False),
        sa.Column('key_prefix', sa.String(20), nullable=False),
        sa.Column('scopes', sa.JSON, default=['read']),
        sa.Column('last_used_at', sa.DateTime),
        sa.Column('expires_at', sa.DateTime),
        sa.Column('created_by', sa.String(36)),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
    )
    
    # 创建知识库表
    op.create_table(
        'knowledge_bases',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('organization_id', sa.String(36), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('config', sa.JSON, default={}),
        sa.Column('is_public', sa.Boolean, default=False),
        sa.Column('created_by', sa.String(36)),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # 创建文档表
    op.create_table(
        'documents',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('organization_id', sa.String(36), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('kb_id', sa.String(36), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('file_type', sa.String(50)),
        sa.Column('content', sa.Text),
        sa.Column('metadata', sa.JSON, default={}),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('created_by', sa.String(36)),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # 创建文档分块表
    op.create_table(
        'document_chunks',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('doc_id', sa.String(36), nullable=False),
        sa.Column('kb_id', sa.String(36), nullable=False),
        sa.Column('chunk_index', sa.Integer),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('metadata', sa.JSON, default={}),
        sa.Column('embedding_id', sa.String(100)),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
    )
    
    # 创建对话表
    op.create_table(
        'conversations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('kb_id', sa.String(36), nullable=False),
        sa.Column('title', sa.String(500)),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # 创建消息表
    op.create_table(
        'messages',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('conversation_id', sa.String(36), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('sources', sa.JSON),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
    )
    
    # 创建知识图谱实体表
    op.create_table(
        'graph_entities',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('kb_id', sa.String(36), nullable=False),
        sa.Column('doc_id', sa.String(36)),
        sa.Column('entity_type', sa.String(100), nullable=False),
        sa.Column('entity_name', sa.String(500), nullable=False),
        sa.Column('properties', sa.JSON, default={}),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
    )
    
    # 创建知识图谱关系表
    op.create_table(
        'graph_relations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('kb_id', sa.String(36), nullable=False),
        sa.Column('source_id', sa.String(36), nullable=False),
        sa.Column('target_id', sa.String(36), nullable=False),
        sa.Column('relation_type', sa.String(100), nullable=False),
        sa.Column('properties', sa.JSON, default={}),
        sa.Column('confidence', sa.Float, default=1.0),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
    )
    
    # 创建审计日志表
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('organization_id', sa.String(36), sa.ForeignKey('organizations.id')),
        sa.Column('user_id', sa.String(36)),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(50)),
        sa.Column('resource_id', sa.String(36)),
        sa.Column('details', sa.JSON, default={}),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('user_agent', sa.String(500)),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
    )
    
    # 创建索引
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_username', 'users', ['username'])
    op.create_index('idx_docs_kb', 'documents', ['kb_id'])
    op.create_index('idx_chunks_doc', 'document_chunks', ['doc_id'])
    op.create_index('idx_chunks_kb', 'document_chunks', ['kb_id'])
    op.create_index('idx_graph_kb', 'graph_entities', ['kb_id'])
    op.create_index('idx_graph_kb_rel', 'graph_relations', ['kb_id'])


def downgrade() -> None:
    # 删除表
    op.drop_table('audit_logs')
    op.drop_table('graph_relations')
    op.drop_table('graph_entities')
    op.drop_table('messages')
    op.drop_table('conversations')
    op.drop_table('document_chunks')
    op.drop_table('documents')
    op.drop_table('knowledge_bases')
    op.drop_table('api_keys')
    op.drop_table('invitations')
    op.drop_table('organization_members')
    op.drop_table('users')
    op.drop_table('organizations')
