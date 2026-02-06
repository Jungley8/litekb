"""
数据库工厂 - 开发 SQLite，生产 PostgreSQL
"""
import os
from loguru import logger


DB_BACKEND = os.getenv("DB_BACKEND", "sqlite")  # sqlite / postgresql


# 选择数据库后端
if DB_BACKEND == "sqlite":
    from app.db.sqlite_store import sqlite_store
    db = sqlite_store
    logger.info(f"Using SQLite: {sqlite_store.db_path}")

elif DB_BACKEND == "postgresql":
    try:
        from app.db.postgres_store import postgres_store
        db = postgres_store
        logger.info("Using PostgreSQL")
    except ImportError:
        from app.db.sqlite_store import sqlite_store
        db = sqlite_store
        logger.warning("PostgreSQL not available, falling back to SQLite")

else:
    from app.db.sqlite_store import sqlite_store
    db = sqlite_store
    logger.warning(f"Unknown backend: {DB_BACKEND}, using SQLite")


# 便捷函数
def get_db():
    """获取数据库实例"""
    return db
