"""
SQLite 数据库存储
"""
import sqlite3
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from contextlib import contextmanager
from loguru import logger


DB_PATH = os.getenv("DB_PATH", "./data/litekb.db")


class SQLiteStore:
    """SQLite 存储"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or DB_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 用户表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT,
                hashed_password TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        
        # 知识库表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_bases (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                doc_count INTEGER DEFAULT 0,
                created_by TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """)
        
        # 文档表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                kb_id TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT,
                metadata TEXT,
                status TEXT DEFAULT 'indexed',
                created_at TEXT NOT NULL,
                FOREIGN KEY (kb_id) REFERENCES knowledge_bases(id)
            )
        """)
        
        # 对话表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                kb_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                messages TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (kb_id) REFERENCES knowledge_bases(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # 分享表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shares (
                id TEXT PRIMARY KEY,
                token TEXT UNIQUE NOT NULL,
                resource_type TEXT NOT NULL,
                resource_id TEXT NOT NULL,
                title TEXT NOT NULL,
                password TEXT,
                view_count INTEGER DEFAULT 0,
                expires_at TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                created_by TEXT
            )
        """)
        
        # 统计表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stat_type TEXT NOT NULL,
                stat_key TEXT NOT NULL,
                stat_value INTEGER DEFAULT 0,
                updated_at TEXT NOT NULL,
                UNIQUE(stat_type, stat_key)
            )
        """)
        
        # 索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_docs_kb ON documents(kb_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_convs_kb ON conversations(kb_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_shares_resource ON shares(resource_type, resource_id)")
        
        conn.commit()
        conn.close()
        logger.info(f"SQLite initialized: {self.db_path}")
    
    @contextmanager
    def _get_conn(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    # ========== 用户 ==========
    
    def create_user(self, user_id: str, data: Dict) -> Dict:
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO users VALUES (?, ?, ?, ?, ?)",
                [user_id, data["username"], data.get("email"), data["hashed_password"], datetime.utcnow().isoformat()]
            )
            conn.commit()
        return data
    
    def get_user(self, user_id: str) -> Optional[Dict]:
        with self._get_conn() as conn:
            cursor = conn.execute("SELECT * FROM users WHERE id = ?", [user_id])
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        with self._get_conn() as conn:
            cursor = conn.execute("SELECT * FROM users WHERE username = ?", [username])
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def list_users(self) -> List[Dict]:
        with self._get_conn() as conn:
            cursor = conn.execute("SELECT * FROM users")
            return [dict(row) for row in cursor.fetchall()]
    
    # ========== 知识库 ==========
    
    def create_kb(self, kb_id: str, data: Dict) -> Dict:
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO knowledge_bases VALUES (?, ?, ?, ?, ?, ?)",
                [kb_id, data["name"], data.get("description"), 0, data["created_by"], datetime.utcnow().isoformat()]
            )
            conn.commit()
        return data
    
    def get_kb(self, kb_id: str) -> Optional[Dict]:
        with self._get_conn() as conn:
            cursor = conn.execute("SELECT * FROM knowledge_bases WHERE id = ?", [kb_id])
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def list_kbs(self) -> List[Dict]:
        with self._get_conn() as conn:
            cursor = conn.execute("SELECT * FROM knowledge_bases")
            return [dict(row) for row in cursor.fetchall()]
    
    def update_kb(self, kb_id: str, data: Dict) -> bool:
        with self._get_conn() as conn:
            cursor = conn.execute("SELECT * FROM knowledge_bases WHERE id = ?", [kb_id])
            if not cursor.fetchone():
                return False
            
            for key, value in data.items():
                conn.execute(f"UPDATE knowledge_bases SET {key} = ? WHERE id = ?", [value, kb_id])
            conn.commit()
            return True
    
    def delete_kb(self, kb_id: str) -> bool:
        with self._get_conn() as conn:
            # 删除关联文档
            conn.execute("DELETE FROM documents WHERE kb_id = ?", [kb_id])
            conn.execute("DELETE FROM conversations WHERE kb_id = ?", [kb_id])
            # 删除知识库
            cursor = conn.execute("DELETE FROM knowledge_bases WHERE id = ?", [kb_id])
            conn.commit()
            return cursor.rowcount > 0
    
    def increment_doc_count(self, kb_id: str, delta: int = 1):
        with self._get_conn() as conn:
            conn.execute("UPDATE knowledge_bases SET doc_count = doc_count + ? WHERE id = ?", [delta, kb_id])
            conn.commit()
    
    # ========== 文档 ==========
    
    def create_doc(self, doc_id: str, data: Dict) -> Dict:
        import json
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO documents VALUES (?, ?, ?, ?, ?, ?, ?)",
                [doc_id, data["kb_id"], data["title"], data.get("content"), 
                 json.dumps(data.get("metadata", {})), "indexed", datetime.utcnow().isoformat()]
            )
            conn.commit()
            
            # 更新计数
            self.increment_doc_count(data["kb_id"], 1)
        
        return data
    
    def get_doc(self, doc_id: str) -> Optional[Dict]:
        with self._get_conn() as conn:
            cursor = conn.execute("SELECT * FROM documents WHERE id = ?", [doc_id])
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def list_docs(self, kb_id: str = None, skip: int = 0, limit: int = 100) -> List[Dict]:
        with self._get_conn() as conn:
            if kb_id:
                cursor = conn.execute("SELECT * FROM documents WHERE kb_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?", 
                                     [kb_id, limit, skip])
            else:
                cursor = conn.execute("SELECT * FROM documents ORDER BY created_at DESC LIMIT ? OFFSET ?", 
                                     [limit, skip])
            return [dict(row) for row in cursor.fetchall()]
    
    def delete_doc(self, doc_id: str) -> bool:
        with self._get_conn() as conn:
            # 获取 kb_id
            cursor = conn.execute("SELECT kb_id FROM documents WHERE id = ?", [doc_id])
            row = cursor.fetchone()
            if not row:
                return False
            
            kb_id = row["kb_id"]
            cursor = conn.execute("DELETE FROM documents WHERE id = ?", [doc_id])
            conn.commit()
            
            # 更新计数
            if cursor.rowcount > 0:
                self.increment_doc_count(kb_id, -1)
                return True
            return False
    
    # ========== 对话 ==========
    
    def create_conversation(self, conv_id: str, data: Dict) -> Dict:
        import json
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO conversations VALUES (?, ?, ?, ?, ?)",
                [conv_id, data["kb_id"], data["user_id"], json.dumps(data.get("messages", [])), datetime.utcnow().isoformat()]
            )
            conn.commit()
        return data
    
    def get_conversation(self, conv_id: str) -> Optional[Dict]:
        with self._get_conn() as conn:
            cursor = conn.execute("SELECT * FROM conversations WHERE id = ?", [conv_id])
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def list_conversations(self, kb_id: str = None, user_id: str = None) -> List[Dict]:
        with self._get_conn() as conn:
            if kb_id:
                cursor = conn.execute("SELECT * FROM conversations WHERE kb_id = ? ORDER BY created_at DESC", [kb_id])
            elif user_id:
                cursor = conn.execute("SELECT * FROM conversations WHERE user_id = ? ORDER BY created_at DESC", [user_id])
            else:
                cursor = conn.execute("SELECT * FROM conversations ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]
    
    # ========== 分享 ==========
    
    def create_share(self, share_id: str, data: Dict) -> Dict:
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO shares VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [share_id, data["token"], data["resource_type"], data["resource_id"], data["title"],
                 data.get("password"), 0, data.get("expires_at"), 1, datetime.utcnow().isoformat(), data.get("created_by")]
            )
            conn.commit()
        return data
    
    def get_share(self, share_id: str) -> Optional[Dict]:
        with self._get_conn() as conn:
            cursor = conn.execute("SELECT * FROM shares WHERE id = ?", [share_id])
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_share_by_token(self, token: str) -> Optional[Dict]:
        with self._get_conn() as conn:
            cursor = conn.execute("SELECT * FROM shares WHERE token = ?", [token])
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def list_shares(self, kb_id: str = None) -> List[Dict]:
        with self._get_conn() as conn:
            if kb_id:
                cursor = conn.execute("SELECT * FROM shares WHERE resource_id = ? AND is_active = 1", [kb_id])
            else:
                cursor = conn.execute("SELECT * FROM shares WHERE is_active = 1")
            return [dict(row) for row in cursor.fetchall()]
    
    def update_share_view(self, share_id: str):
        with self._get_conn() as conn:
            conn.execute("UPDATE shares SET view_count = view_count + 1 WHERE id = ?", [share_id])
            conn.commit()
    
    def delete_share(self, share_id: str) -> bool:
        with self._get_conn() as conn:
            cursor = conn.execute("UPDATE shares SET is_active = 0 WHERE id = ?", [share_id])
            conn.commit()
            return cursor.rowcount > 0
    
    # ========== 统计 ==========
    
    def increment_stat(self, stat_type: str, key: str, value: int = 1):
        with self._get_conn() as conn:
            cursor = conn.execute(
                "INSERT INTO stats (stat_type, stat_key, stat_value, updated_at) VALUES (?, ?, ?, ?) "
                "ON CONFLICT(stat_type, stat_key) DO UPDATE SET stat_value = stat_value + ?, updated_at = ?",
                [stat_type, key, value, datetime.utcnow().isoformat(), value, datetime.utcnow().isoformat()]
            )
            conn.commit()
    
    def get_stats(self, stat_type: str) -> Dict:
        with self._get_conn() as conn:
            cursor = conn.execute("SELECT stat_key, stat_value FROM stats WHERE stat_type = ?", [stat_type])
            return {row["stat_key"]: row["stat_value"] for row in cursor.fetchall()}


# 全局实例
sqlite_store = SQLiteStore()
