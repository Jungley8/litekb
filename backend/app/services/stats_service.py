"""
统计服务
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class StatsSummary:
    """统计摘要"""

    total_kbs: int
    total_docs: int
    total_chunks: int
    total_conversations: int
    storage_used_mb: float


@dataclass
class UsageTrend:
    """使用趋势"""

    date: str
    count: int
    type: str  # docs, conversations, searches


class StatsService:
    """统计服务"""

    def get_summary(self, org_id: str) -> StatsSummary:
        """获取统计摘要"""
        # TODO: 从数据库查询
        return StatsSummary(
            total_kbs=5,
            total_docs=128,
            total_chunks=1250,
            total_conversations=342,
            storage_used_mb=156.5,
        )

    def get_usage_trends(self, org_id: str, days: int = 30) -> List[UsageTrend]:
        """获取使用趋势"""
        trends = []
        today = datetime.utcnow()

        for i in range(days):
            date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            trends.append(UsageTrend(date=date, count=10 + (i % 7) * 5, type="mixed"))

        return list(reversed(trends))

    def get_popular_docs(self, org_id: str, limit: int = 10) -> List[Dict]:
        """获取热门文档"""
        return [
            {"id": "1", "title": "AI 入门指南", "views": 1250},
            {"id": "2", "title": "Transformer 详解", "views": 980},
            {"id": "3", "title": "RAG 最佳实践", "views": 756},
        ][:limit]

    def get_popular_searches(self, org_id: str, limit: int = 10) -> List[Dict]:
        """获取热门搜索"""
        return [
            {"query": "注意力机制", "count": 256},
            {"query": "BERT", "count": 189},
            {"query": "GPT", "count": 156},
        ][:limit]

    def get_response_stats(self, org_id: str) -> Dict[str, Any]:
        """获取回答统计"""
        return {
            "avg_response_time": 1.2,  # 秒
            "avg_sources_used": 3.5,
            "satisfaction_rate": 0.92,
            "total_questions": 1250,
            "this_week": 342,
        }

    def get_activity_heatmap(self, org_id: str, days: int = 28) -> Dict[str, Any]:
        """获取活动热力图数据"""
        heatmap = {}
        today = datetime.utcnow()

        for i in range(days):
            date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            heatmap[date] = {"documents": 5 + (i % 10), "conversations": 10 + (i % 15)}

        return heatmap

    def get_resources_by_type(self, org_id: str) -> Dict[str, int]:
        """按类型统计资源"""
        return {"pdf": 45, "docx": 32, "txt": 28, "md": 23, "other": 5}


# 全局实例
stats_service = StatsService()
