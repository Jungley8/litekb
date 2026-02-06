"""
JSON 文件持久化存储
"""
import json
import os
from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger


class JSONStore:
    """JSON 文件存储"""
    
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(os.path.join(data_dir, "json"), exist_ok=True)
    
    def _get_path(self, table: str) -> str:
        return os.path.join(self.data_dir, "json", f"{table}.json")
    
    def _load(self, table: str) -> Dict:
        """加载数据"""
        path = self._get_path(table)
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Load {table} failed: {e}")
        return {}
    
    def _save(self, table: str, data: Dict):
        """保存数据"""
        path = self._get_path(table)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    
    # ========== 用户 ==========
    
    def create_user(self, user_id: str, data: Dict) -> Dict:
        users = self._load("users")
        data["created_at"] = datetime.utcnow().isoformat()
        users[user_id] = data
        self._save("users", users)
        return data
    
    def get_user(self, user_id: str) -> Optional[Dict]:
        users = self._load("users")
        return users.get(user_id)
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        users = self._load("users")
        for u in users.values():
            if u.get("username") == username:
                return u
        return None
    
    def list_users(self) -> list:
        users = self._load("users")
        return list(users.values())
    
    # ========== 知识库 ==========
    
    def create_kb(self, kb_id: str, data: Dict) -> Dict:
        kbs = self._load("knowledge_bases")
        data["created_at"] = datetime.utcnow().isoformat()
        data["doc_count"] = 0
        kbs[kb_id] = data
        self._save("knowledge_bases", kbs)
        return data
    
    def get_kb(self, kb_id: str) -> Optional[Dict]:
        kbs = self._load("knowledge_bases")
        return kbs.get(kb_id)
    
    def list_kbs(self) -> list:
        kbs = self._load("knowledge_bases")
        return list(kbs.values())
    
    def update_kb(self, kb_id: str, data: Dict) -> bool:
        kbs = self._load("knowledge_bases")
        if kb_id in kbs:
            kbs[kb_id].update(data)
            self._save("knowledge_bases", kbs)
            return True
        return False
    
    def delete_kb(self, kb_id: str) -> bool:
        kbs = self._load("knowledge_bases")
        if kb_id in kbs:
            del kbs[kb_id]
            self._save("knowledge_bases", kbs)
            return True
        return False
    
    # ========== 文档 ==========
    
    def create_doc(self, doc_id: str, data: Dict) -> Dict:
        docs = self._load("documents")
        data["created_at"] = datetime.utcnow().isoformat()
        data["status"] = "indexed"
        docs[doc_id] = data
        self._save("documents", docs)
        
        # 更新 KB 计数
        kb_id = data.get("kb_id")
        if kb_id:
            kbs = self._load("knowledge_bases")
            if kb_id in kbs:
                kbs[kb_id]["doc_count"] = kbs[kb_id].get("doc_count", 0) + 1
                self._save("knowledge_bases", kbs)
        
        return data
    
    def get_doc(self, doc_id: str) -> Optional[Dict]:
        docs = self._load("documents")
        return docs.get(doc_id)
    
    def list_docs(self, kb_id: str = None, skip: int = 0, limit: int = 100) -> list:
        docs = self._load("documents")
        if kb_id:
            docs = [d for d in docs.values() if d.get("kb_id") == kb_id]
        return list(docs.values())[skip:skip+limit]
    
    def delete_doc(self, doc_id: str) -> bool:
        docs = self._load("documents")
        if doc_id in docs:
            kb_id = docs[doc_id].get("kb_id")
            del docs[doc_id]
            self._save("documents", docs)
            
            # 更新 KB 计数
            if kb_id:
                kbs = self._load("knowledge_bases")
                if kb_id in kbs:
                    kbs[kb_id]["doc_count"] = max(0, kbs[kb_id].get("doc_count", 1) - 1)
                    self._save("knowledge_bases", kbs)
            
            return True
        return False
    
    # ========== 会话 ==========
    
    def create_conversation(self, conv_id: str, data: Dict) -> Dict:
        convs = self._load("conversations")
        data["created_at"] = datetime.utcnow().isoformat()
        convs[conv_id] = data
        self._save("conversations", convs)
        return data
    
    def get_conversation(self, conv_id: str) -> Optional[Dict]:
        convs = self._load("conversations")
        return convs.get(conv_id)
    
    def list_conversations(self, kb_id: str = None) -> list:
        convs = self._load("conversations")
        if kb_id:
            convs = [c for c in convs.values() if c.get("kb_id") == kb_id]
        return list(convs.values())
    
    # ========== 分享 ==========
    
    def create_share(self, share_id: str, data: Dict) -> Dict:
        shares = self._load("shares")
        data["created_at"] = datetime.utcnow().isoformat()
        data["view_count"] = 0
        data["is_active"] = True
        shares[share_id] = data
        self._save("shares", shares)
        return data
    
    def get_share(self, share_id: str) -> Optional[Dict]:
        shares = self._load("shares")
        return shares.get(share_id)
    
    def list_shares(self, kb_id: str = None) -> list:
        shares = self._load("shares")
        if kb_id:
            shares = [s for s in shares.values() if s.get("resource_id") == kb_id]
        return list(shares.values())
    
    def delete_share(self, share_id: str) -> bool:
        shares = self._load("shares")
        if share_id in shares:
            del shares[share_id]
            self._save("shares", shares)
            return True
        return False
    
    # ========== 统计 ==========
    
    def increment_stat(self, stat_type: str, key: str, value: int = 1):
        """增加统计"""
        stats = self._load("stats")
        if stat_type not in stats:
            stats[stat_type] = {}
        if key not in stats[stat_type]:
            stats[stat_type][key] = 0
        stats[stat_type][key] += value
        self._save("stats", stats)
    
    def get_stats(self, stat_type: str) -> Dict:
        stats = self._load("stats")
        return stats.get(stat_type, {})


# 全局实例
json_store = JSONStore()
