"""
WebSocket 实时通信服务
"""
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import json
import asyncio
from collections import defaultdict

from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger


class MessageType(str, Enum):
    """消息类型"""
    CHAT = "chat"
    PROGRESS = "progress"
    NOTIFICATION = "notification"
    ERROR = "error"
    TYPING = "typing"
    PRESENCE = "presence"
    DOCUMENT_UPDATE = "document_update"


@dataclass
class WebSocketMessage:
    """WebSocket 消息"""
    type: MessageType
    payload: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    conversation_id: Optional[str] = None


class ConnectionManager:
    """WebSocket 连接管理器"""
    
    def __init__(self):
        # conversation_id -> set of WebSocket
        self.active_connections: Dict[str, set] = defaultdict(set)
        # user_id -> WebSocket
        self.user_connections: Dict[str, WebSocket] = {}
        # websocket -> user_id
        self.connection_users: Dict[WebSocket, str] = {}
    
    async def connect(
        self,
        websocket: WebSocket,
        user_id: str,
        conversation_id: Optional[str] = None
    ):
        """建立连接"""
        await websocket.accept()
        
        self.user_connections[user_id] = websocket
        self.connection_users[websocket] = user_id
        
        if conversation_id:
            self.active_connections[conversation_id].add(websocket)
            # 通知其他人
            await self.broadcast_presence(conversation_id, user_id, "joined")
    
    async def disconnect(
        self,
        websocket: WebSocket,
        user_id: str,
        conversation_id: Optional[str] = None
    ):
        """断开连接"""
        if websocket in self.user_connections:
            del self.user_connections[user_id]
        
        if websocket in self.connection_users:
            del self.connection_users[websocket]
        
        if conversation_id and websocket in self.active_connections[conversation_id]:
            self.active_connections[conversation_id].remove(websocket)
            await self.broadcast_presence(conversation_id, user_id, "left")
    
    async def send_personal_message(
        self,
        message: WebSocketMessage,
        user_id: str
    ):
        """发送个人消息"""
        if user_id in self.user_connections:
            websocket = self.user_connections[user_id]
            try:
                await websocket.send_json(message.__dict__)
            except Exception as e:
                logger.error(f"Send message error: {e}")
    
    async def broadcast(
        self,
        message: WebSocketMessage,
        conversation_id: str
    ):
        """广播到会话"""
        connections = self.active_connections.get(conversation_id, set())
        
        for connection in connections:
            try:
                await connection.send_json(message.__dict__)
            except Exception as e:
                logger.error(f"Broadcast error: {e}")
    
    async def broadcast_presence(
        self,
        conversation_id: str,
        user_id: str,
        status: str
    ):
        """广播在线状态"""
        message = WebSocketMessage(
            type=MessageType.PRESENCE,
            payload={"user_id": user_id, "status": status},
            conversation_id=conversation_id
        )
        await self.broadcast(message, conversation_id)
    
    async def broadcast_notification(
        self,
        title: str,
        body: str,
        user_ids: Optional[List[str]] = None
    ):
        """发送通知"""
        message = WebSocketMessage(
            type=MessageType.NOTIFICATION,
            payload={"title": title, "body": body}
        )
        
        if user_ids:
            for user_id in user_ids:
                await self.send_personal_message(message, user_id)
        else:
            # 广播给所有人
            for user_id in self.user_connections:
                await self.send_personal_message(message, user_id)
    
    def get_online_users(self, conversation_id: str) -> List[str]:
        """获取在线用户"""
        connections = self.active_connections.get(conversation_id, set())
        return [
            self.connection_users.get(conn)
            for conn in connections
            if self.connection_users.get(conn)
        ]


# 全局连接管理器
manager = ConnectionManager()


# ==================== WebSocket 端点 ====================

from fastapi import APIRouter, Depends
from app.auth import get_current_user

router = APIRouter()


@router.websocket("/ws/chat/{conversation_id}")
async def websocket_chat(
    websocket: WebSocket,
    conversation_id: str,
    user_id: str = "anonymous"  # TODO: 从 token 获取
):
    """聊天 WebSocket"""
    await manager.connect(websocket, user_id, conversation_id)
    
    try:
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type", "chat")
            
            if message_type == "chat":
                # 转发消息给其他人
                message = WebSocketMessage(
                    type=MessageType.CHAT,
                    payload=data.get("payload", {}),
                    conversation_id=conversation_id
                )
                await manager.broadcast(message, conversation_id)
            
            elif message_type == "typing":
                # 广播打字状态
                await manager.broadcast(
                    WebSocketMessage(
                        type=MessageType.TYPING,
                        payload={"user_id": user_id, "is_typing": data.get("is_typing", False)},
                        conversation_id=conversation_id
                    ),
                    conversation_id
                )
    
    except WebSocketDisconnect:
        await manager.disconnect(websocket, user_id, conversation_id)


@router.websocket("/ws/notifications")
async def websocket_notifications(
    websocket: WebSocket,
    user_id: str = "anonymous"
):
    """通知 WebSocket (个人)"""
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            data = await websocket.receive_json()
            # 处理个人消息
            pass
    
    except WebSocketDisconnect:
        await manager.disconnect(websocket, user_id)


# ==================== 通知服务 ====================

class NotificationService:
    """通知服务"""
    
    @staticmethod
    async def notify_document_uploaded(
        kb_id: str,
        doc_title: str,
        user_ids: List[str]
    ):
        """通知文档上传"""
        await manager.broadcast_notification(
            title="文档上传完成",
            body=f"「{doc_title}」已成功上传并索引",
            user_ids=user_ids
        )
    
    @staticmethod
    async def notify_mention(
        mentioned_user_id: str,
        from_user: str,
        document_id: str,
        context: str
    ):
        """通知被提及"""
        await manager.send_personal_message(
            WebSocketMessage(
                type=MessageType.NOTIFICATION,
                payload={
                    "title": "你被提及",
                    "body": f"{from_user} 在文档中提及了你",
                    "data": {"document_id": document_id, "context": context}
                }
            ),
            mentioned_user_id
        )
    
    @staticmethod
    async def notify_invitation(
        user_id: str,
        org_name: str,
        inviter: str
    ):
        """通知邀请"""
        await manager.send_personal_message(
            WebSocketMessage(
                type=MessageType.NOTIFICATION,
                payload={
                    "title": "加入组织",
                    "body": f"{inviter} 邀请你加入 {org_name}",
                    "action": "accept_invitation"
                }
            ),
            user_id
        )


# ==================== SSE 备用方案 ====================

from sse_starlette.sse import EventSourceResponse
from fastapi import Request


async def notification_stream(request: Request):
    """SSE 通知流"""
    async def event_generator():
        queue = asyncio.Queue()
        
        # TODO: 将队列注册到管理器
        
        try:
            while True:
                if await request.is_disconnected():
                    break
                
                message = await asyncio.wait_for(queue.get(), timeout=30)
                yield message
        except asyncio.TimeoutError:
            yield {"event": "heartbeat", "data": "ping"}
    
    return EventSourceResponse(event_generator())
