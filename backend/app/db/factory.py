"""
数据库工厂 - ORM 统一接口
"""
import os
from loguru import logger


DB_BACKEND = os.getenv("DB_BACKEND", "sqlite")  # sqlite / postgresql


# 选择数据库后端
if DB_BACKEND == "sqlite":
    from app.db.orm_store import orm_store
    db = orm_store
    logger.info(f"Using SQLite ORM: {orm_store.db_url}")

elif DB_BACKEND == "postgresql":
    try:
        from app.db.postgres_store import postgres_store
        db = postgres_store
        logger.info("Using PostgreSQL ORM")
    except ImportError:
        from app.db.orm_store import orm_store
        db = orm_store
        logger.warning("PostgreSQL not available, falling back to SQLite")

else:
    from app.db.orm_store import orm_store
    db = orm_store
    logger.warning(f"Unknown backend: {DB_BACKEND}, using SQLite ORM")


# 便捷函数
def get_db():
    """获取数据库实例"""
    return db


# 初始化数据库
from app.models import init_db
init_db()
