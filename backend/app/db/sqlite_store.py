"""
完整的 SQLite 数据库存储
"""
import sqlite3
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from contextlib import contextmanager
from loguru import logger


DB_PATH = os.getenv("DB_PATH", "./data/litekb.db")


class SQLiteStore:
    """SQLite 存储 - 完整表结构"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or DB_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """初始化所有表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # ========== 1. 用户表 ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE,
                hashed_password TEXT NOT NULL,
                avatar_url TEXT,
                is_active INTEGER DEFAULT 1,
                is_superuser INTEGER DEFAULT 0,
                last_login_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # ========== 2. 组织表 ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS organizations (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                slug TEXT UNIQUE NOT NULL,
                description TEXT,
                logo_url TEXT,
                owner_id TEXT NOT NULL,
                plan TEXT DEFAULT 'free',
                settings TEXT,  -- JSON
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (owner_id) REFERENCES users(id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS organization_members (
                id TEXT PRIMARY KEY,
                org_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'member',  -- owner/admin/member/viewer
                invited_by TEXT,
                joined_at TEXT NOT NULL,
                UNIQUE(org_id, user_id),
                FOREIGN KEY (org_id) REFERENCES organizations(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # ========== 3. API Keys ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id TEXT PRIMARY KEY,
                key_hash TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                org_id TEXT,
                user_id TEXT NOT NULL,
                permissions TEXT,  -- JSON
                last_used_at TEXT,
                expires_at TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                FOREIGN KEY (org_id) REFERENCES organizations(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # ========== 4. Token 黑名单 ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS revoked_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token_hash TEXT UNIQUE NOT NULL,
                user_id TEXT,
                reason TEXT,
                revoked_at TEXT NOT NULL,
                expires_at TEXT NOT NULL
            )
        """)
        
        # ========== 5. 知识库表 ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_bases (
                id TEXT PRIMARY KEY,
                org_id TEXT,
                name TEXT NOT NULL,
                description TEXT,
                embedding_model TEXT DEFAULT 'text-embedding-3-small',
                chunk_size INTEGER DEFAULT 512,
                chunk_overlap INTEGER DEFAULT 50,
                rag_mode TEXT DEFAULT 'naive',  -- naive/contextual/graph-augmented
                is_public INTEGER DEFAULT 0,
                settings TEXT,  -- JSON
                created_by TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (org_id) REFERENCES organizations(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS kb_members (
                id TEXT PRIMARY KEY,
                kb_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'member',
                joined_at TEXT NOT NULL,
                UNIQUE(kb_id, user_id),
                FOREIGN KEY (kb_id) REFERENCES knowledge_bases(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # ========== 6. 文档表 ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                kb_id TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT,
                content_type TEXT DEFAULT 'text/plain',
                file_size INTEGER,
                file_hash TEXT,
                status TEXT DEFAULT 'indexed',  -- pending/indexing/indexed/error
                error_message TEXT,
                metadata TEXT,  -- JSON
                lang TEXT DEFAULT 'zh',
                char_count INTEGER,
                created_by TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                indexed_at TEXT,
                FOREIGN KEY (kb_id) REFERENCES knowledge_bases(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """)
        
        # ========== 7. 文档块表 (向量检索) ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_chunks (
                id TEXT PRIMARY KEY,
                doc_id TEXT NOT NULL,
                kb_id TEXT NOT NULL,
                content TEXT NOT NULL,
                token_count INTEGER,
                metadata TEXT,  -- JSON
                embedding blob,
                created_at TEXT NOT NULL,
                FOREIGN KEY (doc_id) REFERENCES documents(id),
                FOREIGN KEY (kb_id) REFERENCES knowledge_bases(id)
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_kb ON document_chunks(kb_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_doc ON document_chunks(doc_id)")
        
        # ========== 8. 图谱实体表 ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entities (
                id TEXT PRIMARY KEY,
                kb_id TEXT NOT NULL,
                name TEXT NOT NULL,
                type TEXT NOT NULL,  -- PERSON/ORG/LOCATION/etc
                description TEXT,
                properties TEXT,  -- JSON
                source_doc_id TEXT,
                confidence REAL DEFAULT 1.0,
                aliases TEXT,  -- JSON
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (kb_id) REFERENCES knowledge_bases(id),
                FOREIGN KEY (source_doc_id) REFERENCES documents(id)
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entities_kb ON entities(kb_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(kb_id, type)")
        
        # ========== 9. 图谱关系表 ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS relations (
                id TEXT PRIMARY KEY,
                kb_id TEXT NOT NULL,
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                relation_type TEXT NOT NULL,  -- RELATED_TO/DEPENDS_ON/etc
                description TEXT,
                confidence REAL DEFAULT 1.0,
                source_doc_id TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (kb_id) REFERENCES knowledge_bases(id),
                FOREIGN KEY (source_id) REFERENCES entities(id),
                FOREIGN KEY (target_id) REFERENCES entities(id),
                FOREIGN KEY (source_doc_id) REFERENCES documents(id)
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_relations_kb ON relations(kb_id)")
        
        # ========== 10. 对话表 ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                kb_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                title TEXT,
                mode TEXT DEFAULT 'naive',
                temperature REAL DEFAULT 0.1,
                messages TEXT NOT NULL,  -- JSON
                token_count INTEGER,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (kb_id) REFERENCES knowledge_bases(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conv_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                token_count INTEGER,
                sources TEXT,  -- JSON
                created_at TEXT NOT NULL,
                FOREIGN KEY (conv_id) REFERENCES conversations(id)
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conv_id)")
        
        # ========== 11. 分享表 ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shares (
                id TEXT PRIMARY KEY,
                token TEXT UNIQUE NOT NULL,
                resource_type TEXT NOT NULL,  -- kb/doc/conv/search
                resource_id TEXT NOT NULL,
                title TEXT NOT NULL,
                password_hash TEXT,
                view_password TEXT,
                view_count INTEGER DEFAULT 0,
                max_views INTEGER,
                expires_at TEXT,
                is_active INTEGER DEFAULT 1,
                created_by TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_shares_resource ON shares(resource_type, resource_id)")
        
        # ========== 12. 导入导出任务 ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS import_jobs (
                id TEXT PRIMARY KEY,
                kb_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                source_type TEXT NOT NULL,  -- file/url/notion
                source_url TEXT,
                file_name TEXT,
                status TEXT DEFAULT 'pending',  -- pending/processing/completed/failed
                progress INTEGER DEFAULT 0,
                total_items INTEGER,
                processed_items INTEGER,
                error_message TEXT,
                settings TEXT,  -- JSON
                created_at TEXT NOT NULL,
                completed_at TEXT,
                FOREIGN KEY (kb_id) REFERENCES knowledge_bases(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS export_jobs (
                id TEXT PRIMARY KEY,
                kb_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                format TEXT NOT NULL,  -- markdown/json/html/csv
                status TEXT DEFAULT 'pending',
                file_path TEXT,
                file_size INTEGER,
                error_message TEXT,
                created_at TEXT NOT NULL,
                completed_at TEXT,
                expires_at TEXT,
                FOREIGN KEY (kb_id) REFERENCES knowledge_bases(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # ========== 13. 插件表 ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS plugins (
                id TEXT PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                version TEXT NOT NULL,
                description TEXT,
                settings TEXT,  -- JSON
                is_enabled INTEGER DEFAULT 1,
                hooks TEXT,  -- JSON
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # ========== 14. 用户设置 ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                id TEXT PRIMARY KEY,
                user_id TEXT UNIQUE NOT NULL,
                settings TEXT NOT NULL DEFAULT '{}',  -- JSON
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # ========== 15. 组织邀请 ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS org_invitations (
                id TEXT PRIMARY KEY,
                org_id TEXT NOT NULL,
                email TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'member',
                token TEXT UNIQUE NOT NULL,
                invited_by TEXT NOT NULL,
                status TEXT DEFAULT 'pending',  -- pending/accepted/expired/revoked
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                FOREIGN KEY (org_id) REFERENCES organizations(id),
                FOREIGN KEY (invited_by) REFERENCES users(id)
            )
        """)
        
        # ========== 16. 统计表 ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stat_type TEXT NOT NULL,
                stat_key TEXT NOT NULL,
                stat_value INTEGER DEFAULT 0,
                date TEXT,
                updated_at TEXT NOT NULL,
                UNIQUE(stat_type, stat_key, date)
            )
        """)
        
        # ========== 17. 操作日志 ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                org_id TEXT,
                action TEXT NOT NULL,  -- create/update/delete/login/logout
                resource_type TEXT,
                resource_id TEXT,
                details TEXT,  -- JSON
                ip_address TEXT,
                user_agent TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (org_id) REFERENCES organizations(id)
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_logs(created_at)")
        
        conn.commit()
        conn.close()
        logger.info(f"SQLite initialized: {self.db_path}")
    
    @contextmanager
    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    # ========== 辅助方法 ==========
    
    def _now(self):
        return datetime.utcnow().isoformat()
    
    def _dict_from_row(self, row):
        return dict(row) if row else None
    
    # ========== 用户 ==========
    
    def create_user(self, user_id: str, data: Dict) -> Dict:
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [user_id, data["username"], data.get("email"), data["hashed_password"],
                 data.get("avatar_url"), 1, 0, None, self._now(), self._now()]
            )
            conn.commit()
        return data
    
    def get_user(self, user_id: str) -> Optional[Dict]:
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM users WHERE id = ?", [user_id]).fetchone()
            return self._dict_from_row(row)
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM users WHERE username = ?", [username]).fetchone()
            return self._dict_from_row(row)
    
    def update_user(self, user_id: str, data: Dict) -> bool:
        with self._get_conn() as conn:
            for key, value in data.items():
                conn.execute(f"UPDATE users SET {key} = ?, updated_at = ? WHERE id = ?", 
                           [value, self._now(), user_id])
            conn.commit()
            return True
    
    def list_users(self) -> List[Dict]:
        with self._get_conn() as conn:
            return [self._dict_from_row(r) for r in conn.execute("SELECT * FROM users").fetchall()]
    
    # ========== 组织 ==========
    
    def create_organization(self, org_id: str, data: Dict) -> Dict:
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO organizations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [org_id, data["name"], data.get("slug"), data.get("description"),
                 data.get("logo_url"), data["owner_id"], "free", "{}", self._now(), self._now()]
            )
            conn.commit()
        return data
    
    def get_organization(self, org_id: str) -> Optional[Dict]:
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM organizations WHERE id = ?", [org_id]).fetchone()
            return self._dict_from_row(row)
    
    def list_organizations(self) -> List[Dict]:
        with self._get_conn() as conn:
            return [self._dict_from_row(r) for r in conn.execute("SELECT * FROM organizations").fetchall()]
    
    def add_org_member(self, member_id: str, data: Dict):
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO organization_members VALUES (?, ?, ?, ?, ?, ?)",
                [member_id, data["org_id"], data["user_id"], data.get("role", "member"),
                 data.get("invited_by"), self._now()]
            )
            conn.commit()
    
    def list_org_members(self, org_id: str) -> List[Dict]:
        with self._get_conn() as conn:
            return [self._dict_from_row(r) for r in 
                   conn.execute("SELECT * FROM organization_members WHERE org_id = ?", [org_id]).fetchall()]
    
    # ========== 知识库 ==========
    
    def create_kb(self, kb_id: str, data: Dict) -> Dict:
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO knowledge_bases VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [kb_id, data.get("org_id"), data["name"], data.get("description"),
                 data.get("embedding_model", "text-embedding-3-small"),
                 data.get("chunk_size", 512), data.get("chunk_overlap", 50),
                 data.get("rag_mode", "naive"), data.get("is_public", 0), "{}",
                 data["created_by"], self._now(), self._now()]
            )
            conn.commit()
        return data
    
    def get_kb(self, kb_id: str) -> Optional[Dict]:
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM knowledge_bases WHERE id = ?", [kb_id]).fetchone()
            return self._dict_from_row(row)
    
    def list_kbs(self, org_id: str = None) -> List[Dict]:
        with self._get_conn() as conn:
            if org_id:
                return [self._dict_from_row(r) for r in 
                       conn.execute("SELECT * FROM knowledge_bases WHERE org_id = ?", [org_id]).fetchall()]
            return [self._dict_from_row(r) for r in 
                   conn.execute("SELECT * FROM knowledge_bases").fetchall()]
    
    def update_kb(self, kb_id: str, data: Dict) -> bool:
        with self._get_conn() as conn:
            for key, value in data.items():
                conn.execute(f"UPDATE knowledge_bases SET {key} = ?, updated_at = ? WHERE id = ?",
                           [value, self._now(), kb_id])
            conn.commit()
            return True
    
    def delete_kb(self, kb_id: str) -> bool:
        with self._get_conn() as conn:
            conn.execute("DELETE FROM document_chunks WHERE kb_id = ?", [kb_id])
            conn.execute("DELETE FROM entities WHERE kb_id = ?", [kb_id])
            conn.execute("DELETE FROM relations WHERE kb_id = ?", [kb_id])
            cursor = conn.execute("DELETE FROM knowledge_bases WHERE id = ?", [kb_id])
            conn.commit()
            return cursor.rowcount > 0
    
    # ========== 文档 ==========
    
    def create_doc(self, doc_id: str, data: Dict) -> Dict:
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO documents VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [doc_id, data["kb_id"], data["title"], data.get("content"), data.get("content_type", "text/plain"),
                 data.get("file_size"), data.get("file_hash"), "pending", None, "{}",
                 data.get("lang", "zh"), data.get("char_count", 0), data["created_by"], self._now(), self._now(), None]
            )
            conn.commit()
        return data
    
    def get_doc(self, doc_id: str) -> Optional[Dict]:
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM documents WHERE id = ?", [doc_id]).fetchone()
            return self._dict_from_row(row)
    
    def list_docs(self, kb_id: str = None, skip: int = 0, limit: int = 100) -> List[Dict]:
        with self._get_conn() as conn:
            if kb_id:
                return [self._dict_from_row(r) for r in 
                       conn.execute("SELECT * FROM documents WHERE kb_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
                                  [kb_id, limit, skip]).fetchall()]
            return [self._dict_from_row(r) for r in 
                   conn.execute("SELECT * FROM documents ORDER BY created_at DESC LIMIT ? OFFSET ?",
                               [limit, skip]).fetchall()]
    
    def update_doc(self, doc_id: str, data: Dict) -> bool:
        with self._get_conn() as conn:
            for key, value in data.items():
                conn.execute(f"UPDATE documents SET {key} = ?, updated_at = ? WHERE id = ?",
                           [value, self._now(), doc_id])
            conn.commit()
            return True
    
    def delete_doc(self, doc_id: str) -> bool:
        with self._get_conn() as conn:
            conn.execute("DELETE FROM document_chunks WHERE doc_id = ?", [doc_id])
            cursor = conn.execute("DELETE FROM documents WHERE id = ?", [doc_id])
            conn.commit()
            return cursor.rowcount > 0
    
    # ========== 文档块 ==========
    
    def create_chunk(self, chunk_id: str, data: Dict):
        with self._get_conn() as conn:
            import json
            conn.execute(
                "INSERT INTO document_chunks VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                [chunk_id, data["doc_id"], data["kb_id"], data["content"],
                 data.get("token_count"), json.dumps(data.get("metadata", {})), None, self._now()]
            )
            conn.commit()
    
    def list_chunks(self, kb_id: str = None, doc_id: str = None, limit: int = 100) -> List[Dict]:
        with self._get_conn() as conn:
            import json
            if kb_id:
                return [self._dict_from_row(r) for r in 
                       conn.execute("SELECT * FROM document_chunks WHERE kb_id = ? LIMIT ?", [kb_id, limit]).fetchall()]
            if doc_id:
                return [self._dict_from_row(r) for r in 
                       conn.execute("SELECT * FROM document_chunks WHERE doc_id = ? LIMIT ?", [doc_id, limit]).fetchall()]
            return []
    
    # ========== 图谱实体 ==========
    
    def create_entity(self, entity_id: str, data: Dict):
        with self._get_conn() as conn:
            import json
            conn.execute(
                "INSERT INTO entities VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [entity_id, data["kb_id"], data["name"], data["type"], data.get("description"),
                 json.dumps(data.get("properties", {})), data.get("source_doc_id"),
                 data.get("confidence", 1.0), json.dumps(data.get("aliases", [])), self._now(), self._now()]
            )
            conn.commit()
    
    def list_entities(self, kb_id: str = None, entity_type: str = None, limit: int = 100) -> List[Dict]:
        with self._get_conn() as conn:
            if entity_type:
                return [self._dict_from_row(r) for r in 
                       conn.execute("SELECT * FROM entities WHERE kb_id = ? AND type = ? LIMIT ?", 
                                    [kb_id, entity_type, limit]).fetchall()]
            if kb_id:
                return [self._dict_from_row(r) for r in 
                       conn.execute("SELECT * FROM entities WHERE kb_id = ? LIMIT ?", [kb_id, limit]).fetchall()]
            return []
    
    # ========== 图谱关系 ==========
    
    def create_relation(self, rel_id: str, data: Dict):
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO relations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [rel_id, data["kb_id"], data["source_id"], data["target_id"], 
                 data["relation_type"], data.get("description"), data.get("confidence", 1.0),
                 data.get("source_doc_id"), self._now()]
            )
            conn.commit()
    
    def list_relations(self, kb_id: str = None, source_id: str = None, limit: int = 100) -> List[Dict]:
        with self._get_conn() as conn:
            if source_id:
                return [self._dict_from_row(r) for r in 
                       conn.execute("SELECT * FROM relations WHERE source_id = ? LIMIT ?", [source_id, limit]).fetchall()]
            if kb_id:
                return [self._dict_from_row(r) for r in 
                       conn.execute("SELECT * FROM relations WHERE kb_id = ? LIMIT ?", [kb_id, limit]).fetchall()]
            return []
    
    # ========== 对话 ==========
    
    def create_conversation(self, conv_id: str, data: Dict):
        with self._get_conn() as conn:
            import json
            conn.execute(
                "INSERT INTO conversations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [conv_id, data["kb_id"], data["user_id"], data.get("title"), 
                 data.get("mode", "naive"), data.get("temperature", 0.1),
                 json.dumps(data.get("messages", [])), 0, self._now(), self._now()]
            )
            conn.commit()
    
    def get_conversation(self, conv_id: str) -> Optional[Dict]:
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM conversations WHERE id = ?", [conv_id]).fetchone()
            return self._dict_from_row(row)
    
    def list_conversations(self, kb_id: str = None, user_id: str = None, limit: int = 50) -> List[Dict]:
        with self._get_conn() as conn:
            if kb_id:
                return [self._dict_from_row(r) for r in 
                       conn.execute("SELECT * FROM conversations WHERE kb_id = ? ORDER BY updated_at DESC LIMIT ?",
                                   [kb_id, limit]).fetchall()]
            if user_id:
                return [self._dict_from_row(r) for r in 
                       conn.execute("SELECT * FROM conversations WHERE user_id = ? ORDER BY updated_at DESC LIMIT ?",
                                   [user_id, limit]).fetchall()]
            return []
    
    def add_message(self, msg_id: str, data: Dict):
        with self._get_conn() as conn:
            import json
            conn.execute(
                "INSERT INTO messages VALUES (?, ?, ?, ?, ?, ?, ?)",
                [msg_id, data["conv_id"], data["role"], data["content"],
                 data.get("token_count"), json.dumps(data.get("sources", [])), self._now()]
            )
            conn.commit()
    
    def list_messages(self, conv_id: str) -> List[Dict]:
        with self._get_conn() as conn:
            return [self._dict_from_row(r) for r in 
                   conn.execute("SELECT * FROM messages WHERE conv_id = ? ORDER BY created_at", [conv_id]).fetchall()]
    
    # ========== 分享 ==========
    
    def create_share(self, share_id: str, data: Dict):
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO shares VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [share_id, data["token"], data["resource_type"], data["resource_id"], data["title"],
                 data.get("password_hash"), data.get("view_password"), 0, data.get("max_views"),
                 data.get("expires_at"), 1, data["created_by"], self._now()]
            )
            conn.commit()
    
    def get_share(self, share_id: str) -> Optional[Dict]:
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM shares WHERE id = ?", [share_id]).fetchone()
            return self._dict_from_row(row)
    
    def get_share_by_token(self, token: str) -> Optional[Dict]:
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM shares WHERE token = ? AND is_active = 1", [token]).fetchone()
            return self._dict_from_row(row)
    
    def increment_share_view(self, share_id: str):
        with self._get_conn() as conn:
            conn.execute("UPDATE shares SET view_count = view_count + 1 WHERE id = ?", [share_id])
            conn.commit()
    
    def list_shares(self, resource_type: str = None, resource_id: str = None) -> List[Dict]:
        with self._get_conn() as conn:
            if resource_type and resource_id:
                return [self._dict_from_row(r) for r in 
                       conn.execute("SELECT * FROM shares WHERE resource_type = ? AND resource_id = ? AND is_active = 1",
                                   [resource_type, resource_id]).fetchall()]
            return [self._dict_from_row(r) for r in 
                   conn.execute("SELECT * FROM shares WHERE is_active = 1").fetchall()]
    
    # ========== 统计 ==========
    
    def increment_stat(self, stat_type: str, stat_key: str, value: int = 1, date: str = None):
        with self._get_conn() as conn:
            date = date or datetime.utcnow().strftime("%Y-%m-%d")
            conn.execute(
                "INSERT INTO stats (stat_type, stat_key, stat_value, date, updated_at) VALUES (?, ?, ?, ?, ?) "
                "ON CONFLICT(stat_type, stat_key, date) DO UPDATE SET stat_value = stat_value + ?, updated_at = ?",
                [stat_type, stat_key, value, date, self._now(), value, self._now()]
            )
            conn.commit()
    
    def get_stats(self, stat_type: str, date: str = None) -> List[Dict]:
        with self._get_conn() as conn:
            if date:
                return [self._dict_from_row(r) for r in 
                       conn.execute("SELECT * FROM stats WHERE stat_type = ? AND date = ?", [stat_type, date]).fetchall()]
            return [self._dict_from_row(r) for r in 
                   conn.execute("SELECT * FROM stats WHERE stat_type = ?", [stat_type]).fetchall()]
    
    # ========== API Keys ==========
    
    def create_api_key(self, key_id: str, data: Dict):
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO api_keys VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [key_id, data["key_hash"], data["name"], data.get("org_id"), data["user_id"],
                 "{}", None, None, 1, self._now()]
            )
            conn.commit()
    
    def get_api_key(self, key_hash: str) -> Optional[Dict]:
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM api_keys WHERE key_hash = ? AND is_active = 1", [key_hash]).fetchone()
            return self._dict_from_row(row)
    
    # ========== Token 黑名单 ==========
    
    def revoke_token(self, token_hash: str, user_id: str = None, expires_in: int = 86400):
        with self._get_conn() as conn:
            expires_at = datetime.utcnow().timestamp() + expires_in
            conn.execute(
                "INSERT INTO revoked_tokens (token_hash, user_id, revoked_at, expires_at) VALUES (?, ?, ?, ?)",
                [token_hash, user_id, self._now(), expires_at]
            )
            conn.commit()
    
    def is_token_revoked(self, token_hash: str) -> bool:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT 1 FROM revoked_tokens WHERE token_hash = ? AND expires_at > ?",
                [token_hash, datetime.utcnow().timestamp()]
            ).fetchone()
            return row is not None
    
    # ========== 审计日志 ==========
    
    def log_action(self, data: Dict):
        with self._get_conn() as conn:
            import json
            conn.execute(
                "INSERT INTO audit_logs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [data.get("id"), data.get("user_id"), data.get("org_id"), data["action"],
                 data.get("resource_type"), data.get("resource_id"), json.dumps(data.get("details", {})),
                 data.get("ip_address"), data.get("user_agent"), self._now()]
            )
            conn.commit()
    
    def list_audit_logs(self, user_id: str = None, limit: int = 100) -> List[Dict]:
        with self._get_conn() as conn:
            if user_id:
                return [self._dict_from_row(r) for r in 
                       conn.execute("SELECT * FROM audit_logs WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
, limit]).fetch                                   [user_idall()]
            return [self._dict_from_row(r) for r in 
                   conn.execute("SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT ?", [limit]).fetchall()]


# 全局实例
sqlite_store = SQLiteStore()
