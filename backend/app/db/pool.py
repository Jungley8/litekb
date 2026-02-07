"""
数据库连接池配置
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from typing import Generator
import os
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# 数据库连接池配置
DATABASE_POOL_CONFIG = {
    "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
    "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20")),
    "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30")),
    "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "3600")),
    "pool_pre_ping": True,  # 连接前检查
}


def create_db_engine(database_url: str, poolclass=None):
    """创建数据库引擎"""

    if "sqlite" in database_url:
        # SQLite 不使用连接池
        return create_engine(
            database_url, connect_args={"check_same_thread": False}, echo=False
        )

    # PostgreSQL 使用连接池
    poolclass = poolclass or QueuePool

    engine = create_engine(
        database_url,
        poolclass=poolclass,
        **DATABASE_POOL_CONFIG,
        echo=False,  # 生产环境设为 False
        echo_pool=False,
    )

    # 启用连接前检查
    @event.listens_for(engine, "connect")
    def on_connect(dbapi_connection, connection_record):
        """连接时设置字符集"""
        if hasattr(dbapi_connection, "set_client_encoding"):
            dbapi_connection.set_client_encoding("UTF8")

    # 连接池事件
    @event.listens_for(engine, "checkout")
    def on_checkout(dbapi_connection, connection_record, connection_proxy):
        """检出连接时检查"""
        try:
            # 执行简单查询检查连接
            cursor = dbapi_connection.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
        except Exception as e:
            logger.error(f"Connection checkout failed: {e}")
            raise

    return engine


def get_session_factory(engine):
    """获取会话工厂"""
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_scoped_session(engine):
    """获取作用域会话"""
    return scoped_session(get_session_factory(engine))


async def get_db_session() -> Generator:
    """获取数据库会话 (依赖注入)"""
    from app.db.factory import db

    session = db.get_session()
    try:
        yield session
    finally:
        session.close()


# 连接池监控
class PoolMonitor:
    """连接池监控"""

    def __init__(self, engine):
        self.engine = engine
        self.pool = engine.pool

    def get_stats(self) -> dict:
        """获取连接池统计"""
        return {
            "pool_size": self.pool.size(),
            "pool_checkedin": self.pool.checkedin(),
            "pool_checkedout": self.pool.checkedout(),
            "pool_overflow": self.pool.overflow(),
            "pool_timeout": self.pool.timeout(),
        }


# 创建引擎实例
engine = create_db_engine(settings.database_url)
pool_monitor = PoolMonitor(engine)


def init_db_pool():
    """初始化数据库连接池"""
    logger.info(
        f"Database pool initialized: "
        f"size={DATABASE_POOL_CONFIG['pool_size']}, "
        f"max_overflow={DATABASE_POOL_CONFIG['max_overflow']}"
    )
