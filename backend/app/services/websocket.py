"""
WebSocket 服务
"""
from typing import Dict, Set, Optional
from loguru import logger
from datetime import datetime


class ConnectionManager:
    """WebSocket 连接管理器"""
    
    def __init__(self):
        # user_id -> set of connections
        self.active_connections: Dict[str, Set] = {}
        # connection_id -> connection_info
        self.connections: Dict[str, Dict] = {}
    
    async def connect(
        self,
        websocket,
        user_id: str = "anonymous",
        kb_id: Optional[str] = None,
    ):
        """建立连接"""
        
        connection_id = f"{user_id}_{datetime.now().timestamp()}"
        
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(connection_id)
        self.connections[connection_id] = {
            "websocket": websocket,
            "user_id": user_id,
            "kb_id": kb_id,
            "connected_at": datetime.now(),
        }
        
        logger.info(f"WebSocket connected: {connection_id}")
        
        return connection_id
    
    async def disconnect(self, connection_id: str):
        """断开连接"""
        
        if connection_id in self.connections:
            info = self.connections[connection_id]
            user_id = info.get("user_id")
            
            if user_id and user_id in self.active_connections:
                self.active_connections[user_id].discard(connection_id)
            
            del self.connections[connection_id]
            
            logger.info(f"WebSocket disconnected: {connection_id}")
    
    async def send_personal_message(
        self,
        message: str,
        user_id: str,
    ):
        """发送消息给用户"""
        
        if user_id in self.active_connections:
            for connection_id in self.active_connections[user_id]:
                if connection_id in self.connections:
                    ws = self.connections[connection_id]["websocket"]
                    await ws.send_text(message)
    
    async def broadcast_to_kb(
        self,
        message: str,
        kb_id: str,
        exclude_user: Optional[str] = None,
    ):
        """广播到知识库"""
        
        for connection_id, info in self.connections.items():
            if info.get("kb_id") == kb_id:
                if exclude_user and info.get("user_id") == exclude_user:
                    continue
                
                ws = info["websocket"]
                await ws.send_text(message)
    
    async def broadcast(self, message: str):
        """广播到所有连接"""
        
        for info in self.connections.values():
            ws = info["websocket"]
            await ws.send_text(message)
    
    def get_connection_count(self, user_id: Optional[str] = None) -> int:
        """获取连接数"""
        
        if user_id:
            return len(self.active_connections.get(user_id, set()))
        
        return len(self.connections)
    
    def get_online_users(self) -> List[str]:
        """获取在线用户"""
        
        return list(self.active_connections.keys())


# 全局实例
manager = ConnectionManager()


# SSE 事件类型
class SSEEvents:
    """SSE 事件类型"""
    
    CHUNK = "chunk"
    SOURCES = "sources"
    DONE = "done"
    ERROR = "error"
    PROGRESS = "progress"
    NOTIFICATION = "notification"
    
    @classmethod
    def chunk(cls, data: str) -> str:
        return f"event: {cls.CHUNK}\ndata: {data}\n\n"
    
    @classmethod
    def sources(cls, sources: list) -> str:
        import json
        return f"event: {cls.SOURCES}\ndata: {json.dumps({'sources': sources})}\n\n"
    
    @classmethod
    def done(cls) -> str:
        return f"event: {cls.DONE}\n\n"
    
    @classmethod
    def error(cls, message: str) -> str:
        import json
        return f"event: {cls.ERROR}\ndata: {json.dumps({'detail': message})}\n\n"
