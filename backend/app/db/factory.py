"""
数据库工厂 - 支持多种后端
"""
from typing import Optional
from loguru import logger


class DatabaseFactory:
    """数据库工厂"""
    
    _instance = None
    _backend = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def init(self, backend: str = None):
        """初始化数据库"""
        backend = backend or os.getenv("DB_BACKEND", "json")
        
        if backend == "json":
            from app.db.json_store import json_store
            self._backend = json_store
            logger.info("使用 JSON 文件存储")
        
        elif backend == "sqlite":
            # 未来支持 SQLite
            from app.db.sqlite_store import sqlite_store
            self._backend = sqlite_store
            logger.info("使用 SQLite 存储")
        
        elif backend == "postgresql":
            # 未来支持 PostgreSQL
            from app.db.postgres_store import postgres_store
            self._backend = postgres_store
            logger.info("使用 PostgreSQL 存储")
        
        else:
            raise ValueError(f"Unknown database backend: {backend}")
    
    @property
    def db(self):
        if self._backend is None:
            self.init()
        return self._backend


# 全局数据库实例
db = DatabaseFactory()


# 便捷函数
def get_db():
    """获取数据库实例"""
    return db.db


# 初始化
import os
DB_BACKEND = os.getenv("DB_BACKEND", "json")
db.init(DB_BACKEND)
