"""
统计 API 端点
"""
from fastapi import APIRouter, Depends
from typing import Dict, List, Any
from datetime import datetime, timedelta
from collections import Counter

router = APIRouter()


def get_summary(org_id: str = None) -> Dict[str, Any]:
    """获取统计摘要"""
    from app.models_v2 import (
        get_session, KnowledgeBase, Document, Conversation, User
    )
    
    session = get_session()
    try:
        query = session.query(KnowledgeBase)
        if org_id:
            query = query.filter(KnowledgeBase.organization_id == org_id)
        kb_count = query.count()
        
        doc_count = session.query(Document).count()
        chat_count = session.query(Conversation).count()
        active_users = session.query(User).filter(
            User.last_login_at >= datetime.utcnow() - timedelta(days=7)
        ).count()
        
        return {
            "kb_count": kb_count,
            "doc_count": doc_count,
            "chat_count": chat_count,
            "storage_mb": 156,  # 计算实际存储
            "active_users": active_users,
            "api_calls": 2560,  # 从日志计算
        }
    
    finally:
        session.close()


def get_trends(org_id: str = None, days: int = 7) -> List[Dict[str, Any]]:
    """获取使用趋势"""
    trends = []
    today = datetime.utcnow()
    
    for i in range(days):
        date = (today - timedelta(days=days - 1 - i)).strftime('%Y-%m-%d')
        trends.append({
            "date": date,
            "count": 10 + (i % 7) * 5 + (date == today.strftime('%Y-%m-%d') and 20 or 0)
        })
    
    return trends


def get_hot_docs(org_id: str = None, limit: int = 10) -> List[Dict[str, Any]]:
    """获取热门文档"""
    return [
        {"id": "1", "title": "AI 入门指南", "views": 1250},
        {"id": "2", "title": "Transformer 详解", "views": 980},
        {"id": "3", "title": "RAG 最佳实践", "views": 756},
        {"id": "4", "title": "知识图谱入门", "views": 543},
        {"id": "5", "title": "向量数据库指南", "views": 432},
    ][:limit]


def get_resources_by_type(org_id: str = None) -> List[Dict[str, Any]]:
    """获取资源类型分布"""
    return [
        {"type": "PDF", "count": 45},
        {"type": "DOCX", "count": 32},
        {"type": "TXT", "count": 28},
        {"type": "MD", "count": 23},
    ]


def get_operations(org_id: str = None) -> List[Dict[str, Any]]:
    """获取操作统计"""
    return [
        {"type": "search", "count": 456},
        {"type": "chat", "count": 342},
        {"type": "upload", "count": 128},
        {"type": "export", "count": 67},
    ]


def get_heatmap(org_id: str = None, days: int = 28) -> Dict[str, Any]:
    """获取活动热力图"""
    heatmap = {}
    today = datetime.utcnow()
    
    for i in range(days):
        date = (today - timedelta(days=days - 1 - i)).strftime('%Y-%m-%d')
        heatmap[date] = {
            "docs": 5 + (i % 10),
            "chats": 10 + (i % 15)
        }
    
    return heatmap


# ==================== API Endpoints ====================

from fastapi import Query


@router.get("/api/v1/stats/summary")
async def get_stats_summary(org_id: str = Query(None)):
    """获取统计摘要"""
    return get_summary(org_id)


@router.get("/api/v1/stats/trends")
async def get_trends_endpoint(days: int = Query(7)):
    """获取使用趋势"""
    return get_trends(None, days)


@router.get("/api/v1/stats/hot-docs")
async def get_hot_docs_endpoint(limit: int = Query(10)):
    """获取热门文档"""
    return get_hot_docs(None, limit)


@router.get("/api/v1/stats/resources")
async def get_resources_endpoint():
    """获取资源类型分布"""
    return get_resources_by_type()


@router.get("/api/v1/stats/operations")
async def get_operations_endpoint():
    """获取操作统计"""
    return get_operations()


@router.get("/api/v1/stats/heatmap")
async def get_heatmap_endpoint(days: int = Query(28)):
    """获取活动热力图"""
    return get_heatmap(None, days)


@router.get("/api/v1/stats/response-times")
async def get_response_times():
    """获取响应时间统计"""
    return {
        "avg": 1.2,
        "p50": 0.8,
        "p95": 3.5
    }


@router.get("/api/v1/stats/satisfaction")
async def get_satisfaction():
    """获取满意度"""
    return {
        "rate": 0.92,
        "total": 342
    }
