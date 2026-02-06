"""Alembic 数据库迁移配置"""
import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic.runtime.migration import MigrationContext
from alembic.config import Config
from alembic import command

# 添加项目路径
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.models_v2 import Base
from app.config import settings


def get_url():
    """获取数据库 URL"""
    return settings.database_url


def get_engine():
    """获取数据库引擎"""
    from sqlalchemy import create_engine
    return create_engine(get_url(), poolclass=pool.NullPool)


def get_connection():
    """获取数据库连接"""
    engine = get_engine()
    return engine.connect()


def run_migrations_offline():
    """离线运行迁移"""
    url = get_url()
    configuration = {
        'sqlalchemy.url': url
    }
    
    fileConfig('alembic.ini')
    context = MigrationContext.configure(
        url=url,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """在线运行迁移"""
    configuration = {
        'sqlalchemy.url': get_url()
    }
    
    engine = engine_from_config(
        configuration,
        prefix='sqlalchemy.',
        poolclass=pool.NullPool
    )
    
    with engine.connect() as connection:
        context = MigrationContext.configure(
            connection=connection,
            target_metadata=Base.metadata
        )
        
        with context.begin_transaction():
            context.run_migrations()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Database migrations')
    parser.add_argument('--offline', action='store_true', help='Run offline')
    args = parser.parse_args()
    
    if args.offline:
        run_migrations_offline()
    else:
        run_migrations_online()
